# Báo cáo Review Độc Lập — Phase 1 (PRD-0 & Test Contract v1.0)

- **Vai trò:** Independent Phase 1 Reviewer (tách biệt với tác giả viết code Phase 1)
- **Thời điểm review:** 2026-11-20 (`Git HEAD: e18fac7`, cộng thêm các file tài liệu/proof đang chờ commit trong working tree)
- **Phạm vi kiểm tra:** Kiến trúc 3 tầng, tính tất định, tuân thủ Test Contract v1.0, chất lượng bộ test, tài liệu SDLC & bằng chứng trước khi gắn tag `phase-1`
- **Phán quyết cuối cùng:** **`APPROVED`**

---

## 1. Các hạng mục đã kiểm tra chi tiết

### 1.1. Kiến trúc, ranh giới module & tính tất định (`core/`)
- Đã đọc và kiểm tra trực tiếp `src/dao_den_long/core/__init__.py`, `src/dao_den_long/core/config.py`, `src/dao_den_long/core/engine.py`, cùng kiểm tra AST toàn bộ lệnh `import`/`from ... import` trong `src/dao_den_long/core/*.py`:
  - `config.py` chỉ import `__future__`, `dataclasses`, `json`, `math`, `pathlib`, `typing`.
  - `engine.py` chỉ import `__future__`, `dataclasses`, `math`, `random`, `typing`, `dao_den_long.core.config`. Toàn bộ sinh số ngẫu nhiên dùng `self._rng = random.Random(self.seed)` riêng của instance; **không** gọi global `random.*`, **không** import `time`, `http`, `web`, hay DOM/UI.
- Bước thời gian cố định `TICK_RATE = 60`, `DT = 1.0 / TICK_RATE` (`core/config.py:14-15`).
- Khoảng cách tương tác/va chạm/vùng an toàn đều tính trên mặt phẳng ngang `XZ` bằng `_xz_dist` (`math.hypot(ax - bx, az - bz)`).
- Tọa độ và `time_left_s` trong `Night1Simulation.snapshot()` được làm tròn 3 chữ số thập phân qua `_r3()` và chuẩn hóa `-0.0 -> 0.0` (`core/engine.py:22-25, 548-587`).
- Tầng Web (`src/dao_den_long/web/server.py`, `src/dao_den_long/web/static/app.js`) đọc trạng thái qua `Night1Simulation` và không làm thay đổi bất kỳ byte đầu ra nào của chế độ headless.

### 1.2. Tuân thủ Test Contract v1.0 (`game.contract.json`, `headless/`, `core/`)
- **`game.contract.json` & `core/config.py`:**
  - `game.contract.json` có đủ các khóa cấp cao (`contract_version: "1.0"`, `team: "2A202603525-BuiGiaHuy"`, `build_cmd`, `run_cmd`, `headless_cmd`, `tuning`) cùng đầy đủ 19 tham số `tuning` và 5 trọng số `score`.
  - `load_tuning()` trong `core/config.py:65-97` đọc trực tiếp toàn bộ 19 tham số `tuning` và 5 tham số `score` từ `game.contract.json`.
- **Headless CLI & Validation (`headless/runner.py`, `headless/validation.py`):**
  - Hỗ trợ đúng các cờ: `--seed`, `--night`, `--scenario`, `--inputs`, `--ticks`, `--out`, `--snapshot-every`.
  - Kiểm tra chặt chẽ và trả về mã thoát `2` (`ContractInputError` hoặc `argparse` / check `--night != 1`, `--ticks < 0`, `--snapshot-every < 1`, JSON lỗi, `frames[].tick` không tăng nghiêm ngặt hoặc âm/bool, `move` ngoài `[-1, 1]` hoặc chứa `NaN`, `lanterns[].id` ngoài `L1..L5`).
- **Ngữ nghĩa vòng lặp tick & điều khiển:**
  - Phát `snapshot` tại `tick = 0` trước khi áp dụng bất kỳ input nào (`runner.py:41`).
  - Vòng lặp `for k in range(ticks)` đọc input tại tick `k` (giữ trạng thái `held` cho các trường không xuất hiện ở frame `k`) và thực thi `sim.step(inp)` tạo trạng thái `tick = k + 1`.
  - Chuẩn hóa vector `move` khi `math.hypot(mx, mz) > 1.0` (`engine.py:320-323`).
  - Xoay `cam_yaw_deg` khớp chính xác công thức `x' = x*cosθ + z*sinθ`, `z' = -x*sinθ + z*cosθ` (`engine.py:324-328`).
  - Xử lý rising-edge đúng cho `jump`, `interact`, `pulse` qua `_prev_buttons` (`engine.py:297-304`).
  - Kiểm tra đếm ngược `time_left_s = max(0.0, initial_time_left_s - sim_tick / TICK_RATE)` và điều kiện kết thúc `all_lit`, `no_flames`, `dawn`.
- **Scenario & JSONL Schema:**
  - Dựng `scenario` (`player`, `lanterns`, `motes`, `shades`, `random_motes`, `random_shades`, `time_left_s`) không phát event và giữ `score == 0` tại tick 0.
  - Đầu ra JSONL xuất UTF-8 với LF (`\n`), gồm các dòng `snapshot`, `event`, và dòng `end` bắt buộc cuối cùng (`{"type":"end","ticks":...,"state":...,"score":...}`).

### 1.3. Chất lượng bộ Test & Tài liệu SDLC
- Đã kiểm tra toàn bộ 3 file test (`tests/test_phase1_core.py`, `tests/test_phase1_contract.py`, `tests/test_phase1_web.py`) và 5 file kịch bản trong `tests/scenarios/`:
  - Tổng cộng 13 test thực chất (6 unit test core, 6 integration test subprocess headless theo Contract v1.0, 1 router test web `/health`, `/`, `/static/app.js`, `/api/state`, `/api/tick`, `/api/reset`, chặn path traversal `/static/../server.py`, và JSON lỗi `400`).
  - **Không có** test rỗng, test luôn đạt giả, hay `@unittest.skip` / `pytest.mark.skip`.
- `docs/notes/decisions.md` (ADR-003 và bảng theo dõi thay đổi) giải thích rõ lý do xóa và thay thế `tests/test_cp0_smoke.py` bằng 3 bộ test Phase 1.
- `docs/notes/assumptions.md`, `docs/notes/ai-log.md`, `docs/notes/retro.md`, `docs/proof/phase-1/README.md`, và `docs/proof/phase-1/verify-output.txt` được cập nhật đầy đủ và trung thực (bao gồm ghi nhận rõ phần giao diện trình duyệt mới được kiểm chứng qua router API `/api/tick` + `/api/reset`, chưa tự động mở trình duyệt vì môi trường agent thiếu `chrome_devtools` MCP).

---

## 2. Các lệnh đã tự chạy độc lập & kết quả quan sát

1. `git status` và `git log --oneline -n 8`:
   - 4 commit Phase 1 từ `e7dd78c` đến `e18fac7`; working tree có các file tài liệu (`CHANGELOG.md`, `CREDITS.md`, `README.md`, `docs/notes/*.md`) đã chỉnh sửa và thư mục `docs/proof/phase-1/` chưa commit.
2. Kiểm tra AST import của `src/dao_den_long/core/*.py`:
   - Chỉ chứa stdlib an toàn (`__future__`, `dataclasses`, `json`, `math`, `pathlib`, `random`, `typing`) và `dao_den_long.core.config`.
3. `python scripts/verify.py`:
   - Mã thoát `0` (`OVERALL RESULT: PASS`).
   - `Test Contract v1.0 Schema (game.contract.json)`: `PASS` (`contract_version=1.0, team=2A202603525-BuiGiaHuy, lanterns=5`).
   - `Unit & Contract Tests (unittest)`: `Ran 13 tests in 2.676s` -> `OK`.
   - `Headless Determinism (SHA-256 x2)`: `PASS`
     - `[win_scenario] SHA-256=f1499fcfa3874fb7949f12fe8151cee96f87c530c84964104c16eded6e2db98b | lines=35 | end=(state=won, ticks=226, score=2090)`
     - `[default_night1] SHA-256=f2b56ce71daeccbdb4dc99fe77c377958ee75f9f5dda88fc7a3542aa1064991c | lines=32 | end=(state=playing, ticks=300, score=0)`
     - Khớp nguyên văn SHA-256, số dòng và kết quả `end` trong `docs/proof/phase-1/verify-output.txt`.
   - `Secret & Hygiene Scan`: `PASS` (`0 env files or secret key patterns found`).
4. `pytest -v`:
   - Mã thoát `0`, `13 passed in 2.77s`.
5. Kiểm tra bổ sung qua CLI (`run.py headless`) cho các trường hợp biên:
   - Chạy `win_scenario` + `win_inputs` và soi trực tiếp các dòng JSONL `snapshot`, `event`, `end`: khớp schema Contract v1.0, tick 0 đứng tại `[0.0, 0.0, 0.0]` với `score: 0`, tick 226 emit `deposit`, `lantern_lit`, `game_over` rồi `snapshot` cuối và `end`.
   - `--ticks 0` -> mã thoát `0`, 2 dòng (`['snapshot', 'end']`), xuống dòng LF (`crlf= False`).
   - `move: [NaN, 0]` trong `--inputs` -> mã thoát `2`.
   - `lanterns: [{"id": "L6", "lit": true}]` trong `--scenario` -> mã thoát `2`.
   - `--ticks -1` và `--snapshot-every 0` -> mã thoát `2`.
   - `docs/proof/phase-1/verify-output.txt` dùng LF (`crlf= False`).

---

## 3. Phát hiện / Lưu ý không chặn duyệt (Non-blocking Findings)

1. **Cần commit tài liệu & bằng chứng trước khi gắn tag `phase-1`:** `git status` hiện vẫn còn các thay đổi chưa commit (`CHANGELOG.md`, `CREDITS.md`, `README.md`, `docs/notes/*`, `docs/proof/phase-1/`). Cần commit sạch các file này trước khi chạy `git tag phase-1` để tag chứa đủ bằng chứng và review.
2. **Trùng lặp ID tiềm ẩn khi scenario trộn ID tường minh và tự sinh cho `motes` (`src/dao_den_long/core/engine.py:158-167`):** `shades` đã dùng `used_ids` + `_next_unique_shade_id()` để tránh trùng ID, nhưng `motes` vẫn gọi tuần tự `_next_mote_id()` (`M1`, `M2`, ...) mà chưa kiểm tra tập ID đã khai báo trong `scenario["motes"]`. Hiện tại chưa ảnh hưởng tới các scenario chuẩn (thường truyền mảng tọa độ `[x, y, z]`) nhưng nên đồng bộ ở phase sau.
3. **Chi tiết UX nhỏ ở tầng Web (`src/dao_den_long/web/static/app.js:224, 724-725` — không ảnh hưởng `core/` hay `headless/`):**
   - Gợi ý `[E]` trên HUD hiện ở khoảng cách `interact_radius + 0.3` (`3.3m`), rộng hơn `interact_radius` (`3.0m`) của server một chút.
   - Phím `ArrowLeft` / `ArrowRight` xoay camera ngược chiều hướng nhìn trái/phải so với quy ước trục của `mat4LookAt`.
4. **`test_tuning_matches_contract_json` (`tests/test_phase1_core.py:24-32`):** Mới assert tường minh 4/19 trường `tuning`; các trường còn lại vẫn được đọc trực tiếp từ `game.contract.json` qua `load_tuning()` và kiểm tra gián tiếp qua các test hành vi.

---

## 4. Kết luận

- **Phán quyết:** **`APPROVED`**
- **Điều kiện thao tác trước khi tag:** Commit toàn bộ thay đổi tài liệu và thư mục `docs/proof/phase-1/` (bao gồm file `review.md` này), chạy lại `python scripts/verify.py --write-proof` nếu muốn cập nhật timestamp/Git HEAD mới nhất vào `verify-output.txt`, sau đó gắn tag `phase-1`.
