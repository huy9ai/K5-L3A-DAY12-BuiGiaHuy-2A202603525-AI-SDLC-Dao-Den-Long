# Đảo Đèn Lồng — Day 12 AI SDLC (Phase 3: Đèn Cạn Dầu · Contract v1.2)

> **Video demo (< 5 phút):** *(Chưa quay — sẽ cập nhật link công khai tại Release `v1.0.0` ở Checkpoint 5)*

Game 3D góc nhìn thứ ba: **Mây** trong tà **Áo Dài truyền thống Việt Nam & Nón Lá** mang đèn lồng nhỏ, vượt qua chuỗi **3 Đêm** trên ba hòn đảo (**Đảo Bến**, **Đảo Cau**, **Đảo Chuông**) thu thập đom đóm, thắp sáng & châm dầu cho các Đèn Lồng Lớn, ngăn **Bóng Mực** hút dầu, đối phó **Gió Lạc** & gió mạnh và giữ đủ đèn sáng tới tận bình minh.

---

## Cài đặt & Chạy game (≤ 3 lệnh)

Yêu cầu duy nhất: **Python 3.10+** (không cần `npm`, không cần `pip install`; hỗ trợ Linux, macOS và Windows).

```bash
git clone https://github.com/huy9ai/K5-L3A-DAY12-BuiGiaHuy-2A202603525-AI-SDLC-Dao-Den-Long.git
cd K5-L3A-DAY12-BuiGiaHuy-2A202603525-AI-SDLC-Dao-Den-Long
python3 run.py
```

*(Trên Windows dùng `python run.py`, sau đó mở trình duyệt tới `http://127.0.0.1:8000`. Docker: `docker build -t dao-den-long . && docker run -p 8000:8000 dao-den-long`.)*

---

## Điều khiển

| Phím / Thao tác | Chức năng |
|---|---|
| `W` `A` `S` `D` / `↑` `↓` | Di chuyển theo hướng camera (`D` qua phải, `A` qua trái) |
| `Space` | Nhảy (`7.0 m/s`, khi đứng trên mặt đất) |
| `Shift` hoặc Chuột phải | Lướt nhanh (`14.0 m/s` trong `0.2 s`, hồi `1.5 s`, giữ nguyên độ cao khi lướt trên không) |
| `E` hoặc `F` | Thắp đèn (`10` lần đầu / `5` thắp lại) hoặc **Châm dầu** cho đèn đang sáng chưa đầy (`+10` dầu/đom đóm) |
| `Q` | Tỏa Sáng xua Bóng Mực & Gió Lạc (tốn `3` đom đóm, bán kính 3D `5.0 m`, hồi `3.0 s`; `+15` điểm nếu trúng Bóng Mực đang hút dầu) |
| Kéo chuột hoặc `←` `→` / Cuộn chuột | Xoay và phóng gần/xa camera góc nhìn thứ ba |
| `Esc` hoặc `P` | Tạm dừng game (Menu: Tiếp tục / Chơi lại Đêm / Cài đặt & Bảng màu dễ phân biệt / Về Menu) |

---

## Luật chơi & Thông số chuẩn (`game.contract.json` v1.2)

Toàn bộ số liệu chuẩn được đồng bộ trực tiếp từ [game.contract.json](game.contract.json):
- **Mục tiêu Bình minh (Thay thế luật thắng sớm ở Phase 3):**
  - **Đêm 1 — Đảo Bến:** `240 s`, giữ `≥ 3/5` đèn sáng tới bình minh.
  - **Đêm 2 — Đảo Cau:** `270 s`, giữ `≥ 4/6` đèn sáng tới bình minh (cầu tre, 2 bục nhảy, Bùa Gió, Gió Lạc).
  - **Đêm 3 — Đảo Chuông:** `300 s`, giữ `≥ 5/7` đèn sáng tới bình minh (3 tầng, 2 dốc, bục nhảy, tháp chuông, gió mạnh mỗi `30 s`).
- **Nhiên liệu đèn & Bóng Mực hút dầu:**
  - Đèn vừa thắp có `fuel = 100`, tự hao `1.0/giây` (tính theo đơn vị nguyên `1/60`). Hết dầu (`fuel <= 0`) đèn tắt (`lantern_out`), nhớ `ever_lit = true` và lần thắp lại chỉ cần `5` đom đóm.
  - Đèn có `fuel < 30` mất vùng an toàn `6 m` và nhấp nháy chậm `1 Hz`; Bóng Mực ở trạng thái `wander` sẽ tiến vào `<= 2 m` chuyển sang trạng thái `drain` hút thêm `5/giây` (cộng dồn nhiều con). Châm dầu lên `>= 30` khôi phục vùng an toàn và đẩy Bóng Mực ra mép `6 m` trong `<= 30` tick.
- **Sức chứa đom đóm tăng dần:** `min(20, 10 + 2 × số lần thắp thành công trong Đêm)`.
- **Bảng điểm Phase 3:**
  - `+5` mỗi đom đóm nạp vào đèn (thắp mới, thắp lại hoặc châm dầu).
  - `+100` thắp đèn lần đầu · `+40` thắp lại đèn đã từng sáng.
  - `+5` mỗi Bóng Mực trúng Tỏa Sáng (hoặc **tổng `+15`** nếu ngay trước đó đang `drain`).
  - Thưởng thắng Bình minh: `+50 + floor(fuel)` cho mỗi đèn đang sáng + `+50` cho mỗi Ngọn Lửa còn lại (không còn thưởng thời gian).
- **Chế độ mù màu (Bảng màu dễ phân biệt):** Lưu bền trong `localStorage`; đổi viền & mắt Bóng Mực sang `#00B3FF`, màu cảnh báo UI sang `#FFFFFF` kèm biểu tượng `⚠`; đèn tắt xẹp `20%` kèm vết rách dễ nhận biết không cần màu.

---

## Chế độ Headless (Test Contract v1.2) & Kiểm chứng

```bash
# Chạy headless theo Test Contract v1.2
python3 run.py headless --seed 42 --night 1 --ticks 600 --out out_n1.jsonl
python3 run.py headless --seed 42 --night 2 --ticks 600 --out out_n2.jsonl
python3 run.py headless --seed 42 --night 3 --ticks 18000 --out out_n3.jsonl

# Chạy toàn bộ bộ kiểm chứng (Contract v1.2, Unit + Hồi quy + Phase 3, 5x SHA-256, Benchmark 21.600 tick <= 30s)
python3 scripts/verify.py
```

---

## Sáng tạo của tôi

Mọi phần sáng tạo nằm riêng tại tầng hiển thị & âm thanh (`src/dao_den_long/web/`), **không làm thay đổi bất kỳ byte nào của đầu ra chế độ headless**:
- **Mây mặc Áo Dài truyền thống Việt Nam & Nón Lá (`drawMayAoDai`):** Tạo hình Mây bằng WebGL2 với thân Áo Dài cổ đứng màu trắng ngà (`#E8E2D0`), quần lụa rộng, hai tà áo trước/sau viền vàng (`#F2C14E`) phấp phới theo tốc độ chạy, khăn lụa đỏ (`#C8102E`) tung bay, búi tóc gọn và chiếc **Nón Lá** vàng tre nhiều vành treo lồng đèn giấy mini đung đưa phía trước.
- **Ánh sáng điểm động & Bầu trời cổ tích:** Shader WebGL2 tính ánh sáng điểm vàng ấm tỏa ra từ tối đa 7 Đèn Lồng Lớn đang sáng lên mặt đảo/tháp chuông/nhân vật, sương mù đêm theo khoảng cách, bầu trời 60 ngôi sao lấp lánh cùng vầng trăng khuyết, vách đá đảo nổi và rặng tre ven đảo Đêm 1.
- **Đom đóm bay 2 vòng quanh Mây & Thanh dầu trực quan:** Hạt đom đóm bay thành 2 vòng đồng tâm khi sức chứa tăng từ `10 → 20`; thanh dầu chiếu 3D phía trên mỗi đèn đang sáng, tia hút dầu tím/xanh dương khi Bóng Mực `drain`, và 12 hiệu ứng âm thanh + nhạc đêm procedural bằng Web Audio API.
- **Bằng chứng không phá Test Contract:** Toàn bộ kiểm thử hồi quy Phase 1–2, bộ test Phase 3 và 5 kịch bản SHA-256 trong [docs/proof/phase-3/verify-output.txt](docs/proof/phase-3/verify-output.txt) xác nhận headless tuân thủ 100% Contract v1.2.

---

## Tài liệu SDLC, Bằng chứng & Harness AI

- **Harness AI & CI:** [AGENTS.md](AGENTS.md), [.agents/skills/](.agents/skills/), [.githooks/pre-commit](.githooks/pre-commit), [.claude/settings.json](.claude/settings.json), [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **Ghi chép SDLC:** [assumptions.md](docs/notes/assumptions.md), [decisions.md](docs/notes/decisions.md) (ADR-001..005), [ai-log.md](docs/notes/ai-log.md), [retro.md](docs/notes/retro.md)
- **Bằng chứng kiểm chứng:** [Phase 3 Proof](docs/proof/phase-3/README.md) · [Phase 2 Proof](docs/proof/phase-2/README.md) · [Phase 1 Proof](docs/proof/phase-1/README.md) · [CP0 Proof](docs/proof/cp0/README.md)
- **Bản quyền & Nguồn:** [LICENSE](LICENSE), [CREDITS.md](CREDITS.md), [CHANGELOG.md](CHANGELOG.md), [LAB_SPEC.md](docs/LAB_SPEC.md)
