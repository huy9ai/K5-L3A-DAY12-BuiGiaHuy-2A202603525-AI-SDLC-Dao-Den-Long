# Nhật ký dùng AI, lỗi AI & quản lý Token

> Ghi trung thực các công cụ/agent đã dùng, lỗi AI gặp phải, cách chỉnh harness để không lặp lại và ước tính token/chi phí mỗi phase.

---

## Tổng hợp theo Phase

| Phase | Vai trò AI & Lời nhắc chính | Ước tính Token (In / Out) | Cách tiết kiệm token đã áp dụng |
|---|---|---|---|
| CP0 | Dựng cấu trúc repo, harness AI (`AGENTS.md`, skills, hooks, CI), lõi Python + WebGL2 smoke | ~25k / ~6k *(ước lượng)* | Đọc song song tài liệu 1 lần; chọn zero-dependency stdlib không tốn context debug build tool |
| Phase 1 | Phân tích PRD-0 & Contract v1.0; viết core 60Hz, headless CLI, WebGL2 Đảo Bến, tests + subagent review | ~55k / ~14k *(ước lượng)* | Đọc `game.contract.json` làm nguồn duy nhất; chạy gộp kiểm chứng theo batch |
| Phase 2 | Sửa lỗi camera/điều khiển ngược Phase 1; chuẩn hóa 3 bản đồ (`maps.py`), 12-step tick order, Contract v1.1, giao diện 3 Đêm + benchmark + review | ~75k / ~22k *(ước lượng)* | Tách `maps.py` khỏi `engine.py` giúp 3 Đêm dùng chung 1 động cơ mô phỏng; viết song song batch fixture & test |
| Phase 3 | Thực thi Change Request `TICKET-03` ("Đèn cạn dầu", Contract v1.2, `fuel_60` nguyên `1/60`, Shade `drain`, luật Bình minh, sức chứa `10..20`, Colorblind) + nâng cấp thẩm mỹ Áo Dài & Nón Lá WebGL2 + ADR-005 + Changelog Breaking Changes + Review độc lập | ~68k / ~19k *(ước lượng)* | Đọc đồng thời tất cả file test/spec trong 1 lượt; thực hiện viết hàng loạt toàn bộ fixture/test/docs song song; chỉ chạy lại `verify.py` sau khi sửa gọn hết toàn bộ lỗi báo cáo |
| Phase 4 | *(chưa bắt đầu)* | | |

---

## Lỗi AI đã phát hiện & Cách chỉnh Harness

| Phase | Lỗi AI gặp phải | Cách phát hiện | Chỉnh sửa Harness (`AGENTS.md` / skill / hook / code) để không tái diễn |
|---|---|---|---|
| CP0 | Không kết nối được Chrome DevTools MCP để đọc tự động Lab Board | Subagent `browser` báo thiếu MCP server | Dừng đúng quy tắc, nhờ học viên dán nguyên văn đề bài |
| CP0 | Test TCP loopback lỗi `WinError 10013` trong sandbox Windows | Chạy `scripts/verify.py` và đọc traceback | Tách `dispatch_request` thuần + live HTTP test trong Ubuntu CI |
| Phase 1 | Đặt 2 đom đóm thừa dưới chân ở unit test gây fail lần đầu; dùng `&&` trên PowerShell 5.1 | Đọc traceback & sửa test kiểm tra cả tick kế tiếp | Bổ sung quy tắc vào `AGENTS.md` & `decisions.md` |
| Phase 1 (phát hiện sang Phase 2) | **Lỗi nghiêm trọng ở WebGL2 `mat4LookAt`:** Đảo dấu `x_cam = (-zz, 0, zx)` làm lật ngược cả bản đồ lẫn phím `A/D` | Học viên trực tiếp chơi thử bản 3D Phase 1 và báo lại | Sửa `x_cam = (zz, 0, -zx)` trong `app.js`, thêm assertion công thức `mat4LookAt` trong `test_phase1_web.py`, cập nhật `AGENTS.md` & `independent-review/SKILL.md` |
| Phase 2 | Lần chạy benchmark 21.600 tick đầu tiên dừng sớm ở ~2.500 tick do Bóng Mực tự sinh hạ hết 3 lửa (`lines=250`) | Đọc kỹ dòng log `lines=250` trong output của `verify.py` | Tạo `p2_perf_21600_scenario.json` (`invuln_ticks=25000`) và assert `end.ticks == 21600` trong `scripts/verify.py` & `test_phase2_features.py` |
| Phase 3 | Đặt `L5` trong kịch bản test vào tọa độ `[0, 0, 25]` trùng với vị trí mặc định của `L1` (90° trên Đảo Bến) — trước Phase 3 không lộ lỗi vì đèn sáng không nhận tương tác, sang Phase 3 `L1` sáng nhận châm dầu và thắng tie-break `id` trước `L5`; ngoài ra cố gán thuộc tính lên `TuningConfig` frozen | Chạy `scripts/verify.py` và đọc log sự kiện (`refuel` thay vì `deposit`) + `FrozenInstanceError` | Đưa toàn bộ fixture Đêm 1 về đúng vị trí `L1` (`[0, 0, 25]`) không chồng đèn và dùng `dataclasses.replace`; cập nhật `AGENTS.md` & `independent-review/SKILL.md` với checklist riêng cho Contract v1.2 |
