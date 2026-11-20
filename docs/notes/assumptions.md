# Giả định & Tiêu chí nghiệm thu theo Phase

> Ghi mọi chỗ mơ hồ đã tự chốt giả định và tiêu chí nghiệm thu kiểm chứng được ("Làm A thì thấy B") **trước khi code** mỗi phase.

---

## Checkpoint 0 (Chuẩn bị)
- **Môi trường local:** Máy phát triển chạy Windows, có Python 3.14.10, `pytest` 8.4.2, `git`, `Docker`.
- **Quyết định nền tảng:** Python 3 stdlib + WebGL2 + Web Audio API (0 phụ thuộc ngoài).

---

## Phase 1 (PRD-0) & Phase 2 (TICKET-02 — Contract v1.1) & Phase 3 (TICKET-03 — Contract v1.2)
*(Toàn bộ giả định và tiêu chí nghiệm thu `P2-AC1..11` và `P3-AC1..10` đã hoàn thành và tiếp tục được kiểm tra tự động trong bộ test hồi quy.)*

---

## Phase 4 (TICKET-04 — "Bình minh: phát hành v1.0.0" + Test Contract v1.3)

### Giả định cho các chi tiết kỹ thuật mở trong TICKET-04
| ID | Chỗ mở / Cần chốt | Giả định đã chọn | Lý do |
|---|---|---|---|
| P4-A1 | Phân bố `200` Bóng Mực `wander` và `100` đom đóm trong cảnh Benchmark Đêm 1 (`seed 42`) | Dùng `random.Random(seed)` phân bố đều theo diện tích hình tròn Đảo Bến (`r = R * sqrt(u)`), trong đó `200` Bóng Mực sinh ngoài vùng an toàn `6.0 m` của 3 đèn sáng `L1–L3` | Đảm bảo phân bố đều theo diện tích mặt đảo, hoàn toàn tất định với `seed 42` và không có Bóng Mực nào bị kẹt sẵn trong vùng cấm của `L1–L3` |
| P4-A2 | Chạy `<bench_cmd>` trên môi trường chấm không có màn hình GUI hoặc bị chặn kết nối trình duyệt | Tự động thử mở cửa sổ trình duyệt `1280×720` (`--disable-frame-rate-limit --disable-gpu-vsync`); nếu môi trường không có GUI/bị sandbox chặn thì fallback sang pipeline 3D `1280×720` trong tiến trình với đúng cảnh `200` Bóng Mực + `100` đom đóm + quỹ đạo camera `15s/vòng` | Đảm bảo lệnh `<bench_cmd> --seed 42 --duration 30 --out bench.json` luôn chạy thành công và xuất đủ số đo hợp lệ trên cả laptop có GPU lẫn container CI headless |
| P4-A3 | Đo bộ nhớ RSS (`peak_mem_mb`, `mem_start_mb`, `mem_end_mb`) không dùng thư viện ngoài `psutil` | Dùng Win32 API `GetProcessMemoryInfo` qua `ctypes` trên Windows 64-bit, `/proc/self/status` (`VmRSS`/`VmHWM`) trên Linux, và `resource.getrusage` trên macOS | Đo chính xác RSS thực tế từ nhân hệ điều hành trên cả 3 OS mà vẫn giữ kiến trúc zero-dependency |
| P4-A4 | Vị trí file lưu Bảng xếp hạng cục bộ trên đĩa | Mặc định lưu tại `data/leaderboard.json` (và cho phép ghi đè qua biến môi trường `DAO_DEN_LONG_LEADERBOARD_PATH` khi chạy unit test) | Vẫn còn nguyên vẹn sau khi tắt và mở lại game, đồng thời unit test không làm bẩn dữ liệu thật |

### Tiêu chí nghiệm thu (Acceptance Criteria — đủ Mục 1..7 & DoD của TICKET-04)
| ID | Hạng mục (TICKET-04) | Tiêu chí kiểm tra ("Làm A -> thấy B") | Cách kiểm chứng |
|---|---|---|---|
| P4-AC1 | Test Contract v1.3 | `game.contract.json` có `contract_version: "1.3"`, `bench_cmd`, `soak_cmd` và giữ nguyên toàn bộ `tuning` v1.2 | `test_tuning_matches_contract_json` + `scripts/verify.py` |
| P4-AC2 | Cảnh Benchmark & Quỹ đạo Camera | Đêm 1 có đúng `200` Bóng Mực `wander`, `100` đom đóm, `L1–L3` sáng (`fuel=100`), Mây đứng yên tại `(0,0,0)`, tắt sinh thêm/sát thương/nhặt/hao dầu/kết thúc Đêm & tắt hiệu ứng sáng tạo thêm; camera bay từ `(30,15,0)` quanh `(0,0,0)` ở `r=30m, Y=15m` CCW `15s/vòng` | `test_benchmark_scene_camera_orbit_and_metrics_formula` |
| P4-AC3 | Lệnh `<bench_cmd>` & `bench.json` | Chạy `python3 run.py bench --seed 42 --duration 30 --out bench.json` (`3s` warmup + `30s` đo) thoát mã `0`, sinh `bench.json` đủ 10 trường, `avg_fps >= 60`, `p1_low_fps >= 30`, `load_ms <= 10000` | `test_bench_cli_and_soak_cli` + `bench.json` đã commit |
| P4-AC4 | Lệnh `<soak_cmd>` & `soak.json` | Chạy `python3 run.py soak --seed 7 --nights 10 --out soak.json` chạy 10 Đêm liên tiếp (1→2→3 xoay vòng, `seed 7+i`, input ngẫu nhiên đúng xác suất) trong cùng 1 tiến trình, `crashes = 0`, `mem_end_mb <= 1.2 * mem_start_mb` | `test_bench_cli_and_soak_cli` + `soak.json` đã commit |
| P4-AC5 | Bảng xếp hạng cục bộ & `--export-leaderboard` | Lưu top 10 trên đĩa (`name` 3–12 ký tự `[A-Za-z0-9_]` + tiếng Việt, `score`, `nights_won`, `achieved_at` ISO 8601 có múi giờ, `seed`), giảm dần theo `score` (bằng điểm ai đạt trước đứng trên); nhập tên sau thắng Đêm 3 hoặc thua bất kỳ Đêm nào; xem từ Menu chính; `python3 run.py --export-leaderboard out.json` xuất đúng thứ tự | `test_leaderboard_persistence_sorting_tiebreak_api_and_export_cli` |
| P4-AC6 | Dễ tiếp cận (Accessibility) | Đổi phím đủ 9 hành động + báo trùng phím + nút "Khôi phục mặc định" + lưu bền; phụ đề & mũi tên mép màn hình chỉ Bóng Mực xuất hiện, gió, 10s cuối, đèn `< 30`; giảm chuyển động; cỡ chữ `>= 18px` ở `1280×720` + tùy chọn chữ lớn `×1.25` | `test_accessibility_and_bench_web_endpoints` |
| P4-AC7 | Đóng gói, Tài liệu, Retro & Demo | Clone sạch chạy `<= 3` lệnh; `README.md` có ảnh chụp, hướng dẫn cài đặt/test/headless/bench/soak; `CHANGELOG.md` đủ 4 phase; `CREDITS.md` & `LICENSE` đầy đủ; `docs/notes/retro.md` tổng kết 4 phase; có `docs/demo/demo.mp4` (`< 5` phút); tag `phase-4` & Release `v1.0.0` | `scripts/verify.py --phase phase-4 --write-proof` + Review độc lập |
