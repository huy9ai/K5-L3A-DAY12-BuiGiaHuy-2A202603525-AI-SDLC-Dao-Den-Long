# Evaluation theo Phase & Retrospective Tổng Kết Dự Án (Đảo Đèn Lồng v1.0.0)

---

## 1. Đánh giá từng Phase (Phase-by-Phase Evaluation)

### Phase 1 (PRD-0 — Đêm 1: Đảo Bến + Test Contract v1.0)
- **Yêu cầu đạt:** Hoàn thành trọn vẹn mô phỏng 60Hz Đêm 1, CLI headless theo Test Contract v1.0, giao diện 3D WebGL2 + âm thanh ngũ cung Web Audio API, 13/13 test tự động và Review độc lập `APPROVED`.
- **Lỗi phát hiện & bài học:** Khi học viên chơi thử bản 3D phát hiện lỗi đảo dấu tích có hướng `x_cam` trong `mat4LookAt` khiến bản đồ bị lật ngược và bấm `D` đi sang trái. Bài học rút ra: test headless chỉ bảo vệ tầng `core/`, còn ma trận view/projection 3D cần có cả kiểm chứng toán học lẫn chơi thử trực tiếp.

### Phase 2 (TICKET-02 — Ba hòn đảo + Test Contract v1.1)
- **Yêu cầu đạt:** Đồng bộ 100% số liệu chuẩn Phần 1 vào `game.contract.json` (`1.1`); tách `maps.py` cài đặt chuẩn xác hình học 3 Đêm (**Đảo Bến**, **Đảo Cau** hai bờ cầu tre + 2 bục nhảy, **Đảo Chuông** 3 tầng + 2 dốc + bục nhảy + tháp chuông + gió mạnh mỗi 30s); cài đặt thứ tự 12 bước trong tick, Lướt (mặt đất & giữ nguyên `Y` trên không), Rơi (`Y < -10m`), 5 trạng thái Bóng Mực, Gió Lạc, Bùa Gió, Tạm dừng (`tick` vs `sim_tick`), sửa triệt để lỗi camera `mat4LookAt`, hoàn thiện UI Chiến dịch 3 Đêm + 11 SFX và benchmark 21.600 tick (`1.220s <= 30.0s`).
- **Điểm mạnh kiến trúc:** Việc tách `maps.py` khỏi `engine.py` giúp cả 3 Đêm dùng chung một pipeline 12 bước duy nhất, không nhân bản logic vật lý.

### Phase 3 (TICKET-03 — Change Request "Đèn cạn dầu" + Test Contract v1.2)
- **Yêu cầu đạt:** Xử lý gọn Change Request phá vỡ tương thích trong thời gian ngắn: chuyển nhiên liệu đèn sang đơn vị số nguyên `1/60` (`fuel_60 ∈ [0, 6000]`) loại bỏ hoàn toàn sai số dấu phẩy động tại mốc ranh giới `fuel == 30.0` và phép `ceil((100 - fuel) / 10)`; bổ sung trạng thái thứ 6 của Bóng Mực (`drain` hút `5/s` cộng dồn, phát `fuel_drain` mỗi 60 tick); thay luật thắng sớm `all_lit` bằng `dawn_survived` (`>= ceil(0.6 * total)` đèn sáng lúc bình minh, ưu tiên `no_flames` trước); sức chứa tăng dần `10..20`; Chế độ mù màu (`#00B3FF`, `#FFFFFF` + `⚠`, đèn tắt xẹp 20% + vết rách, nhấp nháy 1 Hz + thanh dầu 3D); nâng cấp thẩm mỹ **Mây mặc Áo Dài truyền thống Việt Nam & Nón Lá** + ánh sáng điểm động WebGL2.
- **Kỷ luật SDLC:** Ghi đầy đủ **ADR-005** trong `docs/notes/decisions.md` và mục `Breaking Changes` trong `CHANGELOG.md`, cập nhật có giải trình các test bị luật mới thay thế (**0 test bị skip âm thầm**).

### Phase 4 & Release `v1.0.0` (TICKET-04 — Non-functional + Release + Test Contract v1.3)
- **Yêu cầu đạt:**
  - **Chế độ Benchmark (`python3 run.py bench --seed 42 --duration 30 --out bench.json`):** Cảnh chuẩn Đêm 1 `1280×720` với đúng `200` Bóng Mực `wander`, `100` đom đóm, `3` đèn sáng `L1–L3`, tắt sinh thêm/sát thương/nhặt/hao dầu/kết thúc Đêm & tắt hiệu ứng sáng tạo thêm, camera bay vòng `r=30m, Y=15m, T=15s` CCW từ `(30,15,0)` nhìn vào `(0,0,0)`, `3s` khởi động + `30s` đo thật. Kết quả trong `bench.json` vượt xa ngưỡng (`avg_fps >= 60`, `p1_low_fps >= 30`, `load_ms <= 10000`).
  - **Soak Test 10 Đêm (`python3 run.py soak --seed 7 --nights 10 --out soak.json`):** Chạy 10 Đêm liên tiếp xoay vòng 1→2→3 trong cùng tiến trình (~1.72s), `crashes = 0`, bộ nhớ RSS ổn định tuyệt đối (`26.14 MB -> 26.19 MB`, tăng `< 0.2%`, thấp hơn nhiều ngưỡng `<= 20%`).
  - **Bảng xếp hạng cục bộ & Accessibility:** Lưu bền Top 10 trên đĩa (`data/leaderboard.json`), hỗ trợ tên `3–12` ký tự `[A-Za-z0-9_]` và tiếng Việt có dấu, nhập tên sau thắng Đêm 3 hoặc thua bất kỳ Đêm nào, lệnh `--export-leaderboard out.json`; đổi phím đủ 9 hành động có báo trùng phím & khôi phục mặc định; phụ đề + mũi tên mép màn hình chỉ Bóng Mực xuất hiện, gió, 10s cuối, đèn `< 30`; giảm chuyển động; cỡ chữ `>= 18px` + tùy chọn chữ lớn `×1.25`.
  - **Đóng gói & Demo:** Đầy đủ `bench.json`, `soak.json`, ảnh chụp `docs/demo/preview.png`, video demo `docs/demo/demo.mp4` (`< 5` phút), tag `phase-4` và Release `v1.0.0`.

---

## 2. Retrospective Tổng Kết Cuối Dự Án

### 2.1. Số liệu tổng hợp toàn dự án
- **Các mốc hoàn thành:** `CP0` → `phase-1` (Contract v1.0) → `phase-2` (Contract v1.1) → `phase-3` (Contract v1.2) → `phase-4` & `v1.0.0` (Contract v1.3).
- **Bộ kiểm thử tự động:** **31/31 test PASS** (`test_phase1_core.py`, `test_phase1_contract.py`, `test_phase1_web.py`, `test_phase2_features.py`, `test_phase3_features.py`, `test_phase4_features.py`), **0 test bị skip**.
- **Tính tất định & Hiệu năng:** 5 kịch bản headless trên cả 3 Đêm khớp mã băm SHA-256 tuyệt đối qua nhiều lần chạy và giữa Python `3.10` / `3.14`; 21.600 tick Đêm 3 chạy trong `~1.9s` (giới hạn `<= 30s`); Soak test 10 Đêm chạy trong `~1.72s` với `0` crash và độ lệch RAM `< 0.2%`.
- **Tổng token AI ước tính:** Khoảng **~285k input tokens / ~79k output tokens** cho toàn bộ 4 phase + CP0 + 4 lượt Independent Review.

### 2.2. Điều hiệu quả nhất khi làm việc với AI
1. **Kiến trúc Zero-Dependency tách 4 tầng rõ rệt (`core/` ↔ `headless/` ↔ `ops.py` ↔ `web/`):** Nhờ giữ `core/` thuần Python 3 stdlib và đọc mọi hằng số từ `game.contract.json`, mỗi khi đề bài thay đổi lớn (Phase 2 chuẩn hóa số liệu & thêm 2 đảo, Phase 3 thay luật đèn & luật thắng, Phase 4 thêm `bench`/`soak`/leaderboard), AI chỉ cần sửa đúng tầng liên quan mà không làm vỡ các phần khác.
2. **Đơn vị số nguyên `1/60` (`fuel_60`) cho bài toán thời gian thực:** Chốt biểu diễn nhiên liệu bằng số nguyên `0..6000` ngay từ thiết kế Phase 3 giúp tránh toàn bộ lỗi làm tròn số thực ở các điều kiện biên khắt khe (`fuel == 30.0` giữ vùng an toàn, `29.983` mất vùng an toàn, `ceil((100 - fuel) / 10)` khi châm dầu).
3. **Viết và chạy kiểm chứng theo lô (Batch Operations):** Mỗi lượt làm việc đều đọc tất cả file cần thiết cùng lúc và cập nhật đồng loạt code + test + tài liệu trước khi chạy `scripts/verify.py`, giảm số vòng lặp hội thoại và tiết kiệm đáng kể quota token.

### 2.3. Những lần AI sai, cách phát hiện & bài học đáng nhớ
1. **Lỗi đảo dấu tích có hướng trong `mat4LookAt` (Phase 1 → sửa ở Phase 2):**
   - *Nguyên nhân:* AI viết `x_cam = (-zz, 0, zx)` thay vì `cross((0,1,0), z_cam) = (zz, 0, -zx)` khiến trục `y_cam` bị âm, làm bản đồ 3D lộn ngược và phím `D`/`A` bị ngược trái/phải.
   - *Cách phát hiện:* Học viên trực tiếp mở trình duyệt chơi thử Phase 1 và phát hiện ngay cảm giác điều khiển bị ngược.
   - *Khắc phục:* Sửa công thức chuẩn right-handed, bổ sung regression test kiểm tra mã nguồn `mat4LookAt` trong `test_phase1_web.py` và đưa vào checklist bắt buộc của `.agents/skills/independent-review/SKILL.md`.
2. **Benchmark 21.600 tick dừng sớm ở ~2.500 tick trong lần chạy thử đầu (Phase 2):**
   - *Nguyên nhân:* Khi chạy headless mặc định không có input, Bóng Mực sinh ra ở tick 300 đuổi tới đánh hết 3 Ngọn Lửa của Mây ở khoảng tick 2.500 nên mô phỏng kết thúc sớm dù lệnh vẫn trả mã `0`.
   - *Cách phát hiện:* Đọc kỹ con số `lines=250` trong log của `scripts/verify.py` thay vì chỉ nhìn dòng chữ `PASS`.
   - *Khắc phục:* Tạo `p2_perf_21600_scenario.json` (`invuln_ticks: 25000`) và thêm khẳng định bắt buộc `end.ticks == 21600` trong cả `verify.py` và unit test.
3. **Trùng tọa độ đèn `L5` và `L1` tại `[0, 0, 25]` khi chuyển sang Phase 3:**
   - *Nguyên nhân:* Trên Đảo Bến, `L1` mặc định nằm ở góc `90°` = `[0, 0, 25]`. Ở Phase 1–2 đèn đã sáng không nhận tương tác nên đặt `L5` tắt tại `[0, 0, 25]` không sao; sang Phase 3 đèn đang sáng nhận tương tác châm dầu nên `L1` (đã hao 1 chút dầu, `id` nhỏ hơn `L5`) được chọn để `refuel` thay vì nạp vào `L5`.
   - *Cách phát hiện:* Bộ test `test_phase1_contract.py` và `test_phase3_features.py` báo thiếu sự kiện `deposit`/`lantern_lit` ngay ở lần chạy `verify.py` đầu tiên.
   - *Khắc phục:* Đặt đèn mục tiêu trong các scenario Đêm 1 đúng vào `L1` tại `[0, 0, 25]` để không bao giờ có 2 đèn chồng lên nhau.
4. **Cắt cụt handle 64-bit `GetCurrentProcess()` trong `ctypes` trên Windows (Phase 4):**
   - *Nguyên nhân:* Không khai báo `restype = wt.HANDLE` khiến pseudo-handle `-1` bị cắt thành 32-bit dương, gây lỗi `WinError 0xc0000008`.
   - *Cách phát hiện:* Chạy lệnh kiểm tra nhỏ cho hàm đo RSS ngay trước khi ghép vào `ops.py`.

### 2.4. Thành phần Harness nào giúp nhiều nhất?
- **`scripts/verify.py` + `.githooks/pre-commit`:** Là chốt chặn giá trị nhất. Mọi `git commit` đều tự động kích hoạt kiểm tra schema `game.contract.json`, chạy toàn bộ unit/contract tests, so sánh mã băm SHA-256 x2 trên cả 3 Đêm, kiểm tra ngưỡng `bench.json`/`soak.json` và quét secret. Nhờ vậy không một commit đỏ nào lọt được vào lịch sử git.
- **`.agents/skills/independent-review/SKILL.md` (Subagent Review độc lập cuối mỗi phase):** Việc khởi tạo một subagent tách biệt đóng vai trò kiểm toán viên đối kháng (adversarial reviewer) tự viết script kiểm thử biên ở cuối mỗi phase đã giúp phát hiện sớm các chi tiết tinh tế (như nối mép dốc `inner_r - 0.1` ở Đêm 3, chênh cao `abs(s.y - l.y)` khi `drain`, hay đồng bộ màu `.wind-badge` ở chế độ mù màu).
- **`AGENTS.md`:** Giữ toàn bộ quy ước tọa độ cực, thứ tự 12 bước trong tick, ranh giới cấm `time.*` trong `core/` và lệnh chuẩn trên một trang ngắn gọn, giúp cả agent chính lẫn subagent review nắm bắt quy tắc ngay lập tức mà không tốn token đọc lại nhiều file.

### 2.5. Chiến lược tiết kiệm Token đã áp dụng
- **Zero-dependency Python stdlib + Vanilla WebGL2:** Không tốn hàng chục nghìn token để cài đặt, cấu hình hay gỡ lỗi các lỗi tương thích của `npm`, `webpack`, `three.js` hay thư viện C++ bên thứ ba.
- **Nguồn chân lý đơn (`game.contract.json`) & Dùng chung động cơ (`maps.py` + `engine.py`):** Mọi thông số được đọc từ một file duy nhất; 3 Đêm dùng chung một lớp `GameSimulation`.
- **Gộp thao tác đọc/ghi song song & Không poll:** Luôn đọc các file liên quan trong cùng một lượt và chỉ chạy `scripts/verify.py` sau khi hoàn tất cả đợt chỉnh sửa.

### 2.6. Nếu làm lại từ đầu sẽ thay đổi gì?
1. **Viết unit test cho ma trận camera 3D (`mat4LookAt`, `mat4Perspective`, `projectToScreen`) ngay từ Phase 1:** Kiểm tra định thức `det > 0`, hướng vector `right = (+1, 0, 0)` và `up = (0, +1, 0)` tại `yaw = 0` ngay từ đầu sẽ chặn được lỗi ngược camera Phase 1 trước cả khi mở trình duyệt.
2. **Kiểm tra bất biến "không trùng tọa độ thực thể tĩnh" khi nạp `scenario`:** Thêm cảnh báo sớm nếu một scenario đặt 2 đèn lồng trùng vị trí `(x, y, z)` để tránh lỗi tie-break khi luật tương tác mở rộng ở các phase sau.
