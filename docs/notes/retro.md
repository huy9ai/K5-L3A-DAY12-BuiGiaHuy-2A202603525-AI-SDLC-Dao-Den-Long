# Evaluation theo Phase & Retro cuối dự án

---

## 1. Đánh giá từng Phase

### Phase 1 (PRD-0 — Đêm 1: Đảo Bến + Test Contract v1.0)
- **Yêu cầu đạt / chưa đạt:**
  - **ĐẠT:** Đầy đủ game 3D WebGL2 Đêm 1 – Đảo Bến (Mây đội nón lá có đèn lồng, 5 Đèn Lồng Lớn, đom đóm, Bóng Mực, nhảy, tỏa sáng xua Bóng Mực, thắng/thua/điểm/chơi lại, HUD, âm thanh procedural), `game.contract.json`, chế độ headless Test Contract v1.0 tất định từng byte, bộ test đơn vị + tích hợp + router web, cùng review độc lập.
  - **LƯU Ý:** Phần chơi trực tiếp trên trình duyệt được kiểm chứng bằng unit/router tests của API `/api/tick` + `/api/reset`; chưa tự động mở cửa sổ Chrome kiểm tra thị giác trong phiên agent do thiếu `chrome_devtools` MCP (học viên có thể mở `http://127.0.0.1:8000` sau `python run.py` để xác nhận trực quan).
- **Hồi quy:** Thay thế `test_cp0_smoke.py` bằng 3 bộ test Phase 1 (`test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py`) có lý do ghi trong [decisions.md](decisions.md); toàn bộ 13/13 test và kiểm tra SHA-256 đều PASS.
- **Điều cần chỉnh ở phase sau:** Giữ ranh giới `core/` <-> `web/` chặt chẽ khi `Ticket-02 · Ba hòn đảo` mở rộng bản đồ nhiều đảo; sẵn sàng cập nhật `game.contract.json` nếu Test Contract nâng phiên bản.

### Phase 2 (Ticket-02) — *Chưa thực hiện*
- **Yêu cầu đạt / chưa đạt:**
- **Hồi quy Phase 1:**
- **Điều cần chỉnh ở phase sau:**

### Phase 3 (Ticket-03) — *Chưa thực hiện*
- **Yêu cầu đạt / chưa đạt:**
- **Xử lý thay đổi luật cũ & hồi quy:**
- **Điều cần chỉnh ở phase sau:**

### Phase 4 (Ticket-04) — *Chưa thực hiện*
- **Yêu cầu đạt / chưa đạt (kèm đo hiệu năng):**
- **Hồi quy Phase 1–3:**

---

## 2. Retro tổng kết cuối dự án (Hoàn thành ở Checkpoint 5)
- **Số liệu tổng hợp:**
- **Điều hiệu quả nhất khi làm với AI:**
- **Điều không hiệu quả / sai lầm đáng nhớ:**
- **Harness nào giúp nhiều nhất:**
- **Nếu làm lại từ đầu sẽ đổi gì:**
