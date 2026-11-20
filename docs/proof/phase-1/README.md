# Bằng chứng kiểm chứng Phase 1 (PRD-0 — Đêm 1: Đảo Bến + Test Contract v1.0)

- **Báo cáo chạy thật:** [verify-output.txt](verify-output.txt)
- **Đánh giá độc lập (Independent Review):** [review.md](review.md)
- **Ghi chép giả định & tiêu chí nghiệm thu:** [assumptions.md](../../notes/assumptions.md)

## Bảng truy vết Yêu cầu → Bằng chứng

| Yêu cầu (PRD-0 & Contract v1.0) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `game.contract.json` hợp lệ & đồng bộ 100% với engine | Kiểm tra schema + so sánh mọi giá trị `tuning` với `load_tuning()` | [verify-output.txt](verify-output.txt), `test_tuning_matches_contract_json` | DAT |
| Khối lượng công thức di chuyển, xoay `cam_yaw_deg`, chuẩn hóa vector, nhảy & trọng lực | Chạy 60 tick theo trục/góc quay & kiểm tra tọa độ | `test_movement_yaw_and_vector_normalization`, `test_jump_rising_edge_and_gravity` | DAT |
| Nhặt đom đóm, giới hạn `carry_capacity = 6`, rising-edge nạp đèn & thắp đèn `L1..L5` | Scenario có sẵn 8 đom đóm & đèn cận kề; giữ nút `interact` qua nhiều tick | `test_pickup_capacity_and_rising_edge_deposit`, [win_scenario.json](../../../tests/scenarios/win_scenario.json) | DAT |
| Tỏa sáng xua Bóng Mực (`stunned`, đẩy lùi `6m`, tốn `2` đom đóm, cooldown `3.0s`) | Kích hoạt `pulse` trong phạm vi `7.0m`, thử nhấn tiếp ngay khi còn cooldown | `test_pulse_stuns_pushes_and_enforces_cooldown`, `test_win_scenario_full_flow_and_determinism` | DAT |
| Đèn đã thắp chặn Bóng Mực ngoài `safe_radius = 5.0m` | Chạy `safe_radius_scenario.json` 180 tick | `test_lit_lantern_safe_radius_blocks_shade` | DAT |
| Thua do mất hết lửa (`no_flames` + `hit_drop_ratio = 0.5`) & thua hết giờ (`dawn`) | Chạy `lose_flames_scenario.json` & `lose_dawn_scenario.json` qua CLI headless | `test_lose_no_flames_and_drop_ratio`, `test_lose_dawn` | DAT |
| Thắng khi thắp đủ 5 đèn (`all_lit`) & tính đủ thưởng điểm | Chạy kịch bản thắng `win_scenario.json` + `win_inputs.json` -> `ticks=226, score=2090` | `test_win_scenario_full_flow_and_determinism`, [verify-output.txt](verify-output.txt) | DAT |
| Dựng `scenario` không phát sự kiện / không cộng điểm | Khởi tạo đèn đặt sẵn `lit: true`, kiểm tra `score == 0` | `test_scenario_setup_emits_no_score_and_preserves_other_lanterns` | DAT |
| Headless CLI tất định tuyệt đối & mã thoát `2` khi file inputs/scenario sai | Chạy `run.py headless` 2 lần so sánh SHA-256 trên 2 kịch bản; thử 4 trường hợp đầu vào lỗi | [verify-output.txt](verify-output.txt), `test_default_night1_determinism_without_scenario`, `test_invalid_inputs_and_scenarios_exit_code_2` | DAT |
| Giao diện 3D WebGL2 + HUD + chơi lại + sáng tạo âm thanh (không làm đổi headless) | Kiểm tra API `/health`, `/`, `/static/app.js`, `/api/state`, `/api/tick`, `/api/reset` & chặn path traversal | `test_web_routes_gameplay_tick_and_reset` | DAT (API/Router) / CHUA TU DONG MO TRINH DUYET (thiếu Chrome DevTools MCP — xác nhận thủ công trên `http://127.0.0.1:8000`) |
