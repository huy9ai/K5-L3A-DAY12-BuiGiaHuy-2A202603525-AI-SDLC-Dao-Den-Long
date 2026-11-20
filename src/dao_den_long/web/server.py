"""Zero-dependency HTTP server serving the 3D WebGL2 game and simulation API."""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from typing import Any
from urllib.parse import unquote, urlparse

from dao_den_long.core.config import TICK_RATE, load_tuning
from dao_den_long.core.engine import InputFrame, Night1Simulation

STATIC_DIR = Path(__file__).resolve().parent / "static"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}


class SimulationSession:
    """Thread-safe live Night 1 session driving the 3D browser client."""

    def __init__(self, seed: int = 42) -> None:
        self._lock = threading.Lock()
        self._seed = seed
        self._tuning = load_tuning()
        self._sim = Night1Simulation(seed=self._seed, tuning=self._tuning)

    def _payload(self, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "snapshot": self._sim.snapshot(),
            "tuning": asdict(self._tuning),
            "cooldowns": {
                "pulse_s": round(self._sim.player.pulse_cooldown_ticks / TICK_RATE, 3),
                "invuln_s": round(self._sim.player.invuln_ticks / TICK_RATE, 3),
            },
            "facing_yaw_deg": round(self._sim.player.facing_yaw_deg, 2),
            "events": events or [],
        }

    def state(self) -> dict[str, Any]:
        with self._lock:
            return self._payload([])

    def step_ticks(self, body: dict[str, Any]) -> dict[str, Any]:
        raw_move = body.get("move", [0.0, 0.0])
        mx = max(-1.0, min(1.0, float(raw_move[0]))) if isinstance(raw_move, (list, tuple)) and len(raw_move) == 2 else 0.0
        mz = max(-1.0, min(1.0, float(raw_move[1]))) if isinstance(raw_move, (list, tuple)) and len(raw_move) == 2 else 0.0
        cam_yaw = float(body.get("cam_yaw_deg", 0.0))
        jump = bool(body.get("jump", False))
        interact = bool(body.get("interact", False))
        pulse = bool(body.get("pulse", False))
        raw_steps = body.get("steps", 1)
        steps = max(1, min(4, int(raw_steps) if isinstance(raw_steps, (int, float)) else 1))

        inp = InputFrame(
            move=(mx, mz),
            cam_yaw_deg=cam_yaw,
            jump=jump,
            interact=interact,
            pulse=pulse,
        )
        all_events: list[dict[str, Any]] = []
        with self._lock:
            for _ in range(steps):
                if self._sim.state != "playing":
                    break
                all_events.extend(self._sim.step(inp))
            return self._payload(all_events)

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        with self._lock:
            if seed is not None:
                self._seed = int(seed)
            self._tuning = load_tuning()
            self._sim = Night1Simulation(seed=self._seed, tuning=self._tuning)
            return self._payload([])


def _json_response(status: HTTPStatus, payload: dict[str, Any]) -> tuple[HTTPStatus, str, bytes]:
    body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    return status, "application/json; charset=utf-8", body


def dispatch_request(
    session: SimulationSession,
    method: str,
    target_path: str,
    body: bytes = b"",
) -> tuple[HTTPStatus, str, bytes]:
    """Pure HTTP router returning (status, content_type, body_bytes)."""
    route = urlparse(target_path).path

    if method == "GET":
        if route == "/health":
            return _json_response(
                HTTPStatus.OK,
                {"status": "ok", "phase": "phase-1", "contract_version": "1.0"},
            )

        if route == "/api/state":
            return _json_response(HTTPStatus.OK, session.state())

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
        parsed_body: dict[str, Any] = {}
        if body.strip():
            try:
                loaded = json.loads(body.decode("utf-8"))
                if not isinstance(loaded, dict):
                    return _json_response(HTTPStatus.BAD_REQUEST, {"error": "JSON body must be object"})
                parsed_body = loaded
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                return _json_response(HTTPStatus.BAD_REQUEST, {"error": f"Invalid JSON: {exc}"})

        if route == "/api/tick":
            return _json_response(HTTPStatus.OK, session.step_ticks(parsed_body))
        if route == "/api/reset":
            raw_seed = parsed_body.get("seed")
            new_seed = int(raw_seed) if isinstance(raw_seed, int) and not isinstance(raw_seed, bool) else None
            return _json_response(HTTPStatus.OK, session.reset(seed=new_seed))
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
        req_body = b""
        if method == "POST":
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length > 0:
                req_body = self.rfile.read(min(length, 65536))

        status, content_type, resp_body = dispatch_request(
            self.server.session, method, self.path, req_body
        )
        cache_control = "no-store" if content_type.startswith("application/json") else "no-cache"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", cache_control)
        self.send_header("Content-Length", str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body)

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
