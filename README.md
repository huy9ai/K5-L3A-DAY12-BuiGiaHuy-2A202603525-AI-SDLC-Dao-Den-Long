# Đảo Đèn Lồng — Day 12 AI SDLC (Phase 1: Đêm 1 – Đảo Bến)

> **Video demo (< 5 phút):** *(Chưa quay — sẽ cập nhật link công khai tại Release `v1.0.0` ở Checkpoint 5)*

Game 3D góc nhìn thứ ba: **Mây** đội nón lá mang đèn lồng nhỏ, chạy quanh hòn đảo tròn **Đảo Bến** thu thập đom đóm, thắp sáng lại **5 Đèn Lồng Lớn** (`L1`–`L5`) và né hoặc tỏa sáng xua **Bóng Mực** trong sương đen.

---

## Cài đặt & Chạy game (≤ 3 lệnh)

Yêu cầu duy nhất: **Python 3.10+** (không cần `npm`, không cần `pip install`; hỗ trợ Linux, macOS và Windows).

```bash
git clone https://github.com/huy9ai/K5-L3A-DAY12-BuiGiaHuy-2A202603525-AI-SDLC-Dao-Den-Long.git
cd K5-L3A-DAY12-BuiGiaHuy-2A202603525-AI-SDLC-Dao-Den-Long
python3 run.py
```

*(Trên Windows dùng `python run.py`, sau đó mở trình duyệt tới `http://127.0.0.1:8000`. Hoặc chạy bằng Docker: `docker build -t dao-den-long . && docker run -p 8000:8000 dao-den-long`.)*

---

## Điều khiển

| Phím / Thao tác | Chức năng |
|---|---|
| `W` `A` `S` `D` / `↑` `↓` | Di chuyển theo góc nhìn camera |
| `Space` | Nhảy |
| `E` hoặc `F` | Nạp đom đóm vào Đèn Lồng Lớn gần nhất (bán kính `3.0m`, cần `4` đom đóm để thắp sáng) |
| `Q` hoặc `Shift` hoặc Chuột phải | Tỏa sáng xua Bóng Mực (tốn `2` đom đóm, bán kính `7.0m`, choáng `3.0s`, đẩy lùi `6.0m`, hồi `3.0s`) |
| Kéo chuột hoặc `←` `→` / Cuộn chuột | Xoay và phóng gần/xa camera góc nhìn thứ ba |
| `R` | Chơi lại Đêm 1 |
| `M` | Bật/tắt âm thanh |

---

## Cách tính điểm & Thông số (`game.contract.json`)

Toàn bộ thông số gameplay nằm trong [game.contract.json](game.contract.json) (`Test Contract v1.0`):

- **Nhặt 1 đom đóm:** `+10` điểm (`per_mote = 10`, sức chứa tối đa `carry_capacity = 6`).
- **Tỏa sáng trúng 1 Bóng Mực:** `+50` điểm (`per_stun = 50`).
- **Thắp sáng 1 Đèn Lồng Lớn:** `+200` điểm (`per_lantern = 200`, cần `lantern_cost = 4`).
- **Thưởng khi thắng (thắp đủ 5 đèn):** `+5` điểm mỗi giây còn lại (`floor(time_left_s) × 5`) và `+100` điểm mỗi ngọn lửa còn lại (`flames × 100`, tối đa `3` lửa).
- **Khi bị Bóng Mực chạm:** mất `1` ngọn lửa, đánh rơi `50%` số đom đóm đang giữ (`floor(carried × 0.5)`), bất tử tạm `2.0s`. Đèn đã thắp tạo vùng an toàn bán kính `5.0m` (`safe_radius = 5.0`) chặn Bóng Mực. `fall_enabled = false` (mép đảo có ranh giới mềm, không phạt rơi).

---

## Chế độ Headless (Test Contract v1.0) & Kiểm chứng

```bash
# Chạy chế độ headless đúng Test Contract v1.0
python3 run.py headless --seed 42 --night 1 --ticks 600 --out out.jsonl

# Chạy toàn bộ bộ kiểm chứng (Contract, Unit test, Headless Scenario, Determinism SHA-256, Quét bảo mật)
python3 scripts/verify.py
```

---

## Sáng tạo của tôi

Mọi mở rộng sáng tạo đều được giữ tách biệt hoàn toàn ở tầng hiển thị & âm thanh (`src/dao_den_long/web/`), **không làm thay đổi bất kỳ byte nào của đầu ra chế độ headless**:
- **Bầu không khí đảo sáng dần theo tiến độ:** Bầu trời và mặt đất đảo chuyển dần từ tím sương đêm sang vàng cam ấm khi từng Đèn Lồng Lớn (`1/5` → `5/5`) được thắp sáng, kèm vòng hào quang vùng an toàn `safe_radius` trên mặt đất.
- **Tạo hình Mây & Đom đóm quay quanh:** Mây đội nón lá có chiếc đèn lồng nhỏ treo trước nón, cùng các đốm đom đóm đang giữ bay vòng quanh nhân vật và sóng ánh sáng tỏa ra khi kích hoạt Tỏa sáng.
- **Âm thanh ngũ cung procedural (Web Audio API):** Tự sinh âm thanh chuông nhẹ khi nhặt đom đóm, hợp âm ấm khi thắp đèn, tiếng sóng tỏa sáng và cảnh báo khi chạm Bóng Mực — không dùng file audio ngoài, không rủi ro bản quyền.
- **Bằng chứng không phá Test Contract:** Toàn bộ kiểm thử [test_phase1_contract.py](tests/test_phase1_contract.py) và kết quả SHA-256 trong [docs/proof/phase-1/verify-output.txt](docs/proof/phase-1/verify-output.txt) xác nhận headless tuân thủ 100% Contract v1.0.

---

## Tài liệu SDLC, Bằng chứng & Harness AI

- **Harness AI & CI:** [AGENTS.md](AGENTS.md), [.agents/skills/](.agents/skills/), [.githooks/pre-commit](.githooks/pre-commit), [.claude/settings.json](.claude/settings.json), [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **Ghi chép SDLC:** [assumptions.md](docs/notes/assumptions.md), [decisions.md](docs/notes/decisions.md), [ai-log.md](docs/notes/ai-log.md), [retro.md](docs/notes/retro.md)
- **Bằng chứng kiểm chứng:** [Phase 1 Proof](docs/proof/phase-1/README.md) · [CP0 Proof](docs/proof/cp0/README.md)
- **Bản quyền & Nguồn:** [LICENSE](LICENSE), [CREDITS.md](CREDITS.md), [CHANGELOG.md](CHANGELOG.md), [LAB_SPEC.md](docs/LAB_SPEC.md)
