# Changelog

## [0.1.0] - Phase 1 (PRD-0 + Test Contract v1.0)
### Added
- `game.contract.json` (`contract_version: "1.0"`) as single source of truth for all Night 1 tuning and scoring parameters.
- Pure deterministic 60Hz `Night1Simulation` core (`src/dao_den_long/core/config.py`, `engine.py`): WASD + camera-yaw movement, vector normalization, rising-edge jump/interact/pulse, mote pickup & carry capacity, 5 Great Lanterns (`L1..L5`) with `safe_radius`, Shadow Ink chase + stun + pushback + drop ratio + invulnerability, dawn timer, and scoring.
- Strict Test Contract v1.0 headless CLI (`src/dao_den_long/headless/runner.py`, `validation.py`) supporting `--seed`, `--night 1`, `--scenario`, `--inputs`, `--ticks`, `--out`, `--snapshot-every` with exit code `2` on invalid contract inputs.
- Playable WebGL2 3D Đêm 1 – Đảo Bến (`src/dao_den_long/web/`): May with nón lá + hanging lantern, orbiting carried fireflies, 5 Great Lanterns warming the island sky/ground, Shadow Ink enemies, expanding pulse VFX, HUD, replay overlay, and procedural Web Audio chimes.
- Phase 1 test suite (`tests/test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py`) and reusable contract scenarios under `tests/scenarios/`.
- Phase 1 traceability proof and independent subagent review under `docs/proof/phase-1/`.

### Changed
- Replaced CP0 hello-world tests (`tests/test_cp0_smoke.py`) with full Phase 1 core/contract/web test suites (recorded in `docs/notes/decisions.md`).
- Upgraded `scripts/verify.py`, `AGENTS.md`, `.github/workflows/ci.yml`, and `Dockerfile` for Test Contract v1.0 verification.

## [0.0.1] - CP0 (Preparation Foundation)
### Added
- Archived original lab README to `docs/LAB_SPEC.md` and preserved all guide/rubric/rules docs.
- Added repo hygiene (`.gitignore`, `.gitattributes` enforcing LF), `LICENSE` (MIT), `CREDITS.md`, `pyproject.toml`, and `Dockerfile`.
- Added AI harness: `AGENTS.md`, skills (`verify-phase`, `independent-review`), `.githooks/pre-commit`, `.claude/settings.json` Stop hook, and `.github/workflows/ci.yml` (`ubuntu-latest`).
- Built zero-dependency deterministic core, headless CLI, WebGL2 hello world, and `scripts/verify.py`.
