"""Unit and CLI tests for Phase 4 (TICKET-04 / Test Contract v1.3):
- Standardized 1280x720 Benchmark scene, camera orbit, formulas, and CLI (`run.py bench`)
- Multi-night in-process Soak test & RSS memory stability (`run.py soak`)
- Persistent Local Leaderboard, tie-breaking, Vietnamese/ASCII validation, HTTP API, and CLI (`run.py --export-leaderboard`)
- Accessibility: key remapping + conflict detection, subtitles & shade edge arrow, reduced motion, >=18px + x1.25 font size
"""

from __future__ import annotations

from http import HTTPStatus
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dao_den_long.ops import (  # noqa: E402
    LeaderboardStore,
    benchmark_camera_pose,
    build_benchmark_simulation,
    compute_bench_metrics,
    step_benchmark_wander,
    validate_player_name,
)
from dao_den_long.web.server import SimulationSession, dispatch_request  # noqa: E402


class TestPhase4Features(unittest.TestCase):
    def test_benchmark_scene_camera_orbit_and_metrics_formula(self) -> None:
        sim = build_benchmark_simulation(seed=42)
        self.assertEqual(sim.night, 1)
        self.assertEqual([sim.player.x, sim.player.y, sim.player.z], [0.0, 0.0, 0.0])
        self.assertEqual(len(sim.shades), 200)
        self.assertTrue(all(s.state == "wander" for s in sim.shades))
        self.assertEqual(len(sim.motes), 100)

        lit_ids = [l.id for l in sim.lanterns if l.lit]
        self.assertEqual(lit_ids, ["L1", "L2", "L3"])
        self.assertTrue(all(l.fuel_60 == 6000 for l in sim.lanterns if l.lit))

        # Step 120 ticks of benchmark wander: shades move, but no spawns, no damage, no pickup, no fuel decay, no game_over
        init_pos = [(s.x, s.z) for s in sim.shades]
        for _ in range(120):
            step_benchmark_wander(sim)
        moved_pos = [(s.x, s.z) for s in sim.shades]
        self.assertNotEqual(init_pos, moved_pos)
        self.assertEqual(len(sim.shades), 200)
        self.assertEqual(len(sim.motes), 100)
        self.assertEqual(sim.player.flames, 3)
        self.assertEqual(sim.player.carried, 0)
        self.assertTrue(all(l.fuel_60 == 6000 for l in sim.lanterns if l.lit))
        self.assertEqual(sim.state, "playing")

        # Camera orbit: r=30m, Y=15m, looks at (0,0,0), starts at 0 deg (30,15,0), CCW 15s period
        eye0, tgt0 = benchmark_camera_pose(0.0)
        self.assertEqual(tgt0, (0.0, 0.0, 0.0))
        self.assertAlmostEqual(eye0[0], 30.0, places=4)
        self.assertAlmostEqual(eye0[1], 15.0, places=4)
        self.assertAlmostEqual(eye0[2], 0.0, places=4)

        eye_q1, _ = benchmark_camera_pose(3.75)  # 90 deg CCW
        self.assertAlmostEqual(eye_q1[0], 0.0, places=4)
        self.assertAlmostEqual(eye_q1[1], 15.0, places=4)
        self.assertAlmostEqual(eye_q1[2], 30.0, places=4)

        eye_full, _ = benchmark_camera_pose(15.0)
        self.assertAlmostEqual(eye_full[0], 30.0, places=4)
        self.assertAlmostEqual(eye_full[2], 0.0, places=4)

        # Exact metrics formula check: N=100 frames (99 frames at 10ms, 1 frame at 20ms)
        dts = [10.0] * 99 + [20.0]
        m = compute_bench_metrics(
            dts_ms=dts,
            load_ms=420.0,
            peak_mem_mb=32.5,
            vsync_off=True,
            renderer="TestRenderer 1.0",
        )
        self.assertEqual(m["contract_version"], "1.3")
        self.assertEqual(m["frames"], 100)
        self.assertAlmostEqual(m["avg_fps"], round(1000.0 * 100 / 1010.0, 1), places=1)
        # k = max(1, ceil(0.01 * 100)) = 1 -> worst dt = 20.0ms -> p1_low_fps = 1000 / 20 = 50.0
        self.assertEqual(m["p1_low_fps"], 50.0)
        self.assertEqual(m["frame_ms_p95"], 10.0)
        self.assertEqual(m["load_ms"], 420.0)
        self.assertEqual(m["peak_mem_mb"], 32.5)
        self.assertTrue(m["vsync_off"])

    def test_bench_cli_and_soak_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            bench_out = tmp_dir / "bench_test.json"
            env = dict(os.environ, DAO_DEN_LONG_BENCH_NO_BROWSER="1")

            # Run benchmark CLI (3s warmup + 1s measurement)
            res_b = subprocess.run(
                [sys.executable, "run.py", "bench", "--seed", "42", "--duration", "1", "--out", str(bench_out)],
                cwd=ROOT_DIR,
                env=env,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_b.returncode, 0, msg=res_b.stderr.decode("utf-8", errors="replace"))
            b_data = json.loads(bench_out.read_text(encoding="utf-8"))
            self.assertEqual(b_data["contract_version"], "1.3")
            self.assertGreaterEqual(b_data["avg_fps"], 60.0)
            self.assertGreaterEqual(b_data["p1_low_fps"], 30.0)
            self.assertLessEqual(b_data["load_ms"], 10000.0)
            self.assertGreater(b_data["frames"], 50)
            self.assertIsNotNone(b_data["peak_mem_mb"])
            self.assertTrue(b_data["vsync_off"])

            # Invalid bench duration -> exit code 2
            res_b_err = subprocess.run(
                [sys.executable, "run.py", "bench", "--seed", "42", "--duration", "0", "--out", str(bench_out)],
                cwd=ROOT_DIR,
                env=env,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_b_err.returncode, 2)

            # Run soak CLI (4 consecutive nights in-process)
            soak_out = tmp_dir / "soak_test.json"
            res_s = subprocess.run(
                [sys.executable, "run.py", "soak", "--seed", "7", "--nights", "4", "--out", str(soak_out)],
                cwd=ROOT_DIR,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_s.returncode, 0, msg=res_s.stderr.decode("utf-8", errors="replace"))
            s_data = json.loads(soak_out.read_text(encoding="utf-8"))
            self.assertEqual(s_data["nights"], 4)
            self.assertEqual(s_data["crashes"], 0)
            self.assertEqual(len(s_data["results"]), 4)
            self.assertTrue(all(r in ("won", "lost") for r in s_data["results"]))
            self.assertGreater(s_data["mem_start_mb"], 0)
            self.assertLessEqual(s_data["mem_end_mb"], 1.2 * s_data["mem_start_mb"])
            self.assertGreater(s_data["duration_s"], 0)

            # Verify committed bench.json and soak.json at repo root if present
            for root_file, key_check in (("bench.json", "avg_fps"), ("soak.json", "mem_end_mb")):
                rf = ROOT_DIR / root_file
                if rf.is_file():
                    loaded = json.loads(rf.read_text(encoding="utf-8"))
                    self.assertIn(key_check, loaded)

    def test_leaderboard_persistence_sorting_tiebreak_api_and_export_cli(self) -> None:
        # Name validation (3-12 ASCII [A-Za-z0-9_] + Vietnamese accented support)
        self.assertEqual(validate_player_name("May_01"), "May_01")
        self.assertEqual(validate_player_name("Mây_ĐảoĐèn"), "Mây_ĐảoĐèn")
        for bad in ("ab", "abcdefghijklm", "bad name", "may@123", ""):
            with self.assertRaises(ValueError):
                validate_player_name(bad)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            lb_file = tmp_dir / "leaderboard.json"
            export_file = tmp_dir / "exported.json"
            store = LeaderboardStore(path=lb_file)

            # Insert 12 entries including a score tie (1500) to verify stable chronological tie-break and top-10 cap
            store.add_entry(name="First_1500", score=1500, nights_won=2, seed=42, achieved_at="2026-11-20T10:00:00+07:00")
            store.add_entry(name="Second_1500", score=1500, nights_won=2, seed=43, achieved_at="2026-11-20T10:05:00+07:00")
            for idx in range(10):
                store.add_entry(
                    name=f"Player_{idx:02d}",
                    score=100 * (idx + 1),
                    nights_won=idx % 4,
                    seed=10 + idx,
                    achieved_at=f"2026-11-20T11:{idx:02d}:00+07:00",
                )

            # Reload from disk to verify persistence across restarts
            reloaded = LeaderboardStore(path=lb_file).load_entries()
            self.assertEqual(len(reloaded), 10)
            self.assertEqual(reloaded[0]["name"], "First_1500")
            self.assertEqual(reloaded[1]["name"], "Second_1500")
            self.assertEqual(reloaded[2]["score"], 1000)
            self.assertEqual(reloaded[-1]["score"], 300)  # 100 and 200 dropped outside top 10

            # HTTP API /api/leaderboard GET & POST
            session = SimulationSession(seed=42, night=1, leaderboard_path=lb_file)
            st, _, body = dispatch_request(
                session,
                "POST",
                "/api/leaderboard",
                json.dumps({"name": "Top_Champion", "score": 3200, "nights_won": 3, "seed": 99}).encode("utf-8"),
            )
            self.assertEqual(st, HTTPStatus.OK)
            top_list = json.loads(body.decode("utf-8"))["entries"]
            self.assertEqual(top_list[0]["name"], "Top_Champion")
            self.assertEqual(top_list[0]["score"], 3200)

            st_bad, _, _ = dispatch_request(
                session,
                "POST",
                "/api/leaderboard",
                json.dumps({"name": "x!", "score": 100}).encode("utf-8"),
            )
            self.assertEqual(st_bad, HTTPStatus.BAD_REQUEST)

            # CLI: python run.py --export-leaderboard out.json
            env = dict(os.environ, DAO_DEN_LONG_LEADERBOARD_PATH=str(lb_file))
            res_exp = subprocess.run(
                [sys.executable, "run.py", "--export-leaderboard", str(export_file)],
                cwd=ROOT_DIR,
                env=env,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_exp.returncode, 0, msg=res_exp.stderr.decode("utf-8", errors="replace"))
            exported = json.loads(export_file.read_text(encoding="utf-8"))
            self.assertEqual(len(exported["entries"]), 10)
            self.assertEqual(exported["entries"][0]["name"], "Top_Champion")
            self.assertEqual(exported["entries"][1]["name"], "First_1500")
            self.assertEqual(exported["entries"][2]["name"], "Second_1500")

    def test_accessibility_and_bench_web_endpoints(self) -> None:
        session = SimulationSession(seed=42, night=1)

        # Benchmark init endpoint returns 200 shades + 100 motes + 3 lit lanterns
        st, _, body = dispatch_request(session, "GET", "/api/bench_init?seed=42")
        self.assertEqual(st, HTTPStatus.OK)
        bench_init = json.loads(body.decode("utf-8"))
        self.assertEqual(len(bench_init["snapshot"]["shades"]), 200)
        self.assertEqual(len(bench_init["snapshot"]["motes"]), 100)
        self.assertEqual(sum(1 for l in bench_init["snapshot"]["lanterns"] if l["lit"]), 3)

        # Verify accessibility controls in index.html, style.css, and app.js
        _, _, html_b = dispatch_request(session, "GET", "/")
        _, _, css_b = dispatch_request(session, "GET", "/static/style.css")
        _, _, js_b = dispatch_request(session, "GET", "/static/app.js")
        html_src = html_b.decode("utf-8")
        css_src = css_b.decode("utf-8")
        js_src = js_b.decode("utf-8")

        for token in (
            "input-reduced-motion",
            "input-large-text",
            "input-subtitles",
            "keybind-grid",
            "btn-reset-keys",
            "subtitle-banner",
            "shade-edge-arrow",
            "screen-leaderboard",
            "leaderboard-save-box",
        ):
            self.assertIn(token, html_src)

        self.assertIn("font-size: 18px;", css_src)
        self.assertIn("font-size: 22.5px;", css_src)
        self.assertIn("body.reduced-motion", css_src)
        self.assertIn("findKeybindConflicts", js_src)
        self.assertIn("DEFAULT_KEYBINDS", js_src)
        self.assertIn("startBrowserBenchmark", js_src)


if __name__ == "__main__":
    unittest.main()
