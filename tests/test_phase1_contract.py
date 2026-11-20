"""Subprocess regression tests verifying Test Contract v1.1 compliance for Night 1."""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"


def run_headless_cli(*args: str, out_file: Path) -> subprocess.CompletedProcess[bytes]:
    cmd = [sys.executable, "run.py", "headless", *args, "--out", str(out_file)]
    return subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, check=False)


def parse_jsonl(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


class TestPhase1Contract(unittest.TestCase):
    def test_win_scenario_full_flow_and_determinism(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out1 = Path(tmp) / "win1.jsonl"
            out2 = Path(tmp) / "win2.jsonl"
            args = (
                "--seed", "42",
                "--night", "1",
                "--scenario", str(SCENARIOS_DIR / "win_scenario.json"),
                "--inputs", str(SCENARIOS_DIR / "win_inputs.json"),
                "--ticks", "600",
                "--snapshot-every", "10",
            )
            p1 = run_headless_cli(*args, out_file=out1)
            p2 = run_headless_cli(*args, out_file=out2)

            self.assertEqual(p1.returncode, 0, msg=p1.stderr.decode("utf-8", errors="replace"))
            self.assertEqual(p2.returncode, 0, msg=p2.stderr.decode("utf-8", errors="replace"))
            self.assertEqual(out1.read_bytes(), out2.read_bytes())

            records = parse_jsonl(out1)
            self.assertEqual(records[0]["type"], "snapshot")
            self.assertEqual(records[0]["tick"], 0)
            self.assertEqual(records[0]["night"], 1)
            self.assertEqual(records[0]["score"], 0)
            self.assertEqual(records[-1]["type"], "end")
            self.assertEqual(records[-1]["state"], "won")
            self.assertGreater(records[-1]["score"], 0)

            event_names = [r["name"] for r in records if r["type"] == "event"]
            self.assertEqual(event_names[0], "night_start")
            self.assertEqual(event_names.count("mote_picked"), 10)
            self.assertIn("pulse", event_names)
            self.assertIn("deposit", event_names)
            self.assertIn("lantern_lit", event_names)
            self.assertEqual(event_names[-1], "game_over")

            game_over = [r for r in records if r["type"] == "event" and r["name"] == "game_over"][0]
            self.assertEqual(game_over["data"], {"result": "won", "reason": "all_lit"})

    def test_lose_no_flames_and_drop_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "lose_flames.jsonl"
            res = run_headless_cli(
                "--seed", "9",
                "--night", "1",
                "--scenario", str(SCENARIOS_DIR / "lose_flames_scenario.json"),
                "--ticks", "300",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr.decode("utf-8", errors="replace"))
            records = parse_jsonl(out)
            hits = [r for r in records if r["type"] == "event" and r["name"] == "player_hit"]
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["data"], {"by": "shade", "flames": 0, "dropped": 1})
            self.assertEqual(records[-1]["type"], "end")
            self.assertEqual(records[-1]["state"], "lost")
            game_over = [r for r in records if r["type"] == "event" and r["name"] == "game_over"][0]
            self.assertEqual(game_over["data"], {"result": "lost", "reason": "no_flames"})

    def test_lose_dawn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "lose_dawn.jsonl"
            res = run_headless_cli(
                "--seed", "9",
                "--night", "1",
                "--scenario", str(SCENARIOS_DIR / "lose_dawn_scenario.json"),
                "--ticks", "200",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0)
            records = parse_jsonl(out)
            self.assertEqual(records[-1]["type"], "end")
            self.assertEqual(records[-1]["ticks"], 60)
            self.assertEqual(records[-1]["state"], "lost")
            game_over = [r for r in records if r["type"] == "event" and r["name"] == "game_over"][0]
            self.assertEqual(game_over["data"], {"result": "lost", "reason": "dawn"})

    def test_lit_lantern_safe_radius_blocks_shade(self) -> None:
        contract = json.loads((ROOT_DIR / "game.contract.json").read_text(encoding="utf-8"))
        safe_radius = contract["tuning"]["safe_radius"]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "safe.jsonl"
            res = run_headless_cli(
                "--seed", "3",
                "--night", "1",
                "--scenario", str(SCENARIOS_DIR / "safe_radius_scenario.json"),
                "--ticks", "180",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0)
            records = parse_jsonl(out)
            snapshots = [r for r in records if r["type"] == "snapshot"]
            for snap in snapshots[1:]:
                sx, _, sz = snap["shades"][0]["pos"]
                self.assertGreaterEqual(math.hypot(sx, sz), safe_radius)
                self.assertEqual(snap["player"]["flames"], 3)
            self.assertEqual(records[-1]["state"], "playing")

    def test_default_night1_determinism_without_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out1 = Path(tmp) / "def1.jsonl"
            out2 = Path(tmp) / "def2.jsonl"
            r1 = run_headless_cli("--seed", "777", "--night", "1", "--ticks", "360", out_file=out1)
            r2 = run_headless_cli("--seed", "777", "--night", "1", "--ticks", "360", out_file=out2)
            self.assertEqual(r1.returncode, 0)
            self.assertEqual(r2.returncode, 0)
            self.assertEqual(out1.read_bytes(), out2.read_bytes())
            # Standardized Night 1 spawns 2 shades at tick 300
            records = parse_jsonl(out1)
            spawn_evs = [r for r in records if r["type"] == "event" and r["name"] == "shade_spawned"]
            self.assertEqual([e["data"]["id"] for e in spawn_evs], ["S1", "S2"])

    def test_invalid_inputs_and_scenarios_exit_code_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            out = tmp_dir / "err.jsonl"

            bad_ticks = tmp_dir / "bad_ticks.json"
            bad_ticks.write_text(
                json.dumps({"frames": [{"tick": 5}, {"tick": 5}]}),
                encoding="utf-8",
            )
            res1 = run_headless_cli("--seed", "1", "--night", "1", "--inputs", str(bad_ticks), "--ticks", "10", out_file=out)
            self.assertEqual(res1.returncode, 2)
            self.assertTrue(res1.stderr.strip())

            bad_move = tmp_dir / "bad_move.json"
            bad_move.write_text(
                json.dumps({"frames": [{"tick": 0, "move": [2.0, 0.0]}]}),
                encoding="utf-8",
            )
            res2 = run_headless_cli("--seed", "1", "--night", "1", "--inputs", str(bad_move), "--ticks", "10", out_file=out)
            self.assertEqual(res2.returncode, 2)

            bad_json = tmp_dir / "bad_json.json"
            bad_json.write_text("{not valid json", encoding="utf-8")
            res3 = run_headless_cli("--seed", "1", "--night", "1", "--scenario", str(bad_json), "--ticks", "10", out_file=out)
            self.assertEqual(res3.returncode, 2)

            res4 = run_headless_cli("--seed", "1", "--night", "9", "--ticks", "10", out_file=out)
            self.assertEqual(res4.returncode, 2)


if __name__ == "__main__":
    unittest.main()
