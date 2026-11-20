# AGENTS.md — Đảo Đèn Lồng (AI Harness & Rules)

## Kiến trúc & ranh giới module
- `src/dao_den_long/core/`: Logic thuần Python 3 stdlib, **tất định tuyệt đối** (chỉ dùng `random.Random(seed)`, timestep cố định `dt`; CẤM `time.*`, global `random`, DOM, HTTP, UI).
- `src/dao_den_long/headless/`: CLI tuân thủ chính xác **Test Contract** của phase hiện tại.
- `src/dao_den_long/web/`: Server HTTP stdlib + giao diện 3D WebGL2 (`static/`). Mọi sáng tạo thêm chỉ nằm ở tầng này, KHÔNG được làm thay đổi output headless.

## Lệnh chuẩn (Windows / macOS / Linux)
- Chạy game 3D: `python3 run.py` (Windows: `python run.py`) -> `http://127.0.0.1:8000`
- Chạy headless: `python3 run.py headless --seed 42 --ticks 20`
- Kiểm chứng tổng (1 lệnh): `python3 scripts/verify.py`
- Chạy pytest (tùy chọn): `pytest -v`

## Quy tắc bắt buộc
1. **Trung thực tuyệt đối:** Không tạo test luôn đạt, không sửa tay output. Yêu cầu chưa xong ghi rõ `CHUA DAT` kèm lý do.
2. **Không tắt test âm thầm:** Khi ticket mới làm test cũ sai, sửa hoặc xóa test đó kèm lý do rõ trong `docs/notes/decisions.md`.
3. **Không kết thúc khi đỏ:** Không báo hoàn thành nếu `scripts/verify.py` trả mã khác `0`.
4. **Bảo vệ tính tất định:** Mọi file văn bản/proof xuất bằng `encoding="utf-8"` và `newline="\n"`; headless chỉ gọi `sys.executable`.
5. **Review độc lập mỗi phase:** Trước khi tag `phase-N`, dùng subagent/session khác người viết code thực hiện review theo `.agents/skills/independent-review/SKILL.md` và lưu tại `docs/proof/phase-N/review.md`.
6. **Bảo mật & Git:** Không commit `.env`/API key; không `git push --force` sau khi đã gắn tag.

## Thành phần Harness & Khi nào dùng
| Thành phần | Đường dẫn | Khi nào sử dụng |
|---|---|---|
| Hướng dẫn dự án | `AGENTS.md` | Nạp đầu mọi phiên AI; cập nhật khi AI mắc cùng lỗi lần 2 |
| Skill kiểm chứng | `.agents/skills/verify-phase/SKILL.md` | Cuối mỗi bước build hoặc trước khi lưu bằng chứng phase |
| Skill review độc lập | `.agents/skills/independent-review/SKILL.md` | Cuối mỗi phase trước khi gắn tag `phase-N` |
| Git pre-commit hook | `.githooks/pre-commit` | Tự chạy trước mỗi `git commit` (chặn `.env` và test đỏ) |
| Claude Stop hook | `.claude/settings.json` | Tự chặn agent dừng phiên nếu `verify.py --quick` đang đỏ |
| GitHub Actions CI | `.github/workflows/ci.yml` | Tự chạy trên `ubuntu-latest` mỗi lần `push` và tag `phase-*` |
