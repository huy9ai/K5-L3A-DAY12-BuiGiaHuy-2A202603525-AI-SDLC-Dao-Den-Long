# Nhật ký quyết định thiết kế & thay đổi yêu cầu (Decisions / ADR)

> Ghi ngắn gọn mọi quyết định kiến trúc lớn và lý do cập nhật/sửa/xóa test cũ khi yêu cầu thay đổi giữa các phase.

---

## ADR-001: Python 3 Standard Library Core + Vanilla WebGL2 (CP0)
- **Bối cảnh:** Yêu cầu chạy được trên macOS/Linux, trong khi máy có sẵn Python 3.14, pytest, git, Docker.
- **Quyết định:** Tách 3 tầng `core/` (Python stdlib tất định), `headless/`, và `web/` (HTTP server stdlib + WebGL2 thuần).

## ADR-002: Tách hàm định tuyến HTTP thuần `dispatch_request` (CP0)
- **Bối cảnh:** Kết nối loopback TCP tới `127.0.0.1` bị chặn trong sandbox Windows (`WinError 10013`).
- **Quyết định:** Test router qua `dispatch_request` trong process và kiểm tra live TCP trên Ubuntu CI.

## ADR-003: `game.contract.json` là Nguồn chân lý duy nhất & Thay thế bộ smoke test CP0 (Phase 1)
- **Quyết định:** Đọc `tuning` trực tiếp từ `game.contract.json` và thay `tests/test_cp0_smoke.py` bằng bộ test Contract v1.0.

## ADR-004: Chuẩn hóa Contract v1.1, Kiến trúc bản đồ `maps.py` & Sửa lỗi Camera `mat4LookAt` (Phase 2)
- **Bối cảnh:**
  1. `TICKET-02` thay các hằng số Phase 1 tự chọn và nâng cấp `Test Contract v1.1` (3 Đêm, Lướt, Gió Lạc, Bùa Gió, Tạm dừng, Gió Đêm 3).
  2. Học viên phát hiện bản đồ 3D ở Phase 1 bị lộn ngược và bấm `D` đi sang trái thay vì phải.
- **Quyết định:**
  1. Tách cấu hình hình học 3 Đêm sang `src/dao_den_long/core/maps.py` (`build_night_map`).
  2. Cập nhật `game.contract.json` lên `1.1`, cập nhật các fixture & regression test theo số chuẩn mới.
  3. Sửa phép tính tích có hướng `x_cam = cross((0,1,0), z_cam) = (zz, 0, -zx)` trong `mat4LookAt` của `app.js`.

## ADR-005: Change Request "Đèn cạn dầu" — Mô hình trạng thái đèn dùng số nguyên `1/60`, AI `drain` & Luật thắng Bình minh (Phase 3)
- **Bối cảnh:** `TICKET-03` là **Change Request phá vỡ tương thích** nhằm giữ độ căng thẳng cuối Đêm: đèn đã thắp bị hao dầu và có thể tắt, Bóng Mực có thể hút dầu đèn yếu (`fuel < 30`), và mục tiêu chuyển từ "thắp hết đèn là thắng sớm" sang "giữ đủ đèn sáng tới bình minh" (`Test Contract v1.2`).
- **Quyết định thiết kế:**
  1. **Mô hình trạng thái đèn dùng số nguyên `fuel_60` (`0..6000`):**
     - Thay vì cộng trừ float `1/60` gây lệch sai số sau hàng nghìn tick (ví dụ mốc ranh giới đúng `30.0` của vùng an toàn hoặc `ceil((100 - fuel) / 10)` khi châm dầu), mọi phép tính nhiên liệu trong `LanternState` dùng đơn vị nguyên `1/60` (`fuel_60`: tối đa `6000`, hao `1`/tick, mỗi Bóng Mực `drain` trừ thêm `5`/tick, ngưỡng vùng an toàn `fuel_60 >= 1800` tương ứng đúng `30.0`, châm dầu `needed = (6000 - fuel_60 + 599) // 600`, thưởng bình minh `50 + (fuel_60 // 60)`). Chỉ làm tròn 1 chữ số thập phân khi xuất snapshot/event (`0` nếu đèn tắt).
     - Bổ sung trường `ever_lit: bool` và `relit_count: int` trên `LanternState`: đèn tắt khi `fuel_60 <= 0` ngay sau Bước 2 (`deposited = 0`, `ever_lit = True`, phát `lantern_out`); lần thắp lại tốn `5` đom đóm (`+40` điểm, `relight: true`), lần đầu vẫn `10` đom đóm (`+100` điểm, `relight: false`).
  2. **Mở rộng máy trạng thái Bóng Mực (6 trạng thái) & thứ tự trong tick:**
     - Thêm trạng thái `drain` với `target_lantern_id` và `drain_ticks` (phát `fuel_drain` mỗi `60` tick hút).
     - Chỉ Bóng Mực ở `wander` mới đi về đèn sáng yếu (`fuel < 30`, tốc độ `wander 2 m/s`) rồi sang `drain` khi cách `<= 2 m`; nhiều con cùng hút cộng dồn (`5/s` mỗi con + `1/s` tự hao). Bóng đang `chase` không đổi mục tiêu.
     - Từ `drain`: chuyển `chase` khi Mây vào `<= 6 m`, `stunned` khi trúng Tỏa Sáng (thưởng tổng `+15` thay vì `+5`), `wander` khi đèn tắt / châm lên `>= 30` / ra ngoài `2 m`. Hết choáng luôn về `wander`.
     - Khi châm dầu đưa đèn từ `< 30` lên `>= 30`, mọi Bóng Mực trong vùng `6 m` lập tức thoát `drain` và được đẩy ra mép `6 m` trong `<= 30` tick mà không gây sát thương (giống lúc mới thắp).
  3. **Luật thắng Bình minh & Sức chứa tăng dần:**
     - Loại bỏ nhánh thắng sớm `all_lit` ở Bước 11; Đêm 1/2/3 có thời lượng `240/270/300 s`.
     - Tại Bước 11, luôn kiểm tra `flames <= 0 -> lost (no_flames)` trước (kể cả đúng tick bình minh); sau đó nếu `time_left_s <= 0`, thắng `dawn_survived` khi `lit >= ceil(0.6 * total)` (`3/5`, `4/6`, `5/7`) và cộng thưởng `+50 + floor(fuel)` mỗi đèn sáng + `50 × flames` (bỏ thưởng thời gian); ngược lại thua `dawn`.
     - Sức chứa động `min(20, 10 + 2 * successful_lights)` tăng sau mỗi lần thắp/thắp lại thành công trong Đêm (không tính đèn đặt sẵn ở scenario và không tính châm dầu).
  4. **Nâng cấp trực quan & Chế độ mù màu thuần tầng `web/`:**
     - Toàn bộ cải tiến thẩm mỹ (Áo Dài + Nón Lá cho Mây, ánh sáng điểm từ đèn lồng, sao/trăng/tre, thanh dầu trên đầu đèn, hình dạng xẹp 20% + vết rách cho đèn tắt, và chế độ "Bảng màu dễ phân biệt" `#00B3FF` + `#FFFFFF` + `⚠`) đặt hoàn toàn trong `src/dao_den_long/web/`, bảo toàn 100% tính tất định headless.
- **Hệ quả lên bộ test cũ (không skip âm thầm):**
  - Toàn bộ 7 test tính năng Phase 2 (`test_phase2_features.py`) và các test Phase 1 không bị thay đổi (`lose_no_flames`, `lose_dawn`, `safe_radius`, default Night 1 determinism, exit code `2`) giữ nguyên và PASS 100%.
  - Các test Phase 1 kiểm tra trực tiếp luật cũ bị `[THAY THẾ]` (`all_lit`, `per_mote=10`, `contract_version=1.1`, đèn sáng không nhận tương tác) được cập nhật rõ ràng trong bảng dưới.

---

## Thay đổi thiết kế & Test bị ảnh hưởng qua các Phase
| Phase | Luật cũ bị đổi | Thay đổi thiết kế | Test cũ bị ảnh hưởng & Cách xử lý (Sửa/Xóa + Lý do) |
|---|---|---|---|
| CP0 | — | Khởi tạo kiến trúc 3 tầng + cổng kiểm chứng `scripts/verify.py` | Chưa có |
| Phase 1 | Thay `HelloSimulation` & CLI CP0 bằng `Night1Simulation` + Contract v1.0 | Đọc `tuning` từ `game.contract.json`, nâng cấp CLI & web | Xóa `tests/test_cp0_smoke.py` và thay bằng `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py` vì CLI CP0 không tương thích Contract v1.0 |
| Phase 2 | Thay tham số Phase 1 bằng số liệu chuẩn Phần 1 + Contract v1.1; thêm Đêm 2–3, Lướt, Rơi, Gió Lạc, Bùa Gió, Tạm dừng, Gió | Tách `maps.py`, nâng `GameSimulation` theo 12 bước chuẩn & v1.1, sửa `mat4LookAt` trong `app.js` | Cập nhật `win_scenario.json`, `win_inputs.json`, `safe_radius_scenario.json`, `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py` cho đúng số chuẩn Contract v1.1 |
| Phase 3 | `[THAY THẾ]` đèn sáng nhận châm dầu & hao dầu tới tắt (`lantern_out`), Bóng Mực `drain` đèn `< 30`, bỏ thắng sớm `all_lit` -> thắng `dawn_survived` (`>= 60%`), đổi bảng điểm (`per_mote 10->5`, bỏ thưởng thời gian), nâng Contract v1.2 | Dùng `fuel_60` nguyên `1/60`, thêm `drain`, `ever_lit`, `relit_count`, `capacity` động `10..20`, luật bình minh, Áo Dài/Nón Lá & Colorblind UI (ADR-005) | 1. **`tests/scenarios/win_scenario.json`**: Đổi đèn mục tiêu chưa sáng sang `L1` (vị trí chuẩn `[0,0,25]`, tránh trùng tọa độ với `L1` sáng khi đèn sáng đã nhận tương tác châm dầu) và đặt `time_left_s: 5.0` để kiểm chứng thắp 5/5 không thắng sớm mà thắng `dawn_survived` tại tick 300.<br>2. **`tests/test_phase1_core.py`**: Cập nhật kiểm tra `contract_version == "1.2"`, thời lượng `240/270/300`, `per_mote == 5`, `per_second_left == 0`, `lantern_lit.data["relight"] == False`, `capacity == 12`, `fuel == 100.0`.<br>3. **`tests/test_phase1_contract.py`**: Cập nhật `test_win_scenario_full_flow_and_determinism` kiểm tra `reason == "dawn_survived"` tại tick 300 và `lit_ev["tick"] < 300` (xác nhận không thắng sớm).<br>4. **`tests/test_phase1_web.py`**: Cập nhật `/health` sang `phase-3` / `1.2` và thêm kiểm tra `Áo Dài`, `drawMayAoDai`, `input-colorblind`, `#00B3FF`, `fuel-bars-layer`, `win_needed`.<br>5. Thêm mới `tests/test_phase3_features.py` cùng 2 kịch bản headless Phase 3 (`p3_fuel_relight_refuel_*`, `p3_shade_drain_*`). |
