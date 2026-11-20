"""Zero-dependency HTTP server serving the 3D WebGL2 scene and simulation API."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from dao_den_long.core.engine import HelloSimulation, SimConfig

STATIC_DIR = Path(__file__).resolve().parent / "static"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}


class SimulationSession:
    """Thread-safe wrapper around the deterministic simulation."""

    def __init__(self, seed: int = 42) -> None:
        self._lock = threading.Lock()
        self._sim = HelloSimulation(SimConfig(seed=seed))

    def snapshot(self, *, step: bool = True, action: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            if step:
                self._sim.step(action=action)
            return self._sim.snapshot()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._sim.reset()
            return self._sim.snapshot()


def _json_response(status: HTTPStatus, payload: dict[str, Any]) -> tuple[HTTPStatus, str, bytes]:
    body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    return status, "application/json; charset=utf-8", body


def dispatch_request(
    session: SimulationSession,
    method: str,
    target_path: str,
) -> tuple[HTTPStatus, str, bytes]:
    """Pure HTTP router returning (status, content_type, body_bytes)."""
    parsed = urlparse(target_path)
    route = parsed.path

    if method == "GET":
        if route == "/health":
            return _json_response(HTTPStatus.OK, {"status": "ok", "phase": "cp0"})

        if route == "/api/state":
            query = parse_qs(parsed.query)
            should_step = query.get("step", ["1"])[0] != "0"
            return _json_response(HTTPStatus.OK, session.snapshot(step=should_step))

        if route == "/":
            index_file = STATIC_DIR / "index.html"
            if index_file.is_file():
                return HTTPStatus.OK, CONTENT_TYPES[".html"], index_file.read_bytes()
            return _json_response(HTTPStatus.NOT_FOUND, {"error": "index.html missing"})

        if route.startswith("/static/"):
            rel = unquote(route[len("/static/"):]).lstrip("/")
            static_root = STATIC_DIR.resolve()
            target = (static_root / rel).resolve()
            if not target.is_relative_to(static_root) or not target.is_file():
                return _json_response(HTTPStatus.NOT_FOUND, {"error": "asset not found"})
            content_type = CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
            return HTTPStatus.OK, content_type, target.read_bytes()

        return _json_response(HTTPStatus.NOT_FOUND, {"error": "not found"})

    if method == "POST":
        if route == "/api/pulse":
            return _json_response(HTTPStatus.OK, session.snapshot(step=True, action={"pulse": True}))
        if route == "/api/reset":
            return _json_response(HTTPStatus.OK, session.reset())
        return _json_response(HTTPStatus.NOT_FOUND, {"error": "not found"})

    return _json_response(HTTPStatus.NOT_FOUND, {"error": "not found"})


class _LanternHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_cls: type[BaseHTTPRequestHandler],
        session: SimulationSession,
        quiet: bool,
    ) -> None:
        self.session = session
        self.quiet = quiet
        super().__init__(server_address, handler_cls)


class _LanternRequestHandler(BaseHTTPRequestHandler):
    server: _LanternHTTPServer

    def log_message(self, format: str, *args: object) -> None:
        if not self.server.quiet:
            super().log_message(format, *args)

    def _handle(self, method: str) -> None:
        status, content_type, body = dispatch_request(self.server.session, method, self.path)
        cache_control = "no-store" if content_type.startswith("application/json") else "no-cache"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", cache_control)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    seed: int = 42,
    quiet: bool = False,
) -> tuple[ThreadingHTTPServer, int]:
    """Create and bind the HTTP server, returning (server, actual_port)."""
    session = SimulationSession(seed=seed)
    server = _LanternHTTPServer((host, port), _LanternRequestHandler, session, quiet)
    return server, int(server.server_address[1])


def serve(host: str = "127.0.0.1", port: int = 8000, *, seed: int = 42) -> None:
    """Start blocking HTTP server until interrupted."""
    server, actual_port = create_server(host=host, port=port, seed=seed, quiet=False)
    print(f"Dao Den Long 3D running at http://{host}:{actual_port} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
