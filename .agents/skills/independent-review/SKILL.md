---
name: independent-review
description: Perform an independent audit of code, Contract v1.3 compliance, benchmark/soak/leaderboard/accessibility requirements, camera orientation, performance, and proof before tagging a phase.
---

# Skill: Independent Phase Review

Dùng skill này bởi một subagent hoặc phiên AI **tách biệt với người/agent đã viết code** trước khi gắn tag `phase-N` và `v1.0.0`.

## Checklist kiểm tra
1. **Diff & Kiến trúc:** Xác nhận `src/dao_den_long/core/` không import `http`, `web`, UI, `time`, hay global `random`; nhiên liệu đèn dùng đơn vị nguyên `1/60` (`fuel_60`).
2. **Test Contract v1.3 & Yêu cầu Phase 4 (TICKET-04):**
   - Kiểm tra `game.contract.json` (`contract_version: "1.3"`, có `bench_cmd` và `soak_cmd`).
   - Kiểm tra chế độ Benchmark (`run.py bench --seed 42 --duration 30 --out bench.json`): cảnh Đêm 1 `1280×720`, đúng `200` Bóng Mực `wander` + `100` đom đóm + `3` đèn sáng `L1–L3`, tắt sinh thêm/sát thương/nhặt/hao dầu/kết thúc Đêm và tắt hiệu ứng sáng tạo thêm, camera bay vòng `r=30m, Y=15m, T=15s` CCW từ `(30,15,0)` nhìn vào `(0,0,0)`, `3s` warmup, công thức `avg_fps`, `p1_low_fps`, `frame_ms_p95`, `load_ms`, `peak_mem_mb`.
   - Kiểm tra Soak test (`run.py soak --seed 7 --nights 10 --out soak.json`): 10 Đêm liên tiếp xoay vòng 1→2→3 trong cùng tiến trình, `seed 7 + i`, xác suất input chuẩn (`30` tick đổi hướng, `5%` nhảy, `3%` lướt, `2%` tỏa sáng, `10%` tương tác), `crashes == 0`, `mem_end_mb <= 1.2 * mem_start_mb`.
   - Kiểm tra Bảng xếp hạng cục bộ: lưu top 10 trên đĩa, tên `3–12` ký tự `[A-Za-z0-9_]` (+ tiếng Việt), `score` giảm dần (bằng điểm ai đạt trước đứng trên), nhập tên sau thắng Đêm 3 hoặc thua bất kỳ Đêm nào, lệnh `--export-leaderboard out.json`.
   - Kiểm tra Dễ tiếp cận (Accessibility): đổi phím 9 hành động + phát hiện trùng phím + khôi phục mặc định + lưu bền; phụ đề & mũi tên mép màn hình chỉ Bóng Mực xuất hiện, gió, 10s cuối, đèn `< 30`; giảm chuyển động; cỡ chữ `>= 18px` + chữ lớn `×1.25`.
3. **Hồi quy Phase 1–3 & Hồ sơ phát hành:** Mọi test cũ còn hiệu lực vẫn đạt (0 skip âm thầm), `bench.json` và `soak.json` chạy thật đã commit, `README.md`, `CHANGELOG.md` (4 phase), `CREDITS.md`, `LICENSE`, `docs/notes/retro.md` đầy đủ.
4. **Chạy lại độc lập:** Tự thực thi `python scripts/verify.py` và `pytest -v` và ghi phán quyết `APPROVED` / `CHANGES_REQUESTED` vào `docs/proof/<phase>/review.md`.
