# AGENTS.md — Đảo Đèn Lồng (AI Harness & Rules)

## Kiến trúc & ranh giới module
- `game.contract.json`: Nguồn chân lý duy nhất cho tham số `tuning` (**Contract v1.1**); `src/dao_den_long/core/config.py` đọc trực tiếp từ đây.
- `src/dao_den_long/core/`: Logic thuần Python 3 stdlib (`config.py`, `maps.py`, `engine.py`), **tất định tuyệt đối** (60 tick/giây `DT = 1/60`, chỉ dùng `random.Random(seed)`, góc cực đo từ `+X` ngược chiều kim đồng hồ trong mặt phẳng `XZ`, tọa độ làm tròn 3 chữ số thập phân; CẤM `time.*`, global `random`, DOM, HTTP, UI).
- `src/dao_den_long/core/engine.py`: Tuân thủ chặt **thứ tự 12 bước trong 1 tick**, 5 trạng thái Bóng Mực (`spawning`, `wander`, `chase`, `recoil`, `stunned`), Gió Lạc, Bùa Gió, Lướt (`dash`), Rơi (`Y < -10`), Tạm dừng (`pause`) và Gió Đêm 3.
- `src/dao_den_long/headless/`: CLI tuân thủ **Test Contract v1.1** (`--night 1|2|3`, rising-edge nút bấm; file inputs/scenario/flag sai trả mã thoát `2`).
- `src/dao_den_long/web/`: Server HTTP stdlib + WebGL2 3D (`static/`). Camera `mat4LookAt` phải giữ chuẩn **right-handed (`x_cam = normalize(cross(up, z_cam))`)** để bản đồ thuận chiều và `WASD` đúng trái/phải. Sáng tạo thêm chỉ ở tầng này, KHÔNG làm đổi output headless.

## Lệnh chuẩn (Windows / macOS / Linux)
- Chạy game 3D: `python3 run.py` (Windows: `python run.py`) -> `http://127.0.0.1:8000`
- Chạy headless (Contract v1.1): `python3 run.py headless --seed 42 --night 1 --ticks 600 --out /tmp/out.jsonl`
- Kiểm chứng tổng & benchmark (1 lệnh): `python3 scripts/verify.py`
- Chạy pytest (tùy chọn): `pytest -v`

## Quy tắc bắt buộc
1. **Trung thực tuyệt đối:** Không tạo test luôn đạt, không sửa tay output. Yêu cầu chưa xong ghi rõ `CHUA DAT` kèm lý do.
2. **Không tắt test âm thầm:** Khi ticket mới làm test cũ sai, sửa hoặc thay thế test đó kèm lý do rõ trong `docs/notes/decisions.md`.
3. **Không kết thúc khi đỏ:** Không báo hoàn thành nếu `scripts/verify.py` trả mã khác `0`.
4. **Bảo vệ tính tất định & hiệu năng:** Mọi file văn bản/proof/JSONL xuất bằng `encoding="utf-8"` và `newline="\n"`; headless chỉ gọi `sys.executable`; 1 Đêm đầy đủ (21.600 tick) phải chạy xong trong `<= 30s`.
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
