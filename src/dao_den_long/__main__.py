"""CLI router for Dao Den Long."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from dao_den_long.headless.runner import main as headless_main
from dao_den_long.web.server import serve


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch between headless simulation mode and 3D web server mode."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "headless":
        return headless_main(args[1:])

    if args and args[0] == "serve":
        args = args[1:]

    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Dao Den Long - 3D Web Server (or use 'run.py headless ...')",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parsed = parser.parse_args(args)
    serve(host=parsed.host, port=parsed.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
