# Bằng chứng Checkpoint 0 (CP0 — Chuẩn bị môi trường & khung dự án)

## Bảng truy vết kiểm chứng CP0

| Mục CP0 (`CHECKPOINTS.md`) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Tạo repo cá nhân, đúng quy ước tên & kiểm tra `Public` trên GitHub | Kiểm tra `origin` URL (`K5-L3A-DAY12-BuiGiaHuy-2A202603525-AI-SDLC-Dao-Den-Long`) | Repo GitHub remote; xác nhận chế độ Public trên web GitHub do học viên tự kiểm | DAT (tên & remote) / CHUA XAC NHAN (Public UI — học viên kiểm) |
| Chọn công cụ AI, engine, ngôn ngữ & chạy thử chương trình "hello" 3D + headless | Chạy `python scripts/verify.py --phase cp0 --write-proof` & `pytest -v` (kiểm tra core, headless CLI và router WebGL2) | [verify-output.txt](verify-output.txt) | DAT (3/3 unit & smoke tests PASS) |
| Tính tất định headless bước đầu (cùng seed/ticks -> cùng output byte) | Chạy `run.py headless --seed 42 --ticks 30` 2 lần, so sánh SHA-256 | [verify-output.txt](verify-output.txt) | DAT (SHA-256 trùng khớp `9868f662...`) |
| Sẵn sàng nơi ghi chép (giả định, quyết định, AI log, retro) & Harness AI + CI | Kiểm tra file trong `docs/notes/`, `AGENTS.md`, `.agents/skills/`, `.githooks/pre-commit`, `.claude/settings.json`, `.github/workflows/ci.yml` | Các file đã commit trên nhánh `main` | DAT |
| Mở tab Phase 1 trên Lab Board (`claude.ai`) và hỏi thử trợ giảng | Thử mở qua browser agent | Trình duyệt thiếu kết nối Chrome DevTools MCP nên chưa tự đọc được Lab Board | CHUA DAT (cần học viên đăng nhập claude.ai và dán `PRD-0` + `Test Contract`) |
