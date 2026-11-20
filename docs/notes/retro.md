# Evaluation theo Phase & Retro cuối dự án

---

## 1. Đánh giá từng Phase

### Phase 1 (PRD-0 — Đêm 1: Đảo Bến + Test Contract v1.0)
- **Yêu cầu đạt / chưa đạt:** Đạt toàn bộ lõi headless & tính năng Phase 1; tuy nhiên khi chơi bản 3D phát hiện lỗi đảo trục trong `mat4LookAt` khiến bản đồ bị lật ngược và bấm `D` đi sang trái.
- **Điều cần chỉnh:** Đã sửa triệt để ở Phase 2 và khóa bằng regression test.

### Phase 2 (TICKET-02 — Ba hòn đảo + Test Contract v1.1)
- **Yêu cầu đạt / chưa đạt:** Đạt toàn bộ 3 bản đồ chuẩn, 12 bước tick, Lướt, Rơi, 5 trạng thái Bóng Mực, Gió Lạc, Bùa Gió, Tạm dừng, Gió Đêm 3, sửa camera `mat4LookAt`, giao diện 3 Đêm + 11 SFX và benchmark 21.600 tick `1.220s <= 30s`.
- **Điều cần chỉnh:** Giữ ranh giới sạch giữa `maps.py`, `engine.py`, `headless/` và `web/` để đón Change Request ở Phase 3.

### Phase 3 (TICKET-03 — Change Request "Đèn cạn dầu" + Test Contract v1.2)
- **Yêu cầu đạt / chưa đạt:**
  - **ĐẠT:** Mô hình nhiên liệu nguyên `1/60` (`fuel_60` `0..6000`), hao dầu `1/s`, châm dầu `ceil((100-fuel)/10)`, tắt đèn `lantern_out` (`ever_lit`, thắp lại tốn `5`), Bóng Mực trạng thái `drain` (hút `5/s` cộng dồn, `fuel_drain` mỗi 60 tick, mất vùng an toàn khi `< 30` và giữ ở đúng `30.0`, đẩy ra mép `6 m` trong `<= 30` tick khi châm lên `>= 30`, thưởng `+15` khi Tỏa Sáng con đang `drain`), luật thắng Bình minh (`240/270/300 s`, bỏ `all_lit`, ngưỡng `3/5` - `4/6` - `5/7`, `no_flames` ưu tiên trước), sức chứa động `10..20`, bảng điểm mới, Chế độ mù màu (`#00B3FF`, `#FFFFFF` + `⚠`, đèn tắt xẹp 20% + vết rách, nhấp nháy 1 Hz + thanh dầu), nâng cấp thẩm mỹ Áo Dài + Nón Lá & ánh sáng điểm WebGL2.
  - **DoD đầy đủ:** Có ADR-005 trong `docs/notes/decisions.md`, mục `Breaking Changes` trong `CHANGELOG.md`, cập nhật có lý do các test bị ảnh hưởng (không skip âm thầm), toàn bộ test không bị thay thế của Phase 1–2 tiếp tục PASS 100%, và review độc lập lưu tại `docs/proof/phase-3/review.md`.
  - **LƯU Ý:** Kiểm chứng trực quan Áo Dài/Nón Lá, Chế độ mù màu và FPS trình duyệt tiếp tục cần học viên mở `http://127.0.0.1:8000` sau khi chạy `python run.py` do môi trường thiếu `chrome_devtools` MCP.
- **Điều cần chỉnh ở phase sau:** Giữ toàn bộ test Contract v1.2 xanh để sẵn sàng đón **Phase 4 (Ticket-04)** và bước đóng gói `v1.0.0` (CP5).

### Phase 4 (Ticket-04) — *Chưa thực hiện*

---

## 2. Retro tổng kết cuối dự án (Hoàn thành ở Checkpoint 5)
- **Số liệu tổng hợp:**
- **Điều hiệu quả nhất khi làm với AI:**
- **Điều không hiệu quả / sai lầm đáng nhớ:**
- **Harness nào giúp nhiều nhất:**
- **Nếu làm lại từ đầu sẽ đổi gì:**
