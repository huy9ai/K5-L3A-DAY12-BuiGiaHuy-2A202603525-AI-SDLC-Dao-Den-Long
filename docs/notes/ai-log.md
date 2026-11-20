# Nhật ký dùng AI, lỗi AI & quản lý Token

> Ghi trung thực các công cụ/agent đã dùng, lỗi AI gặp phải, cách chỉnh harness để không lặp lại và ước tính token/chi phí mỗi phase.

---

## Tổng hợp theo Phase

| Phase | Vai trò AI & Lời nhắc chính | Ước tính Token (In / Out) | Cách tiết kiệm token đã áp dụng |
|---|---|---|---|
| CP0 | Dựng cấu trúc repo, harness AI (`AGENTS.md`, skills, hooks, CI), lõi Python + WebGL2 smoke | ~25k / ~6k *(ước lượng)* | Đọc song song tài liệu 1 lần; chọn zero-dependency stdlib không tốn context debug build tool |
| Phase 1 | Phân tích PRD-0 & Contract v1.0; viết core 60Hz, headless CLI, WebGL2 Đảo Bến, tests + subagent review | ~55k / ~14k *(ước lượng)* | Đọc `game.contract.json` làm nguồn duy nhất; chạy gộp kiểm chứng theo batch |
| Phase 2 | Sửa lỗi camera/điều khiển ngược Phase 1; chuẩn hóa 3 bản đồ (`maps.py`), 12-step tick order, Contract v1.1 (Lướt, Rơi, Gió Lạc, Bùa Gió, Pause, Gió Đêm 3), giao diện 3 Đêm + benchmark + review | ~75k / ~22k *(ước lượng)* | Tách `maps.py` khỏi `engine.py` giúp 3 Đêm dùng chung 1 động cơ mô phỏng duy nhất (không lặp code); tạo đồng loạt các file fixture & test trong một lượt song song |
| Phase 3 | *(chưa bắt đầu)* | | |
| Phase 4 | *(chưa bắt đầu)* | | |

---

## Lỗi AI đã phát hiện & Cách chỉnh Harness

| Phase | Lỗi AI gặp phải | Cách phát hiện | Chỉnh sửa Harness (`AGENTS.md` / skill / hook / code) để không tái diễn |
|---|---|---|---|
| CP0 | Không kết nối được Chrome DevTools MCP để đọc tự động Lab Board | Subagent `browser` báo thiếu MCP server | Dừng đúng quy tắc, nhờ học viên dán nguyên văn đề bài |
| CP0 | Test TCP loopback lỗi `WinError 10013` trong sandbox Windows | Chạy `scripts/verify.py` và đọc traceback | Tách `dispatch_request` thuần + live HTTP test trong Ubuntu CI |
| Phase 1 | Đặt 2 đom đóm thừa dưới chân ở unit test gây fail lần đầu; dùng `&&` trên PowerShell 5.1 | Đọc traceback & sửa test kiểm tra cả tick kế tiếp | Bổ sung quy tắc vào `AGENTS.md` & `decisions.md` |
| Phase 1 (phát hiện khi chơi thử sang Phase 2) | **Lỗi nghiêm trọng ở WebGL2 `mat4LookAt`:** Đảo dấu `x_cam = (-zz, 0, zx)` thay vì tích có hướng chuẩn `cross((0,1,0), z_cam) = (zz, 0, -zx)` làm `y_cam` đảo âm -> **lật ngược cả bản đồ lẫn trái/phải (`D` đi sang trái)** | Học viên trực tiếp chơi thử bản 3D Phase 1 và báo lại; kiểm tra toán học ma trận xác nhận ngay nguyên nhân gốc | Sửa `x_cam = (zz, 0, -zx)` trong `app.js`, thêm assertion kiểm tra trực tiếp công thức `mat4LookAt` trong `test_phase1_web.py`, cập nhật `AGENTS.md` & `.agents/skills/independent-review/SKILL.md` bắt buộc kiểm tra chuẩn right-handed `lookAt` |
| Phase 2 | Lần chạy benchmark 21.600 tick đầu tiên dừng sớm ở ~2.500 tick do Bóng Mực tự sinh hạ hết 3 lửa (`lines=250`) | Đọc kỹ dòng log `lines=250` trong output của `verify.py` thay vì chỉ thấy `PASS` | Tạo `p2_perf_21600_scenario.json` (`invuln_ticks=25000`) và assert `end.ticks == 21600` trong `scripts/verify.py` & `test_phase2_features.py` |
