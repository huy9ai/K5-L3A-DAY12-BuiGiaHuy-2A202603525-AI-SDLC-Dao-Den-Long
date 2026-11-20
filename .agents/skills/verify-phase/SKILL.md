---
name: verify-phase
description: Run automated unit tests, Contract v1.2 multi-night headless scenarios, determinism checks, full-night performance benchmark, and capture real proof for a lab phase.
---

# Skill: Verify Phase & Capture Proof

Dùng skill này ở cuối mỗi vòng build hoặc trước khi chốt bằng chứng cho `phase-N`.

## Các bước thực hiện
1. Đảm bảo mọi thay đổi đã lưu trên đĩa.
2. Chạy một lệnh kiểm chứng tổng và xuất log thật (gồm schema Contract v1.2, hồi quy Phase 1–2, kịch bản mới Phase 3 về nhiên liệu/drain/dawn_survived/capacity, kiểm tra SHA-256 x2 cả 3 Đêm và benchmark Đêm đầy đủ `<= 30s`):
   - Linux/macOS: `python3 scripts/verify.py --phase <phase-name> --write-proof`
   - Windows: `python scripts/verify.py --phase <phase-name> --write-proof`
3. Kiểm tra exit code phải là `0`. Nếu khác `0`, đọc lỗi, sửa nguyên nhân gốc và chạy lại (không bao giờ sửa tay file `verify-output.txt`).
4. Đối chiếu từng yêu cầu và Acceptance Criteria trong `docs/notes/assumptions.md` với kết quả thực tế vừa chạy.
5. Cập nhật bảng truy vết tại `docs/proof/<phase-name>/README.md` và chạy `pytest -v`.
