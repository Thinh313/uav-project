# Completion · RtR UI/UX redesign UX01

Ngày: 12/10/2026. Phiên bản 0.2. **Đã triển khai và kiểm kỹ thuật trong prototype cục bộ; thẩm mỹ chờ chủ việc đánh giá.** Bản M0 bị chủ việc bác về chất lượng UI; báo cáo này thay đánh giá trình bày trước đó. Chưa có kết quả thử với operator hoặc bằng chứng vượt trội so với GCS khác.

## Thay đổi

Thiết kế lại HTML/CSS/UI controller theo workspace đen, inspector trắng và vàng phụ, font IBM Plex Sans cục bộ, icon SVG thống nhất. Canvas và các kết quả khảo sát giữ vai trò trung tâm. Chọn tuyến bằng chạm hoặc bàn phím; xem footprint tính từ camera; zoom/fit giữ nguyên mission. Menu file, camera disclosure và drawer điều kiện diễn tập giảm cạnh tranh với thao tác chính. Dirty/invalid/valid và vòng đời lệnh có phản hồi chữ. Dữ liệu cũ hiện `—` thay số trông như còn mới; reset cho hủy hoặc xuất log. Sheet mobile giữ focus, Escape và trả đúng điểm mở.

Hai engine `app/core/mission.mjs` và `flight.mjs` giữ nguyên bytes so với manifest M0 (`evidence/ux01/core-preservation.json`). Pure engine, dữ liệu giả lập và giới hạn mission không đổi. Đây vẫn là workbench khảo sát trên mặt phẳng cục bộ; chưa có bản đồ địa lý, drone hoặc camera thật.

## Kết quả theo acceptance criteria

| Tiêu chí | Kết quả / phạm vi | Chứng cứ ở `evidence/ux01/` |
|---|---|---|
| UX-01 branding | PASS token trắng/đen/vàng và font offline. Vàng 1,005% ở 1440×900, 1,549% ở 1024×768, 1,388% ở 1280×720, 0,457% ở 390×844; dưới ngân sách nội bộ 5% | `ux-qa.json`, `palette-measurement.json`, ảnh Plan |
| UX-02 thông tin/hành động | PASS ở 1440×900, 1024×768 và viewport thực 1280×720: basic inputs không bị footer che, summary/validation/tính lại/mở Fly trong khung nhìn; Fly giữ mode/telemetry/trạng thái lệnh/nút lệnh | `ux-qa.json`, `plan-1440.png`, `plan-1024.png`, `plan-1280.png` |
| UX-03 tương phản/vùng chạm/focus | PASS các cặp token đã khai báo; vùng chạm của button/input/summary active trong các trạng thái chọn kiểm ≥44px; thao tác focus và Escape có kiểm | `ux-qa.json`; không phải audit WCAG toàn diện |
| UX-04 hình học và tương tác | PASS tuyến chọn, footprint 90m từ fixture, zoom/fit và chạm trực tiếp SVG; view không đổi settings | `ux-qa.json`, core tests |
| UX-05 regression và stale state | PASS menu file, lưu/mở/xuất/nhập, validation; stale glyph/chữ; request/ACK/observed, rejected và timeout | `browser-qa.json`, `ux-qa.json`, `fly-stale.png` |
| UX-06 mobile/khôi phục | PASS sheet 390×844, advanced scroll, focus trap, Escape, hủy reset giữ log; kiểm overflow tại 390/768/1024/1440px | `ux-qa.json`, `plan-mobile-sheet.png`, `plan-mobile-canvas.png` |
| UX-07 provenance | PASS hash captures, hai domain Refinery, applicable fault injections, canonical adapter/SOT baseline/check/bites/gate | `evidence-checks.json`, các receipts Refinery/SOT; hash tổng 19 captures cho hai domain |
| UX-08 review và báo cáo | PASS render critique một agent, ảnh desktop/tablet/mobile và receipts thật đã lưu. **User aesthetic acceptance: PENDING** | Báo cáo này, `source-manifest.json`, ảnh và kết quả kiểm |

27 core tests PASS; 19 browser regression scenarios PASS; 13 UX checks PASS; syntax PASS. Không có runtime exception trong các lần browser QA. SOT phát hiện sáu lỗi tiêm. Mỗi domain Refinery: bốn original bites áp dụng và hai tamper checks PASS; mười checks không phù hợp cấu hình được ghi N/A, không đổi thành PASS. Kernel phương pháp không bị sửa. Các bản ghi M0 cũ được giữ ở thư mục evidence gốc.

## Nghiên cứu đã giao

[UIUX-RESEARCH](../docs/UIUX-RESEARCH.md) ghi nguồn → quyết định → cách kiểm và protocol thử operator. [UIUX-DESIGN-STANDARD](../docs/UIUX-DESIGN-STANDARD.md) giữ token/interaction/acceptance contract. Domain UI/UX có 12 claims, 12 hồ sơ thu thập cho 10 URL; 10 captures, trong đó shell DJI bị loại khỏi chứng cứ nội dung. ISO có hai lỗi HTTP 403 ghi nguyên trạng và bản trích web thay thế, chỉ abstract công khai. Bốn nhóm nguồn: NASA/DJI/W3C/ISO. Không tự nâng claim thành sự thật sản phẩm hoặc chứng nhận.

## Giới hạn còn phải đo

Thử người điều khiển, ngoài trời/găng tay, controller mục tiêu, Safari/Android và benchmark đối thủ: NOT_CHECKED. Optical summary/camera nâng cao nằm trong vùng inspector scroll; khả năng tìm thông tin này cần đo trong task khảo sát. Metadata phụ có chữ nhỏ 10–11px; độ đọc theo khoảng cách và ánh sáng thực chưa đo. Mã vàng là working token, chưa có brand book. Không kết luận “cao cấp/vượt trội” từ tương phản hoặc tỷ lệ màu. Không có thay đổi tích hợp bay trong milestone này.

## Disk hygiene

Không copy project, cài dependency tree mới, tạo Next distDir hay dùng Docker. Font và OFL lưu trong project (~0,5MB), server loopback giữ để xem. Đã xóa scratch của kiểm fault trong `finally`: `/private/tmp/codex-tmp-aeris-ux01-20261012`; profile browser tạm được Playwright dọn khi đóng. Không có hồ sơ cần giữ trong scratch.
