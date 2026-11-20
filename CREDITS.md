# Credits & Attribution

## Bản gốc của Lab (Day 12 AI SDLC)
- Bối cảnh **Đảo Đèn Lồng** (**Đảo Bến**, **Đảo Cau**, **Đảo Chuông**) và các nhân vật **Mây**, **Ông Đăng**, **Đèn Lồng Lớn**, **Đom đóm**, **Bóng Mực**, **Gió Lạc**, **Bùa Gió** là nguyên bản thuộc bài Lab Day 12 AI SDLC.

## Mã nguồn & Nội dung tự tạo / AI tạo
| Hạng mục | Nguồn / Công cụ | Giấy phép | Ghi chú |
|---|---|---|---|
| Core simulation 3 Đêm, bản đồ chuẩn, mô hình nhiên liệu `1/60`, Test Contract v1.3 Headless CLI | Tự thiết kế & viết cùng Antigravity AI | MIT | Pure Python 3 stdlib |
| Chế độ Benchmark `1280×720`, Soak test 10 Đêm, đo RSS tiến trình (`ctypes`/`/proc`/`resource`) & Bảng xếp hạng cục bộ | Tự thiết kế & viết cùng Antigravity AI | MIT | Pure Python 3 stdlib (`src/dao_den_long/ops.py`) |
| Giao diện 3D WebGL2, Áo Dài & Nón Lá cho Mây, shader ánh sáng điểm động, HUD, Bảng xếp hạng & Bộ tính năng Accessibility | Tự thiết kế & viết cùng Antigravity AI | MIT | Không dùng asset hay thư viện bên ngoài |
| Nhạc nền đêm & 12 SFX procedural (Web Audio API oscillators) | Tự thiết kế & viết cùng Antigravity AI | MIT | Tạo trực tiếp trong trình duyệt, không file mẫu |
| Ảnh chụp `docs/demo/preview.png` & Video demo `docs/demo/demo.mp4` | Sinh tự động từ quỹ đạo `GameSimulation` thật bằng `scripts/generate_demo_media.py` | MIT | Pure Python 3 stdlib (`zlib`, `struct`) |

## Công cụ & Thư viện phát triển
- **Python 3 Standard Library** (`argparse`, `ctypes`, `dataclasses`, `http.server`, `json`, `math`, `platform`, `random`, `struct`, `unittest`, `zlib`) — PSF License.
- **pytest** (tùy chọn cho chạy test nâng cao) — MIT License.

## Asset bổ sung qua các Phase
| Phase | Asset / Âm thanh | Nguồn / Công cụ | Giấy phép |
|---|---|---|---|
| CP0 | Chưa dùng asset ngoài | — | — |
| Phase 1 | Âm thanh ngũ cung & hình khối 3D procedural | Web Audio API + WebGL2 tự viết cùng Antigravity AI | MIT |
| Phase 2 | Mesh 3 đảo, bảng màu chuẩn & 11 SFX procedural | WebGL2 + Web Audio API tự viết cùng Antigravity AI | MIT |
| Phase 3 | Tạo hình Áo Dài & Nón Lá cho Mây, shader ánh sáng điểm đèn lồng, sao/trăng/tre, thanh dầu 3D & âm thanh tắt đèn | WebGL2 + Web Audio API tự viết cùng Antigravity AI | MIT |
| Phase 4 | Ảnh preview `1280×720` (`docs/demo/preview.png`) & video demo `.mp4` (`docs/demo/demo.mp4`) | Tự sinh bằng Python 3 stdlib từ mô phỏng thật | MIT |
