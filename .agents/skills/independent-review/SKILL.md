---
name: independent-review
description: Perform an independent audit of code, multi-night maps, Test Contract v1.1 compliance, camera orientation, performance, and proof before tagging a phase.
---

# Skill: Independent Phase Review

Dùng skill này bởi một subagent hoặc phiên AI **tách biệt với người/agent đã viết code** trước khi gắn tag `phase-N`.

## Checklist kiểm tra
1. **Diff & Kiến trúc:** Chạy `git status` và `git diff` (hoặc `git log -p -n 6`). Xác nhận `src/dao_den_long/core/` không import `http`, `web`, UI, `time`, hay global `random`.
2. **Test Contract v1.1 & Cơ chế Phase 2:**
   - Kiểm tra `game.contract.json` (`contract_version: "1.1"`) khớp `core/config.py`.
   - Kiểm tra hỗ trợ `--night 1|2|3`, thứ tự 12 bước trong tick, trạng thái Bóng Mực (`spawning`, `wander`, `chase`, `recoil`, `stunned`), trường mới trong snapshot/scenario/input/event, và mã thoát `2` khi đầu vào sai.
   - Kiểm tra bản đồ chuẩn Đêm 1, 2, 3 (tọa độ cực từ `+X` CCW, cầu tre, bục nhảy, 3 tầng, 2 dốc, tháp chuông, gió).
3. **Sửa lỗi Camera/Điều khiển 3D (`web/static/app.js`):** Kiểm tra `mat4LookAt` tính `x_cam = cross(up, z_cam) = (zz, 0, -zx)` (không bị lộn ngược map hay ngược phím `A`/`D`).
4. **Chất lượng Test & Hiệu năng:** Kiểm tra không có test rỗng, test luôn PASS giả, hoặc `skip` không có giải thích trong `docs/notes/decisions.md`; xác nhận benchmark 21.600 tick `<= 30s`.
5. **Chạy lại độc lập:** Tự thực thi `python scripts/verify.py` và `pytest -v` và xác nhận exit code `0`.
6. **Ghi kết luận:** Tạo hoặc cập nhật `docs/proof/<phase>/review.md` ghi rõ các mục đã kiểm, lệnh đã chạy, phát hiện (nếu có) và phán quyết `APPROVED` hoặc `CHANGES_REQUESTED`.
