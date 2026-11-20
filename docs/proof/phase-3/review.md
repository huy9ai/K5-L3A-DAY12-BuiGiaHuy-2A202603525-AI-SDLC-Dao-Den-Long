# Báo cáo Review Độc Lập — Phase 3 (TICKET-03: Change Request "Đèn cạn dầu" & Test Contract v1.2)

- **Vai trò:** Independent Phase 3 Reviewer (phiên/subagent tách biệt hoàn toàn với người viết code Phase 3)
- **Thời điểm review:** 2026-11-20 (`Git HEAD: 053813e`, cùng thư mục `docs/proof/phase-3/` đang chờ commit trước khi gắn tag `phase-3`)
- **Phạm vi kiểm tra:** Toàn bộ diff `phase-2..HEAD` (31 file), kiến trúc 3 tầng & AST purity của `core/`, đồng bộ `game.contract.json` v1.2 ↔ `core/config.py`, mô hình nhiên liệu nguyên `1/60` (`fuel_60`), Bóng Mực trạng thái `drain`, luật thắng Bình minh `dawn_survived` & bảng điểm mới, sức chứa động `10..20`, validation mã thoát `2`, WebGL2 camera `mat4LookAt` + Chế độ mù màu + Áo Dài/Nón Lá (`web/static/`), hồ sơ DoD (ADR-005, Breaking Changes, không skip test âm thầm), và tự chạy độc lập `scripts/verify.py`, `pytest -v` cùng 12 kiểm thử biên đối kháng (adversarial probes).
- **Phán quyết cuối cùng:** **`APPROVED`**

---

## 1. Các hạng mục đã kiểm tra chi tiết

### 1.1. Git History, Diff & Ranh giới Kiến trúc (`core/` Purity)
- Đã kiểm tra `git log --oneline -n 8` và `git diff phase-2..HEAD --stat`: gồm 4 commit gọn, phân tách rõ trách nhiệm (`9dc17c6` core & Contract v1.2 → `574e431` WebGL2 Áo Dài/Nón Lá & Colorblind → `4377bf9` tests/scenarios/verify/harness → `053813e` ADR-005/Changelog/docs).
- Quét AST toàn bộ `src/dao_den_long/core/*.py`:
  - `__init__.py`: chỉ re-export `dao_den_long.core.{config,engine,maps}`.
  - `config.py`: chỉ import `__future__`, `dataclasses`, `json`, `pathlib`, `typing`.
  - `maps.py`: chỉ import `__future__`, `dataclasses`, `math`.
  - `engine.py`: chỉ import `__future__`, `dao_den_long.core.{config,maps}`, `dataclasses`, `math`, `random`, `typing`. Xác nhận bằng AST **0 lời gọi global `random.*`** (chỉ dùng `self._rng = random.Random(self.seed)`), **0 import** `time`, `http`, `urllib`, `socket`, `web`, `headless`, hay UI/DOM.
- Tầng `web/` (`server.py`, `static/{index.html,style.css,app.js}`) hoàn toàn độc lập, không tác động bất kỳ byte nào của đầu ra chế độ headless.
- Cả 4 lưu ý nhỏ từ Review Phase 2 (`_invuln_ticks_cfg` động, khóa Bước 8 khi `safe_push_ticks > 0`, lọc drifter `"removed"` lúc init, và nối mép dốc `inner_r - 0.1` trên Đảo Chuông) đã được khắc phục đầy đủ.

### 1.2. Đồng bộ `game.contract.json` v1.2 & `core/config.py`
- `game.contract.json` đặt `"contract_version": "1.2"`, thời lượng `night1/2/3_duration_s` = `240 / 270 / 300`, đủ 8 khóa `tuning` mới (`fuel_max: 100`, `fuel_decay_per_s: 1.0`, `fuel_per_mote: 10`, `relight_cost: 5`, `win_ratio: 0.6`, `drain_per_s: 5`, `low_fuel_threshold: 30`, `capacity_max: 20`) và trọng số `score` mới (`per_mote: 5`, `per_lantern: 100`, `per_stun: 5`, `per_second_left: 0`, `per_flame_left: 50`).
- `core/config.py:load_tuning()` nạp trực tiếp toàn bộ khóa trên; `asdict(load_tuning()) == raw["tuning"]` khớp 100%, và `maps.py` đồng bộ `duration_s = 240.0 / 270.0 / 300.0`.

### 1.3. Cơ chế Nhiên liệu Đèn, Châm dầu, Tắt đèn & Thắp lại (`core/engine.py`)
- **Đơn vị nguyên `1/60` (`engine.py:213-218`):** `fuel_60` trong `[0, 6000]` (`_fuel_max_60 = 6000`, `_fuel_per_mote_60 = 600`, `_fuel_decay_60 = 1`, `_fuel_drain_60 = 5`, `_low_fuel_60 = 1800`). Tránh hoàn toàn sai số cộng dồn dấu phẩy động (đã kiểm chứng thực tế đèn `fuel = 100.0` tắt chính xác tại tick `6000`, không lệch 1 tick).
- **Châm dầu (`engine.py:872-906`):**
  - Đèn đầy (`fuel_60 >= 6000`) không được đưa vào danh sách ứng viên (`used = 0`, bỏ qua sang đèn hợp lệ kế tiếp).
  - Công thức nguyên `needed_motes = (missing_60 + 599) // 600` tương đương chính xác tuyệt đối với `ceil((100 - fuel) / 10)` trên mọi giá trị `missing_60 >= 1`; `used = min(carried, needed_motes)`, cộng `+5 * used` điểm, phát `refuel {"lantern_id", "amount", "fuel"}`, **không** tăng `successful_lights`.
- **Tắt đèn & Thắp lại (`engine.py:700-713, 916-951`):**
  - Ngay cuối Bước 2, mọi đèn `lit` có `fuel_60 <= 0` lập tức đặt `fuel_60 = 0`, `lit = False`, `deposited = 0`, `ever_lit = True`, phát `lantern_out {"lantern_id"}` và giải phóng mọi Bóng Mực đang `drain` về `wander`.
  - Thắp lần đầu (`ever_lit == False`): tốn `10` đom đóm, thưởng `+100`, `lantern_lit {"lantern_id", "relight": false}`.
  - Thắp lại (`ever_lit == True`): tốn `5` đom đóm, thưởng `+40`, tăng `relit_count += 1`, `lantern_lit {"lantern_id", "relight": true}`.

### 1.4. Bóng Mực Trạng thái `drain` & Vùng An Toàn (`core/engine.py`)
- **Ranh giới vùng an toàn `30.0` (`engine.py:444-446`):** `_lantern_has_safe_radius` kiểm tra `lantern.lit and lantern.fuel_60 >= 1800`. Đã kiểm chứng thực tế: tại đúng `30.0` (`1800`) vẫn chặn Bóng Mực vào `< 6 m`; sau 1 tick (`1799`) lập tức mất vùng an toàn và Bóng Mực đi vào được.
- **Đủ 6 trạng thái (`VALID_SHADE_STATES`):** `spawning`, `wander`, `chase`, `recoil`, `stunned`, `drain`.
- **Định tuyến mục tiêu (`engine.py:1065-1119`):**
  - Chỉ Bóng Mực ở `wander` (khi Mây ngoài `12 m`) mới ưu tiên đèn sáng yếu (`fuel < 30`, tie-break `id` tăng dần) trước đèn tắt (`not lit`).
  - Bóng Mực đang `chase` **không** đổi mục tiêu sang đèn yếu.
  - Tiến vào `<= 2.0 m` chuyển `drain`; nhiều con cùng `drain` cộng dồn `5/60` mỗi con + `1/60` tự hao (đã xác nhận cả 2 con = `11/s` và 3 con = `16/s`, phát `fuel_drain` mỗi `60` tick theo thứ tự `shade_id` tăng dần).
- **Mọi chuyển trạng thái từ `drain` và `stunned`:**
  - `drain -> chase` khi Mây vào `<= 6.0 m` (`engine.py:1048-1051`).
  - `drain -> stunned` khi trúng Tỏa Sáng (Bước 7, `engine.py:970-980`), thưởng tổng **`+15`** điểm (so với `+5` cho con không `drain`).
  - `drain -> wander` khi đèn tắt (`engine.py:708-712`), châm lên `>= 30` (`engine.py:907-912`), hoặc ra ngoài `> 2.0 m` (`engine.py:1054-1063`, đồng thời không trừ dầu ở Bước 2 nếu `> 2.0 m`).
  - `stunned` hết thời gian về `wander` (`engine.py:616-618`).
  - Châm dầu đưa đèn từ `< 30` lên `>= 30` lập tức gắn `safe_push_ticks = 30` cho mọi Bóng Mực trong `< 6.0 m` và đẩy ra mép `>= 6.0 m` trong `<= 30` tick không gây sát thương (`engine.py:516-545, 907-914, 1042-1043, 1172`).

### 1.5. Luật thắng Bình minh, Bảng điểm mới & Sức chứa tăng dần
- **Bỏ thắng sớm `all_lit` (`engine.py:1270-1287`):** Đã kiểm chứng thắp 5/5 đèn không kết thúc sớm mà tiếp tục mô phỏng tới bình minh (`time_left_s <= 0`).
- **Ngưỡng `ceil(0.6 * total)`:** Đêm 1 `3/5`, Đêm 2 `4/6`, Đêm 3 `5/7` → `game_over {"result": "won", "reason": "dawn_survived"}`; dưới ngưỡng → `lost / dawn`.
- **Thứ tự ưu tiên đúng tick bình minh:** `flames <= 0` luôn kiểm tra trước (`no_flames` thắng ưu tiên cho cả va chạm Bóng Mực lẫn rơi xuống biển mây); đèn tắt ở Bước 2 đúng tick bình minh không được tính vào số đèn sáng ở Bước 11.
- **Thưởng bình minh:** `sum(50 + (l.fuel_60 // 60) for l in lit_lanterns) + flames * 50`, `0` điểm thưởng thời gian.
- **Sức chứa động (`engine.py:437-442`):** `min(20, 10 + 2 * successful_lights)`; đèn đặt sẵn trong scenario và hành động châm dầu không tăng `successful_lights`; cả thắp mới và thắp lại đều tăng `+2`, chạm trần `20`.

### 1.6. Snapshot, Scenario v1.2 & Validation (Mã thoát `2`)
- Snapshot v1.2 có đủ `player.capacity`, `lanterns[].{fuel, ever_lit, relit_count}` (`fuel = 0` khi tắt, `_r1` 1 chữ số khi sáng; tọa độ/vận tốc/`time_left_s` làm tròn 3 chữ số qua `_r3`).
- `headless/validation.py` kiểm tra chặt `fuel ∈ [0, 100]` (chặn `bool`, âm, `> 100`), `ever_lit` boolean, `relit_count >= 0`, `successful_lights >= 0` (chặn `bool`), `shades[].state ∈ VALID_SHADE_STATES`, `target_lantern_id` đúng phạm vi từng Đêm (`L1..L5` N1, `L1..L6` N2, `L1..L7` N3). Mọi lỗi trả mã thoát `2` kèm thông báo trên `stderr`.

### 1.7. Giao diện 3D WebGL2, Camera, Chế độ Mù màu & Áo Dài / Nón Lá (`web/`)
- **Camera right-handed (`app.js:451-475`):** Giữ nguyên phép `x_cam = (zz, 0, -zx)` chuẩn right-handed (`det = +1`, `yy > 0` tại `yaw = 0`), tương thích hoàn toàn với `buildMoveVector()` (`D -> -1`, `A -> +1`, `W -> +1`).
- **Chế độ mù màu ("Bảng màu dễ phân biệt"):** Checkbox `#input-colorblind` trong Settings (mở được từ cả Main Menu lẫn Pause Menu), lưu bền trong `localStorage` (`dao_den_long_settings_v2`), bật class `body.colorblind`:
  - Viền & mắt Bóng Mực đổi từ `#7A3CFF` sang `#00B3FF` (`[0.0, 0.702, 1.0]`, `app.js:941`).
  - Màu cảnh báo UI đổi `--danger` từ `#FF5A5F` sang `#FFFFFF` (`style.css:14-16`) kèm biểu tượng `⚠ ` trên lửa yếu, đồng hồ gấp, gió và thanh dầu yếu (`app.js:303-330, 639-650`).
  - Đèn tắt xẹp đúng `20%` (`sy = 0.76` so với `0.95` khi sáng) kèm 2 vết rách giấy tối màu (`app.js:908, 915-918`).
  - Đèn sáng yếu `< 30` nhấp nháy đúng `1 Hz` (`Math.sin(animTime * Math.PI * 2.0) > 0` trên đèn 3D + point light và `blink-1hz 1s steps(2, start) infinite` trên thanh dầu chiếu 3D phía trên mỗi đèn sáng) đồng thời tắt vòng `safe_radius` (`app.js:638-654, 810, 820, 906-913`).
- **Tạo hình Áo Dài + Nón Lá (`app.js:757-801`, `mat4ModelPitch`):** Đã kiểm tra phép nhân ma trận `R_y(yaw) * R_x(pitch) * S` hoàn toàn chính xác theo chuẩn column-major WebGL; đầy đủ quần lụa trắng ngà, thân Áo Dài cổ đứng `#E8E2D0`, tay áo dài đung đưa, hai tà trước/sau viền vàng `#F2C14E`, khăn lụa đỏ `#C8102E`, búi tóc, Nón Lá vàng tre treo đèn lồng mini, cùng shader GLSL ES 3.00 hỗ trợ 7 nguồn sáng điểm động (`uLights[7]`) + sương mù đêm.

### 1.8. Hồ sơ Change Request (DoD) & Chất lượng Bộ Test
- `docs/notes/decisions.md`: Có **ADR-005** giải trình đầy đủ mô hình đèn `fuel_60`, AI `drain`, luật thắng Bình minh, và bảng truy vết từng file test cũ bị ảnh hưởng (`win_scenario.json`, `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py`) cùng lý do rõ ràng.
- `CHANGELOG.md`: Có mục `## [0.3.0]` với phần `### Breaking Changes` liệt kê đầy đủ mọi thay đổi phá vỡ tương thích từ v1.1 → v1.2.
- Toàn bộ 5 file test (`27` test) có khẳng định thực chất, **0 test bị skip/tắt âm thầm** (đã quét toàn bộ thư mục `tests/`). Toàn bộ 7 test Phase 2 (`test_phase2_features.py`) và các test Phase 1 không bị thay đổi giữ nguyên và PASS 100%.
- `docs/proof/phase-3/README.md`, `docs/notes/assumptions.md`, `docs/notes/ai-log.md`, `docs/notes/retro.md` đồng nhất, ghi nhận trung thực việc kiểm tra thị giác trình duyệt/FPS cần học viên mở `python run.py` do thiếu `chrome_devtools` MCP.

---

## 2. Kết quả tự chạy độc lập

1. **`python scripts/verify.py`** (trong sandbox):
   - Mã thoát `0` (`OVERALL RESULT: PASS`).
   - `[PASS] Test Contract v1.2 Schema`: `contract_version=1.2, team=2A202603525-BuiGiaHuy, fuel_max=100, win_ratio=0.6, capacity_max=20`.
   - `[PASS] Unit, Regression & Phase 3 Tests (unittest)`: `Ran 27 tests in 7.630s — OK`.
   - `[PASS] 3-Night + Phase 3 Headless Determinism (SHA-256 x2)` — **khớp chính xác từng byte** với `docs/proof/phase-3/verify-output.txt`:
     - `night1_dawn_win`: `069c2a6c2ca8b78824a7d6b8553bfcc5da546caef7752438c5dc17868486d921` (`lines=47`, `won, ticks=300, score=1033`)
     - `night1_p3_fuel_relight`: `6c9504443432f9ae8cd48adc5d0485fa97a5936f11d0f415f14cac04cf717f18` (`lines=76`, `won, ticks=600, score=642`)
     - `night1_p3_shade_drain`: `4a8b99539a5441531f143b8b7c9a48b77cd051303b21377117d54f4ec6ee2972` (`lines=48`, `playing, ticks=400, score=0`)
     - `night2_drifter_charm`: `caa92c689a4276fc923d0a07938fb54358598749ec54fa4ffdbc92d60a1fbc29` (`lines=17`, `playing, ticks=80, score=0`)
     - `night3_ramp_wind`: `06c7d4c062698588ea4657c13521bcbb95aeb86ea17db07b9345e6296c40566b` (`lines=11`, `playing, ticks=80, score=0`)
   - `[PASS] Full-Night Headless Benchmark (21,600 ticks <= 30s)`: `1.862s` (`lines=2174`, vượt xa giới hạn `30.0s`).
   - `[PASS] Secret & Hygiene Scan`: `Scanned 75 text files; 0 env files or secret key patterns found.`
2. **`pytest -v`**:
   - Mã thoát `0`, `27 passed in 8.20s`.
3. **Bộ kiểm thử biên đối kháng độc lập (`audit_phase3.py`):**
   - AST purity (`core/*.py`): 0 import cấm, 0 lời gọi global `random.*`.
   - Hao dầu liên tục `6000` tick từ `100.0`: đèn sáng suốt tick `1..5999` và phát `lantern_out` đúng tick `6000`.
   - Châm dầu thiếu đom đóm (`carried=2 < needed`): tiêu đúng `2`, `+10` điểm, không tăng `capacity`.
   - Bóng Mực `chase` không bỏ Mây để sang đèn yếu; Bóng Mực `wander` ưu tiên đèn sáng yếu hơn đèn tắt ở gần hơn.
   - Ranh giới vùng an toàn thực tế: tại đúng `fuel = 30.0` (`1800`) vẫn đẩy chặn Bóng Mực ngoài `6.0 m`; tick kế tiếp (`1799`) Bóng Mực vào `< 6.0 m`.
   - Bóng Mực `drain` ở `> 2.0 m` chuyển về `wander` mà không trừ dầu; 3 Bóng Mực cùng `drain` trừ đúng `16/s` và phát `fuel_drain` theo thứ tự `S1, S2, S3`.
   - Đúng tick bình minh: đèn tắt ở Bước 2 khiến thua `dawn`; rơi mất ngọn lửa cuối ưu tiên `no_flames` thay vì `dawn_survived`.
   - 12 trường hợp lỗi CLI/scenario v1.2 (`fuel < 0`, `fuel > 100`, `fuel: true`, `ever_lit: "yes"`, `relit_count: -1`, `state: "draining"`, `target_lantern_id` vượt phạm vi Đêm 1/2/3, `successful_lights: true`, cờ lạ `--unknown-flag`, thiếu file scenario) đều trả mã thoát `2`; đầu ra JSONL và các file proof/docs đều dùng thuần LF (`crlf=False`).

---

## 3. Phát hiện (Blocking vs Non-blocking)

### Blocking Findings
- **Không có.**

### Non-blocking Findings (Lưu ý nhỏ để hoàn thiện thêm)
1. **Cần commit `docs/proof/phase-3/` trước khi gắn tag `phase-3`:** `git status -s` hiện còn thư mục `docs/proof/phase-3/` (`README.md`, `verify-output.txt`, và file `review.md` này) chưa commit. Ngoài ra `verify-output.txt` hiện ghi `74 text files` (chạy trước khi tạo `README.md` / `review.md`); có thể chạy lại `python scripts/verify.py --phase phase-3 --write-proof` sau khi hoàn tất commit nếu muốn khớp số file, không ảnh hưởng tính đúng đắn.
2. **Độ lệch nhỏ hiển thị nhắc phím `E` trên UI ở 2 tick đầu sau khi đèn đạt `100.0` (`web/static/app.js:350`):** Do Bước 2 trừ `1/60` trước Bước 5 trong cùng tick, đèn sáng `fuel = 100.0` sau 1 tick có `fuel_60 = 5999` (`_r1` hiển thị `100.0` trên snapshot). Lõi `engine.py` tuân thủ đúng thứ tự 12 bước + `ceil((100 - fuel)/10)` nên nếu bấm `E` ngay ở tick `1..2` vẫn châm `1` đom đóm, trong khi `app.js` ẩn gợi ý `E` cho tới khi `l.fuel < 100` (~`0.05 s` sau). Hoàn toàn vô hại trong thực tế chơi.
3. **Khoảng cách `drain` dùng khoảng cách ngang XZ trên địa hình nhiều tầng Đêm 3 (`core/engine.py:678, 1058, 1080`):** Giống `interact_radius` và `safe_radius`, `drain` đang kiểm tra `_xz_dist <= 2.0 + 1e-9` mà chưa kiểm tra chênh cao `abs(s.y - l.y)`. Trên Đêm 3, `L1` ở Tầng 2 `(0, 6, 6)` cách mép vách đá `r = 8` đúng `2.0 m`; trong di chuyển thường Bóng Mực Tầng 0 dừng ở `r > 8.0`, nhưng ở Phase 4 có thể bổ sung thêm kiểm tra chênh cao `<= ENTITY_MAX_HEIGHT_DIFF` cho chặt chẽ hình học 3D.
4. **Màu chữ `.wind-badge` ở chế độ mù màu (`web/static/style.css:107-116`):** Cảnh báo gió trong chế độ mù màu đã thêm đúng biểu tượng `⚠ `, nhưng màu chữ đang giữ `#FFE58A` thay vì dùng biến `var(--danger)` (`#FFFFFF`) như 3 cảnh báo còn lại (lửa yếu, đồng hồ gấp, thanh dầu yếu). Có thể đồng bộ sang `var(--danger)` ở Phase 4 nếu muốn nhất quán 100%.
5. **Kiểm tra trực quan trình duyệt 3D (Áo Dài/Nón Lá, Mù màu, FPS):** Do môi trường không có `chrome_devtools` MCP, xác nhận WebGL2 đã thực hiện qua kiểm toán mã nguồn shader/ma trận/CSS và HTTP router; khuyến nghị học viên mở `python run.py` kiểm tra mắt trực tiếp trên trình duyệt trước khi quay video demo ở Phase 4.

---

## 4. Kết luận

- **Phán quyết:** **`APPROVED`**
- **Khuyến nghị bước tiếp theo:** Commit thư mục `docs/proof/phase-3/` (gồm `README.md`, `verify-output.txt`, và `review.md` này), rồi gắn tag `phase-3` và sẵn sàng chuyển sang Phase 4.
