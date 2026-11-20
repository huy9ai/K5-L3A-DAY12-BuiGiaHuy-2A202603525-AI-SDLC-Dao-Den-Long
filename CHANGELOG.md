# Changelog

## [0.2.0] - Phase 2 (TICKET-02: Ba hòn đảo & Test Contract v1.1)
### Added
- Standardized all physics, timings, capacities, radii, and scoring in `game.contract.json` (`contract_version: "1.1"`) and `core/config.py`.
- Added standardized maps (`src/dao_den_long/core/maps.py`) for Night 1 (Đảo Bến, r=40m), Night 2 (Đảo Cau twin islands + bamboo bridge + 2 launch pads), and Night 3 (Đảo Chuông 3 tiers + 2 ramps + jump pad + bell tower + wind gusts).
- Added Dash (ground + constant-Y air dash), Fall & 60-tick respawn (`Y < -10m`), 5-state Shade AI (`spawning`, `wander`, `chase`, `recoil`, `stunned`), smooth <=30-tick safe-radius pushout, dropped motes with 480-tick TTL, Gió Lạc (Drifters) steal/drop AI, Bùa Gió (Charms), Pause (`tick` vs `sim_tick`), and Night 3 periodic wind.
- Upgraded headless CLI & validator (`headless/runner.py`, `validation.py`) to Test Contract v1.1 supporting `--night 1|2|3`, `dash`, `pause`, `drifters`, `charms`, and full-night <= 30s benchmark verification.
- Upgraded 3D WebGL2 client (`web/static/`) with full 3-Night Campaign UI (Menu, Intro with Ông Đăng quote, Result, Dawn Victory), Pause modal, persistent Settings (`localStorage`), full HUD + 10-slot mote bar + off-screen unlit-lantern directional arrow, standardized hex palette + ambient formula, and 11 procedural SFX + night ambience.
- Added Phase 2 headless scenarios & tests (`tests/test_phase2_features.py`) and updated regression tests + `scripts/verify.py`.

### Fixed
- Fixed upside-down viewport & reversed `A`/`D` camera orientation in `src/dao_den_long/web/static/app.js` (`mat4LookAt` right-handed cross product `x_cam = (zz, 0, -zx)`).

## [0.1.0] - Phase 1 (PRD-0 + Test Contract v1.0)
### Added
- Initial Night 1 simulation, Test Contract v1.0 headless CLI, WebGL2 game, test suite, and Phase 1 proof/review.

## [0.0.1] - CP0 (Preparation Foundation)
### Added
- Repo hygiene, AI harness, CI workflow, deterministic Python scaffold, and `scripts/verify.py`.
