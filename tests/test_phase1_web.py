"""In-process HTTP router tests for the Phase 1 3D web interface."""

from __future__ import annotations

from http import HTTPStatus
import json
from pathlib import Path
import sys
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dao_den_long.web.server import SimulationSession, dispatch_request  # noqa: E402


class TestPhase1Web(unittest.TestCase):
    def test_web_routes_gameplay_tick_and_reset(self) -> None:
        session = SimulationSession(seed=42)

        status, ctype, body = dispatch_request(session, "GET", "/health")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("application/json", ctype)
        health = json.loads(body.decode("utf-8"))
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["contract_version"], "1.0")

        status, ctype, body = dispatch_request(session, "GET", "/")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("text/html", ctype)
        self.assertIn("Đảo Bến", body.decode("utf-8"))

        status, _, body = dispatch_request(session, "GET", "/static/app.js")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("initWebGL2", body.decode("utf-8"))

        status, _, body = dispatch_request(session, "GET", "/api/state")
        self.assertEqual(status, HTTPStatus.OK)
        initial = json.loads(body.decode("utf-8"))
        self.assertEqual(initial["snapshot"]["tick"], 0)
        self.assertEqual(len(initial["snapshot"]["lanterns"]), 5)

        tick_body = json.dumps({"move": [0, 1], "cam_yaw_deg": 0, "steps": 3}).encode("utf-8")
        status, _, body = dispatch_request(session, "POST", "/api/tick", tick_body)
        self.assertEqual(status, HTTPStatus.OK)
        stepped = json.loads(body.decode("utf-8"))
        self.assertEqual(stepped["snapshot"]["tick"], 3)
        self.assertGreater(stepped["snapshot"]["player"]["pos"][2], 0.0)

        status, _, body = dispatch_request(session, "POST", "/api/reset", b"{}")
        self.assertEqual(status, HTTPStatus.OK)
        reset_data = json.loads(body.decode("utf-8"))
        self.assertEqual(reset_data["snapshot"]["tick"], 0)
        self.assertEqual(reset_data["snapshot"]["player"]["pos"], [0.0, 0.0, 0.0])

        status, _, _ = dispatch_request(session, "GET", "/static/../server.py")
        self.assertEqual(status, HTTPStatus.NOT_FOUND)

        status, _, _ = dispatch_request(session, "POST", "/api/tick", b"{bad json")
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)


if __name__ == "__main__":
    unittest.main()
