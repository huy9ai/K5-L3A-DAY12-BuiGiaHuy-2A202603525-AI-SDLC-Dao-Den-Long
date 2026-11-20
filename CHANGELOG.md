# Changelog

## [0.3.0] - Phase 3 (TICKET-03: Change Request "Đèn cạn dầu" & Test Contract v1.2)
### Breaking Changes
- **Contract version bumped `1.1` → `1.2` (`game.contract.json`):**
  - Night durations reduced from `300 / 330 / 360 s` to `240 / 270 / 300 s`.
  - Added required `tuning` keys: `fuel_max: 100`, `fuel_decay_per_s: 1.0`, `fuel_per_mote: 10`, `relight_cost: 5`, `win_ratio: 0.6`, `drain_per_s: 5`, `low_fuel_threshold: 30`, `capacity_max: 20`.
- **Win condition replaced (`all_lit` removed → `dawn_survived`):**
  - Lighting all lanterns no longer ends the night early (`game_over.reason = "all_lit"` is removed).
  - Victory now requires surviving until dawn (`time_left_s == 0`) with at least `ceil(0.6 × total)` lanterns lit (`3/5` Night 1, `4/6` Night 2, `5/7` Night 3), emitting `game_over {"result": "won", "reason": "dawn_survived"}`. Losing all flames still immediately emits `no_flames` (taking priority on the exact dawn tick).
- **Lantern fuel & interaction rules replaced:**
  - Lit lanterns now decay at `1.0/s` (exact integer `1/60` per tick), can be refueled via Interact (`used = min(carried, ceil((100 - fuel) / 10))`), and extinguish at `fuel <= 0` (`deposited = 0`, `ever_lit = true`, emitting `lantern_out`). Relighting an `ever_lit` lantern costs `5` motes instead of `10`.
  - Lit lanterns with `fuel < 30` lose their `6 m` safe zone (retaining it at exactly `fuel == 30.0`).
- **Shade AI & recovery updated:**
  - Added 6th Shade state `"drain"`: wandering Shades prioritize the nearest weak lit lantern (`fuel < 30`) and drain `5/s` stacked (emitting `fuel_drain` every 60 ticks).
  - Stunned Shades now always recover to `"wander"` instead of checking chase range directly.
- **Scoring formula replaced:**
  - Deposited/refueled mote score changed from `+10` to `+5` (`per_mote = 5`).
  - First light awards `+100`; relight awards `+40`.
  - Pulsing a draining Shade awards `+15` total (`+5` for non-draining).
  - Removed remaining-time bonus (`per_second_left = 0`); replaced with dawn survival bonus `+50 + floor(fuel)` per lit lantern + `+50` per remaining flame.
- **Snapshot & Event schema changes (Contract v1.2):**
  - `lanterns[]` adds `fuel` (1 decimal, `0` when unlit), `ever_lit`, and `relit_count`.
  - `player` adds dynamic `capacity` (`min(20, 10 + 2 * successful_lights)`).
  - `lantern_lit` adds `relight: true|false`; added events `refuel`, `lantern_out`, `fuel_drain`.

### Added
- Dynamic growing firefly capacity (`10 → 20` by `+2` per successful light/relight within a night).
- Colorblind accessibility mode ("Bảng màu dễ phân biệt", saved to `localStorage`): Shade rim/eyes `#7A3CFF → #00B3FF`, UI alerts `#FF5A5F → #FFFFFF` + `⚠`, unlit lanterns squashed 20% with torn-paper slashes, and 1 Hz low-fuel blinking on both 3D lanterns and overhead fuel bars.
- Upgraded 3D WebGL2 visuals (`src/dao_den_long/web/static/`): traditional Vietnamese **Áo Dài** (ivory bodice, high collar, flowing split panels with gold trim, wide silk trousers, crimson scarf) + **Nón Lá** with hanging mini lantern for Mây, dynamic warm point lighting from up to 7 lit lanterns, night fog, starfield & crescent moon, floating island cliffs, and perimeter bamboo (zero impact on headless output).
- Added Phase 3 headless scenarios (`p3_fuel_relight_refuel_*`, `p3_shade_drain_*`) and unit/integration suite `tests/test_phase3_features.py`.

### Fixed
- Resolved all 4 minor Phase 2 review items: dynamic `round(invuln_s * 60)` invulnerability duration, skipping Step 8 inward movement during `safe_push_ticks > 0`, filtering `"removed"` scenario drifters at init, and seamless Night 3 Tier 1 ramp inner overlap (`inner_r - 0.1`).

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
