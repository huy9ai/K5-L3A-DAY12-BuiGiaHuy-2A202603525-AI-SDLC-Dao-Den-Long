# Independent Phase 4 & Release v1.0.0 Review Report (TICKET-04 — Contract v1.3)

- **Reviewer:** Independent Audit Subagent (Adversarial Code, Architecture, Benchmark/Soak, Leaderboard, Accessibility & Release Reviewer — tách biệt hoàn toàn với phiên viết code)
- **Ngày đánh giá:** 2026-11-20
- **Phạm vi kiểm toán:** `phase-3..HEAD` (`190fea0`, `cc13baa`, `4c02656` — 28 files changed, +2811 / -479 lines)
- **Phán quyết (Verdict):** **`APPROVED`** (Đủ điều kiện gắn tag `phase-4` và phát hành `v1.0.0`)

---

## 1. Kiểm tra Kiến trúc, Độ thuần khiết của `core/` & Phản hồi từ Review Phase 3

1. **Độ thuần khiết của `src/dao_den_long/core/`:**
   - Đã quét AST toàn bộ `src/dao_den_long/core/*.py` (`__init__.py`, `config.py`, `maps.py`, `engine.py`): tập module được import chỉ gồm `['__future__', 'dao_den_long', 'dataclasses', 'json', 'math', 'pathlib', 'random', 'typing']`.
   - **0 import** thuộc danh sách cấm (`time`, `ctypes`, `os`, `http`, `urllib`, `socket`, `subprocess`, `sys`, UI/DOM) và **0 lệnh gọi `random.*` toàn cục** (mọi PRNG trong `core/` đi qua `self._rng = random.Random(self.seed)`).
   - Toàn bộ phần đo thời gian thực (`time.perf_counter`), đo bộ nhớ tiến trình RSS đa nền tảng (`ctypes` / `/proc` / `resource`), chạy Benchmark/Soak và lưu đĩa Bảng xếp hạng được tách sạch sang `src/dao_den_long/ops.py` đúng theo **ADR-006**.
2. **Xác nhận đã xử lý 2 ghi chú Non-blocking từ Review Phase 3:**
   - `src/dao_den_long/core/engine.py` đã bổ sung kiểm tra chênh lệch độ cao `abs(s.y - l.y) <= ENTITY_MAX_HEIGHT_DIFF + 1e-9` (`1.5 m`) khi Bóng Mực chọn mục tiêu và duy trì trạng thái `drain` trên bản đồ nhiều tầng (Đảo Chuông).
   - `src/dao_den_long/web/static/style.css` đã đồng bộ màu chữ `.wind-badge` theo `var(--danger)` (`#FFFFFF` kèm biểu tượng `⚠` khi bật chế độ Mù màu).

---

## 2. Kiểm tra Đối kháng Yêu cầu TICKET-04 & Test Contract v1.3

### 2.1. `game.contract.json` (Contract v1.3)
- `contract_version` đã nâng lên `"1.3"`, bổ sung đầy đủ `"bench_cmd": "python3 run.py bench"` và `"soak_cmd": "python3 run.py soak"`.
- Giữ nguyên 100% các khóa `build_cmd`, `run_cmd`, `headless_cmd` và toàn bộ 33 tham số `tuning` của v1.0–v1.2.

### 2.2. Chế độ Benchmark (`python3 run.py bench --seed 42 --duration 30 --out bench.json`)
- **Cảnh đo chuẩn Đêm 1 `1280×720` (`build_benchmark_simulation(seed=42)`):**
  - Đúng Đêm 1 (**Đảo Bến**), Mây đứng yên tại `(0, 0, 0)` với `flames = 3, carried = 0`.
  - Đúng `200` Bóng Mực đều ở trạng thái `wander` phân bố trên đảo bằng `random.Random(seed)` (ngoài vùng an toàn `6.0 m` của đèn sáng).
  - Đúng `100` đom đóm phân bố trên đảo và đúng `3` đèn sáng `L1, L2, L3` (`fuel = 100`, `fuel_60 = 6000`), `L4, L5` tắt.
  - Trong `step_benchmark_wander`: đã tắt hoàn toàn sinh thêm thực thể, sát thương, nhặt đom đóm, hao/hút dầu và `game_over`; `200` Bóng Mực vẫn di chuyển mỗi tick theo đúng luật `wander` (`2.0 m/s`).
  - Trong `app.js` (`isBenchMode`): khóa kích thước canvas `1280×720` và tắt toàn bộ hiệu ứng sáng tạo thêm (trăng, 60 ngôi sao, 12 bụi tre ven đảo, đom đóm bay vòng quanh Mây).
- **Quỹ đạo Camera:**
  - `benchmark_camera_pose(elapsed_s)` và `app.js` đặt camera bay tròn quanh `(0, 0, 0)` với bán kính `30 m`, độ cao `Y = 15 m`, luôn nhìn vào `(0, 0, 0)`.
  - Tại `t = 0s`: góc `0°` → `(30.0, 15.0, 0.0)`.
  - Tại `t = 3.75s` (`1/4` chu kỳ `15s`): góc `90°` ngược chiều kim đồng hồ nhìn từ `+Y` xuống → `(0.0, 15.0, 30.0)`.
- **Thời lượng & Công thức số đo (`compute_bench_metrics`):**
  - Chạy `3 s` khởi động (warmup, bỏ qua không tính) + `--duration` giây đo thật.
  - Công thức khớp chính xác đặc tả: `frames = N`, `avg_fps = (1000 * N) / sum(dt_i)`, `k = max(1, ceil(0.01 * N))` khung hình chậm nhất cho `p1_low_fps = 1000 / avg(worst_k)`, phân vị 95 `frame_ms_p95`, `load_ms`, `peak_mem_mb`, `vsync_off`, `renderer`, `os`.
  - File `bench.json` đã commit tại gốc repo đạt: `avg_fps = 345.4` (ngưỡng `>= 60`), `p1_low_fps = 183.1` (ngưỡng `>= 30`), `frame_ms_p95 = 3.29 ms`, `frames = 10337`, `load_ms = 4152.2 ms` (ngưỡng `<= 10000 ms`), `peak_mem_mb = 29.1 MB`, `vsync_off = true`.

### 2.3. Chế độ Soak Test (`python3 run.py soak --seed 7 --nights 10 --out soak.json`)
- Chạy `10` Đêm liên tiếp xoay vòng Đêm `1 → 2 → 3 → 1...` **trong cùng một tiến trình Python**, với `seed_i = seed + i` (`7 + i`).
- Bộ sinh input ngẫu nhiên theo seed tuân thủ đúng xác suất: mỗi `30` tick đổi hướng di chuyển ngẫu nhiên; mỗi tick `5%` nhảy, `3%` lướt, `2%` tỏa sáng, `10%` tương tác.
- Đo bộ nhớ RSS thực của tiến trình bằng Python stdlib (`GetProcessMemoryInfo` 64-bit trên Windows, `/proc/self/status` trên Linux, `resource` trên macOS).
- File `soak.json` đã commit tại gốc repo đạt: `nights = 10`, `crashes = 0`, `mem_start_mb = 26.14`, `mem_end_mb = 26.19` (`<= 1.2 * 26.14 = 31.37 MB`, chỉ tăng `+0.19%`), `duration_s = 1.72s`.

### 2.4. Bảng xếp hạng cục bộ (Local Leaderboard)
- Lưu bền tối đa `10` dòng cao điểm nhất tại `data/leaderboard.json` (`LeaderboardStore`), sắp xếp theo `score` giảm dần; khi bằng điểm dùng `Timsort` ổn định giữ nguyên thứ tự thời gian (ai đạt trước đứng trên).
- Kiểm tra tên người chơi `3–12` ký tự (`[A-Za-z0-9_]` + chữ cái tiếng Việt có dấu), từ chối tên rỗng/quá ngắn/quá dài/ký tự đặc biệt với HTTP `400 Bad Request`.
- Đầy đủ 5 trường bắt buộc: `name`, `score`, `nights_won`, `achieved_at` (ISO 8601 có múi giờ), `seed`.
- Hiển thị form nhập tên trên màn hình Kết thúc sau khi thắng Đêm 3 (Bình Minh) hoặc thua ở bất kỳ Đêm nào (`#leaderboard-save-box`), có màn hình Bảng xếp hạng từ Menu chính (`#screen-leaderboard`), và hỗ trợ CLI `python3 run.py --export-leaderboard out.json` thoát mã `0`.

### 2.5. Dễ tiếp cận (Accessibility)
- **Đổi phím điều khiển (Key Remapping):** Cho phép đổi toàn bộ 9 hành động (`moveUp`, `moveDown`, `moveLeft`, `moveRight`, `jump`, `dash`, `interact`, `pulse`, `pause`), tự động phát hiện và cảnh báo khi 2 hành động trùng phím (`findKeybindConflicts`, `#keybind-error`), có nút **Khôi phục mặc định** (`#btn-reset-keys`) và lưu bền trong `localStorage`.
- **Phụ đề & chỉ báo hình ảnh (`#subtitle-banner` & `#shade-edge-arrow`):** Hiển thị phụ đề cảnh báo cho Bóng Mực xuất hiện (kèm mũi tên chỉ hướng ở mép màn hình), gió sắp thổi / đang thổi, 10 giây đếm ngược cuối, và đèn lồng có `fuel < 30`.
- **Giảm chuyển động (`#input-reduced-motion`):** Tắt rung camera (`shakeTimer`), tắt chớp màn hình (`#screen-flash`), tắt nhấp nháy nhanh và tắt CSS animations (`body.reduced-motion`).
- **Cỡ chữ UI:** Cỡ chữ gốc `html, body { font-size: 18px; }` ở `1280×720` (mọi thành phần HUD/menu dùng `>= 1rem`), kèm tùy chọn **Chữ lớn (`×1.25` = `22.5 px`)** (`#input-large-text`).

### 2.6. Đóng gói, Tài liệu, Retro & Demo Media
- `README.md` rõ ràng, chạy từ bản clone sạch với `<= 3` lệnh (`git clone`, `cd`, `python3 run.py`), nhúng ảnh chụp `docs/demo/preview.png` (`1280×720` PNG hợp lệ), dẫn link video `docs/demo/demo.mp4` (`938 KB` MP4 hợp lệ, `< 5` phút), hướng dẫn đầy đủ cách tắt VSync khi benchmark và mục "Sáng tạo của tôi".
- Đầy đủ `CHANGELOG.md` (4 phase + CP0), `CREDITS.md`, `LICENSE` (MIT), `docs/notes/retro.md` (Evaluation từng phase + Retrospective 6 mục), `docs/notes/decisions.md` (ADR-001..006).

---

## 3. Kết quả Tự Chạy Kiểm Chứng Độc Lập

Reviewer đã trực tiếp chạy lại `python scripts/verify.py` và `pytest -v` trong sandbox:
- **Test Contract v1.3 Schema:** `PASS` (`contract_version=1.3`, `bench_cmd`, `soak_cmd`).
- **Unit, Regression & Phase 4 Tests:** `31/31 PASS` (`0` skipped) trên cả `unittest` (`14.74s`) và `pytest -v` (`14.68s`).
- **Determinism (5 kịch bản × 2 lần chạy Across Nights 1–3):** `PASS` — khớp tuyệt đối 5 cặp mã băm SHA-256:
  - `night1_dawn_win`: `069c2a6c2ca8b78824a7d6b8553bfcc5da546caef7752438c5dc17868486d921`
  - `night1_p3_fuel_relight`: `6c9504443432f9ae8cd48adc5d0485fa97a5936f11d0f415f14cac04cf717f18`
  - `night1_p3_shade_drain`: `4a8b99539a5441531f143b8b7c9a48b77cd051303b21377117d54f4ec6ee2972`
  - `night2_drifter_charm`: `caa92c689a4276fc923d0a07938fb54358598749ec54fa4ffdbc92d60a1fbc29`
  - `night3_ramp_wind`: `06c7d4c062698588ea4657c13521bcbb95aeb86ea17db07b9345e6296c40566b`
- **Committed `bench.json` & `soak.json` Check:** `PASS` (`avg_fps=345.4`, `p1_low_fps=183.1`, `load_ms=4152.2ms`; `nights=10, crashes=0, mem=26.14->26.19MB`).
- **Full-Night 21,600-tick Stress Benchmark:** `PASS` (`1.962s <= 30.0s`).
- **Secret & Hygiene Scan:** `PASS` (`83` files scanned, `0` issues).

---

## 4. Các Phát Hiện (Findings)

### Blocking Issues (Lỗi chặn phát hành)
- **Không có (0 lỗi chặn).**

### Non-Blocking Observations (Ghi chú nhỏ không chặn phát hành)
1. **Phím phụ cố định trong `app.js` (lines 508–511, 700–701):** Ngoài 9 phím chính có thể đổi tự do trong `settings.keybinds`, trình duyệt vẫn giữ các phím phụ tiện lợi (`ArrowUp`/`ArrowDown` cho tiến/lùi, `ShiftRight` cho lướt, `KeyF` cho tương tác, `Escape` cho tạm dừng). Không ảnh hưởng tới bộ phím mặc định hay kiểm thử đổi phím.
2. **Chuỗi docstring lịch sử trong `core/config.py` và `core/engine.py`:** Docstring đầu file vẫn ghi `"Test Contract v1.2"` do luật mô phỏng trong `core/` không thay đổi giữa v1.2 và v1.3, trong khi `game.contract.json` và `verify.py` đã ở v1.3.

---

## 5. Kết luận
Toàn bộ yêu cầu chức năng và phi chức năng của **TICKET-04 (Test Contract v1.3)** cùng toàn bộ bài kiểm thử hồi quy của **Phase 1–3** đều đạt 100% với bằng chứng số đo thực tế, minh bạch và tất định.

**Phán quyết cuối cùng:** **`APPROVED`** — Cho phép commit bằng chứng, gắn tag `phase-4` và phát hành Release `v1.0.0`.
