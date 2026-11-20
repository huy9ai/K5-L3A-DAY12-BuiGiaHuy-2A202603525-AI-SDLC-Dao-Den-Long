# Changelog

## [0.0.1] - CP0 (Preparation Foundation)
### Added
- Archived original lab README to `docs/LAB_SPEC.md` and preserved all guide/rubric/rules docs.
- Added repo hygiene (`.gitignore`, `.gitattributes` enforcing LF), `LICENSE` (MIT), `CREDITS.md`, `pyproject.toml`, and `Dockerfile`.
- Added AI harness: `AGENTS.md`, skills (`verify-phase`, `independent-review`), `.githooks/pre-commit`, `.claude/settings.json` Stop hook, and `.github/workflows/ci.yml` (`ubuntu-latest`).
- Built zero-dependency deterministic core (`src/dao_den_long/core/`), headless CLI (`src/dao_den_long/headless/`), and WebGL2 3D hello world (`src/dao_den_long/web/`).
- Added 1-command verification & real proof script `scripts/verify.py` and smoke tests `tests/test_cp0_smoke.py`.
- Initialized SDLC note templates under `docs/notes/`.
