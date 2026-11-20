"""Zero-dependency HTTP server serving the 3D WebGL2 game, Leaderboard, and Benchmark API (v1.3)."""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import threading
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from dao_den_long.core.config import load_tuning
from dao_den_long.core.engine import GameSimulation, InputFrame
from dao_den_long.ops import (
    LeaderboardStore,
    build_benchmark_simulation,
    step_benchmark_wander,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".mp4": "video/mp4",
}


class SimulationSession:
    """Thread-safe 3-Night campaign, leaderboard, and benchmark session driving the 3D browser client."""

    def __init__(self, seed: int = 42, night: int = 1, leaderboard_path: Path | None = None) -> None:
        self._lock = threading.Lock()
        self._t_created = time.perf_counter()
        self._seed = seed
        self._night = night
        self._campaign_score = 0
        self._nights_won = 0
        self._night_banked = False
        self._tuning = load_tuning()
        self._sim = GameSimulation(seed=self._seed, night=self._night, tuning=self._tuning)
        self.leaderboard = LeaderboardStore(path=leaderboard_path)
        self.bench_client_connected = False
        self.bench_first_frame_ms: float | None = None
        self.bench_result: dict[str, Any] | None = None
        self.demo_capture_result: dict[str, Any] | None = None

    def _bank_if_won(self) -> None:
        if self._sim.state == "won" and not self._night_banked:
            self._campaign_score += self._sim.score
            self._nights_won = min(3, self._nights_won + 1)
            self._night_banked = True

    def _payload(self, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        self._bank_if_won()
        snap = self._sim.snapshot()
        win_needed = math.ceil(self._tuning.win_ratio * len(self._sim.lanterns) - 1e-9)
        return {
            "snapshot": snap,
            "tuning": asdict(self._tuning),
            "meta": {
                "map_name": self._sim.map_def.name,
                "intro_quote": self._sim.map_def.intro_quote,
                "win_needed": win_needed,
                "campaign_score": self._campaign_score,
                "nights_won": self._nights_won,
                "seed": self._seed,
                "wind_warning": self._sim.wind_warning,
                "facing_yaw_deg": round(self._sim.player.facing_yaw_deg, 2),
                "shades_target": {s.id: s.target_lantern_id for s in self._sim.shades if s.target_lantern_id},
                "ramps": [
                    {
                        "angle_deg": r.angle_deg,
                        "inner_r": r.inner_r,
                        "outer_r": r.outer_r,
                        "half_width": r.half_width,
                        "top_y": r.top_y,
                    }
                    for r in self._sim.map_def.ramps
                ],
                "launch_pads": [
                    {"x": p.x, "y": p.y, "z": p.z, "radius": p.radius}
                    for p in self._sim.map_def.launch_pads
                ],
                "charms_pos": [
                    {"id": c.id, "pos": [c.x, c.y, c.z], "available": c.available}
                    for c in self._sim.charms
                ],
            },
            "events": events or [],
        }

    def state(self) -> dict[str, Any]:
        with self._lock:
            return self._payload([])

    def init_benchmark(self, seed: int = 42) -> dict[str, Any]:
        with self._lock:
            self.bench_client_connected = True
            self._seed = seed
            self._night = 1
            self._tuning = load_tuning()
            self._sim = build_benchmark_simulation(seed=seed)
            if self.bench_first_frame_ms is None:
                self.bench_first_frame_ms = (time.perf_counter() - self._t_created) * 1000.0
            return self._payload([])

    def step_benchmark(self, steps: int = 1) -> dict[str, Any]:
        with self._lock:
            for _ in range(max(1, min(8, steps))):
                step_benchmark_wander(self._sim)
            return self._payload([])

    def step_ticks(self, body: dict[str, Any]) -> dict[str, Any]:
        raw_move = body.get("move", [0.0, 0.0])
        mx = max(-1.0, min(1.0, float(raw_move[0]))) if isinstance(raw_move, (list, tuple)) and len(raw_move) == 2 else 0.0
        mz = max(-1.0, min(1.0, float(raw_move[1]))) if isinstance(raw_move, (list, tuple)) and len(raw_move) == 2 else 0.0
        cam_yaw = float(body.get("cam_yaw_deg", 0.0))
        jump = bool(body.get("jump", False))
        dash = bool(body.get("dash", False))
        interact = bool(body.get("interact", False))
        pulse = bool(body.get("pulse", False))
        pause = bool(body.get("pause", False))
        raw_steps = body.get("steps", 1)
        steps = max(1, min(4, int(raw_steps) if isinstance(raw_steps, (int, float)) else 1))

        inp = InputFrame(
            move=(mx, mz),
            cam_yaw_deg=cam_yaw,
            jump=jump,
            dash=dash,
            interact=interact,
            pulse=pulse,
            pause=pause,
        )
        all_events: list[dict[str, Any]] = []
        with self._lock:
            for i in range(steps):
                if self._sim.state in ("won", "lost"):
                    break
                step_inp = inp if i == 0 else InputFrame(
                    move=inp.move,
                    cam_yaw_deg=inp.cam_yaw_deg,
                    jump=inp.jump,
                    dash=inp.dash,
                    interact=inp.interact,
                    pulse=inp.pulse,
                    pause=False,
                )
                all_events.extend(self._sim.step(step_inp))
                if self._sim.state == "paused":
                    break
            return self._payload(all_events)

    def reset(self, *, night: int | None = None, seed: int | None = None, reset_campaign: bool = False) -> dict[str, Any]:
        with self._lock:
            if reset_campaign:
                self._campaign_score = 0
                self._nights_won = 0
            if night in (1, 2, 3):
                self._night = int(night)
            if seed is not None:
                self._seed = int(seed)
            self._night_banked = False
            self._tuning = load_tuning()
            self._sim = GameSimulation(seed=self._seed, night=self._night, tuning=self._tuning)
            return self._payload([])

    def next_night(self) -> dict[str, Any]:
        with self._lock:
            self._bank_if_won()
            self._night = min(3, self._night + 1)
            self._night_banked = False
            self._tuning = load_tuning()
            self._sim = GameSimulation(seed=self._seed + self._night - 1, night=self._night, tuning=self._tuning)
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
    parsed_url = urlparse(target_path)
    route = parsed_url.path
    query = parse_qs(parsed_url.query)

    if method == "GET":
        if route == "/health":
            return _json_response(
                HTTPStatus.OK,
                {"status": "ok", "phase": "phase-4", "contract_version": "1.3"},
            )
        if route == "/api/state":
            return _json_response(HTTPStatus.OK, session.state())
        if route == "/api/leaderboard":
            return _json_response(HTTPStatus.OK, {"entries": session.leaderboard.load_entries()})
        if route == "/api/bench_init":
            raw_seed = query.get("seed", ["42"])[0]
            try:
                seed = int(raw_seed)
            except ValueError:
                seed = 42
            return _json_response(HTTPStatus.OK, session.init_benchmark(seed=seed))
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
        if route == "/api/bench_tick":
            steps = int(parsed_body.get("steps", 1)) if isinstance(parsed_body.get("steps"), (int, float)) else 1
            return _json_response(HTTPStatus.OK, session.step_benchmark(steps=steps))
        if route == "/api/bench_report":
            if session.bench_first_frame_ms is not None and "load_ms" not in parsed_body:
                parsed_body["load_ms"] = session.bench_first_frame_ms
            session.bench_result = parsed_body
            return _json_response(HTTPStatus.OK, {"status": "recorded"})
        if route == "/api/demo_capture_done":
            session.demo_capture_result = parsed_body
            return _json_response(HTTPStatus.OK, {"status": "captured"})
        if route == "/api/leaderboard":
            name = parsed_body.get("name")
            score = parsed_body.get("score", session._campaign_score)
            nights_won = parsed_body.get("nights_won", session._nights_won)
            seed = parsed_body.get("seed", session._seed)
            achieved_at = parsed_body.get("achieved_at")
            try:
                entries = session.leaderboard.add_entry(
                    name=name,
                    score=int(score),
                    nights_won=int(nights_won),
                    seed=int(seed),
                    achieved_at=str(achieved_at) if achieved_at else None,
                )
            except (ValueError, TypeError) as exc:
                return _json_response(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return _json_response(HTTPStatus.OK, {"entries": entries})
        if route == "/api/reset":
            raw_night = parsed_body.get("night")
            raw_seed = parsed_body.get("seed")
            night = int(raw_night) if isinstance(raw_night, int) and not isinstance(raw_night, bool) and raw_night in (1, 2, 3) else None
            seed = int(raw_seed) if isinstance(raw_seed, int) and not isinstance(raw_seed, bool) else None
            reset_campaign = bool(parsed_body.get("reset_campaign", False))
            return _json_response(HTTPStatus.OK, session.reset(night=night, seed=seed, reset_campaign=reset_campaign))
        if route == "/api/next_night":
            return _json_response(HTTPStatus.OK, session.next_night())
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
                req_body = self.rfile.read(min(length, 32 * 1024 * 1024))

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
) -> tuple[_LanternHTTPServer, int]:
    session = SimulationSession(seed=seed)
    server = _LanternHTTPServer((host, port), _LanternRequestHandler, session, quiet)
    return server, int(server.server_address[1])


def serve(host: str = "127.0.0.1", port: int = 8000, *, seed: int = 42) -> None:
    server, actual_port = create_server(host=host, port=port, seed=seed, quiet=False)
    print(f"Dao Den Long 3D running at http://{host}:{actual_port} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
