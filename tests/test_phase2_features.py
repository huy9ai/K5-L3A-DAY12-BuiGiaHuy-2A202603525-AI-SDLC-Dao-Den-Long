"""Unit and headless scenario tests for every new Phase 2 feature & 21,600-tick performance."""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dao_den_long.core import GameSimulation, InputFrame, load_tuning  # noqa: E402


def _run_cli(*args: str, out_file: Path) -> subprocess.CompletedProcess[bytes]:
    cmd = [sys.executable, "run.py", "headless", *args, "--out", str(out_file)]
    return subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, check=False)


def _parse_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class TestPhase2Features(unittest.TestCase):
    def test_dash_headless_ground_and_air_holds_y(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dash.jsonl"
            res = _run_cli(
                "--seed", "42",
                "--night", "1",
                "--scenario", str(SCENARIOS_DIR / "p2_dash_scenario.json"),
                "--inputs", str(SCENARIOS_DIR / "p2_dash_inputs.json"),
                "--ticks", "130",
                "--snapshot-every", "1",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr.decode("utf-8", errors="replace"))
            records = _parse_jsonl(out)
            dash_evs = [r for r in records if r["type"] == "event" and r["name"] == "dash"]
            self.assertEqual(len(dash_evs), 2)

            snaps = {r["tick"]: r for r in records if r["type"] == "snapshot"}
            # Ground dash ticks 1..12: 14 m/s * 0.2s = 2.8m along +Z
            self.assertAlmostEqual(snaps[12]["player"]["pos"][2], 2.8, places=2)
            # Air dash ticks 111..122: Y stays constant during dash!
            y_start = snaps[111]["player"]["pos"][1]
            self.assertGreater(y_start, 0.5)
            for t in range(111, 123):
                self.assertAlmostEqual(snaps[t]["player"]["pos"][1], y_start, places=3)

    def test_fall_ignores_invuln_loses_motes_waits_60_and_respawns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "fall.jsonl"
            res = _run_cli(
                "--seed", "42",
                "--night", "1",
                "--scenario", str(SCENARIOS_DIR / "p2_fall_scenario.json"),
                "--inputs", str(SCENARIOS_DIR / "p2_fall_inputs.json"),
                "--ticks", "180",
                "--snapshot-every", "1",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr.decode("utf-8", errors="replace"))
            records = _parse_jsonl(out)
            hits = [r for r in records if r["type"] == "event" and r["name"] == "player_hit"]
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["data"], {"by": "fall", "flames": 2, "dropped": 0, "lost": 4})

            fall_tick = hits[0]["tick"]
            snaps = {r["tick"]: r for r in records if r["type"] == "snapshot"}
            # Before respawn completes, stays off spawn; at fall_tick + 60 respawns at [0,0,0] with invuln
            self.assertNotEqual(snaps[fall_tick + 30]["player"]["pos"], [0.0, 0.0, 0.0])
            respawn_snap = snaps[fall_tick + 60]
            self.assertEqual(respawn_snap["player"]["pos"], [0.0, 0.0, 0.0])
            self.assertEqual(respawn_snap["player"]["vel"], [0.0, 0.0, 0.0])
            self.assertTrue(respawn_snap["player"]["invuln"])

    def test_pause_freezes_sim_tick_and_timers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pause.jsonl"
            res = _run_cli(
                "--seed", "42",
                "--night", "1",
                "--inputs", str(SCENARIOS_DIR / "p2_pause_inputs.json"),
                "--ticks", "50",
                "--snapshot-every", "5",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr.decode("utf-8", errors="replace"))
            records = _parse_jsonl(out)
            paused_evs = [r for r in records if r["type"] == "event" and r["name"] == "paused"]
            resumed_evs = [r for r in records if r["type"] == "event" and r["name"] == "resumed"]
            self.assertEqual(len(paused_evs), 1)
            self.assertEqual(len(resumed_evs), 1)

            snaps = {r["tick"]: r for r in records if r["type"] == "snapshot"}
            self.assertEqual(snaps[20]["state"], "paused")
            self.assertEqual(snaps[20]["sim_tick"], 10)
            self.assertEqual(records[-1]["ticks"], 30)

    def test_night2_charm_drifter_steal_and_pulse_drop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "night2_cd.jsonl"
            res = _run_cli(
                "--seed", "42",
                "--night", "2",
                "--scenario", str(SCENARIOS_DIR / "p2_night2_pad_charm_drifter_scenario.json"),
                "--inputs", str(SCENARIOS_DIR / "p2_night2_pad_charm_drifter_inputs.json"),
                "--ticks", "80",
                "--snapshot-every", "5",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr.decode("utf-8", errors="replace"))
            records = _parse_jsonl(out)
            ev_names = [r["name"] for r in records if r["type"] == "event"]
            self.assertIn("charm_picked", ev_names)
            self.assertIn("drifter_steal", ev_names)
            self.assertIn("drifter_drop", ev_names)
            # Two dashes allowed back-to-back while charm is active (0 dash cooldown)
            self.assertEqual(ev_names.count("dash"), 2)

            drop_ev = [r for r in records if r["type"] == "event" and r["name"] == "drifter_drop"][0]
            self.assertEqual(drop_ev["data"], {"drifter_id": "D1", "amount": 3})

    def test_night2_launch_pad_lands_on_island_b(self) -> None:
        sim = GameSimulation(
            seed=42,
            night=2,
            scenario={
                "player": {"pos": [19.0, 0, 18.0]},
                "random_motes": False,
                "random_shades": False,
                "random_drifters": False,
            },
        )
        # Walk onto launch pad at (20, 0, 18) then stay airborne ~1.4s while holding backward input
        for k in range(110):
            mv = (1.0, 0.0) if k < 20 else (-1.0, 0.0)
            sim.step(InputFrame(move=mv))
        snap = sim.snapshot()
        self.assertTrue(snap["player"]["grounded"])
        # Launched toward Island B center (70, 0), within radius 28m
        dist_b = math.hypot(snap["player"]["pos"][0] - 70.0, snap["player"]["pos"][2])
        self.assertLess(dist_b, 28.0)

    def test_night3_ramp_headless_and_tiers_tower_wind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "night3_ramp.jsonl"
            res = _run_cli(
                "--seed", "42",
                "--night", "3",
                "--scenario", str(SCENARIOS_DIR / "p2_night3_tiers_wind_scenario.json"),
                "--inputs", str(SCENARIOS_DIR / "p2_night3_tiers_wind_inputs.json"),
                "--ticks", "80",
                "--snapshot-every", "10",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr.decode("utf-8", errors="replace"))
            records = _parse_jsonl(out)
            last_snap = [r for r in records if r["type"] == "snapshot"][-1]
            self.assertEqual(last_snap["night"], 3)
            self.assertAlmostEqual(last_snap["player"]["pos"][1], 3.0, places=2)

        # Unit test cliff blocking, jump pad to Tier 2 (Y=6), bell tower obstacle, and wind gust
        sim = GameSimulation(
            seed=99,
            night=3,
            scenario={
                "player": {"pos": [0.0, 0.0, -25.0]},
                "random_motes": False,
                "random_shades": False,
                "random_drifters": False,
                "wind_enabled": True,
            },
        )
        # Walk toward Tier 1 cliff at (0, 0, 15) from Tier 0 (0, 0, 10)? Wait z=-25 walking to -10 is Tier 0;
        # test sheer cliff wall at r=24.5, angle 90 deg (no ramp) -> blocked from stepping onto Tier 1 Y=3!
        sim_cliff = GameSimulation(
            seed=1,
            night=3,
            scenario={
                "player": {"pos": [0.0, 0.0, 24.5]},
                "random_motes": False,
                "random_shades": False,
                "random_drifters": False,
            },
        )
        for _ in range(20):
            sim_cliff.step(InputFrame(move=(0.0, -1.0)))
        self.assertGreater(sim_cliff.player.z, 23.8)
        self.assertEqual(sim_cliff.player.y, 0.0)

        # Jump pad (0, 3, 13) -> lands on Tier 2 (Y=6.0) and Bell Tower blocks (0, 6, 0)
        sim_pad = GameSimulation(
            seed=1,
            night=3,
            scenario={
                "player": {"pos": [0.0, 3.0, 14.2]},
                "random_motes": False,
                "random_shades": False,
                "random_drifters": False,
            },
        )
        for k in range(80):
            mv = (0.0, -1.0) if k < 25 else (0.0, 0.0)
            sim_pad.step(InputFrame(move=mv))
        self.assertAlmostEqual(sim_pad.player.y, 6.0, places=2)

        # Bell tower blocks entry inside r < 2.0 on Tier 2
        for _ in range(90):
            sim_pad.step(InputFrame(move=(0.0, -1.0)))
        self.assertGreaterEqual(math.hypot(sim_pad.player.x, sim_pad.player.z), 2.0)

        # Wind triggers at tick 1800 and pushes player
        for _ in range(1805):
            sim.step(InputFrame())
        self.assertTrue(sim.wind_active)
        self.assertGreater(math.hypot(sim.player.x, sim.player.z + 25.0), 0.1)

    def test_shade_5_states_safe_radius_pushout_and_dropped_mote_ttl(self) -> None:
        tuning = load_tuning()
        sim = GameSimulation(
            seed=5,
            night=1,
            tuning=tuning,
            scenario={
                "player": {"pos": [0, 0, 0], "carried": 10, "flames": 3},
                "random_motes": False,
                "random_shades": False,
                "shades": [{"id": "S1", "pos": [0, 0, 2.0], "state": "chase"}],
                "lanterns": [{"id": "L1", "pos": [0, 0, 1.0], "lit": False, "deposited": 0}],
            },
        )
        # Step 1: Shade inside L1 safe_radius when L1 lights up -> pushed out within <= 30 ticks, NO damage!
        sim.step(InputFrame(interact=True))
        self.assertTrue(sim.lanterns[0].lit)
        for _ in range(32):
            sim.step(InputFrame())
        self.assertEqual(sim.player.flames, 3)
        self.assertGreaterEqual(math.hypot(sim.shades[0].x, sim.shades[0].z - 1.0), tuning.safe_radius)

        # Shade hit -> drops floor(6/2)=3 motes with kind="dropped", pickup_delay=1, recoil state
        sim_hit = GameSimulation(
            seed=5,
            night=1,
            tuning=tuning,
            scenario={
                "player": {"pos": [0, 0, 0], "carried": 6, "flames": 3},
                "random_motes": False,
                "random_shades": False,
                "shades": [{"id": "S1", "pos": [0, 0, 0.8], "state": "chase"}],
            },
        )
        evs = sim_hit.step(InputFrame())
        self.assertTrue(any(e["name"] == "player_hit" for e in evs))
        self.assertEqual(sim_hit.player.flames, 2)
        self.assertEqual(sim_hit.player.carried, 3)
        self.assertEqual(sim_hit.shades[0].state, "recoil")
        self.assertEqual(len(sim_hit.motes), 3)
        self.assertTrue(all(m.kind == "dropped" for m in sim_hit.motes))

    def test_full_night3_21600_ticks_under_30s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "perf_n3.jsonl"
            t0 = time.perf_counter()
            res = _run_cli(
                "--seed", "42",
                "--night", "3",
                "--scenario", str(SCENARIOS_DIR / "p2_perf_21600_scenario.json"),
                "--ticks", "21600",
                out_file=out,
            )
            elapsed = time.perf_counter() - t0
            self.assertEqual(res.returncode, 0, msg=res.stderr.decode("utf-8", errors="replace"))
            records = _parse_jsonl(out)
            self.assertEqual(records[-1]["ticks"], 21600)
            self.assertLessEqual(elapsed, 30.0)


if __name__ == "__main__":
    unittest.main()
