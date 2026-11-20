# Bằng chứng kiểm chứng Phase 3 (TICKET-03 — Change Request "Đèn cạn dầu" + Test Contract v1.2)

- **Báo cáo chạy thật & Benchmark 21.600 tick:** [verify-output.txt](verify-output.txt)
- **Đánh giá độc lập (Independent Review):** [review.md](review.md)
- **Quyết định thiết kế & Giải trình test cũ bị ảnh hưởng (ADR-005):** [decisions.md](../../notes/decisions.md)
- **Breaking Changes Changelog:** [CHANGELOG.md](../../../CHANGELOG.md)
- **Giả định & Acceptance Criteria đầy đủ:** [assumptions.md](../../notes/assumptions.md)

## Bảng truy vết Yêu cầu TICKET-03 & DoD → Bằng chứng

| Yêu cầu (TICKET-03 & Contract v1.2) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `game.contract.json` (`1.2`) đồng bộ 100% số liệu & khóa mới (`fuel_max`, `fuel_decay_per_s`, `fuel_per_mote`, `relight_cost`, `win_ratio`, `drain_per_s`, `low_fuel_threshold`, `capacity_max`, `240/270/300 s`, `score`) | So sánh đầy đủ `asdict(load_tuning()) == raw["tuning"]` | [verify-output.txt](verify-output.txt), `test_tuning_matches_contract_json` | DAT |
| Nhiên liệu đèn dùng đơn vị nguyên `1/60`, hao `1/s`, tắt đèn `lantern_out` ngay sau Bước 2, `ever_lit`, thắp lại tốn `5` (`+40`, `relight: true`) | Chạy headless `p3_fuel_relight_refuel_scenario.json` + `p3_fuel_relight_refuel_inputs.json` | `test_headless_fuel_decay_lantern_out_relight_refuel_and_capacity_growth` | DAT |
| Châm dầu `ceil((100 - fuel) / 10)` và bỏ qua đèn đầy (`used = 0`) | Unit test cả 3 trường hợp: `fuel=80.0`, thiếu đúng `10.0`, và đèn đầy `fuel=100` bỏ qua để chọn đèn tắt kế tiếp | `test_refuel_exact_ceil_formula_and_full_lantern_skipped` | DAT |
| Ranh giới vùng an toàn đúng `30.0` (còn) vs `< 30` (mất); Bóng Mực `wander -> drain`, hút `5/s` cộng dồn, `fuel_drain` mỗi `60` tick | Chạy headless `p3_shade_drain_scenario.json` & unit test 2 Bóng Mực cộng dồn (`11/s`), `drain -> chase` (`<= 6m`), `drain -> wander`, `stunned -> wander` | `test_fuel_30_safe_radius_boundary_and_weak_lantern_drain`, `test_multi_shade_drain_stacking_pulse_15_pts_refuel_pushout_and_transitions` | DAT |
| Châm dầu lên `>= 30` đẩy Bóng Mực ra mép `6 m` trong `<= 30` tick không sát thương; Tỏa Sáng con đang `drain` thưởng tổng `+15` | Unit test trực tiếp điểm `+15` vs `+5` và vòng lặp đẩy 30 tick | `test_multi_shade_drain_stacking_pulse_15_pts_refuel_pushout_and_transitions` | DAT |
| Luật thắng Bình minh (`dawn_survived`, bỏ `all_lit`), ngưỡng `3/5` (N1), `4/6` (N2), `5/7` (N3), thưởng `+50 + floor(fuel)` + `50 × flames`, `no_flames` ưu tiên đúng tick bình minh | Chạy headless `win_scenario.json` (xác nhận thắp 5/5 không thắng sớm) & unit test cả 3 Đêm + ưu tiên `no_flames` | `test_win_scenario_full_flow_and_determinism`, `test_dawn_survival_thresholds_all_nights_scoring_and_no_flames_priority` | DAT |
| Sức chứa tăng dần `min(20, 10 + 2 * successful_lights)` (không tính đèn đặt sẵn scenario) & Validation lỗi mã thoát `2` | Chạy headless nhặt đủ 12 đom đóm sau 1 lần thắp + unit test trần 20 + CLI test 3 scenario sai v1.2 | `test_headless_fuel_decay_lantern_out_relight_refuel_and_capacity_growth`, `test_capacity_growth_capped_at_20_and_v12_validation_errors` | DAT |
| Chế độ mù màu (`#00B3FF`, `#FFFFFF` + `⚠`, đèn tắt xẹp `20%` + vết rách, nhấp nháy `1 Hz`, thanh dầu) & Tạo hình Áo Dài + Nón Lá + ánh sáng điểm WebGL2 | Kiểm tra router `/health`, `/`, `/static/app.js`, `/api/state` (`win_needed=3/4/5`) & công thức right-handed `mat4LookAt` | `test_web_routes_campaign_pause_dash_colorblind_aodai_and_camera`, [app.js](../../../src/dao_den_long/web/static/app.js) | DAT (API/Code); kiểm tra thị giác trực tiếp bởi học viên khi mở `python run.py` (do môi trường không có `chrome_devtools` MCP) |
| Hồi quy Phase 1–2 không bị thay thế + Tính tất định 5 kịch bản (SHA-256 x2) + Benchmark 21.600 tick `<= 30s` | Chạy đầy đủ `scripts/verify.py` (27/27 test PASS, 5x SHA-256, 21.600 tick `<= 2.5s`) | [verify-output.txt](verify-output.txt) | DAT |
| DoD Change Request: ADR mô hình đèn & luật thắng, cập nhật test có lý do (0 skip âm thầm), Changelog Breaking Changes, Review độc lập | Đối chiếu [decisions.md](../../notes/decisions.md) (ADR-005), [CHANGELOG.md](../../../CHANGELOG.md), [review.md](review.md) | [decisions.md](../../notes/decisions.md), [CHANGELOG.md](../../../CHANGELOG.md), [review.md](review.md) | DAT |
