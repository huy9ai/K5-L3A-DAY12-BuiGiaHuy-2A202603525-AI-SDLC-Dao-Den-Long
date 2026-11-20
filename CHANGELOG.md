# Changelog

## [1.0.0] - Phase 4 & Release v1.0.0 (TICKET-04: Bình minh — Phát hành v1.0.0 & Test Contract v1.3)
### Added
- **Test Contract v1.3 (`game.contract.json`):** Bumped `contract_version` to `"1.3"`, added `"bench_cmd": "python3 run.py bench"` and `"soak_cmd": "python3 run.py soak"`, preserving all v1.0–v1.2 rules.
- **Standardized 1280×720 Benchmark Mode (`python3 run.py bench --seed 42 --duration 30 --out bench.json`):**
  - Loads Night 1 with exact `200` wandering Shades (`seed 42`), `100` Motes, `3` lit lanterns `L1–L3` (`fuel = 100`), Mây stationary at `(0,0,0)`, disabling spawns/damage/pickup/fuel decay/game over and extra creative props.
  - Camera orbits `(0,0,0)` at radius `30 m`, height `Y = 15 m`, starting at `0°` (`(30,15,0)`), rotating CCW (`15 s` per revolution).
  - Runs `3 s` warmup followed by `--duration` seconds measurement, outputting `bench.json` (`avg_fps`, `p1_low_fps`, `frame_ms_p95`, `frames`, `load_ms`, `peak_mem_mb`, `vsync_off`, `renderer`, `os`) and exiting with code `0`. Committed real `bench.json` to repository root.
- **Multi-Night In-Process Soak Test (`python3 run.py soak --seed 7 --nights 10 --out soak.json`):**
  - Runs 10 consecutive nights (rotating Night 1 → 2 → 3) in a single process with `seed 7 + i` and seeded probabilistic inputs (`30`-tick direction change, `5%` jump, `3%` dash, `2%` pulse, `10%` interact).
  - Measures process RSS via pure Python stdlib (`mem_start_mb`, `mem_end_mb <= 1.2 * mem_start_mb`, `crashes = 0`). Committed real `soak.json` to repository root.
- **Persistent Local Leaderboard (`data/leaderboard.json`, `/api/leaderboard`, `python3 run.py --export-leaderboard out.json`):**
  - Top-10 local leaderboard sorted by `score` descending with chronological tie-breaking.
  - Supports player name input (`3–12` characters `[A-Za-z0-9_]` plus Vietnamese accented letters) after winning Night 3 (Bình Minh) or losing on any night, plus main-menu Leaderboard modal and CLI export `--export-leaderboard`.
- **Accessibility Suite (`web/static/`):**
  - Full key remapping for all 9 actions (`moveUp`, `moveDown`, `moveLeft`, `moveRight`, `jump`, `dash`, `interact`, `pulse`, `pause`) with duplicate-key conflict warning, "Khôi phục mặc định" reset button, and `localStorage` persistence.
  - Visual subtitles & indicators (`#subtitle-banner`) and off-screen Shade edge arrow (`#shade-edge-arrow`) for Shade spawns, upcoming wind gusts, final 10-second countdown, and low-fuel lanterns (`fuel < 30`).
  - Reduced Motion toggle (`#input-reduced-motion`) disabling camera shake, screen flash, and rapid blinking.
  - Minimum `18 px` UI font size at `1280×720` with Large Text (`×1.25` = `22.5 px`) toggle (`#input-large-text`).
- **Demo Media, Packaging & Final Retro:** Added gameplay preview screenshot (`docs/demo/preview.png`), demo video (`docs/demo/demo.mp4`), Phase 4 test suite (`tests/test_phase4_features.py`), and complete 4-phase Retrospective (`docs/notes/retro.md`).

### Fixed
- Added vertical height check (`abs(s.y - l.y) <= 1.5m`) to Shade `drain` targeting for multi-tier islands (Phase 3 Review non-blocking note #3) and aligned `.wind-badge` text color with `var(--danger)` (`#FFFFFF`) in Colorblind mode (note #4).

## [0.3.0] - Phase 3 (TICKET-03: Change Request "Đèn cạn dầu" & Test Contract v1.2)
### Breaking Changes
- **Contract version bumped `1.1` → `1.2` (`game.contract.json`):** Night durations `240 / 270 / 300 s`, added 8 fuel/drain/capacity tuning keys.
- **Win condition replaced (`all_lit` removed → `dawn_survived`):** Must survive until dawn with `>= ceil(0.6 * total)` lit lanterns (`3/5`, `4/6`, `5/7`); `no_flames` takes priority on the dawn tick.
- **Lantern fuel & Shade `drain`:** Integer `1/60` fuel units (`0..6000`), `1/s` decay, `ceil((100-fuel)/10)` refuel, `lantern_out` (`ever_lit`, relight cost `5`), `< 30` loses safe radius, Shade `drain` (`5/s` stacked, `fuel_drain` every 60 ticks), `stunned -> wander`.
- **Scoring & Growing Capacity:** `+5`/mote, `+100` first light, `+40` relight, `+5` stun (`+15` draining), dawn bonus `+50 + floor(fuel)`/lit lantern + `50 * flames` (0 time bonus); capacity `min(20, 10 + 2 * successful_lights)`.

### Added
- Colorblind mode ("Bảng màu dễ phân biệt": `#00B3FF` shade rim/eyes, `#FFFFFF` + `⚠` alerts, 20% squashed unlit lanterns with torn paper, 1 Hz low-fuel blink + overhead fuel bars).
- Upgraded WebGL2 visuals with traditional Vietnamese **Áo Dài** & **Nón Lá** for Mây and dynamic point lights from lit lanterns.

## [0.2.0] - Phase 2 (TICKET-02: Ba hòn đảo & Test Contract v1.1)
### Added
- Standardized physics, 3-Night maps (`Đảo Bến`, `Đảo Cau`, `Đảo Chuông`), 12-step tick order, Dash, Fall (`Y < -10m`), 5-state Shade AI, Drifters, Wind Charms, Pause, Night 3 wind gusts, 3-Night Campaign UI, and 11 Web Audio SFX.
### Fixed
- Fixed right-handed `mat4LookAt` camera orientation (`x_cam = (zz, 0, -zx)`).

## [0.1.0] - Phase 1 (PRD-0 + Test Contract v1.0)
### Added
- Initial Night 1 simulation, Test Contract v1.0 headless CLI, WebGL2 game, test suite, and Phase 1 proof/review.

## [0.0.1] - CP0 (Preparation Foundation)
### Added
- Repo hygiene, AI harness, CI workflow, deterministic Python scaffold, and `scripts/verify.py`.
