# Đảo Đèn Lồng — Day 12 AI SDLC

> **Video demo (< 5 phút):** *(Chưa quay — sẽ cập nhật link công khai tại Release `v1.0.0` ở Checkpoint 5)*

Game 3D góc nhìn thứ ba: **Mây** thu thập đom đóm để thắp lại các Đèn Lồng Lớn và né Bóng Mực trong sương đen. Dự án được xây dựng bằng kiến trúc tách biệt hoàn toàn logic mô phỏng tất định (`core/`) khỏi tầng hiển thị 3D (`web/`), không phụ thuộc thư viện ngoài ở runtime và chạy đồng nhất trên Linux, macOS và Windows.

---

## Cài đặt & Chạy nhanh (≤ 3 lệnh)

Yêu cầu duy nhất: **Python 3.10+** (không cần `npm`, không cần `pip install`).

```bash
git clone https://github.com/huy9ai/K5-L3A-DAY12-BuiGiaHuy-2A202603525-AI-SDLC-Dao-Den-Long.git
cd K5-L3A-DAY12-BuiGiaHuy-2A202603525-AI-SDLC-Dao-Den-Long
python3 run.py
```

*(Trên Windows dùng `python run.py`, sau đó mở trình duyệt tới `http://127.0.0.1:8000`.)*

### Chạy chế độ Headless & Bộ kiểm chứng (1 lệnh)

```bash
# Chạy chế độ headless (CP0 scaffold — sẽ cập nhật theo Test Contract của PRD-0)
python3 run.py headless --seed 42 --ticks 20

# Chạy toàn bộ unit test, kiểm tra tính tất định SHA-256 và quét bảo mật
python3 scripts/verify.py
```

---

## Điều khiển (Bản CP0 Hello 3D)
- **Kéo chuột:** Xoay góc nhìn quanh Đèn Lồng.
- **Space / Nút "Thắp nhịp đèn":** Kích nhịp sáng Đèn Lồng.
- **Nút "Đặt lại":** Đưa mô phỏng về trạng thái ban đầu của seed.

*(Các phím điều khiển nhân vật Mây sẽ được cập nhật ở Phase 1 theo PRD-0.)*

---

## Tài liệu SDLC, Bằng chứng & Harness AI

| Nhóm tài liệu | Đường dẫn | Nội dung |
|---|---|---|
| Đề bài & Quy định gốc | [docs/LAB_SPEC.md](docs/LAB_SPEC.md), [GUIDE.md](GUIDE.md), [RUBRIC.md](RUBRIC.md), [RULES.md](RULES.md), [CHECKPOINTS.md](CHECKPOINTS.md), [SUBMISSION.md](SUBMISSION.md) | Tài liệu gốc của bài Lab |
| Harness AI & CI | [AGENTS.md](AGENTS.md), [.agents/skills/](.agents/skills/), [.githooks/pre-commit](.githooks/pre-commit), [.claude/settings.json](.claude/settings.json), [.github/workflows/ci.yml](.github/workflows/ci.yml) | Hướng dẫn agent, skill kiểm chứng, review độc lập, hook chặn test đỏ và CI Linux |
| Ghi chép SDLC | [assumptions.md](docs/notes/assumptions.md), [decisions.md](docs/notes/decisions.md), [ai-log.md](docs/notes/ai-log.md), [retro.md](docs/notes/retro.md) | Giả định, tiêu chí nghiệm thu, đổi thiết kế, nhật ký AI/token và retro |
| Bằng chứng kiểm chứng | [docs/proof/cp0/](docs/proof/cp0/README.md) | Kết quả chạy thật và báo cáo truy vết theo từng phase |
| Bản quyền & Nguồn | [LICENSE](LICENSE), [CREDITS.md](CREDITS.md), [CHANGELOG.md](CHANGELOG.md) | Giấy phép MIT và nguồn asset |

---

## Sáng tạo của tôi

*(Dành cho Phase 4 — Hạng mục F: các mở rộng gọn ở tầng hiển thị/âm thanh không làm thay đổi đầu ra chế độ headless.)*
