# Đảo Đèn Lồng — Day 12 AI SDLC (Phase 2: Ba hòn đảo · Contract v1.1)

> **Video demo (< 5 phút):** *(Chưa quay — sẽ cập nhật link công khai tại Release `v1.0.0` ở Checkpoint 5)*

Game 3D góc nhìn thứ ba: **Mây** đội nón lá mang đèn lồng nhỏ, vượt qua chuỗi **3 Đêm** trên ba hòn đảo (**Đêm 1 — Đảo Bến**, **Đêm 2 — Đảo Cau**, **Đêm 3 — Đảo Chuông**) thu thập đom đóm, thắp sáng lại các Đèn Lồng Lớn, né/xua **Bóng Mực**, đối phó **Gió Lạc** & gió mạnh và giữ Ngọn Lửa tới bình minh.

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
| `E` hoặc `F` | Nạp đom đóm vào Đèn Lồng Lớn gần nhất (bán kính `2.0 m`, cần `10` đom đóm/đèn) |
| `Q` | Tỏa Sáng xua Bóng Mực & Gió Lạc (tốn `3` đom đóm, bán kính 3D `5.0 m`, hồi `3.0 s`) |
| Kéo chuột hoặc `←` `→` / Cuộn chuột | Xoay và phóng gần/xa camera góc nhìn thứ ba |
| `Esc` hoặc `P` | Tạm dừng game (Menu: Tiếp tục / Chơi lại Đêm / Cài đặt / Về Menu) |

---

## Thông số chuẩn & Cách tính điểm (`game.contract.json` v1.1)

Toàn bộ số liệu chuẩn được đồng bộ trực tiếp từ [game.contract.json](game.contract.json):
- **3 Đêm:** Đêm 1 Đảo Bến (`300 s`, `5` đèn) · Đêm 2 Đảo Cau (`330 s`, `6` đèn, cầu tre + 2 bục nhảy + Bùa Gió + Gió Lạc) · Đêm 3 Đảo Chuông (`360 s`, `7` đèn, 3 tầng + 2 dốc + bục nhảy + tháp chuông + gió mạnh mỗi `30 s`).
- **Điểm số chuẩn hóa:**
  - `+10` mỗi đom đóm **nạp vào đèn** (`per_mote = 10`).
  - `+100` mỗi Đèn Lồng Lớn được thắp sáng (`per_lantern = 100`).
  - `+5` mỗi Bóng Mực trúng Tỏa Sáng (`per_stun = 5`, kể cả đang choáng).
  - Thưởng thắng Đêm: `+ floor(giây còn lại) × 2 + 50 × Ngọn Lửa còn lại`. Tổng điểm chiến dịch = tổng điểm các Đêm đã thắng.
- **Rơi khỏi đảo (`Y < -10 m`) & Bị đánh:** Rơi mất `1` Ngọn Lửa (bỏ qua bất tử), mất toàn bộ đom đóm đang giữ, chờ `60 tick` rồi hồi sinh với bất tử `90 tick`. Bị Bóng Mực chạm mất `1` Ngọn Lửa, rơi `floor(đang mang / 2)` đom đóm tồn tại `480 tick` (nhặt lại được từ tick sau).

---

## Chế độ Headless (Test Contract v1.1) & Kiểm chứng

```bash
# Chạy headless cho Đêm 1, 2 hoặc 3 theo Test Contract v1.1
python3 run.py headless --seed 42 --night 1 --ticks 600 --out out_n1.jsonl
python3 run.py headless --seed 42 --night 2 --ticks 600 --out out_n2.jsonl
python3 run.py headless --seed 42 --night 3 --ticks 21600 --out out_n3.jsonl

# Chạy toàn bộ bộ kiểm chứng (Contract v1.1, Unit + Hồi quy, 3-Night SHA-256, Benchmark 21.600 tick <= 30s)
python3 scripts/verify.py
```

---

## Sáng tạo của tôi

Mọi phần sáng tạo nằm riêng tại tầng hiển thị & âm thanh (`src/dao_den_long/web/`), **không làm thay đổi bất kỳ byte nào của đầu ra chế độ headless**:
- **Thể hiện 3 hòn đảo & bảng màu chuẩn bằng WebGL2 thuần:** Đảo Cau hai bờ cầu tre, Đảo Chuông 3 tầng với vách đứng, dốc gỗ và tháp chuông, hiệu ứng hạt lá bay khi Đêm 3 báo gió, cùng ánh sáng môi trường tăng theo công thức `0.15 + 0.55 × (đèn sáng / tổng đèn)`.
- **Mây đội nón lá + khăn đỏ & hệ thống âm thanh procedural Web Audio:** Tự sinh nhạc nền đêm nhẹ và đầy đủ 11 hiệu ứng âm thanh (nhặt, nạp/thắp đèn, Tỏa Sáng, bị đánh, nhảy, lướt, thắng, thua, Bóng Mực xuất hiện, báo gió, đếm ngược 10 giây cuối) mà không cần file âm thanh ngoài.
- **Bằng chứng không phá Test Contract:** Toàn bộ kiểm thử hồi quy Phase 1 + kiểm thử Phase 2 và 3-Night SHA-256 trong [docs/proof/phase-2/verify-output.txt](docs/proof/phase-2/verify-output.txt) xác nhận headless tuân thủ 100% Contract v1.1.

---

## Tài liệu SDLC, Bằng chứng & Harness AI

- **Harness AI & CI:** [AGENTS.md](AGENTS.md), [.agents/skills/](.agents/skills/), [.githooks/pre-commit](.githooks/pre-commit), [.claude/settings.json](.claude/settings.json), [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **Ghi chép SDLC:** [assumptions.md](docs/notes/assumptions.md), [decisions.md](docs/notes/decisions.md), [ai-log.md](docs/notes/ai-log.md), [retro.md](docs/notes/retro.md)
- **Bằng chứng kiểm chứng:** [Phase 2 Proof](docs/proof/phase-2/README.md) · [Phase 1 Proof](docs/proof/phase-1/README.md) · [CP0 Proof](docs/proof/cp0/README.md)
- **Bản quyền & Nguồn:** [LICENSE](LICENSE), [CREDITS.md](CREDITS.md), [CHANGELOG.md](CHANGELOG.md), [LAB_SPEC.md](docs/LAB_SPEC.md)
