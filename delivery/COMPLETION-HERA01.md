# Completion · Hera controller baseline HERA01

12/10/2026. **DONE cho đọc nguồn, cập nhật đích cài đặt và browser reference QA.** Người dùng xác nhận cài trên tay cầm Hera; HeraHub 2.0 được nhận diện là GCS model candidate trong bộ spec, chưa xác nhận exact delivered revision. Không có APK hoặc adapter phần cứng được cài trong đợt này.

Đã inventory 32 file; trích 16 XLSX, 7 DOCX, 2 PDF ở `hardware/herahub2/sources`, gồm vị trí ô/block/trang và hash của 25 file nguồn. Nguồn ngoài workspace chỉ đọc. Ảnh/STEP/file không đuôi còn inventory-only. Brochure HeraHub được render hai trang trong project để xem tư thế màn hình/grip/phím; không dùng render làm bằng chứng keycode/channel.

Profile 22 trường giữ spec claims và unknowns. Màn hình 1280×800/10,1″ và Android 13 là source claims nhất quán trong master/spec; thay đổi 1920×1200 nằm trong history. Brightness 1800/2000 nits và CPU topology 1+2+3 so với 1+4+3 giữ **CONFLICT/null**. Claim sáu luồng 1080p, hot-swap, RAM/GPU và các link không được chuyển thành benchmark. Chưa thấy BOM cấp linh kiện có part-number/revision của tay cầm trong bộ cung cấp.

## Contract và verify

| Tiêu chí | Trạng thái | Chứng cứ |
|---|---|---|
| HERA-01 source/profile/intent | PASS byte/location/status scope: 25 source hashes, 18 profile locators, 3 Android web captures; conflicts/unknowns giữ null. SOT có 13 records; source target intent được review, accept baseline và gate | `hardware/herahub2/profile.json`, `evidence/hera01/hardware-integrity.txt`, SOT receipts |
| HERA-02 touch reference | PASS 7 checks: basic fields/actions không clip; chọn tuyến/footprint/zoom; menu/camera; dirty/recalculate; Fly visibility; ACK/observed; bốn workspace không overflow/runtime exception | `evidence/hera01/reference-qa.json`, `hera-plan-reference.png`, `hera-fly-reference.png` |
| HERA-03 Android metrics/lifecycle | NOT_CHECKED | Không có thiết bị/emulator trong scope |
| HERA-04 physical input mapping | NOT_CHECKED | HID/UART/SDK, keycodes/axes, calibration và RC routing chưa cung cấp |
| HERA-05 adapter/performance/power | NOT_CHECKED | RF/RTK/payload/codec thực, latency/thermal và battery handover chưa đo |
| HERA-06 signed APK/SITL/HIL | NOT_CHECKED | Chưa có source/build/device configuration để nghiệm thu tích hợp |

Chromium test dùng `hasTouch=true`, viewport 1280×800 và DPR=1 giả định. Đó là khung tham chiếu theo panel, không phải dp/insets/window của Android thực hoặc test Hera. Tài liệu Google Android được lưu riêng để truy nguồn: dp/sp, touch target 48dp, KeyEvent/MotionEvent chỉ áp dụng khi input device hỗ trợ tương ứng. Proposed production requirements ở [HERA-CONTROLLER-BASELINE](../docs/HERA-CONTROLLER-BASELINE.md); ADR-005 và TIP-HERA01 ghi scope.

App HTML/CSS/controller và hai core engines giữ nguyên bytes so với UX01 (`app-preservation.json`). 27 core / 19 browser / 13 UX PASS của UX01 là kết quả kế thừa cho app không đổi; không báo là chạy mới ở HERA01. Hai domain Refinery và SOT integrity/fault/gate được chạy mới, receipts riêng trong `evidence/hera01`. Một test đầu mong đợi nhầm câu dirty-message; đã sửa kỳ vọng và kiểm thêm disable/enable hành động. Receipt lỗi test ban đầu giữ ở `reference-qa-first-run.json`; không có thay đổi app để né test.

Single-agent source review/verify. Component BOM, exact hardware revision, display density/font scale/usable window, Android build, SDK/input map, RF module và source RAGAS còn cần cho bước tích hợp. Không tự gán nút L/R hay joystick cho lệnh bay.

## Hygiene

Không copy project hoặc thư mục spec, không parse/copy STEP 232MB, không cài dependency/SDK, không tạo build folder hoặc dùng Docker. Các bản trích văn bản và hai render nhỏ giữ trong project. Scratch kiểm fault đã xóa trong `finally`: `/private/tmp/codex-tmp-aeris-hera01-20261012`. Không cần dọn dữ liệu của người dùng trong RTR-Specification.
