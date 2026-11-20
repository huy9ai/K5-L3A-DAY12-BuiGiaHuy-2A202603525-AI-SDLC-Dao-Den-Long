---
name: independent-review
description: Perform an independent audit of code, tests, Test Contract compliance, and proof before tagging a phase.
---

# Skill: Independent Phase Review

Dùng skill này bởi một subagent hoặc phiên AI **tách biệt với người/agent đã viết code** trước khi gắn tag `phase-N`.

## Checklist kiểm tra
1. **Diff & Kiến trúc:** Chạy `git status` và `git diff` (hoặc `git log -p -n 5`). Xác nhận `src/dao_den_long/core/` không import `http`, `web`, UI, `time`, hay global `random`.
2. **Test Contract & Determinism:** Kiểm tra CLI headless khớp nguyên văn định dạng, cờ lệnh, schema JSON và exit code của tài liệu phase.
3. **Chất lượng Test:** Kiểm tra không có test rỗng, test luôn PASS giả, hoặc `@unittest.skip` / `pytest.mark.skip` không có giải thích trong `docs/notes/decisions.md`.
4. **Chạy lại độc lập:** Tự thực thi `python scripts/verify.py` (hoặc `python3 scripts/verify.py`) và xác nhận exit code `0`.
5. **Bằng chứng & Ghi chú:** Đối chiếu `docs/proof/<phase>/README.md` và `docs/proof/<phase>/verify-output.txt` xem có khớp mã hiện tại không; kiểm tra `docs/notes/ai-log.md` và `docs/notes/assumptions.md` đã được cập nhật.
6. **Ghi kết luận:** Tạo hoặc cập nhật `docs/proof/<phase>/review.md` ghi rõ các mục đã kiểm, lệnh đã chạy, lỗi phát hiện (nếu có) và phán quyết `APPROVED` hoặc `CHANGES_REQUESTED`.
