# Giả định & Tiêu chí nghiệm thu theo Phase

> Ghi mọi chỗ mơ hồ đã tự chốt giả định và tiêu chí nghiệm thu kiểm chứng được ("Làm A thì thấy B") **trước khi code** mỗi phase.

---

## Checkpoint 0 (Chuẩn bị)
- **Môi trường local:** Máy phát triển chạy Windows, có Python 3.14.10, `pytest` 8.4.2, `git`, `Docker` (chưa cài `node`/`npm`).
- **Quyết định nền tảng:** Chọn Python 3 stdlib + WebGL2 để không phụ thuộc cài thêm gói ngoài, chạy đồng nhất trên Windows/macOS/Linux.

---

## Phase 1 (PRD-0 — Đêm 1: Đảo Bến + Test Contract v1.0)

### Giả định cho các chỗ PRD-0 để mở
| ID | Chỗ mơ hồ trong PRD-0 | Giả định đã chọn (khớp `game.contract.json`) | Lý do |
|---|---|---|---|
| P1-A1 | Kích thước đảo & vị trí 5 Đèn Lồng Lớn | Đảo tròn bán kính `50m`, tâm `(0, 0, 0)`; `L1..L5` bố trí đều trên vòng bán kính `25m` với `L1` tại `[0, 0, 25]` | Khớp ví dụ scenario `L1: [0,0,25]` trong Contract D và đủ rộng cho 5 vùng đèn cách nhau ~`29.4m` |
| P1-A2 | Rơi khỏi đảo (`fall_enabled`) | `fall_enabled = false`, mép đảo chặn mềm người chơi trong bán kính `50m` (mở rộng động nếu scenario đặt thực thể xa hơn) | An toàn cho chơi thử ở Phase 1, không phát sự kiện rơi ngoài ý muốn |
| P1-A3 | Các thông số `tuning` & `score` | `player_speed=6.0`, `carry_capacity=6`, `lantern_cost=4`, `pickup_radius=1.5`, `interact_radius=3.0`, `pulse_cost=2`, `pulse_radius=7.0`, `pulse_stun_s=3.0`, `pulse_push_m=6.0`, `pulse_cooldown_s=3.0`, `safe_radius=5.0`, `shade_speed=3.8`, `shade_hit_radius=1.2`, `flames=3`, `invuln_s=2.0`, `hit_drop_ratio=0.5`, `night1_duration_s=300` | `6 * 0.5 = 3` số nguyên chẵn; đủ 1 lần thắp đèn (`4`) + 1 lần pulse (`2`) từ túi đầy; thời lượng 5 phút cân bằng Đêm 1 |
| P1-A4 | Tốc độ sinh ngẫu nhiên khi `random_motes`/`random_shades` bật | Khởi đầu `15` đom đóm (`M1..M15`), tối đa `18` (bù mỗi `240` tick); khởi đầu `2` Bóng Mực (`S1, S2`), tối đa `5` (thêm mỗi `2100` tick ngoài `safe_radius`) | Giữ nhịp độ chơi mượt, không quá thưa cũng không gây quá tải ở giai đoạn đầu |
| P1-A5 | Thưởng thời gian & ngọn lửa khi thắng | `floor(round(time_left_s, 6)) * 5 + flames * 100` | Rõ ràng, tất định, tránh sai số dấu phẩy động khi tròn giây |
| P1-A6 | Số lượng Bóng Mực & đom đóm khi `scenario` truyền danh sách | Theo đúng Contract D: thay thế danh sách ban đầu, đánh ID tự động tuần tự (`S1..`, `M1..`) không trùng ID đã khai báo, giữ nguyên 0 event / 0 điểm khi dựng | Tuân thủ nguyên văn Test Contract v1.0 mục D |

### Tiêu chí nghiệm thu (Acceptance Criteria)
| ID | Yêu cầu | Tiêu chí kiểm tra ("Làm A -> thấy B") | Cách kiểm chứng |
|---|---|---|---|
| P1-AC1 | `game.contract.json` hợp lệ & đồng bộ | Đọc `game.contract.json` và khởi tạo `Night1Simulation` -> mọi thông số tuning khớp nhau tuyệt đối | `test_tuning_matches_contract_json` + `scripts/verify.py` |
| P1-AC2 | Di chuyển + xoay camera + chuẩn hóa vector + nhảy | Chạy 60 tick với `move=[1,1]` -> đi đúng `6.0m` theo hướng 45°; `cam_yaw_deg=90` + `move=[0,1]` -> đi `+X`; nhấn `jump` -> `y > 0` rồi đáp `y = 0` | `test_movement_yaw_and_vector_normalization`, `test_jump_rising_edge_and_gravity` |
| P1-AC3 | Nhặt đom đóm & nạp đèn (rising edge) | Đi qua 8 đom đóm -> chỉ nhặt `6` (`carry_capacity`), `+60` điểm; giữ `interact=true` 2 tick gần đèn -> nạp `4` đom đóm đúng 1 lần, đèn `lit=true`, `+200` điểm | `test_pickup_capacity_and_rising_edge_deposit` |
| P1-AC4 | Tỏa sáng xua Bóng Mực & hồi chiêu | Nhấn `pulse` gần `S1` -> `S1` đổi `state="stunned"`, bị đẩy lùi `6m`, mất `2` đom đóm, `+50` điểm; nhấn lại ngay -> bị chặn bởi cooldown | `test_pulse_stuns_pushes_and_enforces_cooldown` |
| P1-AC5 | Bóng Mực đuổi, `safe_radius`, chạm mất lửa & rơi đom đóm | Đèn sáng giữ Bóng Mực ở `dist >= 5.0m`; khi bị chạm với `flames=1, carried=2` -> `flames=0, dropped=1`, `game_over(lost, no_flames)` | `test_lit_lantern_safe_radius_blocks_shade`, `test_lose_no_flames_and_drop_ratio` |
| P1-AC6 | Thắng (`all_lit`) & thua hết giờ (`dawn`) | Nạp đủ đèn cuối -> `game_over(won, all_lit)` + thưởng điểm; hết `time_left_s` -> `game_over(lost, dawn)` | `test_win_scenario_full_flow_and_determinism`, `test_lose_dawn` |
| P1-AC7 | Tính tất định & mã lỗi Contract B/C | Chạy `run.py headless` 2 lần cùng seed/scenario/inputs -> file JSONL giống nhau từng byte; inputs/scenario lỗi -> exit code `2` | `test_default_night1_determinism_without_scenario`, `test_invalid_inputs_and_scenarios_exit_code_2` |
| P1-AC8 | Chơi được 3D + HUD + chơi lại (Playable WebGL2) | Mở `/` hiển thị HUD, đảo, Mây đội nón lá, 5 đèn, đom đóm, Bóng Mực; `/api/tick` cập nhật trạng thái; `/api/reset` chơi lại | `test_web_routes_gameplay_tick_and_reset` + kiểm tra trực tiếp trên trình duyệt |

---

## Phase 2 (Ticket-02 — Ba hòn đảo) — *Chờ dán nội dung Ticket-02*
*(Sẽ cập nhật giả định & Acceptance Criteria ngay khi bước sang Phase 2)*

## Phase 3 (Ticket-03) — *Chờ phát hành*

## Phase 4 (Ticket-04) — *Chờ phát hành*
