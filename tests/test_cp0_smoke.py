"""CP0 smoke tests for core determinism, headless CLI, and 3D web router."""

from __future__ import annotations

from http import HTTPStatus
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dao_den_long.core.engine import HelloSimulation, SimConfig  # noqa: E402
from dao_den_long.web.server import SimulationSession, dispatch_request  # noqa: E402


class TestCP0Smoke(unittest.TestCase):
    def test_core_determinism(self) -> None:
        sim_a = HelloSimulation(SimConfig(seed=123))
        sim_b = HelloSimulation(SimConfig(seed=123))
        for tick in range(60):
            action = {"pulse": True} if tick == 10 else None
            sim_a.step(action)
            sim_b.step(action)

        snap_a = sim_a.snapshot()
        snap_b = sim_b.snapshot()
        self.assertEqual(snap_a, snap_b)
        self.assertEqual(snap_a["tick"], 60)
        self.assertEqual(len(snap_a["fireflies"]), 5)

    def test_headless_cli_deterministic_json(self) -> None:
        cmd = [sys.executable, "run.py", "headless", "--seed", "42", "--ticks", "30"]
        proc1 = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, check=False)
        proc2 = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, check=False)

        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(proc1.stdout, proc2.stdout)

        data = json.loads(proc1.stdout.decode("utf-8"))
        self.assertEqual(data["phase"], "cp0")
        self.assertEqual(data["seed"], 42)
        self.assertEqual(data["tick"], 30)

    def test_web_router_health_api_and_static(self) -> None:
        session = SimulationSession(seed=42)

        status, ctype, body = dispatch_request(session, "GET", "/health")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("application/json", ctype)
        self.assertEqual(json.loads(body.decode("utf-8")), {"status": "ok", "phase": "cp0"})

        status, ctype, body = dispatch_request(session, "GET", "/")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("text/html", ctype)
        self.assertIn("Đảo Đèn Lồng", body.decode("utf-8"))

        status, ctype, body = dispatch_request(session, "GET", "/static/app.js")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("application/javascript", ctype)
        self.assertIn("initWebGL2", body.decode("utf-8"))

        status, _, body = dispatch_request(session, "GET", "/api/state?step=0")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(json.loads(body.decode("utf-8"))["tick"], 0)

        status, _, body = dispatch_request(session, "GET", "/api/state")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(json.loads(body.decode("utf-8"))["tick"], 1)

        status, _, body = dispatch_request(session, "POST", "/api/pulse")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertGreater(json.loads(body.decode("utf-8"))["lantern"]["glow"], 1.0)

        status, _, body = dispatch_request(session, "POST", "/api/reset")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(json.loads(body.decode("utf-8"))["tick"], 0)

        status, _, _ = dispatch_request(session, "GET", "/static/../server.py")
        self.assertEqual(status, HTTPStatus.NOT_FOUND)

        status, _, _ = dispatch_request(session, "GET", "/unknown")
        self.assertEqual(status, HTTPStatus.NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
