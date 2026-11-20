# AGENTS.md — Đảo Đèn Lồng (AI Harness & Rules)

## Kiến trúc & ranh giới module
- `game.contract.json`: Nguồn chân lý duy nhất cho tham số `tuning` (**Contract v1.2**); `src/dao_den_long/core/config.py` đọc trực tiếp từ đây.
- `src/dao_den_long/core/`: Logic thuần Python 3 stdlib (`config.py`, `maps.py`, `engine.py`), **tất định tuyệt đối** (60 tick/giây `DT = 1/60`, chỉ dùng `random.Random(seed)`, góc cực đo từ `+X` ngược chiều kim đồng hồ trong `XZ`, nhiên liệu đèn tính bằng số nguyên đơn vị `1/60` `fuel_60 ∈ [0, 6000]`, tọa độ làm tròn 3 chữ số, `fuel` 1 chữ số; CẤM `time.*`, global `random`, DOM, HTTP, UI).
- `src/dao_den_long/core/engine.py`: Tuân thủ chặt **thứ tự 12 bước** (trừ dầu & tắt đèn `fuel <= 0` ngay cuối bước 2), 6 trạng thái Bóng Mực (`spawning`, `wander`, `chase`, `recoil`, `stunned`, `drain`), luật thắng bình minh `dawn_survived` (`>= ceil(0.6 * total)` đèn sáng, không thắng sớm `all_lit`), sức chứa tăng dần `10..20`.
- `src/dao_den_long/headless/`: CLI tuân thủ **Test Contract v1.2** (`--night 1|2|3`, rising-edge nút bấm; file inputs/scenario/flag sai trả mã thoát `2`).
- `src/dao_den_long/web/`: Server HTTP stdlib + WebGL2 3D (`static/`). Camera `mat4LookAt` giữ chuẩn **right-handed (`x_cam = normalize(cross(up, z_cam))`)**. Hỗ trợ chế độ mù màu, thanh dầu, đèn tắt xẹp 20% + vết rách, Mây mặc Áo Dài + Nón Lá. Sáng tạo chỉ ở tầng này, KHÔNG làm đổi output headless.

## Lệnh chuẩn (Windows / macOS / Linux)
- Chạy game 3D: `python3 run.py` (Windows: `python run.py`) -> `http://127.0.0.1:8000`
- Chạy headless (Contract v1.2): `python3 run.py headless --seed 42 --night 1 --ticks 600 --out /tmp/out.jsonl`
- Kiểm chứng tổng & benchmark (1 lệnh): `python3 scripts/verify.py`
- Chạy pytest (tùy chọn): `pytest -v`

## Quy tắc bắt buộc
1. **Trung thực tuyệt đối:** Không tạo test luôn đạt, không sửa tay output. Yêu cầu chưa xong ghi rõ `CHUA DAT` kèm lý do.
2. **Không tắt test âm thầm:** Khi Change Request làm test cũ sai, sửa hoặc thay thế kèm ADR/lý do trong `docs/notes/decisions.md` và ghi Breaking Changes trong `CHANGELOG.md`.
3. **Không kết thúc khi đỏ:** Không báo hoàn thành nếu `scripts/verify.py` trả mã khác `0`.
4. **Bảo vệ tính tất định & hiệu năng:** Xuất file bằng `encoding="utf-8"` và `newline="\n"`; headless chỉ gọi `sys.executable`; 1 Đêm đầy đủ chạy xong trong `<= 30s`.
5. **Review độc lập mỗi phase:** Trước khi tag `phase-N`, dùng subagent/session khác người viết code review theo `.agents/skills/independent-review/SKILL.md` và lưu tại `docs/proof/phase-N/review.md`.
6. **Bảo mật & Git:** Không commit `.env`/API key; không `git push --force` sau khi đã gắn tag.

## Thành phần Harness & Khi nào dùng
| Thành phần | Đường dẫn | Khi nào sử dụng |
|---|---|---|
| Hướng dẫn dự án | `AGENTS.md` | Nạp đầu mọi phiên AI; cập nhật ở mỗi phase / khi phát hiện lỗi lặp |
| Skill kiểm chứng | `.agents/skills/verify-phase/SKILL.md` | Cuối mỗi bước build hoặc trước khi lưu bằng chứng phase |
| Skill review độc lập | `.agents/skills/independent-review/SKILL.md` | Cuối mỗi phase trước khi gắn tag `phase-N` |
| Git pre-commit hook | `.githooks/pre-commit` | Tự chạy trước mỗi `git commit` (chặn `.env` và test đỏ) |
| Claude Stop hook | `.claude/settings.json` | Tự chặn agent dừng phiên nếu `verify.py --quick` đang đỏ |
| GitHub Actions CI | `.github/workflows/ci.yml` | Tự chạy trên `ubuntu-latest` mỗi lần `push` và tag `phase-*` |
