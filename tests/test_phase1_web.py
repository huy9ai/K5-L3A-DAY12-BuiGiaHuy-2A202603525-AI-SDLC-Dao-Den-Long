"""In-process HTTP router tests for Phase 2 3-Night campaign & fixed camera orientation."""

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
    def test_web_routes_campaign_pause_dash_and_camera_fix(self) -> None:
        session = SimulationSession(seed=42, night=1)

        status, ctype, body = dispatch_request(session, "GET", "/health")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("application/json", ctype)
        health = json.loads(body.decode("utf-8"))
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["phase"], "phase-2")
        self.assertEqual(health["contract_version"], "1.1")

        status, ctype, body = dispatch_request(session, "GET", "/")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("text/html", ctype)
        self.assertIn("Ba Hòn Đảo", body.decode("utf-8"))

        # Verify mat4LookAt right-handed fix in app.js (cross(up, z_cam) -> xx = zz, xz = -zx)
        status, _, body = dispatch_request(session, "GET", "/static/app.js")
        self.assertEqual(status, HTTPStatus.OK)
        js_src = body.decode("utf-8")
        self.assertIn("let xx = zz;", js_src)
        self.assertIn("let xz = -zx;", js_src)

        status, _, body = dispatch_request(session, "GET", "/api/state")
        self.assertEqual(status, HTTPStatus.OK)
        initial = json.loads(body.decode("utf-8"))
        self.assertEqual(initial["snapshot"]["night"], 1)
        self.assertEqual(len(initial["snapshot"]["lanterns"]), 5)

        # Tick with dash
        tick_body = json.dumps({"move": [0, 1], "cam_yaw_deg": 0, "dash": True, "steps": 3}).encode("utf-8")
        status, _, body = dispatch_request(session, "POST", "/api/tick", tick_body)
        self.assertEqual(status, HTTPStatus.OK)
        stepped = json.loads(body.decode("utf-8"))
        self.assertEqual(stepped["snapshot"]["tick"], 3)
        self.assertGreater(stepped["snapshot"]["player"]["dash_cd_s"], 0.0)

        # Pause & resume via /api/tick
        status, _, body = dispatch_request(session, "POST", "/api/tick", json.dumps({"pause": True}).encode("utf-8"))
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(json.loads(body.decode("utf-8"))["snapshot"]["state"], "paused")

        # Next night advances to Night 2 (6 lanterns)
        status, _, body = dispatch_request(session, "POST", "/api/next_night", b"{}")
        self.assertEqual(status, HTTPStatus.OK)
        night2 = json.loads(body.decode("utf-8"))
        self.assertEqual(night2["snapshot"]["night"], 2)
        self.assertEqual(len(night2["snapshot"]["lanterns"]), 6)

        # Reset to Night 3 (7 lanterns)
        status, _, body = dispatch_request(
            session, "POST", "/api/reset", json.dumps({"night": 3, "reset_campaign": True}).encode("utf-8")
        )
        self.assertEqual(status, HTTPStatus.OK)
        night3 = json.loads(body.decode("utf-8"))
        self.assertEqual(night3["snapshot"]["night"], 3)
        self.assertEqual(len(night3["snapshot"]["lanterns"]), 7)

        status, _, _ = dispatch_request(session, "GET", "/static/../server.py")
        self.assertEqual(status, HTTPStatus.NOT_FOUND)

        status, _, _ = dispatch_request(session, "POST", "/api/tick", b"{bad json")
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)


if __name__ == "__main__":
    unittest.main()
