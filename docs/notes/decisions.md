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
  1. `TICKET-02` thay các hằng số Phase 1 tự chọn (`carry_capacity 6->10`, `lantern_cost 4->10`, `pickup_radius 1.5->1.0`, `interact_radius 3.0->2.0`, `safe_radius 5.0->6.0`, `pulse_cost 2->3`, `pulse_radius 7.0->5.0`, `fall_enabled false->true`, điểm `+10` chuyển sang lúc **nạp đèn**) và nâng cấp `Test Contract v1.1` (3 Đêm, Lướt, Gió Lạc, Bùa Gió, Tạm dừng, Gió Đêm 3).
  2. Học viên phát hiện bản đồ 3D ở Phase 1 bị lộn ngược và bấm `D` đi sang trái thay vì phải.
- **Quyết định:**
  1. Tách cấu hình hình học 3 Đêm sang `src/dao_den_long/core/maps.py` (`build_night_map`) để `GameSimulation` xử lý thống nhất thứ tự 12 bước trên cả 3 Đêm mà không trùng lặp code.
  2. Cập nhật `game.contract.json` lên `1.1`, cập nhật các fixture `tests/scenarios/win_scenario.json`, `win_inputs.json`, `safe_radius_scenario.json` và `tests/test_phase1_core.py`, `tests/test_phase1_contract.py` theo đúng các số chuẩn mới (với kiểm chứng hồi quy đầy đủ).
  3. Sửa phép tính tích có hướng `x_cam = cross((0,1,0), z_cam) = (zz, 0, -zx)` trong `mat4LookAt` của `app.js` để trục `Y` hướng lên thuận chiều và phím `A/D` đúng trái/phải.

---

## Thay đổi thiết kế & Test bị ảnh hưởng qua các Phase
| Phase | Luật cũ bị đổi | Thay đổi thiết kế | Test cũ bị ảnh hưởng & Cách xử lý (Sửa/Xóa + Lý do) |
|---|---|---|---|
| CP0 | — | Khởi tạo kiến trúc 3 tầng + cổng kiểm chứng `scripts/verify.py` | Chưa có |
| Phase 1 | Thay `HelloSimulation` & CLI CP0 bằng `Night1Simulation` + Contract v1.0 | Đọc `tuning` từ `game.contract.json`, nâng cấp CLI & web | Xóa `tests/test_cp0_smoke.py` và thay bằng `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py` vì CLI CP0 không tương thích Contract v1.0 |
| Phase 2 | Thay tham số Phase 1 bằng số liệu chuẩn Phần 1 + Contract v1.1; thêm Đêm 2–3, Lướt, Rơi, Gió Lạc, Bùa Gió, Tạm dừng, Gió | Tách `maps.py`, nâng `GameSimulation` theo 12 bước chuẩn & v1.1, sửa `mat4LookAt` trong `app.js` | Cập nhật `win_scenario.json`, `win_inputs.json`, `safe_radius_scenario.json`, `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py` cho đúng số chuẩn Contract v1.1 (`lantern_cost=10`, `+10` lúc nạp, `safe_radius=6.0`, `pulse_push_m=4.0` trong 15 tick) và giữ nguyên toàn bộ các trường hợp hồi quy thắng/thua/tất định/mã lỗi `2` |
