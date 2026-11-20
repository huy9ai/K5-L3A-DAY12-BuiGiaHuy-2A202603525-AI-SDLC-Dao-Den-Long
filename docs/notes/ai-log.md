# Nhật ký dùng AI, lỗi AI & quản lý Token

> Ghi trung thực các công cụ/agent đã dùng, lỗi AI gặp phải, cách chỉnh harness để không lặp lại và ước tính token/chi phí mỗi phase.

---

## Tổng hợp theo Phase

| Phase | Vai trò AI & Lời nhắc chính | Ước tính Token (In / Out) | Cách tiết kiệm token đã áp dụng |
|---|---|---|---|
| CP0 | Dựng cấu trúc repo, harness AI (`AGENTS.md`, skills, hooks, CI), lõi Python + WebGL2 smoke | ~25k / ~6k *(ước lượng)* | Đọc song song tài liệu 1 lần; chọn zero-dependency stdlib không tốn context debug build tool |
| Phase 1 | Phân tích PRD-0 & Test Contract v1.0; cài đặt `core/` 60Hz, `headless/` CLI + validator mã `2`, WebGL2 3D Đảo Bến + Web Audio, bộ test + scenarios, subagent review độc lập | ~55k / ~14k *(ước lượng)* | Dùng `game.contract.json` làm nguồn duy nhất, tách `core` khỏi `web`, gộp các lệnh sửa/chạy kiểm chứng theo batch, không nạp thêm thư viện 3D nặng vào ngữ cảnh |
| Phase 2 | *(chưa bắt đầu)* | | |
| Phase 3 | *(chưa bắt đầu)* | | |
| Phase 4 | *(chưa bắt đầu)* | | |

---

## Lỗi AI đã phát hiện & Cách chỉnh Harness

| Phase | Lỗi AI gặp phải | Cách phát hiện | Chỉnh sửa Harness (`AGENTS.md` / skill / hook / code) để không tái diễn |
|---|---|---|---|
| CP0 | Không kết nối được Chrome DevTools MCP để đọc tự động Lab Board | Subagent `browser` báo thiếu MCP server | Dừng đúng quy tắc, không đoán đề; nhờ học viên dán nguyên văn `PRD-0` và `Test Contract v1.0` |
| CP0 | Test socket TCP loopback tới `127.0.0.1` lỗi `WinError 10013` trong sandbox Windows; `&&` không chạy trên PowerShell 5.1 | Chạy thật `scripts/verify.py` và đọc traceback | Tách `dispatch_request` thuần trong `web/server.py` + thêm kiểm tra live HTTP trong Ubuntu CI |
| Phase 1 | Quên kiểm chứng hệ tọa độ camera vs công thức `cam_yaw_deg` của Contract C dễ làm đảo phím `A/D`; đồng thời đặt thừa 2 đom đóm dưới chân người chơi ở `test_pickup_capacity_and_rising_edge_deposit` làm test tưởng nhầm số lượng nhặt lại | Tự đối chiếu tích có hướng vector `cross(fwd, up)` trước khi viết `app.js`, và đọc kỹ traceback lần chạy đầu của `test_phase1_core.py` | Ghi rõ trong `AGENTS.md` các bất biến của Contract v1.0 (hệ quy ước góc quay, làm tròn 3 chữ số, rising-edge, mã thoát `2`) và cập nhật `scripts/verify.py` kiểm tra đồng bộ schema `game.contract.json` mỗi lần commit |
| Phase 1 (phòng ngừa) | `Dockerfile` ban đầu chỉ copy `pyproject.toml` & `run.py`, nếu quên copy `game.contract.json` sẽ lỗi khi chạy container | Tự kiểm tra danh sách file được `core/config.py` đọc trước khi đóng gói | Cập nhật `Dockerfile` copy `game.contract.json` ngay trong Phase 1 |
| Phase 1 (review) | Trùng ID tiềm ẩn cho `motes` khi scenario trộn ID tường minh & tự sinh; prompt HUD rộng hơn `interact_radius` 0.3m; mũi tên xoay camera ngược chiều; test chỉ check 4/19 khóa tuning | Subagent review độc lập (`docs/proof/phase-1/review.md`) phát hiện trước khi tag | Khắc phục gọn (`77dd7af`): thống nhất `_next_unique_id` cho cả `motes` & `shades`, khớp HUD/camera và assert toàn bộ `asdict(tuning) == raw["tuning"]` |
