# Evaluation theo Phase & Retro cuối dự án

---

## 1. Đánh giá từng Phase

### Phase 1 (PRD-0 — Đêm 1: Đảo Bến + Test Contract v1.0)
- **Yêu cầu đạt / chưa đạt:** Đạt toàn bộ lõi headless & tính năng Phase 1; tuy nhiên khi người dùng tự chơi bản 3D phát hiện lỗi đảo ngược trục `x_cam`/`y_cam` trong `mat4LookAt` khiến bản đồ bị lật ngược và bấm `D` đi sang trái.
- **Điều cần chỉnh:** Đã sửa triệt để ngay đầu Phase 2 và thêm test kiểm tra ma trận view.

### Phase 2 (TICKET-02 — Ba hòn đảo + Test Contract v1.1)
- **Yêu cầu đạt / chưa đạt:**
  - **ĐẠT:** Chuẩn hóa toàn bộ hằng số & bảng điểm vào `game.contract.json` (`1.1`); cài đặt đủ 3 bản đồ chuẩn (`Đảo Bến`, `Đảo Cau` + cầu tre + 2 bục nhảy, `Đảo Chuông` 3 tầng + 2 dốc + bục nhảy + tháp chuông + gió mạnh); cài đặt đúng thứ tự 12 bước trong tick; đầy đủ Dash, Rơi (`Y < -10`), 5 trạng thái Bóng Mực (`spawning/wander/chase/recoil/stunned`), đẩy `safe_radius` <= 30 tick, Gió Lạc, Bùa Gió, Tạm dừng (`pause`), sửa lỗi lật camera `mat4LookAt`, giao diện 3 Đêm (Menu, Intro Ông Đăng, Pause, Cài đặt lưu `localStorage`, HUD 10 ô, mũi tên ngoài màn hình, 11 SFX + nhạc đêm).
  - **Hiệu năng:** Mô phỏng headless 21.600 tick (Đêm 3) hoàn tất dưới ngưỡng `30s` (xem số đo thật trong `docs/proof/phase-2/verify-output.txt`).
  - **LƯU Ý:** Phần trực quan 3D và FPS thực tế `>= 30 FPS` ở `1280×720` trên trình duyệt chưa đo tự động qua Chrome vì thiếu `chrome_devtools` MCP; bộ đếm FPS được tích hợp sẵn trên HUD góc trên phải để học viên kiểm chứng trực tiếp khi chạy `python run.py`.
- **Hồi quy Phase 1:** Toàn bộ kiểm thử hồi quy Đêm 1 đã cập nhật theo số chuẩn Phần 1 và đều PASS.
- **Điều cần chỉnh ở phase sau:** Giữ thiết kế tách lớp `maps.py` <-> `engine.py` <-> `web/` để sẵn sàng đón các thay đổi luật ở `Ticket-03` (Phase 3 chỉ có 30 phút!).

### Phase 3 (Ticket-03) — *Chưa thực hiện*
### Phase 4 (Ticket-04) — *Chưa thực hiện*

---

## 2. Retro tổng kết cuối dự án (Hoàn thành ở Checkpoint 5)
- **Số liệu tổng hợp:**
- **Điều hiệu quả nhất khi làm với AI:**
- **Điều không hiệu quả / sai lầm đáng nhớ:**
- **Harness nào giúp nhiều nhất:**
- **Nếu làm lại từ đầu sẽ đổi gì:**
