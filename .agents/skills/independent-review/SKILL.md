---
name: independent-review
description: Perform an independent audit of code, Contract v1.2 compliance, fuel/drain/dawn_survived change request, ADR/Breaking Changes hygiene, camera orientation, performance, and proof before tagging a phase.
---

# Skill: Independent Phase Review

Dùng skill này bởi một subagent hoặc phiên AI **tách biệt với người/agent đã viết code** trước khi gắn tag `phase-N`.

## Checklist kiểm tra
1. **Diff & Kiến trúc:** Xác nhận `src/dao_den_long/core/` không import `http`, `web`, UI, `time`, hay global `random`; nhiên liệu đèn dùng đơn vị nguyên `1/60` (`fuel_60`) tránh sai số dấu phẩy động.
2. **Test Contract v1.2 & Change Request (TICKET-03):**
   - Kiểm tra `game.contract.json` (`contract_version: "1.2"`) khớp `core/config.py`.
   - Kiểm tra hao dầu `1/60`/tick, hút dầu `5/60`/tick + sự kiện `fuel_drain` mỗi 60 tick, `lantern_out`, châm dầu `ceil((100-fuel)/10)` bỏ qua đèn đầy, thắp lại tốn `5` (`ever_lit`), 6 trạng thái Bóng Mực (`spawning/wander/chase/recoil/stunned/drain`), hết choáng về `wander`, `+15` điểm khi Tỏa Sáng trúng con đang `drain`, luật thắng `dawn_survived` (không thắng sớm `all_lit`), sức chứa `10 + 2 * successful_lights` tối đa `20`.
   - Kiểm tra mã thoát `2` khi file inputs/scenario/flag sai.
3. **Giao diện 3D & Khả năng tiếp cận (`web/static/`):** Kiểm tra `mat4LookAt` right-handed, chế độ mù màu (`#00B3FF`, `#FFFFFF` + `⚠`), đèn tắt xẹp 20% + vết rách, thanh dầu + nhấp nháy `1 Hz` khi `fuel < 30`, tạo hình Áo Dài + Nón Lá.
4. **Hồ sơ Change Request & Chất lượng Test:** Kiểm tra có ADR trong `docs/notes/decisions.md`, mục Breaking Changes trong `CHANGELOG.md`, không có test tắt/skip âm thầm, và benchmark `<= 30s`.
5. **Chạy lại độc lập:** Tự thực thi `python scripts/verify.py` và `pytest -v` và ghi phán quyết `APPROVED` / `CHANGES_REQUESTED` vào `docs/proof/<phase>/review.md`.
