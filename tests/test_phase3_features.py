"""Comprehensive unit & headless tests for Phase 3 (TICKET-03 / Test Contract v1.2)."""

from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
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


class TestPhase3Features(unittest.TestCase):
    def test_headless_fuel_decay_lantern_out_relight_refuel_and_capacity_growth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out1 = Path(tmp) / "p3_fuel_1.jsonl"
            out2 = Path(tmp) / "p3_fuel_2.jsonl"
            args = (
                "--seed", "42",
                "--night", "1",
                "--scenario", str(SCENARIOS_DIR / "p3_fuel_relight_refuel_scenario.json"),
                "--inputs", str(SCENARIOS_DIR / "p3_fuel_relight_refuel_inputs.json"),
                "--ticks", "700",
                "--snapshot-every", "10",
            )
            r1 = _run_cli(*args, out_file=out1)
            r2 = _run_cli(*args, out_file=out2)
            self.assertEqual(r1.returncode, 0, msg=r1.stderr.decode("utf-8", errors="replace"))
            self.assertEqual(r2.returncode, 0, msg=r2.stderr.decode("utf-8", errors="replace"))
            self.assertEqual(out1.read_bytes(), out2.read_bytes())

            records = _parse_jsonl(out1)
            out_evs = [r for r in records if r["type"] == "event" and r["name"] == "lantern_out"]
            self.assertEqual(len(out_evs), 1)
            self.assertEqual(out_evs[0]["tick"], 60)
            self.assertEqual(out_evs[0]["data"], {"lantern_id": "L1"})

            # Relight costs 5 motes, awards +25 (5*5) + 40 = 65, sets relight=True, grows capacity 10->12
            lit_evs = [r for r in records if r["type"] == "event" and r["name"] == "lantern_lit"]
            self.assertEqual(len(lit_evs), 1)
            self.assertEqual(lit_evs[0]["data"], {"lantern_id": "L1", "relight": True})

            refuel_evs = [r for r in records if r["type"] == "event" and r["name"] == "refuel"]
            self.assertEqual(len(refuel_evs), 1)
            self.assertEqual(refuel_evs[0]["data"], {"lantern_id": "L1", "amount": 1, "fuel": 100.0})

            snaps = {r["tick"]: r for r in records if r["type"] == "snapshot"}
            self.assertEqual(snaps[0]["player"]["capacity"], 10)
            self.assertEqual(snaps[70]["player"]["capacity"], 12)
            l1_70 = next(l for l in snaps[70]["lanterns"] if l["id"] == "L1")
            self.assertEqual(l1_70["relit_count"], 1)
            self.assertTrue(l1_70["ever_lit"])

            # After walking onto the 12 motes at [0,0,22], carried reaches 12 (the new grown capacity!)
            self.assertEqual(snaps[170]["player"]["carried"], 12)

            # Ends at dawn (tick 600) with 3/5 lit -> dawn_survived
            end_rec = records[-1]
            self.assertEqual(end_rec["state"], "won")
            self.assertEqual(end_rec["ticks"], 600)
            go_ev = [r for r in records if r["type"] == "event" and r["name"] == "game_over"][0]
            self.assertEqual(go_ev["data"], {"result": "won", "reason": "dawn_survived"})

    def test_refuel_exact_ceil_formula_and_full_lantern_skipped(self) -> None:
        tuning = load_tuning()
        # Case 1: fuel=80.0 (decays 1/60 to 79.9833 on tick 1 -> missing 20.0167 -> ceil(2.00167) = 3 motes)
        sim1 = GameSimulation(
            seed=1,
            night=1,
            tuning=tuning,
            scenario={
                "player": {"pos": [0, 0, 0], "carried": 5},
                "random_motes": False,
                "random_shades": False,
                "lanterns": [{"id": "L1", "pos": [0, 0, 1.0], "lit": True, "fuel": 80.0}],
            },
        )
        evs1 = sim1.step(InputFrame(interact=True))
        ref1 = [e for e in evs1 if e["name"] == "refuel"]
        self.assertEqual(len(ref1), 1)
        self.assertEqual(ref1[0]["data"], {"lantern_id": "L1", "amount": 3, "fuel": 100.0})
        self.assertEqual(sim1.player.carried, 2)
        self.assertEqual(sim1.score, 15)  # 3 * 5

        # Case 2: exact 10.0 missing (after 60 ticks from 91.0 -> fuel=90.0 exactly -> ceil(10/10)=1 mote)
        sim2 = GameSimulation(
            seed=1,
            night=1,
            tuning=tuning,
            scenario={
                "player": {"pos": [0, 0, 0], "carried": 5},
                "random_motes": False,
                "random_shades": False,
                "lanterns": [{"id": "L1", "pos": [0, 0, 1.0], "lit": True, "fuel": 91.0}],
            },
        )
        for _ in range(59):
            sim2.step(InputFrame())
        evs2 = sim2.step(InputFrame(interact=True))
        ref2 = [e for e in evs2 if e["name"] == "refuel"]
        self.assertEqual(len(ref2), 1)
        self.assertEqual(ref2[0]["data"], {"lantern_id": "L1", "amount": 1, "fuel": 100.0})
        self.assertEqual(sim2.player.carried, 4)

        # Case 3: full lantern (fuel_60 == 6000) is NOT selected; prefers unlit L2!
        tuning_no_decay = replace(load_tuning(), fuel_decay_per_s=0.0)
        sim3 = GameSimulation(
            seed=1,
            night=1,
            tuning=tuning_no_decay,
            scenario={
                "player": {"pos": [0, 0, 0], "carried": 3},
                "random_motes": False,
                "random_shades": False,
                "lanterns": [
                    {"id": "L1", "pos": [0, 0, 0.5], "lit": True, "fuel": 100.0},
                    {"id": "L2", "pos": [0, 0, 1.5], "lit": False, "deposited": 0},
                ],
            },
        )
        evs3 = sim3.step(InputFrame(interact=True))
        self.assertFalse(any(e["name"] == "refuel" for e in evs3))
        dep3 = [e for e in evs3 if e["name"] == "deposit"]
        self.assertEqual(len(dep3), 1)
        self.assertEqual(dep3[0]["data"]["lantern_id"], "L2")

    def test_fuel_30_safe_radius_boundary_and_weak_lantern_drain(self) -> None:
        # Exactly fuel == 30.0 (fuel_60 == 1800) retains safe radius; < 30 loses safe radius
        sim = GameSimulation(
            seed=2,
            night=1,
            scenario={
                "player": {"pos": [0, 0, -30], "carried": 0, "flames": 3},
                "random_motes": False,
                "random_shades": False,
                "lanterns": [{"id": "L1", "pos": [0, 0, 25], "lit": True, "fuel": 30.0}],
            },
        )
        self.assertTrue(sim._lantern_has_safe_radius(sim.lanterns[0]))
        sim.step(InputFrame())  # fuel_60 becomes 1799 < 1800
        self.assertFalse(sim._lantern_has_safe_radius(sim.lanterns[0]))

        # Headless scenario: wander shade walks to weak L1, enters drain, emits fuel_drain every 60 ticks, extinguishes L1
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "drain.jsonl"
            res = _run_cli(
                "--seed", "42",
                "--night", "1",
                "--scenario", str(SCENARIOS_DIR / "p3_shade_drain_scenario.json"),
                "--inputs", str(SCENARIOS_DIR / "p3_shade_drain_inputs.json"),
                "--ticks", "400",
                "--snapshot-every", "10",
                out_file=out,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr.decode("utf-8", errors="replace"))
            records = _parse_jsonl(out)
            drain_evs = [r for r in records if r["type"] == "event" and r["name"] == "fuel_drain"]
            self.assertGreaterEqual(len(drain_evs), 2)
            self.assertEqual(drain_evs[0]["data"]["lantern_id"], "L1")
            self.assertEqual(drain_evs[0]["data"]["shade_id"], "S1")
            out_evs = [r for r in records if r["type"] == "event" and r["name"] == "lantern_out"]
            self.assertEqual(len(out_evs), 1)
            self.assertEqual(out_evs[0]["data"], {"lantern_id": "L1"})
            # After L1 extinguishes, S1 returns to wander
            last_snap = [r for r in records if r["type"] == "snapshot"][-1]
            self.assertEqual(last_snap["shades"][0]["state"], "wander")

    def test_multi_shade_drain_stacking_pulse_15_pts_refuel_pushout_and_transitions(self) -> None:
        # 1) Two draining shades stack: 1/s decay + 2 * 5/s drain = 11/s -> 11 fuel lost in 60 ticks
        sim = GameSimulation(
            seed=3,
            night=1,
            scenario={
                "player": {"pos": [0, 0, -25], "carried": 0, "flames": 3},
                "random_motes": False,
                "random_shades": False,
                "lanterns": [{"id": "L1", "pos": [0, 0, 25], "lit": True, "fuel": 25.0}],
                "shades": [
                    {"id": "S1", "pos": [0, 0, 26.0], "state": "drain", "target_lantern_id": "L1"},
                    {"id": "S2", "pos": [0, 0, 24.0], "state": "drain", "target_lantern_id": "L1"},
                ],
            },
        )
        for _ in range(60):
            sim.step(InputFrame())
        l1 = next(l for l in sim.lanterns if l.id == "L1")
        self.assertEqual(l1.fuel_60, (25 - 11) * 60)

        # 2) Pulsing a draining shade awards +15 total score (vs +5 for non-draining), and stunned -> wander on expiry
        sim_pulse = GameSimulation(
            seed=4,
            night=1,
            scenario={
                "player": {"pos": [0, 0, 22.0], "carried": 5, "flames": 3},
                "random_motes": False,
                "random_shades": False,
                "lanterns": [{"id": "L1", "pos": [0, 0, 25.0], "lit": True, "fuel": 20.0}],
                "shades": [
                    {"id": "S1", "pos": [0, 0, 25.5], "state": "drain", "target_lantern_id": "L1"},
                    {"id": "S2", "pos": [0, 0, 20.0], "state": "chase"},
                ],
            },
        )
        evs = sim_pulse.step(InputFrame(pulse=True))
        self.assertTrue(any(e["name"] == "pulse" for e in evs))
        self.assertEqual(sim_pulse.score, 15 + 5)  # +15 for draining S1, +5 for chasing S2
        self.assertEqual(sim_pulse.shades[0].state, "stunned")
        sim_pulse.player.z = -25.0
        for _ in range(120):
            sim_pulse.step(InputFrame())
        self.assertEqual(sim_pulse.shades[0].state, "wander")

        # 3) drain -> chase when May enters <= 6m
        sim_chase = GameSimulation(
            seed=5,
            night=1,
            scenario={
                "player": {"pos": [0, 0, 20.5], "carried": 0, "flames": 3},
                "random_motes": False,
                "random_shades": False,
                "lanterns": [{"id": "L1", "pos": [0, 0, 25.0], "lit": True, "fuel": 20.0}],
                "shades": [{"id": "S1", "pos": [0, 0, 26.0], "state": "drain", "target_lantern_id": "L1"}],
            },
        )
        sim_chase.step(InputFrame())
        self.assertEqual(sim_chase.shades[0].state, "chase")

        # 4) Refueling weak lantern to >= 30 switches draining shade to wander & pushes it outside 6m in <= 30 ticks without damage
        sim_ref = GameSimulation(
            seed=6,
            night=1,
            scenario={
                "player": {"pos": [0, 0, 24.0], "carried": 3, "flames": 3},
                "random_motes": False,
                "random_shades": False,
                "lanterns": [{"id": "L1", "pos": [0, 0, 25.0], "lit": True, "fuel": 20.0}],
                "shades": [{"id": "S1", "pos": [0, 0, 26.5], "state": "drain", "target_lantern_id": "L1"}],
            },
        )
        sim_ref.step(InputFrame(interact=True))
        self.assertEqual(sim_ref.shades[0].state, "wander")
        for _ in range(30):
            sim_ref.step(InputFrame())
        self.assertEqual(sim_ref.player.flames, 3)
        self.assertGreaterEqual(math.hypot(sim_ref.shades[0].x, sim_ref.shades[0].z - 25.0), 6.0)

    def test_dawn_survival_thresholds_all_nights_scoring_and_no_flames_priority(self) -> None:
        # Night 1 needs 3/5, Night 2 needs 4/6, Night 3 needs 5/7
        for night, total, needed in ((1, 5, 3), (2, 6, 4), (3, 7, 5)):
            # Below threshold -> lost (dawn)
            sim_lose = GameSimulation(
                seed=10,
                night=night,
                scenario={
                    "random_motes": False,
                    "random_shades": False,
                    "random_drifters": False,
                    "wind_enabled": False,
                    "time_left_s": 0.5,
                    "lanterns": [{"id": f"L{i + 1}", "lit": True, "fuel": 80.0} for i in range(needed - 1)],
                },
            )
            evs = []
            for _ in range(30):
                evs = sim_lose.step(InputFrame())
            self.assertEqual(sim_lose.state, "lost")
            self.assertEqual(evs[-1]["data"], {"result": "lost", "reason": "dawn"})

            # At threshold -> won (dawn_survived) with exact bonus: sum(50 + floor(fuel)) + 50 * flames
            sim_win = GameSimulation(
                seed=10,
                night=night,
                scenario={
                    "player": {"flames": 2},
                    "random_motes": False,
                    "random_shades": False,
                    "random_drifters": False,
                    "wind_enabled": False,
                    "time_left_s": 1.0,
                    "lanterns": [{"id": f"L{i + 1}", "lit": True, "fuel": 80.0} for i in range(needed)],
                },
            )
            evs_w = []
            for _ in range(60):
                evs_w = sim_win.step(InputFrame())
            self.assertEqual(sim_win.state, "won")
            self.assertEqual(evs_w[-1]["data"], {"result": "won", "reason": "dawn_survived"})
            # Each lit lantern decayed 1.0s from 80.0 -> 79.0 -> bonus = 50 + 79 = 129 per lantern + 2 * 50 flames
            self.assertEqual(sim_win.score, needed * (50 + 79) + 2 * 50)

        # Priority on exact dawn tick: flames == 0 loses with reason "no_flames" even if >= 3/5 lit!
        sim_prio = GameSimulation(
            seed=11,
            night=1,
            scenario={
                "player": {"pos": [0, 0, 0], "flames": 1},
                "random_motes": False,
                "random_shades": False,
                "time_left_s": 1 / 60,
                "lanterns": [
                    {"id": "L1", "lit": True, "fuel": 90.0},
                    {"id": "L2", "lit": True, "fuel": 90.0},
                    {"id": "L3", "lit": True, "fuel": 90.0},
                ],
                "shades": [{"id": "S1", "pos": [0, 0, 0.5], "state": "chase"}],
            },
        )
        evs_p = sim_prio.step(InputFrame())
        self.assertEqual(sim_prio.state, "lost")
        go_p = [e for e in evs_p if e["name"] == "game_over"][0]
        self.assertEqual(go_p["data"], {"result": "lost", "reason": "no_flames"})

    def test_capacity_growth_capped_at_20_and_v12_validation_errors(self) -> None:
        sim = GameSimulation(
            seed=1,
            night=1,
            scenario={"player": {"successful_lights": 6}, "random_motes": False, "random_shades": False},
        )
        self.assertEqual(sim.player_capacity(), 20)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            out = tmp_dir / "err.jsonl"

            for idx, bad_obj in enumerate(
                (
                    {"lanterns": [{"id": "L1", "lit": True, "fuel": 150}]},
                    {"shades": [{"id": "S1", "pos": [0, 0, 5], "state": "drain", "target_lantern_id": "L9"}]},
                    {"player": {"successful_lights": -1}},
                )
            ):
                sc_file = tmp_dir / f"bad_{idx}.json"
                sc_file.write_text(json.dumps(bad_obj), encoding="utf-8")
                res = _run_cli("--seed", "1", "--night", "1", "--scenario", str(sc_file), "--ticks", "5", out_file=out)
                self.assertEqual(res.returncode, 2, msg=f"case {idx} expected exit 2")


if __name__ == "__main__":
    unittest.main()
