# Bằng chứng kiểm chứng Phase 2 (TICKET-02 — Ba hòn đảo + Test Contract v1.1)

- **Báo cáo chạy thật & Benchmark 21.600 tick:** [verify-output.txt](verify-output.txt)
- **Đánh giá độc lập (Independent Review):** [review.md](review.md)
- **Ghi chép giả định & Acceptance Criteria đầy đủ:** [assumptions.md](../../notes/assumptions.md)

## Bảng truy vết Yêu cầu TICKET-02 → Bằng chứng

| Yêu cầu (TICKET-02 & Contract v1.1) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `game.contract.json` (`1.1`) đồng bộ 100% số liệu chuẩn Phần 1 | So sánh mọi trường `tuning` & `score` với `load_tuning()` | [verify-output.txt](verify-output.txt), `test_tuning_matches_contract_json` | DAT |
| Sửa lỗi lật ngược map & ngược `D/A` của Phase 1 (`mat4LookAt`) | Kiểm tra công thức tích có hướng right-handed `x_cam = (zz, 0, -zx)` và hướng phím `buildMoveVector()` | `test_web_routes_campaign_pause_dash_and_camera_fix`, [app.js](../../../src/dao_den_long/web/static/app.js) | DAT (Code/Router) / Xác nhận thị giác bởi học viên khi chơi `python run.py` |
| Thứ tự 12 bước trong tick & hồi quy toàn bộ kịch bản Phase 1 | Chạy lại thắng, thua (`no_flames`, `dawn`), `safe_radius`, mã thoát `2` với số chuẩn Phần 1 | [test_phase1_core.py](../../../tests/test_phase1_core.py), [test_phase1_contract.py](../../../tests/test_phase1_contract.py) | DAT (12/12 hồi quy PASS) |
| Lướt (`dash`): 14 m/s, 0.2s, hồi 1.5s, lướt trên không giữ nguyên Y | Chạy headless `p2_dash_scenario.json` + `p2_dash_inputs.json` | `test_dash_headless_ground_and_air_holds_y` | DAT |
| Rơi (`Y < -10`): bỏ qua bất tử, mất hết đom đóm, chờ 60 tick rồi hồi sinh bất tử 90 tick | Chạy headless `p2_fall_scenario.json` + `p2_fall_inputs.json` | `test_fall_ignores_invuln_loses_motes_waits_60_and_respawns` | DAT |
| Bóng Mực 5 trạng thái (`spawning/wander/chase/recoil/stunned`), đẩy `safe_radius` <= 30 tick & đom đóm rơi (`TTL=480`) | Test đèn vừa thắp đẩy Bóng Mực ra mép 6m không sát thương + kiểm tra đom đóm rơi | `test_shade_5_states_safe_radius_pushout_and_dropped_mote_ttl` | DAT |
| Tạm dừng (`pause`): giữ `tick`, đóng băng `sim_tick` & đồng hồ | Chạy headless `p2_pause_inputs.json` | `test_pause_freezes_sim_tick_and_timers` | DAT |
| Đêm 2 (Đảo Cau): 2 đảo, cầu tre, bục nhảy A->B, Bùa Gió, Gió Lạc cướp & thả | Chạy headless `p2_night2_pad_charm_drifter_scenario.json` & test phóng qua đảo B | `test_night2_charm_drifter_steal_and_pulse_drop`, `test_night2_launch_pad_lands_on_island_b` | DAT |
| Đêm 3 (Đảo Chuông): 3 tầng, vách đứng, 2 dốc, bục nhảy tầng 2, tháp chuông, gió mạnh mỗi 30s | Chạy headless `p2_night3_tiers_wind_scenario.json` & test vách/tháp/bục nhảy/gió | `test_night3_ramp_headless_and_tiers_tower_wind` | DAT |
| Tính tất định 3 Đêm (`--night 1\|2\|3`, SHA-256 x2) | Chạy 2 lần mỗi Đêm 1, 2, 3 và so sánh SHA-256 byte-exact | [verify-output.txt](verify-output.txt) | DAT |
| Hiệu năng headless Đêm đầy đủ (21.600 tick `<= 30s`) | Chạy `p2_perf_21600_scenario.json` đủ 21.600 tick Đêm 3 | [verify-output.txt](verify-output.txt), `test_full_night3_21600_ticks_under_30s` | DAT (`~1.15s <= 30.0s`) |
| Giao diện 3 Đêm (Menu, Intro Ông Đăng, Pause, Settings, HUD 10 ô, mũi tên chỉ đèn, 11 SFX, bảng màu chuẩn) & FPS >= 30 ở 1280×720 | Kiểm tra router `/api/*` + kiểm tra trực quan khi chạy trình duyệt | `test_web_routes_campaign_pause_dash_and_camera_fix` | DAT (API/Code); FPS trình duyệt tích hợp sẵn đồng hồ đo trên HUD (chưa tự động mở Chrome do thiếu `chrome_devtools` MCP) |
