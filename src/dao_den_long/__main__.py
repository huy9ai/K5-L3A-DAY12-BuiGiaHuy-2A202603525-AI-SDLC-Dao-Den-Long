"""CLI router for Dao Den Long (3D web server, headless, bench, soak, leaderboard export)."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from dao_den_long.headless.runner import main as headless_main
from dao_den_long.ops import LeaderboardStore, bench_main, soak_main
from dao_den_long.web.server import serve


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch between headless, bench, soak, leaderboard export, and 3D web server mode."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "headless":
        return headless_main(args[1:])
    if args and args[0] == "bench":
        return bench_main(args[1:])
    if args and args[0] == "soak":
        return soak_main(args[1:])

    if args and args[0] == "serve":
        args = args[1:]

    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Dao Den Long - 3D Web Server, Leaderboard Export, or Subcommands (headless | bench | soak)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument(
        "--export-leaderboard",
        type=Path,
        default=None,
        help="Export top-10 local leaderboard JSON to the given file path and exit",
    )
    parsed = parser.parse_args(args)

    if parsed.export_leaderboard is not None:
        store = LeaderboardStore()
        store.export_to_file(parsed.export_leaderboard)
        return 0

    serve(host=parsed.host, port=parsed.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
