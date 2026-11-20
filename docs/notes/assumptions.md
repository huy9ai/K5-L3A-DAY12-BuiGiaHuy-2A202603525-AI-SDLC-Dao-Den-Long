# Giả định & Tiêu chí nghiệm thu theo Phase

> Ghi mọi chỗ mơ hồ đã tự chốt giả định và tiêu chí nghiệm thu kiểm chứng được ("Làm A thì thấy B") **trước khi code** mỗi phase.

---

## Checkpoint 0 (Chuẩn bị)
- **Môi trường local:** Máy phát triển chạy Windows, có Python 3.14.10, `pytest` 8.4.2, `git`, `Docker`.
- **Quyết định nền tảng:** Python 3 stdlib + WebGL2 + Web Audio API (0 phụ thuộc ngoài).

---

## Phase 1 (PRD-0 — Đêm 1: Đảo Bến + Test Contract v1.0)
*(Đã hoàn thành và được chuẩn hóa lại số liệu sang Contract v1.1 ở Phase 2 theo TICKET-02.)*

---

## Phase 2 (TICKET-02 — Ba hòn đảo + Test Contract v1.1)

### Giả định cho các chi tiết kỹ thuật mở trong TICKET-02
| ID | Chỗ mở / Cần chốt | Giả định đã chọn | Lý do |
|---|---|---|---|
| P2-A1 | Điểm xuất phát người chơi ở Đêm 3 (Đảo Chuông) | `(0, 0, -15)` hướng `+Z` | Tâm `(0, 0)` của Đảo Chuông bị chiếm bởi Tầng 2 (`r <= 8m, Y=6`) và Tháp Chuông (`r <= 2m, Y=6..14`); đặt tại `(0, 0, -15)` trên Tầng 0 an toàn, không vướng tháp và nhìn thẳng về đồi bậc thang |
| P2-A2 | Đường đi của Gió Lạc khi `idle` và `flee` | Gió Lạc là sinh vật bay trên không (`Y ~ 1.0–1.5m`) nên không bị chặn bởi mặt nước/vách đá, lượn vòng chậm `2 m/s` quanh khu vực spawn khi `idle` | Khớp mô tả "dải lụa xám xanh bay nhanh", không bị kẹt địa hình cầu tre Đảo Cau |
| P2-A3 | Hạt đom đóm rơi bị đánh gần mép đảo | Nếu điểm rơi vòng `1.5–2.5m` rơi ra ngoài biển mây thì giữ hạt tại chân Mây trên mặt đất đảo gần nhất | Tránh rơi đom đóm xuống khoảng không không thể nhặt lại |
| P2-A4 | Thời gian tăng tốc/dừng (`<= 0.1 s`) | Phản hồi đạt vận tốc chuẩn ngay trong 1 tick (`1/60s ≈ 0.0167s <= 0.1s`) | Đáp ứng đúng yêu cầu `<= 0.1 s` đồng thời giữ độ chính xác toán học cho test quãng đường `speed * t` |
| P2-A5 | Giá trị `ttl_s` của đom đóm thường (`kind: "random"`) trong snapshot | `null` (`None`) cho đom đóm thường vĩnh viễn và số giây thực (`> 0`) cho đom đóm rơi (`kind: "dropped"`) | Phân biệt rõ loại không hết hạn với loại có TTL 480 tick (`8.0s`) |

### Tiêu chí nghiệm thu (Acceptance Criteria — đủ Phần 1, 2, 3, 4 của TICKET-02)
| ID | Hạng mục (TICKET-02) | Tiêu chí kiểm tra ("Làm A -> thấy B") | Cách kiểm chứng |
|---|---|---|---|
| P2-AC1 | Số liệu chuẩn & Contract v1.1 | `game.contract.json` bản `1.1` khớp mọi hằng số Phần 1 & 4; `core/config.py` nạp nguyên vẹn | `test_tuning_matches_contract_json` |
| P2-AC2 | Thứ tự 12 bước & Hồi quy Phase 1 | Mọi kịch bản thắng/thua/safe_radius Đêm 1 chạy đúng với số chuẩn (`lantern_cost=10`, `safe_radius=6.0`, `+10` điểm khi nạp) | `test_phase1_core.py` & `test_phase1_contract.py` |
| P2-AC3 | Lướt (`dash`) mặt đất & trên không | Nhấn `dash` -> chạy `14 m/s` trong `12 tick` (`2.8m`), hồi `90 tick`; lướt khi đang nhảy giữ nguyên tọa độ `Y` | `test_dash_headless_ground_and_air_holds_y` |
| P2-AC4 | Rơi khỏi đảo (`Y < -10`) | Đi ra mép đảo dù có `invuln_ticks=120` -> rơi xuống `Y < -10`, mất `1` lửa + mất hết đom đóm (`by="fall", lost=4`), chờ `60 tick` rồi hồi sinh tại spawn với `vel=0` và `invuln=true` | `test_fall_ignores_invuln_loses_motes_waits_60_and_respawns` |
| P2-AC5 | Bóng Mực 5 trạng thái, recoil, đẩy safe_radius 30 tick & đom đóm rơi | Đèn vừa thắp đẩy Bóng Mực bên trong ra mép `6m` trong `<= 30` tick và không gây sát thương; khi chạm Mây tạo đom đóm `dropped` (`TTL=480`) và chuyển `recoil` | `test_shade_5_states_safe_radius_pushout_and_dropped_mote_ttl` |
| P2-AC6 | Tỏa Sáng 3D + đẩy 15 tick | Nhấn `pulse` (3 đom đóm) -> check khoảng cách 3D `<= 5m` từ `Y+0.8`, đẩy lùi `4m` trong `15 tick`, `+5` điểm/con | `test_pulse_3d_distance_15_tick_push_and_cooldown` |
| P2-AC7 | Tạm dừng (`pause`) | Nhấn `pause` -> `tick` tiếp tục tăng nhưng `sim_tick` và `time_left_s` đứng yên, `state="paused"`; nhấn lần 2 -> `resumed` | `test_pause_freezes_sim_tick_and_timers` |
| P2-AC8 | Đêm 2: Đảo Cau, cầu tre, bục nhảy, Gió Lạc & Bùa Gió | Đi vào bục `(20,0,18)` -> bay ~1.4s đáp sang đảo B (`r < 28m` quanh `(70,0)`) không bị ghi đè phím; nhặt Bùa Gió chạy `7.2 m/s` & Lướt 0 hồi chiêu; Gió Lạc cướp 3 đom đóm rồi Tỏa Sáng đánh rơi lại `drifter_drop` | `test_night2_launch_pad_lands_on_island_b`, `test_night2_charm_drifter_steal_and_pulse_drop` |
| P2-AC9 | Đêm 3: 3 tầng, dốc, vách, bục nhảy tầng 2, tháp chuông & gió mạnh | Leo dốc `30°` lên `Y=3`; bị chặn ở vách dựng đứng & tháp chuông `r < 2m`; bục `(0,3,13)` phóng lên tầng 2 `Y=6`; gió thổi ở tick `1800` đẩy `2 m/s` | `test_night3_ramp_headless_and_tiers_tower_wind` |
| P2-AC10 | Sửa lỗi lật camera/phím Phase 1 & giao diện 3 Đêm đầy đủ | `mat4LookAt` dùng chuẩn right-handed `x_cam = (zz, 0, -zx)`; UI có Menu, Intro Ông Đăng, Pause, Cài đặt lưu `localStorage`, HUD 10 ô, mũi tên chỉ đèn ngoài màn hình, 11 SFX & bảng màu chuẩn | `test_web_routes_campaign_pause_dash_and_camera_fix` + kiểm tra trực quan |
| P2-AC11 | Hiệu năng headless 21.600 tick | Chạy đầy đủ Đêm 3 `21.600` tick ở chế độ headless trong `<= 30.0s` | `test_full_night3_21600_ticks_under_30s` + `scripts/verify.py` |

---

## Phase 3 (Ticket-03) — *Chờ phát hành*
## Phase 4 (Ticket-04) — *Chờ phát hành*
