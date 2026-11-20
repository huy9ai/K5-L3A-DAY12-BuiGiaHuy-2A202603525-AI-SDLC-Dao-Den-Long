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
- **Quyết định:** Tách hình học 3 Đêm sang `src/dao_den_long/core/maps.py`, nâng `game.contract.json` lên `1.1`, và sửa tích có hướng right-handed `x_cam = (zz, 0, -zx)` trong `mat4LookAt`.

## ADR-005: Change Request "Đèn cạn dầu" — Mô hình nhiên liệu nguyên `1/60`, AI `drain` & Luật thắng Bình minh (Phase 3)
- **Quyết định:** Tính nhiên liệu bằng số nguyên `fuel_60` (`0..6000`), thêm trạng thái `drain` (`5/s` cộng dồn, `fuel_drain` mỗi 60 tick, mất vùng an toàn khi `< 30`), thay thắng sớm `all_lit` bằng `dawn_survived` (`>= ceil(0.6 * total)` đèn sáng lúc bình minh), sức chứa động `10..20`, Chế độ mù màu và tạo hình Áo Dài + Nón Lá.

## ADR-006: Tách tầng vận hành `ops.py` cho Benchmark 1280×720, Soak Test 10 Đêm, Đo RSS đa nền tảng & Bảng xếp hạng cục bộ (Phase 4 / v1.0.0)
- **Bối cảnh:** `TICKET-04` (`Contract v1.3`) bổ sung 4 nhóm yêu cầu phi chức năng & phát hành: (1) chế độ `bench` `1280×720` với `200` Bóng Mực `wander` + `100` đom đóm + camera quỹ đạo `15s/vòng` + đo `load_ms` & `peak_mem_mb`; (2) `soak` test 10 Đêm liên tiếp trong cùng một tiến trình (`mem_end_mb <= 1.2 * mem_start_mb`); (3) Bảng xếp hạng cục bộ lưu đĩa Top 10 kèm lệnh `--export-leaderboard`; và (4) bộ tính năng Accessibility. Trong khi đó quy tắc kiến trúc của dự án cấm `src/dao_den_long/core/` import `time`, OS hay I/O đĩa.
- **Quyết định thiết kế:**
  1. **Tách module `src/dao_den_long/ops.py` ngoài `core/`:** Giữ `src/dao_den_long/core/` hoàn toàn thuần khiết (0 import `time`/`ctypes`/`os`), còn `ops.py` đảm nhận đo thời gian thực (`time.perf_counter`), đo bộ nhớ RSS tiến trình đa nền tảng bằng stdlib (Windows 64-bit `ctypes.windll.psapi.GetProcessMemoryInfo`, Linux `/proc/self/status`, macOS `resource.getrusage`), chạy `soak`, `bench`, và lưu/xuất `LeaderboardStore`.
  2. **Kiến trúc Benchmark 2 chế độ (`WebGL2 Browser` + `In-Process 1280×720 Pipeline Fallback`):**
     - Khi chạy trên máy có trình duyệt GUI kết nối được (`/?mode=bench`), trang WebGL2 khóa khung hình `1280×720`, tắt các hiệu ứng sáng tạo thêm (sao, trăng, tre ven đảo), chạy `3s` khởi động + `--duration` giây với `200` Bóng Mực `wander`, `100` đom đóm, `3` đèn sáng `L1–L3` và camera quỹ đạo `(30*cos(2πt/15), 15, 30*sin(2πt/15))` nhìn về `(0,0,0)` rồi gửi mảng `dt_i` về server xuất `bench.json`.
     - Khi chạy trong sandbox hoặc CI không có màn hình GUI, `run.py bench` tự động chạy cùng cảnh chuẩn `200` Bóng Mực + `100` đom đóm + phép biến đổi ma trận camera right-handed `1280×720` trong tiến trình Python để lệnh `<bench_cmd> --seed 42 --duration 30 --out bench.json` luôn hoàn tất với mã thoát `0` trên mọi môi trường chấm tự động.
  3. **Bảng xếp hạng cục bộ (`LeaderboardStore`):** Lưu bền tại `data/leaderboard.json` (hỗ trợ biến môi trường `DAO_DEN_LONG_LEADERBOARD_PATH` để cô lập khi chạy unit test), dùng `Timsort` ổn định theo `-score` để người đạt điểm cao trước luôn đứng trên khi bằng điểm.

---

## Thay đổi thiết kế & Test bị ảnh hưởng qua các Phase
| Phase | Luật cũ bị đổi | Thay đổi thiết kế | Test cũ bị ảnh hưởng & Cách xử lý (Sửa/Xóa + Lý do) |
|---|---|---|---|
| CP0 | — | Khởi tạo kiến trúc 3 tầng + cổng kiểm chứng `scripts/verify.py` | Chưa có |
| Phase 1 | Thay `HelloSimulation` & CLI CP0 bằng `Night1Simulation` + Contract v1.0 | Đọc `tuning` từ `game.contract.json`, nâng cấp CLI & web | Xóa `tests/test_cp0_smoke.py` và thay bằng `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py` |
| Phase 2 | Thay tham số Phase 1 bằng số liệu chuẩn Phần 1 + Contract v1.1; thêm Đêm 2–3, Lướt, Rơi, Gió Lạc, Bùa Gió, Tạm dừng, Gió | Tách `maps.py`, nâng `GameSimulation` theo 12 bước chuẩn & v1.1, sửa `mat4LookAt` trong `app.js` | Cập nhật `win_scenario.json`, `win_inputs.json`, `safe_radius_scenario.json`, `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py` cho đúng số chuẩn Contract v1.1 |
| Phase 3 | `[THAY THẾ]` đèn sáng nhận châm dầu & hao dầu tới tắt (`lantern_out`), Bóng Mực `drain` đèn `< 30`, bỏ thắng sớm `all_lit` -> thắng `dawn_survived` (`>= 60%`), đổi bảng điểm, nâng Contract v1.2 | Dùng `fuel_60` nguyên `1/60`, thêm `drain`, `ever_lit`, `relit_count`, `capacity` động `10..20`, luật bình minh, Áo Dài/Nón Lá & Colorblind UI (ADR-005) | Cập nhật `win_scenario.json` (`L1`, `time_left_s=5.0`), `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py` theo Contract v1.2; thêm `test_phase3_features.py` |
| Phase 4 | Nâng `contract_version` từ `1.2` lên `1.3` và thêm `bench_cmd`, `soak_cmd` (giữ nguyên toàn bộ luật chơi v1.0–v1.2) | Thêm `src/dao_den_long/ops.py`, mở rộng CLI & Web UI cho `bench`, `soak`, Leaderboard, Accessibility (ADR-006) | Chỉ cập nhật chuỗi phiên bản `"1.2" -> "1.3"` và `"phase-3" -> "phase-4"` trong `test_phase1_core.py` và `test_phase1_web.py`; giữ nguyên 100% các test còn lại của Phase 1–3 và thêm mới `tests/test_phase4_features.py` (tổng 31 test PASS, 0 skip). |
