# Nhật ký quyết định thiết kế & thay đổi yêu cầu (Decisions / ADR)

> Ghi ngắn gọn mọi quyết định kiến trúc lớn và lý do cập nhật/sửa/xóa test cũ khi yêu cầu thay đổi giữa các phase.

---

## ADR-001: Python 3 Standard Library Core + Vanilla WebGL2 (CP0)
- **Bối cảnh:** Đề bài yêu cầu chạy được trên macOS/Linux (chấm tự động qua chế độ headless), trong khi máy phát triển hiện tại chỉ có sẵn Python 3.14, pytest, git và Docker (chưa có Node.js/npm).
- **Quyết định:**
  - Tầng `core/` viết thuần Python 3 stdlib (`dataclasses`, `math`, `random`), timestep cố định `dt`, không đụng UI hay đồng hồ hệ thống.
  - Tầng `headless/` gọi trực tiếp `core/` để đảm bảo không lệch hành vi giữa bản chơi 3D và bản chấm tự động.
  - Tầng `web/` dùng `ThreadingHTTPServer` + WebGL2 thuần (kèm fallback Canvas2D), hoàn toàn offline, 0 phụ thuộc bên ngoài và 0 rủi ro bản quyền asset.
- **Hệ quả:** Clone sạch chạy bằng 1 lệnh trên cả Windows/macOS/Linux; chạy headless cực nhẹ; dễ mở rộng theo `PRD-0`..`Ticket-04`.

## ADR-002: Tách hàm định tuyến HTTP thuần `dispatch_request` (CP0)
- **Bối cảnh:** Khi chạy `test_web_server_health_and_static` qua TCP loopback trong sandbox Windows, kết nối socket tới `127.0.0.1` bị chặn với `WinError 10013`.
- **Quyết định:** Tách logic định tuyến HTTP thành hàm thuần `dispatch_request(session, method, target_path)` trong `src/dao_den_long/web/server.py` để test đơn vị kiểm tra toàn bộ endpoint (`/health`, `/`, `/static/*`, `/api/state`, `/api/pulse`, `/api/reset`, chặn path traversal) hoàn toàn trong process không cần socket TCP; đồng thời bổ sung bước kiểm tra HTTP TCP thật trong `.github/workflows/ci.yml` trên `ubuntu-latest`.
- **Hệ quả:** Test đơn vị chạy tất định và xanh cả trong sandbox hạn chế mạng lẫn ngoài sandbox; HTTP server thật vẫn được kiểm chứng tự động trên Ubuntu CI.

---

## Thay đổi thiết kế & Test bị ảnh hưởng qua các Phase
| Phase | Luật cũ bị đổi | Thay đổi thiết kế | Test cũ bị ảnh hưởng & Cách xử lý (Sửa/Xóa + Lý do) |
|---|---|---|---|
| CP0 | — | Khởi tạo kiến trúc 3 tầng + cổng kiểm chứng `scripts/verify.py` | Chưa có |
