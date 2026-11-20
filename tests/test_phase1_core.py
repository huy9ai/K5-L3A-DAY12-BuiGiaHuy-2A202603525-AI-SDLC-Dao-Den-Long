"""Unit tests for Phase 1 core simulation mechanics and Test Contract tuning sync."""

from __future__ import annotations

from dataclasses import asdict
import math
from pathlib import Path
import sys
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dao_den_long.core import (  # noqa: E402
    InputFrame,
    Night1Simulation,
    load_contract_data,
    load_tuning,
)


class TestPhase1Core(unittest.TestCase):
    def test_tuning_matches_contract_json(self) -> None:
        raw = load_contract_data()
        tuning = load_tuning()
        self.assertEqual(raw["contract_version"], "1.0")
        self.assertEqual(tuning.lantern_count_night1, 5)
        self.assertEqual(asdict(tuning), raw["tuning"])

    def test_movement_yaw_and_vector_normalization(self) -> None:
        sim = Night1Simulation(
            seed=1,
            scenario={"random_motes": False, "random_shades": False},
        )
        # Diagonal input (1, 1) must normalize to unit length -> distance == player_speed * 1.0s
        for _ in range(60):
            sim.step(InputFrame(move=(1.0, 1.0), cam_yaw_deg=0.0))
        snap = sim.snapshot()
        dist = math.hypot(snap["player"]["pos"][0], snap["player"]["pos"][2])
        self.assertAlmostEqual(dist, sim.tuning.player_speed, places=2)
        self.assertAlmostEqual(snap["player"]["pos"][0], snap["player"]["pos"][2], places=2)

        # cam_yaw_deg = 90 with move = [0, 1] -> x' = sin(90) = 1, z' = cos(90) = 0 (+X direction)
        sim_rot = Night1Simulation(
            seed=1,
            scenario={"random_motes": False, "random_shades": False},
        )
        for _ in range(60):
            sim_rot.step(InputFrame(move=(0.0, 1.0), cam_yaw_deg=90.0))
        pos = sim_rot.snapshot()["player"]["pos"]
        self.assertAlmostEqual(pos[0], sim_rot.tuning.player_speed, places=2)
        self.assertAlmostEqual(pos[2], 0.0, places=2)

    def test_jump_rising_edge_and_gravity(self) -> None:
        sim = Night1Simulation(
            seed=1,
            scenario={"random_motes": False, "random_shades": False},
        )
        sim.step(InputFrame(jump=True))
        peak_y = 0.0
        for _ in range(60):
            sim.step(InputFrame(jump=True))
            peak_y = max(peak_y, sim.snapshot()["player"]["pos"][1])
        self.assertGreater(peak_y, 1.0)
        self.assertEqual(sim.snapshot()["player"]["pos"][1], 0.0)

    def test_pickup_capacity_and_rising_edge_deposit(self) -> None:
        tuning = load_tuning()
        motes = [[0, 0, 0] for _ in range(tuning.carry_capacity + 2)]
        sim = Night1Simulation(
            seed=5,
            tuning=tuning,
            scenario={
                "random_motes": False,
                "random_shades": False,
                "motes": motes,
                "lanterns": [{"id": "L1", "pos": [0, 0, 1.0], "deposited": 0}],
            },
        )
        events = sim.step(InputFrame())
        picked_events = [e for e in events if e["name"] == "mote_picked"]
        self.assertEqual(len(picked_events), tuning.carry_capacity)
        self.assertEqual(sim.player.carried, tuning.carry_capacity)
        self.assertEqual(len(sim.motes), 2)

        # Hold interact across 2 ticks -> deposits only once (rising edge)
        ev1 = sim.step(InputFrame(interact=True))
        self.assertTrue(any(e["name"] == "deposit" for e in ev1))
        self.assertTrue(any(e["name"] == "lantern_lit" for e in ev1))
        self.assertTrue(sim.lanterns[0].lit)
        self.assertEqual(sim.player.carried, tuning.carry_capacity - tuning.lantern_cost)

        # Next tick while still holding interact: no second deposit; leftover 2 motes at origin get picked up
        ev2 = sim.step(InputFrame(interact=True))
        self.assertFalse(any(e["name"] == "deposit" for e in ev2))
        self.assertEqual(sim.player.carried, tuning.carry_capacity - tuning.lantern_cost + 2)

    def test_pulse_stuns_pushes_and_enforces_cooldown(self) -> None:
        tuning = load_tuning()
        sim = Night1Simulation(
            seed=7,
            tuning=tuning,
            scenario={
                "player": {"pos": [0, 0, 0], "carried": 5, "flames": 3},
                "random_motes": False,
                "random_shades": False,
                "shades": [{"id": "S1", "pos": [0, 1, 4.0]}],
            },
        )
        ev1 = sim.step(InputFrame(pulse=True))
        pulse_evs = [e for e in ev1 if e["name"] == "pulse"]
        self.assertEqual(len(pulse_evs), 1)
        self.assertEqual(pulse_evs[0]["data"]["stunned_ids"], ["S1"])
        self.assertEqual(sim.shades[0].state, "stunned")
        self.assertGreaterEqual(sim.shades[0].z, 4.0 + tuning.pulse_push_m - 0.01)
        self.assertEqual(sim.player.carried, 5 - tuning.pulse_cost)

        # Immediately release and press pulse again during cooldown -> should NOT fire
        sim.step(InputFrame(pulse=False))
        ev_cd = sim.step(InputFrame(pulse=True))
        self.assertFalse(any(e["name"] == "pulse" for e in ev_cd))

    def test_scenario_setup_emits_no_score_and_preserves_other_lanterns(self) -> None:
        sim = Night1Simulation(
            seed=11,
            scenario={
                "random_motes": False,
                "random_shades": False,
                "motes": [{"id": "M1", "pos": [10, 0, 10]}, [12, 0, 12]],
                "lanterns": [{"id": "L1", "lit": True}, {"id": "L3", "deposited": 2}],
            },
        )
        snap = sim.snapshot()
        self.assertEqual(snap["score"], 0)
        self.assertEqual([m["id"] for m in snap["motes"]], ["M1", "M2"])
        self.assertTrue(snap["lanterns"][0]["lit"])
        self.assertFalse(snap["lanterns"][1]["lit"])
        self.assertEqual(snap["lanterns"][2]["deposited"], 2)
        self.assertFalse(snap["lanterns"][2]["lit"])


if __name__ == "__main__":
    unittest.main()
