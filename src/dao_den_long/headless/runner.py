"""Headless deterministic runner (CP0 scaffold before PRD-0 Test Contract)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from dao_den_long.core.engine import HelloSimulation, SimConfig


def run_headless(seed: int = 42, ticks: int = 20) -> dict[str, Any]:
    """Run deterministic simulation headlessly for the requested tick count."""
    if ticks < 0:
        raise ValueError("ticks must be non-negative")
    sim = HelloSimulation(SimConfig(seed=seed))
    for _ in range(ticks):
        sim.step()
    return sim.snapshot()


def _write_stdout_utf8(text: str) -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.flush()
    else:
        sys.stdout.write(text)
        sys.stdout.flush()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for headless mode."""
    parser = argparse.ArgumentParser(
        prog="run.py headless",
        description="Run Dao Den Long simulation in deterministic headless mode.",
    )
    parser.add_argument("--seed", type=int, default=42, help="PRNG seed (default: 42)")
    parser.add_argument("--ticks", type=int, default=20, help="Number of ticks to run (default: 20)")
    parser.add_argument("--output", type=Path, default=None, help="Optional output JSON file path")
    parsed = parser.parse_args(list(argv) if argv is not None else None)

    if parsed.ticks < 0:
        parser.error("--ticks must be >= 0")

    result = run_headless(seed=parsed.seed, ticks=parsed.ticks)
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

    if parsed.output is not None:
        parsed.output.parent.mkdir(parents=True, exist_ok=True)
        parsed.output.write_text(payload, encoding="utf-8", newline="\n")
    else:
        _write_stdout_utf8(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
