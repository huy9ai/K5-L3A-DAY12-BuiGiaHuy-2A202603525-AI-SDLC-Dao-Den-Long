---
name: verify-phase
description: Run automated unit tests, headless scenarios, determinism checks, and capture real proof for a lab phase.
---

# Skill: Verify Phase & Capture Proof

Dùng skill này ở cuối mỗi vòng build hoặc trước khi chốt bằng chứng cho `phase-N` (hoặc `cp0`).

## Các bước thực hiện
1. Đảm bảo mọi thay đổi đã lưu trên đĩa.
2. Chạy một lệnh kiểm chứng tổng và xuất log thật:
   - Linux/macOS: `python3 scripts/verify.py --phase <phase-name> --write-proof`
   - Windows: `python scripts/verify.py --phase <phase-name> --write-proof`
3. Kiểm tra exit code phải là `0`. Nếu khác `0`, đọc lỗi, sửa nguyên nhân gốc và chạy lại (không bao giờ sửa tay file `verify-output.txt`).
4. Đối chiếu từng yêu cầu trong `docs/notes/assumptions.md` với kết quả thực tế vừa chạy.
5. Cập nhật bảng truy vết tại `docs/proof/<phase-name>/README.md`:
   - Cột: `Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả`
   - Nếu mục nào chưa hoàn thành hoặc lỗi, ghi rõ `CHUA DAT` và nguyên nhân.
6. Nếu đã chạy `pytest`, ghi rõ phiên bản và kết quả chạy thực tế sau lần sửa cuối.
