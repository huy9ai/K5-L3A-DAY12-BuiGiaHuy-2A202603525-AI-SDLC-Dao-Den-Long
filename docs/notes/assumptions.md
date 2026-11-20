# Giả định & Tiêu chí nghiệm thu theo Phase

> Ghi mọi chỗ mơ hồ đã tự chốt giả định và tiêu chí nghiệm thu kiểm chứng được ("Làm A thì thấy B") **trước khi code** mỗi phase.

---

## Checkpoint 0 (Chuẩn bị)
- **Môi trường local:** Máy phát triển chạy Windows, có Python 3.14.10, `pytest` 8.4.2, `git`, `Docker`.
- **Quyết định nền tảng:** Python 3 stdlib + WebGL2 + Web Audio API (0 phụ thuộc ngoài).

---

## Phase 1 (PRD-0 — Đêm 1: Đảo Bến + Test Contract v1.0)
*(Đã hoàn thành và chuẩn hóa dần sang Contract v1.1 ở Phase 2 và v1.2 ở Phase 3.)*

---

## Phase 2 (TICKET-02 — Ba hòn đảo + Test Contract v1.1)

### Giả định cho các chi tiết kỹ thuật mở trong TICKET-02
| ID | Chỗ mở / Cần chốt | Giả định đã chọn | Lý do |
|---|---|---|---|
| P2-A1 | Điểm xuất phát người chơi ở Đêm 3 (Đảo Chuông) | `(0, 0, -15)` hướng `+Z` | Tâm `(0, 0)` của Đảo Chuông bị chiếm bởi Tầng 2 (`r <= 8m, Y=6`) và Tháp Chuông (`r <= 2m, Y=6..14`) |
| P2-A2 | Đường đi của Gió Lạc khi `idle` và `flee` | Sinh vật bay (`Y ~ 1.0–1.5m`) không bị chặn bởi mặt nước/vách đá, lượn chậm `2 m/s` khi `idle` | Khớp mô tả "dải lụa xám xanh bay nhanh", không bị kẹt địa hình cầu tre |
| P2-A3 | Hạt đom đóm rơi bị đánh gần mép đảo | Nếu điểm rơi vòng `1.5–2.5m` rơi ra ngoài biển mây thì giữ hạt tại chân Mây trên mặt đất đảo gần nhất | Tránh mất hạt xuống khoảng không |
| P2-A4 | Thời gian tăng tốc/dừng (`<= 0.1 s`) | Đạt vận tốc chuẩn ngay trong 1 tick (`1/60s <= 0.1s`) | Đáp ứng đúng yêu cầu và giữ chính xác toán học cho test quãng đường |
| P2-A5 | Giá trị `ttl_s` của đom đóm thường (`kind: "random"`) | `null` cho đom đóm thường và số giây thực (`> 0`) cho đom đóm rơi (`kind: "dropped"`) | Phân biệt rõ loại không hết hạn với loại có TTL 480 tick |

*(Toàn bộ tiêu chí nghiệm thu `P2-AC1 .. P2-AC11` của Phase 2 đã đạt và tiếp tục được bảo vệ qua bộ test hồi quy `test_phase2_features.py`.)*

---

## Phase 3 (TICKET-03 — Change Request "Đèn cạn dầu" + Test Contract v1.2)

### Giả định cho các chi tiết kỹ thuật mở trong TICKET-03
| ID | Chỗ mở / Cần chốt | Giả định đã chọn | Lý do |
|---|---|---|---|
| P3-A1 | Tốc độ di chuyển của Bóng Mực `wander` khi đi tới đèn yếu (`fuel < 30`) | Dùng tốc độ trạng thái `wander` (`2.0 m/s`) | Nhất quán với định nghĩa trạng thái `wander` ở Ticket-02 (`2.0 m/s`) |
| P3-A2 | Scenario đặt `state: "drain"` mà không truyền `target_lantern_id` | Tự động gắn với đèn sáng yếu (`fuel < 30`) gần nhất trong `<= 2.0 m` (tie-break `id` nhỏ hơn) | Hỗ trợ linh hoạt cho cả scenario ngắn gọn lẫn scenario chỉ định rõ `target_lantern_id` |
| P3-A3 | Tính chính xác số lượng đom đóm châm dầu `ceil((100 - fuel) / 10)` | Tính trực tiếp trên đơn vị nguyên `1/60`: `needed = (6000 - fuel_60 + 599) // 600` | Loại bỏ hoàn toàn sai số dấu phẩy động, tuân thủ đúng mục "Độ chính xác" trong TICKET-03 |
| P3-A4 | Mục tiêu mũi tên chỉ đèn ngoài màn hình ở Phase 3 | Ưu tiên trỏ tới đèn tắt hoặc đèn sáng yếu (`fuel < 30`) gần nhất | Giúp người chơi kịp thời chạy tới cứu đèn sắp tắt |

### Tiêu chí nghiệm thu (Acceptance Criteria — đủ Mục 1..7 & DoD của TICKET-03)
| ID | Hạng mục (TICKET-03) | Tiêu chí kiểm tra ("Làm A -> thấy B") | Cách kiểm chứng |
|---|---|---|---|
| P3-AC1 | Contract v1.2 & Tuning | `game.contract.json` bản `1.2` có đủ 8 khóa tuning mới, thời lượng `240/270/300 s`, `per_mote=5`, `per_second_left=0`; `core/config.py` nạp khớp 100% | `test_tuning_matches_contract_json` + `scripts/verify.py` |
| P3-AC2 | Hao dầu `1/60`, tắt đèn `lantern_out`, thắp lại tốn `5` | Đèn sáng `fuel=1.0` tắt đúng tick 60 -> `lantern_out`, `deposited=0`, `ever_lit=true`; thắp lại tốn `5` đom đóm (`+25 + 40 = 65` điểm, `relight: true`, `relit_count=1`) | `test_headless_fuel_decay_lantern_out_relight_refuel_and_capacity_growth` |
| P3-AC3 | Châm dầu `ceil((100-fuel)/10)` & bỏ qua đèn đầy | Đèn thiếu `10.0` dầu tốn đúng `1` đom đóm (`refuel`, `+5` điểm); đèn thiếu `20.02` tốn `3`; đèn đầy (`fuel_60=6000`) bị bỏ qua và ưu tiên đèn nhận được kế tiếp | `test_refuel_exact_ceil_formula_and_full_lantern_skipped` |
| P3-AC4 | Ranh giới vùng an toàn `fuel == 30.0` vs `< 30` | Tại đúng `30.0` (`fuel_60=1800`) còn vùng an toàn `6 m`; sau 1 tick (`1799 < 1800`) mất vùng an toàn | `test_fuel_30_safe_radius_boundary_and_weak_lantern_drain` |
| P3-AC5 | Bóng Mực `drain`, cộng dồn `5/s`, `fuel_drain` mỗi 60 tick & các chuyển trạng thái | Bóng `wander` đi tới đèn `< 30` -> `drain`, phát `fuel_drain` mỗi 60 tick; 2 con hút mất `1 + 10 = 11/s`; Mây vào `<= 6 m` -> `chase`; châm lên `>= 30` -> `wander` và đẩy ra mép `6 m` trong `<= 30` tick không gây sát thương; hết choáng -> `wander` | `test_fuel_30_safe_radius_boundary_and_weak_lantern_drain`, `test_multi_shade_drain_stacking_pulse_15_pts_refuel_pushout_and_transitions` |
| P3-AC6 | Tỏa Sáng trúng Bóng Mực đang `drain` | Trúng Bóng Mực đang `drain` cộng tổng `+15` điểm (thay vì `+5` với con đang `chase`) | `test_multi_shade_drain_stacking_pulse_15_pts_refuel_pushout_and_transitions` |
| P3-AC7 | Luật thắng Bình minh & Bảng điểm mới | Thắp đủ 5/5 đèn không kết thúc sớm; tại bình minh thắng `dawn_survived` khi đạt `3/5` (N1), `4/6` (N2), `5/7` (N3) với thưởng `sum(50 + floor(fuel)) + 50 * flames`; dưới ngưỡng thua `dawn`; `flames == 0` đúng tick bình minh ưu tiên `no_flames` | `test_win_scenario_full_flow_and_determinism`, `test_dawn_survival_thresholds_all_nights_scoring_and_no_flames_priority` |
| P3-AC8 | Sức chứa tăng dần `10..20` & Validation lỗi `2` | `capacity = min(20, 10 + 2 * successful_lights)` (scenario pre-lit không tính); scenario sai (`fuel=150`, `target_lantern_id="L9"`, `successful_lights=-1`) trả mã thoát `2` | `test_capacity_growth_capped_at_20_and_v12_validation_errors` |
| P3-AC9 | Chế độ mù màu & Thẩm mỹ Áo Dài / Nón Lá | Cài đặt "Bảng màu dễ phân biệt" lưu `localStorage` đổi Bóng Mực sang `#00B3FF`, cảnh báo `#FFFFFF` + `⚠`, đèn tắt xẹp 20% + vết rách, thanh dầu + đèn `< 30` nhấp nháy 1 Hz; Mây mặc Áo Dài + Nón Lá + ánh sáng điểm WebGL2 | `test_web_routes_campaign_pause_dash_colorblind_aodai_and_camera` |
| P3-AC10 | DoD & Hiệu năng | Có ADR-005, Changelog Breaking Changes, hồi quy Phase 1–2 PASS 100%, 5 kịch bản SHA-256 tất định, benchmark 21.600 tick `<= 30 s`, review độc lập `docs/proof/phase-3/review.md` | `scripts/verify.py --phase phase-3 --write-proof` |

---

## Phase 4 (Ticket-04) — *Chờ phát hành*
