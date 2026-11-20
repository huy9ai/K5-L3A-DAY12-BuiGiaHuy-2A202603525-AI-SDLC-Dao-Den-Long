# Nhật ký quyết định thiết kế & thay đổi yêu cầu (Decisions / ADR)

> Ghi ngắn gọn mọi quyết định kiến trúc lớn và lý do cập nhật/sửa/xóa test cũ khi yêu cầu thay đổi giữa các phase.

---

## ADR-001: Python 3 Standard Library Core + Vanilla WebGL2 (CP0)
- **Bối cảnh:** Đề bài yêu cầu chạy được trên macOS/Linux (chấm tự động qua chế độ headless), trong khi máy phát triển hiện tại chỉ có sẵn Python 3.14, pytest, git và Docker (chưa có Node.js/npm).
- **Quyết định:** Tầng `core/` viết thuần Python 3 stdlib, timestep cố định `dt`, không phụ thuộc UI; `headless/` gọi trực tiếp `core/`; `web/` dùng `ThreadingHTTPServer` + WebGL2 thuần không asset ngoài.
- **Hệ quả:** Chạy đồng nhất Windows/macOS/Linux không cần cài đặt thêm, đảm bảo 0 lệch giữa bản chơi và bản chấm tự động.

## ADR-002: Tách hàm định tuyến HTTP thuần `dispatch_request` (CP0)
- **Bối cảnh:** Khi chạy test socket TCP loopback tới `127.0.0.1` trong sandbox Windows, kết nối bị chặn bởi `WinError 10013`.
- **Quyết định:** Tách định tuyến HTTP thành hàm thuần `dispatch_request(session, method, target_path, body)` trong `src/dao_den_long/web/server.py` để test đơn vị trong process; đồng thời chạy kiểm tra HTTP TCP thật trên Ubuntu CI (`.github/workflows/ci.yml`).
- **Hệ quả:** Test chạy ổn định cả trong sandbox hạn chế mạng lẫn ngoài sandbox.

## ADR-003: `game.contract.json` là Nguồn chân lý duy nhất & Thay thế bộ smoke test CP0 (Phase 1)
- **Bối cảnh:** PRD-0 phát hành **Test Contract v1.0** với các cờ CLI bắt buộc (`--seed`, `--night 1`, `--scenario`, `--inputs`, `--ticks`, `--out`, `--snapshot-every`) và bộ `tuning` trong `game.contract.json`.
- **Quyết định:**
  1. `src/dao_den_long/core/config.py` đọc trực tiếp `game.contract.json` thay cho hằng số cứng, đảm bảo bộ test chấm tự động của giảng viên luôn khớp 100% thông số game.
  2. Thay thế `tests/test_cp0_smoke.py` (vốn test `HelloSimulation` và schema CLI CP0 tạm thời `--ticks 30` không có `--night`/`--out`) bằng bộ test đầy đủ của Phase 1: `tests/test_phase1_core.py`, `tests/test_phase1_contract.py` và `tests/test_phase1_web.py`.
- **Hệ quả:** Loại bỏ hoàn toàn nguy cơ lệch thông số giữa `game.contract.json` và engine; mọi hành vi Phase 1 đều được kiểm chứng theo đúng Contract v1.0.

---

## Thay đổi thiết kế & Test bị ảnh hưởng qua các Phase
| Phase | Luật cũ bị đổi | Thay đổi thiết kế | Test cũ bị ảnh hưởng & Cách xử lý (Sửa/Xóa + Lý do) |
|---|---|---|---|
| CP0 | — | Khởi tạo kiến trúc 3 tầng + cổng kiểm chứng `scripts/verify.py` | Chưa có |
| Phase 1 | Thay `HelloSimulation` & CLI scaffold CP0 bằng `Night1Simulation` + Test Contract v1.0 | Đọc `tuning` từ `game.contract.json`, nâng cấp `headless/runner.py`, `validation.py` (mã thoát `2`) và `web/server.py` (`/api/tick`) | Xóa `tests/test_cp0_smoke.py` và thay bằng `test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py` vì CLI CP0 không còn tương thích với các cờ bắt buộc của Test Contract v1.0 |
