"""Headless CLI runner conforming to Test Contract v1.1 (Nights 1, 2, 3)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from dao_den_long.core.config import load_tuning
from dao_den_long.core.engine import GameSimulation, InputFrame
from dao_den_long.core.maps import build_night_map
from dao_den_long.headless.validation import (
    ContractInputError,
    load_and_validate_inputs,
    load_and_validate_scenario,
)


def run_headless(
    *,
    seed: int,
    night: int,
    ticks: int,
    snapshot_every: int = 10,
    scenario: dict[str, Any] | None = None,
    frames_by_tick: dict[int, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Run deterministic Night 1-3 simulation and return JSONL records."""
    if night not in (1, 2, 3):
        raise ContractInputError(f"Unsupported --night {night}; expected 1, 2, or 3")
    if ticks < 0:
        raise ContractInputError("--ticks must be >= 0")
    if snapshot_every < 1:
        raise ContractInputError("--snapshot-every must be >= 1")

    tuning = load_tuning()
    sim = GameSimulation(seed=seed, night=night, tuning=tuning, scenario=scenario)
    frames = frames_by_tick or {}

    records: list[dict[str, Any]] = [sim.snapshot()]
    held = {
        "move": (0.0, 0.0),
        "cam_yaw_deg": 0.0,
        "jump": False,
        "dash": False,
        "interact": False,
        "pulse": False,
        "pause": False,
    }

    for k in range(ticks):
        if k in frames:
            frame = frames[k]
            if "move" in frame:
                held["move"] = (float(frame["move"][0]), float(frame["move"][1]))
            if "cam_yaw_deg" in frame:
                held["cam_yaw_deg"] = float(frame["cam_yaw_deg"])
            for btn in ("jump", "dash", "interact", "pulse", "pause"):
                if btn in frame:
                    held[btn] = bool(frame[btn])

        inp = InputFrame(
            move=held["move"],
            cam_yaw_deg=held["cam_yaw_deg"],
            jump=held["jump"],
            dash=held["dash"],
            interact=held["interact"],
            pulse=held["pulse"],
            pause=held["pause"],
        )
        events = sim.step(inp)
        records.extend(events)

        if sim.state in ("won", "lost") or (sim.tick % snapshot_every == 0):
            records.append(sim.snapshot())
        if sim.state in ("won", "lost"):
            break

    records.append(sim.end_record())
    return records


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint matching Test Contract v1.1."""
    parser = argparse.ArgumentParser(
        prog="run.py headless",
        description="Run Dao Den Long in deterministic headless mode (Test Contract v1.1).",
    )
    parser.add_argument("--seed", type=int, required=True, help="PRNG seed")
    parser.add_argument("--night", type=int, required=True, help="Night number (1, 2, or 3)")
    parser.add_argument("--scenario", type=Path, default=None, help="Optional scenario JSON path")
    parser.add_argument("--inputs", type=Path, default=None, help="Optional inputs JSON path")
    parser.add_argument("--ticks", type=int, required=True, help="Max ticks to simulate")
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL file path")
    parser.add_argument(
        "--snapshot-every",
        type=int,
        default=10,
        help="Emit snapshot every N ticks (default: 10)",
    )

    parsed = parser.parse_args(list(argv) if argv is not None else None)

    if parsed.night not in (1, 2, 3):
        print(f"Error: unsupported --night {parsed.night} (expected 1, 2, or 3)", file=sys.stderr)
        return 2
    if parsed.ticks < 0:
        print("Error: --ticks must be >= 0", file=sys.stderr)
        return 2
    if parsed.snapshot_every < 1:
        print("Error: --snapshot-every must be >= 1", file=sys.stderr)
        return 2

    try:
        map_def = build_night_map(parsed.night)
        scenario_data = (
            load_and_validate_scenario(parsed.scenario, lantern_count=len(map_def.lantern_spawns))
            if parsed.scenario is not None
            else None
        )
        frames_by_tick = (
            load_and_validate_inputs(parsed.inputs)
            if parsed.inputs is not None
            else None
        )
        records = run_headless(
            seed=parsed.seed,
            night=parsed.night,
            ticks=parsed.ticks,
            snapshot_every=parsed.snapshot_every,
            scenario=scenario_data,
            frames_by_tick=frames_by_tick,
        )
    except ContractInputError as exc:
        print(f"Contract validation error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive runtime failure path
        print(f"Headless runtime error: {exc}", file=sys.stderr)
        return 1

    jsonl = "\n".join(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) for rec in records) + "\n"
    try:
        parsed.out.parent.mkdir(parents=True, exist_ok=True)
        parsed.out.write_text(jsonl, encoding="utf-8", newline="\n")
    except OSError as exc:
        print(f"Failed writing output '{parsed.out}': {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
