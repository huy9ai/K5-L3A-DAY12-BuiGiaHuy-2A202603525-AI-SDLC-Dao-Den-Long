"""Single-command entrypoint for Dao Den Long (3D web server & headless CLI)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dao_den_long.__main__ import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
