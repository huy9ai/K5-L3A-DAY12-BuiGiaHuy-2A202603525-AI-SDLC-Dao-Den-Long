# Báo cáo Review Độc Lập — Phase 2 (TICKET-02 & Test Contract v1.1)

- **Vai trò:** Independent Phase 2 Reviewer (tách biệt với tác giả viết code Phase 2)
- **Thời điểm review:** 2026-11-20 (`Git HEAD: f17dddb`, cộng thêm các file tài liệu/proof đang chờ commit trong working tree)
- **Phạm vi kiểm tra:** Kiến trúc 3 tầng, AST isolation & tính tất định, `game.contract.json` v1.1, bản đồ 3 Đêm, thứ tự 12 bước & toàn bộ cơ chế Phase 2, Test Contract v1.1 CLI/validation, sửa lỗi camera `mat4LookAt` & điều khiển 3D (`app.js`), chất lượng bộ test, tài liệu SDLC/proof, và chạy lại độc lập `scripts/verify.py` + `pytest -v` + CLI probes trước khi gắn tag `phase-2`.
- **Phán quyết cuối cùng:** **`APPROVED`**

---

## 1. Các hạng mục đã kiểm tra chi tiết

### 1.1. Kiến trúc, ranh giới module & tính tất định (`core/`)
- Đã đọc trực tiếp `AGENTS.md`, `src/dao_den_long/core/__init__.py`, `src/dao_den_long/core/config.py`, `src/dao_den_long/core/maps.py`, `src/dao_den_long/core/engine.py`, và chạy quét AST toàn bộ câu lệnh `import` / `from ... import` trong `src/dao_den_long/core/*.py`:
  - `__init__.py`: chỉ re-export từ `dao_den_long.core.config`, `dao_den_long.core.engine`, `dao_den_long.core.maps`.
  - `config.py`: chỉ import `__future__`, `dataclasses`, `json`, `pathlib`, `typing`.
  - `maps.py`: chỉ import `__future__`, `dataclasses`, `math`.
  - `engine.py`: chỉ import `__future__`, `dao_den_long.core.config`, `dao_den_long.core.maps`, `dataclasses`, `math`, `random`, `typing`. Toàn bộ sinh số ngẫu nhiên dùng instance riêng `self._rng = random.Random(self.seed)`; **không** dùng `time.*`, **không** dùng global `random`, **không** import `http`, `web`, hay DOM/UI.
- Xác nhận hằng số thời gian cố định `TICK_RATE = 60`, `DT = 1.0 / TICK_RATE` (`core/config.py:13-14`).
- Xác nhận làm tròn 3 chữ số thập phân và chuẩn hóa `-0.0 -> 0.0` qua `_r3()` (`core/engine.py:56-58`, `1046-1115`).
- Xác nhận lớp `web/` (`server.py`, `static/app.js`, `static/index.html`, `static/style.css`) dùng `GameSimulation` thuần từ `core/` mà không làm đổi bất kỳ byte đầu ra nào của chế độ headless.

### 1.2. Tuân thủ `game.contract.json` v1.1 & `core/config.py`
- `game.contract.json` có `contract_version: "1.1"`, `team: "2A202603525-BuiGiaHuy"`, đầy đủ 24 trường `tuning` (`player_speed: 6.0`, `dash_speed: 14.0`, `dash_duration_s: 0.2`, `dash_cooldown_s: 1.5`, `carry_capacity: 10`, `lantern_cost: 10`, `lantern_count_night1: 5`, `pickup_radius: 1.0`, `interact_radius: 2.0`, `pulse_cost: 3`, `pulse_radius: 5.0`, `night1_duration_s: 300`, `night2_duration_s: 330`, `night3_duration_s: 360`, `flames: 3`, `invuln_s: 1.5`, `hit_drop_ratio: 0.5`, `pulse_stun_s: 2.0`, `pulse_push_m: 4.0`, `pulse_cooldown_s: 3.0`, `safe_radius: 6.0`, `shade_speed: 4.0`, `shade_hit_radius: 1.0`, `fall_enabled: true`) và 5 trọng số `score` (`per_mote: 10`, `per_lantern: 100`, `per_stun: 5`, `per_second_left: 2`, `per_flame_left: 50`).
- `load_tuning()` (`core/config.py:111-148`) đọc trực tiếp toàn bộ tham số `tuning` và `score` từ `game.contract.json`; khớp 1:1 với `asdict(load_tuning())` (được kiểm tra qua `test_tuning_matches_contract_json`).

### 1.3. Bản đồ chuẩn 3 Đêm (`core/maps.py`)
- `_polar(cx, cz, radius, angle_deg, y)` (`maps.py:9-16`) tính `(cx + r*cos(rad), y, cz + r*sin(rad))`, làm tròn 3 chữ số thập phân, khớp tọa độ cực từ `+X` ngược chiều kim đồng hồ trong mặt phẳng `XZ`.
- **Đêm 1 — Đảo Bến (`maps.py:146-175`):** Đĩa tròn bán kính `40m`, spawn `(0, 0, 0)`, 5 Đèn (`L1..L5`), 24 điểm đom đóm (`8` ở `r=12m`, `16` ở `r=33m`), 12 điểm Bóng Mực (`r=37m`), `shade_speed=4.0`, `shade_spawn_interval=480`, `max_shades=6`.
- **Đêm 2 — Đảo Cau (`maps.py:177-215`):** Hai đảo tròn bán kính `28m` tâm `(0, 0)` và `(70, 0)`, cầu tre `x in [26, 44]`, `z in [-2, 2]`, 6 Đèn (`L1..L6`), 24 điểm đom đóm, 16 điểm Bóng Mực, Bùa Gió `C1` tại `(35, 0, 0)`, 2 bục nhảy `(20, 0, 18) -> (70, 0)` và `(50, 0, -18) -> (0, 0)` (`vy=14.0`, `h_speed=24.0`), `has_drifters=True`, `max_shades=8`.
- **Đêm 3 — Đảo Chuông (`maps.py:217-261`):** 3 tầng (`r <= 45m` ở `Y=0`, bán nguyệt `12 <= r <= 24, z > 0` ở `Y=3`, đỉnh `r <= 8` ở `Y=6`), 2 dốc gỗ tại `30°` và `150°` (`inner_r=24`, `outer_r=30`, `half_width=1.5`, `top_y=3.0`), bục nhảy `(0, 3, 13)` (`vy=12.0, vz=-8.0`), tháp chuông cản rắn `r < 2.0, y < 14.0`, 7 Đèn (`L1..L7`), 30 điểm đom đóm, 16 điểm Bóng Mực, 2 Bùa Gió (`C1`, `C2`), `shade_speed=4.5`, `shade_spawn_interval=360`, `max_shades=10`, `has_drifters=True`, `has_wind=True`.

### 1.4. Thứ tự 12 bước, Cơ chế Phase 2 & Test Contract v1.1 (`core/engine.py`, `headless/`)
- **Thứ tự xử lý trong `GameSimulation.step()` (`engine.py:459-1044`):**
  1. Đọc input & rising-edge (`pause`, `jump`, `dash`, `interact`, `pulse`), xử lý `pause` trước; khi `paused` chỉ tăng `tick`, đóng băng `sim_tick` và `time_left_s`.
  2. Giảm bộ đếm (`invuln_ticks`, `charm_ticks`, `dash_cd_ticks`, `pulse_cd_ticks`, `respawn_ticks` hồi sinh ở tick 60 tại spawn với `vel=0` và `invuln_ticks=90`, trạng thái Bóng Mực, `flee` Gió Lạc, `pickup_delay_ticks`/`ttl_ticks` đom đóm, hồi sinh Bùa Gió, đồng hồ gió Đêm 3 chu kỳ 1800 tick với cảnh báo 120 tick và gió 300 tick đẩy `2.0 m/s`).
  3. Di chuyển Mây (xoay `cam_yaw_deg`, `dash` `14 m/s` trong `12 tick` giữ nguyên `Y` trên không, bục nhảy, trọng lực `20 m/s²`, gió Đêm 3) & kiểm tra Rơi (`Y < -10`: bỏ qua `invuln`, mất `1` lửa và toàn bộ đom đóm đang giữ, phát `player_hit` với `by="fall"`, chờ `60` tick hồi sinh).
  4. Nhặt đom đóm (không cộng điểm khi nhặt) & nhặt Bùa Gió (`7.2 m/s`, 0 hồi chiêu lướt trong `600` tick).
  5. Nạp đèn (rising-edge, `+10` điểm/đom đóm khi nạp, `+100` điểm khi đèn sáng, gắn `safe_push_ticks = 30` cho Bóng Mực trong vùng an toàn).
  6. Cập nhật đẩy `safe_radius` (`<= 30` tick ra mép `6.0m`).
  7. Tỏa Sáng (`pulse`, bán kính 3D `5.0m` từ `Y+0.8`, đẩy lùi `4.0m` trong `15` tick, choáng `120` tick, `+5`/Bóng Mực; Gió Lạc đang `chase` chuyển `flee`, đang `flee` có `stolen > 0` đánh rơi lại đom đóm `drifter_drop`).
  8. Di chuyển Bóng Mực (`spawning`, `wander`, `chase`, `recoil`, `stunned`) & Gió Lạc (`idle`, `chase`, `flee`).
  9. Va chạm: Gió Lạc cướp trước (tối đa `3` khi `carried >= 5`), rồi Bóng Mực gây sát thương (chỉ ở `wander`/`chase`, ngoài `safe_radius`, trừ 1 lửa, rơi `floor(carried * 0.5)` hạt `kind="dropped"` với `ttl=480`, `pickup_delay=1`, chuyển Bóng Mực sang `recoil` 60 tick lùi `2m`).
  10. Sinh theo lịch (đom đóm mỗi 240 tick tới cap 30; Bóng Mực 2 con ở tick 300 rồi theo chu kỳ; Gió Lạc mỗi 1200 tick tới tối đa 2).
  11. Đánh giá Thắng/Thua theo thứ tự ưu tiên (`no_flames` -> `all_lit` + thưởng `floor(time_left_s)*2 + flames*50` -> `dawn`).
- **Headless CLI & Validation (`headless/runner.py`, `headless/validation.py`):**
  - Hỗ trợ `--night 1|2|3`, phát snapshot `tick=0` trước vòng lặp, rising-edge chính xác qua biến `held`, xuất JSONL UTF-8 LF với dòng cuối `{"type":"end","ticks":sim_tick,"state":...,"score":...}`.
  - Trả mã thoát `2` khi tham số/JSON/schema sai (`--night` ngoài `1..3`, `--ticks < 0`, `--snapshot-every < 1`, trạng thái Bóng Mực/Gió Lạc không hợp lệ, ID đèn ngoài `L1..LN`, `NaN`/`bool`/vượt biên trong `move`/`tick`, JSON lỗi).

### 1.5. Sửa lỗi Camera & Điều khiển WebGL2 (`src/dao_den_long/web/static/app.js`)
- Đã kiểm tra đại số tuyến tính trực tiếp trên `mat4LookAt` (`app.js:425-451`) và `buildMoveVector` (`app.js:361-370`):
  - Camera nhìn từ `eye = [p.x - sin(yaw)*cos(pitch)*d, ..., p.z - cos(yaw)*cos(pitch)*d]` về mục tiêu `[p.x, p.y + 1.1, p.z]`. Tại `yaw=0`, camera đứng ở `-Z` nhìn về `+Z`, nên `z_cam = normalize(eye - target) ≈ (0, +0.43, -0.90)`.
  - `mat4LookAt` dùng chuẩn **right-handed**: `x_cam = normalize(cross((0, 1, 0), z_cam)) = (zz, 0, -zx)` (`app.js:433-434`). Tại `yaw=0`, `x_cam = (-1, 0, 0)` và `y_cam = cross(z_cam, x_cam)` có `yy = zz*xx - zx*xz ≈ +0.90 > 0` — **bản đồ đứng thuận chiều (+Y hướng lên)**, `-X` nằm bên phải màn hình và `+X` nằm bên trái màn hình.
  - `buildMoveVector()` gán `KeyD -> mx = -1` (`-X`, tức bên **phải** màn hình tại `yaw=0` và tổng quát là hướng `x_cam` bên phải màn hình theo công thức xoay `cam_yaw_deg` trong `engine.py:583-584`) và `KeyA -> mx = +1` (bên **trái** màn hình), `KeyW -> mz = +1` (tiến vào màn hình).
  - Giao diện Web (`index.html`, `style.css`, `app.js`, `server.py`) có đủ Menu 3 Đêm, Intro Ông Đăng, Pause modal, Cài đặt lưu `localStorage`, HUD 10 ô đom đóm, chỉ báo Gió & Bùa Gió, mũi tên chỉ đèn ngoài màn hình, công thức ambient `0.15 + 0.55 * (lit / total)` và 11 SFX procedural + nhạc nền đêm.

### 1.6. Chất lượng bộ Test & Tài liệu SDLC
- Đã đọc toàn bộ 4 file test (`test_phase1_contract.py`, `test_phase1_core.py`, `test_phase1_web.py`, `test_phase2_features.py`) và toàn bộ 15 file scenario trong `tests/scenarios/`:
  - Tổng cộng **21 test** thực chất (6 unit core + 6 contract headless Đêm 1 + 1 web router/camera + 8 Phase 2 feature/map/perf). **Không có** test rỗng, test luôn PASS giả, hay test bị tắt/`skip`.
- `docs/notes/decisions.md` (`ADR-004` + bảng theo dõi) giải thích rõ ràng và trung thực lý do cập nhật các fixture & test Phase 1 (`win_scenario.json`, `win_inputs.json`, `safe_radius_scenario.json`, `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py`) theo tham số chuẩn `Contract v1.1` và sửa `mat4LookAt`.
- `docs/notes/assumptions.md`, `docs/notes/ai-log.md`, `docs/notes/retro.md`, `docs/proof/phase-2/README.md`, và `docs/proof/phase-2/verify-output.txt` đầy đủ, nhất quán và trung thực (bao gồm ghi nhận rõ FPS trực tiếp trên Chrome chưa chạy tự động vì thiếu `chrome_devtools` MCP).

---

## 2. Các lệnh đã tự chạy độc lập & kết quả quan sát

1. `git status` và `git log --oneline -n 10`:
   - Có 4 commit Phase 2 sau tag `phase-1`: `7278498`, `e001ea4`, `5b2ca3b`, `f17dddb`. Working tree còn các file tài liệu (`CHANGELOG.md`, `CREDITS.md`, `README.md`, `docs/notes/*.md`) và thư mục `docs/proof/phase-2/` chưa commit.
2. Quét AST import trên `src/dao_den_long/core/*.py`:
   - Kết quả thực tế:
     - `__init__.py`: `['dao_den_long.core.config', 'dao_den_long.core.engine', 'dao_den_long.core.maps']`
     - `config.py`: `['__future__', 'dataclasses', 'json', 'pathlib', 'typing']`
     - `engine.py`: `['__future__', 'dao_den_long.core.config', 'dao_den_long.core.maps', 'dataclasses', 'math', 'random', 'typing']`
     - `maps.py`: `['__future__', 'dataclasses', 'math']`
3. `python scripts/verify.py`:
   - Mã thoát `0` (`OVERALL RESULT: PASS`).
   - `[PASS] Test Contract v1.1 Schema (game.contract.json)`: `contract_version=1.1, team=2A202603525-BuiGiaHuy, dash_speed=14.0, fall_enabled=True`.
   - `[PASS] Unit, Regression & Phase 2 Tests (unittest)`: `Ran 21 tests in 5.216s` -> `OK`.
   - `[PASS] 3-Night Headless Determinism (SHA-256 x2)`:
     - `[night1_win] SHA-256=a227a4788d1349682037767abd9ef3d0c1bf218d0e0fb8c71997d65562787ef4 | lines=41 | end=(state=won, ticks=235, score=947)`
     - `[night2_drifter_charm] SHA-256=c6ebfa64b354a4a311c79b1a039b36b5f2ef56713b8f7786f0be01695e72f428 | lines=17 | end=(state=playing, ticks=80, score=0)`
     - `[night3_ramp_wind] SHA-256=21360f5dbcf2101f6330ae3806ed5a2f83cd2a1b7b415938451108b0279d5b50 | lines=11 | end=(state=playing, ticks=80, score=0)`
     - Khớp chính xác từng byte hash, số dòng và bản ghi `end` trong `docs/proof/phase-2/verify-output.txt`.
   - `[PASS] Full-Night Headless Benchmark (21,600 ticks <= 30s)`: `Night 3 full 21600-tick headless (with motes+shades+drifters+wind) completed in 1.160s (limit <= 30.0s), lines=2174` (tương đương ~`1.176s` trong `verify-output.txt`).
   - `[PASS] Secret & Hygiene Scan`: `Scanned 67 text files; 0 env files or secret key patterns found.`
4. `pytest -v`:
   - Mã thoát `0`, `21 passed in 5.27s`.
5. Kiểm tra biên bổ sung qua CLI (`run.py headless`) & kiểm tra định dạng (`probe_phase2.py`):
   - Các cờ/đầu vào sai đều trả về mã thoát `2`: `--night 4`, `--night 0`, `--ticks -1`, `--snapshot-every 0`, `shades[].state="flying"`, `state_ticks_left=-1`, `drifters[].state="attack"`, `stolen=-1`, `charms[].available="yes"`, ID đèn vượt phạm vi từng đêm (`L6` ở Đêm 1, `L7` ở Đêm 2, `L8` ở Đêm 3), `bool` ở trường số (`carried`, `tick`, `cam_yaw_deg`, `move`), `NaN` ở tọa độ, tick âm, và giá trị không phải `bool` cho `dash`/`pause`.
   - `--night 2` (6 đèn, chấp nhận `L6`) và `--night 3` (7 đèn, chấp nhận `L7`) với `--ticks 0` trả mã `0`, JSONL chỉ dùng LF (`\n`), gồm đúng `['snapshot', 'end']`.
   - Đêm 3 chạy `360` tick xác nhận Bóng Mực sinh ở tick `300` với trạng thái `"spawning"`, chuyển `"wander"`/`"chase"` sau 30 tick, mọi tọa độ/vận tốc/`time_left_s` đều làm tròn 3 chữ số thập phân và không có `-0.0`.
   - Kiểm tra `docs/proof/phase-2/verify-output.txt`, `docs/proof/phase-2/README.md`, và `docs/notes/*.md` đều dùng chuẩn LF (`crlf=False`).

---

## 3. Phát hiện / Lưu ý không chặn duyệt (Non-blocking Findings)

1. **Cần commit tài liệu & bằng chứng trước khi gắn tag `phase-2`:** `git status` hiện vẫn còn `CHANGELOG.md`, `CREDITS.md`, `README.md`, `docs/notes/*.md` và thư mục `docs/proof/phase-2/` chưa commit. Cần commit toàn bộ (kèm file `review.md` này) trước khi tạo tag `phase-2`.
2. **Hai hằng số chưa đọc động theo `TuningConfig` (`core/engine.py:522, 881, 946`):** Với bộ giá trị mặc định Contract v1.1 (`invuln_s=1.5`, `shade_speed=4.0`), `engine.py` khớp hoàn toàn; tuy nhiên nếu test truyền một `TuningConfig` tùy biến trong Python, `INVULN_TICKS` (`90`) đang cứng thay vì `round(self.tuning.invuln_s * TICK_RATE)` và `self.map_def.shade_speed` được dùng thay cho `self.tuning.shade_speed`. Có thể làm mềm ở phase sau nếu cần.
3. **Đẩy `safe_radius` khi Bóng Mực đang `chase` (`core/engine.py:403, 874-882`):** `_move_shade_step` chỉ khóa biên `safe_radius` khi `safe_push_ticks == 0`. Khi một đèn vừa thắp đẩy Bóng Mực đang `chase` ở bên trong, Bước 6 đẩy ra và Bước 8 vẫn cho nó nhích ngược lại một phần trong ticks 1..28, rồi hoàn tất đẩy ra `6.002m` ở tick 29 (đạt chuẩn `<= 30` tick và không gây sát thương). Ở phase sau có thể khóa luôn chiều đi vào trong lúc `safe_push_ticks > 0` để đường trượt mượt hơn nữa.
4. **`scenario.drifters[].state = "removed"` (`headless/validation.py:159`, `core/engine.py:318-347`):** Validator cho phép `"removed"` trong schema đầu vào nhưng `__post_init__` vẫn giữ phần tử đó trong `self.drifters` như một entity đứng yên. Không ảnh hưởng các kịch bản chuẩn nhưng nên lọc bỏ lúc khởi tạo nếu đầu vào truyền `"removed"`.
5. **Góc nối cực nhỏ ở đỉnh dốc Đêm 3 (`core/maps.py:88-96`):** Khi đứng sát mép ngoài bề rộng dốc (`|perp| ~ 1.5`) ở đoạn `s` trong `[23.954, 24.0)`, `hypot(x, z) > 24.0` trong khi `s < 24.0`, tạo một khe ~4 cm ở góc mép dốc; đi dọc phần thân dốc (`r=24`) hoàn toàn liền mạch.
6. **Xác nhận trình duyệt / FPS thực tế 1280×720 (`web/static/app.js`):** Như đã ghi nhận trung thực trong `docs/proof/phase-2/README.md` và `docs/notes/retro.md`, FPS trình duyệt thực tế được theo dõi qua bộ đếm FPS tích hợp trên HUD và kiểm tra trực quan khi chơi, chưa tự động hóa bằng headless Chrome do môi trường không có `chrome_devtools` MCP.

---

## 4. Kết luận

- **Phán quyết:** **`APPROVED`**
- **Thao tác trước khi gắn tag `phase-2`:** Commit toàn bộ thay đổi tài liệu và thư mục `docs/proof/phase-2/` (bao gồm file `review.md` này), chạy lại `python scripts/verify.py --write-proof` nếu cần cập nhật `Git HEAD` mới nhất vào `verify-output.txt` rồi gắn tag `phase-2`.
