# Nhật ký dùng AI, lỗi AI & quản lý Token

> Ghi trung thực các công cụ/agent đã dùng, lỗi AI gặp phải, cách chỉnh harness để không lặp lại và ước tính token/chi phí mỗi phase.

---

## Tổng hợp theo Phase

| Phase | Vai trò AI & Lời nhắc chính | Ước tính Token (In / Out) | Cách tiết kiệm token đã áp dụng |
|---|---|---|---|
| CP0 | Đọc 6 tài liệu lab, kiểm tra công cụ máy, dựng cấu trúc repo, harness AI (`AGENTS.md`, skills, hooks, CI), lõi Python + WebGL2 smoke | ~25k / ~6k *(ước lượng thô phiên chuẩn bị)* | Đọc song song tài liệu 1 lần; chọn zero-dependency stdlib nên không tốn ngữ cảnh debug build tool/npm |
| Phase 1 | *(chưa bắt đầu)* | | |
| Phase 2 | *(chưa bắt đầu)* | | |
| Phase 3 | *(chưa bắt đầu)* | | |
| Phase 4 | *(chưa bắt đầu)* | | |

---

## Lỗi AI đã phát hiện & Cách chỉnh Harness

| Phase | Lỗi AI gặp phải | Cách phát hiện | Chỉnh sửa Harness (`AGENTS.md` / skill / hook / code) để không tái diễn |
|---|---|---|---|
| CP0 | Không kết nối được Chrome DevTools MCP để đọc tự động Lab Board | Subagent `browser` báo lỗi thiếu MCP server ngay khi mở trang | Dừng đúng quy tắc, không đoán đề bài; dựng khung CP0 độc lập và nhờ người dùng dán `PRD-0` chính xác |
| CP0 (phòng ngừa) | Trên Windows, `python3` có thể trỏ vào Microsoft Store stub và CRLF làm sai hash cross-platform | Kiểm tra tương thích Windows ↔ Ubuntu CI trước khi viết hook | Thêm `.gitattributes` ép `eol=lf`, kiểm tra `python3 --version` trước khi gọi trong `.githooks/pre-commit` & `.claude/settings.json`, dùng `sys.executable` trong Python |
| CP0 | Test `urllib.request.urlopen` vào `127.0.0.1` thất bại với `WinError 10013` trong sandbox Windows hạn chế socket; đồng thời cú pháp `&&` không chạy trên PowerShell 5.1 | Chạy thật `scripts/verify.py` và đọc traceback | Tách `dispatch_request` thuần trong `web/server.py` để test router không cần TCP socket trong sandbox (giữ đủ assertion) + thêm live TCP smoke test vào `.github/workflows/ci.yml` |
