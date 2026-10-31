# Hera / HeraHub · Hardware baseline và yêu cầu giao diện

12/10/2026. Chủ việc xác nhận phần mềm sẽ cài trên tay cầm Hera. Tài liệu cung cấp định danh GCS là **HeraHub 2.0**; HERA 2.0 là máy bay, có một mục HeraHub trong master specification. HeraLink là tên cũ, HeraHub là tên hiện tại theo chủ việc ngày 12/10/2026. Exact revision của tay cầm dùng để nghiệm thu chưa được xác nhận. Chọn HeraHub 2.0 làm model candidate để thiết kế, không coi tên sản phẩm là bằng chứng cấu hình thực.

Đã lập inventory 32 file; trích đọc 16 XLSX, 7 DOCX, 2 PDF với vị trí sheet/ô, block/table hoặc trang và SHA-256. Bảy file ảnh/STEP/không đuôi được inventory, chưa parse. Nguồn gốc ở `/Users/os/Downloads/RTR-Specification` chỉ được đọc, không chỉnh. Trong phạm vi bộ này chưa thấy BOM cấp linh kiện có manufacturer part-number và revision cho tay cầm; có master/variant specs, tài liệu pin/sạc, brochure và báo giá. Tài liệu là dữ liệu nguồn, không phải lệnh triển khai, chứng nhận hoặc quyền ra lệnh bay.

## Căn cứ phần cứng

Nguồn chính: [HERA 2.0 master V1.0.1](</Users/os/Downloads/RTR-Specification/RTR Master Specification/HERA 2.0/HERA 2.0-MASTER-V1.0.1.xlsx>), sheet `Specs`, mục B `HERAHub 2.0` từ dòng 30. Đối chiếu bản Quatest và [HeraHub spec VI](</Users/os/Downloads/RTR-Specification/RTR Variant Specification/Anh Hoàng-HVKTQS/HeraHub 2.0/HeraHub 2.0-HVKTQS-V1.0-Spec-VI.docx>). Các trị số dưới đây là **source claims**, chưa đo trên thiết bị.

| Hạng mục | Nguồn ghi | Locator / xử lý |
|---|---|---|
| Màn hình | LCD cảm ứng 10,1″; 1280×800 | Master `Specs!C31`; DOCX VI `body[25]/table/r2/c2`. `History!D3` ghi đổi từ 1920×1200/1200 nits ngày 16/7/2026; không dùng thông số cũ làm cấu hình hiện tại |
| Độ sáng | Master/spec 1800 nits; brochure 2000 nits | **CONFLICT**: `Specs!C31` và [brochure](</Users/os/Downloads/RTR-Specification/RTR Variant Specification/Anh Hoàng-HVKTQS/HeraHub 2.0/HeraHub-Brochure-digital.pdf>) trang 2. Profile để null, giữ hai candidates; **không chặn phần mềm**, độ sáng đủ theo quyết định chủ việc |
| SoC / RAM / GPU | Qualcomm QCS8550; RAM 16GB; Adreno 740 | `Specs!C32:C33`; khả năng API đồ họa trong spec chưa kiểm driver/firmware |
| Số nhân CPU | Master/table ghi 1+2+3; DOCX EN gọi hexa-core nhưng liệt kê 1+4+3 | **CONFLICT**: `Specs!C32`, DOCX EN `body[17]/p`. Không dùng để đặt ngân sách luồng/hiệu năng |
| Hệ điều hành / storage | Android 13; 512GB, tùy chọn SSD 1TB | `Specs!C40:C41`. Chưa có build fingerprint, storage thực và SDK |
| Video | Tối đa sáu luồng 1080p | `Specs!C35`; đây là capability claim, chưa có codec/fps/bitrate/latency hoặc phép đo decode đồng thời |
| Liên kết / cổng | RF, Cellular, Starlink, Tether; RTK-GNSS; USB-C display, USB3, Ethernet, audio, SIM | `Specs!C36`, `C39`. Brochure/spec feature còn nêu fiber; chưa biết module/link nào đang lắp |
| Điều khiển vật lý | 8 nút, 4 joystick, 4 switch, dial/wheel; trim, limit, dead zone, invert | DOCX EN `body[18]/p`; `Specs!C38`. Hình brochure cho bố trí hai grip, phím L/R; không suy ra keycode/channel từ hình |
| Nguồn điện | Hai pin hot-swap; spec nêu 2,5 giờ/bộ | DOCX EN `body[8]/p`, `Specs!C34`. Bảng pin Quatest riêng ghi 14,4V/3000mAh; không suy ra runtime bằng phép tính danh nghĩa |

Độ sáng không nằm trên critical path phần mềm; giữ lịch sử nguồn, không mở việc phân xử số nits. Những claim NDAA, RTK centimet, “unlimited” hoặc “field-proven” trong marketing không được chuyển thành kết quả kiểm nghiệm phần mềm.

Profile truy nguồn: `hardware/herahub2/profile.json`; raw-file fingerprints và nội dung trích tại `hardware/herahub2/sources`. Android density, usable window dp, key/axis mapping, board/RF revision và decoder limits hiện UNKNOWN.

## Thay đổi yêu cầu thiết kế

1. **Controller trước desktop.** Màn hình ngang 16:10 và tư thế hai tay là bối cảnh chính từ spec/render. Ưu tiên map/video ở giữa, trạng thái và hành động quan trọng ổn định, ít điểm buộc đổi grip. Tablet/mobile/desktop là các cách review/phụ trợ. Tầm với thật và găng tay còn cần kiểm UX; độ sáng được coi là đủ theo chủ việc.
2. **Pixel vật lý, dp và CSS là ba đại lượng khác nhau.** [Android density guidance](https://developer.android.com/training/multiscreen/screendensities) dùng dp cho layout, sp cho chữ. 1280×800 là claim pixel panel; chưa biết `densityDpi`, font scale, system bars và IME. Browser viewport 1280×800 chỉ là reference QA, không phải xác nhận Android window trên HeraHub.
3. **Vùng chạm cho bản Android.** Chọn ít nhất 48×48dp theo [Android touch target guidance](https://support.google.com/accessibility/android/answer/7101858?hl=en), tăng cho thao tác chính sau thử glove. Sàn 44 CSS px của UX01 là kiểm web; không coi đó là đã đạt 48dp. Kiểm độ rõ chữ và thao tác trên thiết bị; không yêu cầu phân xử nits để triển khai.
4. **Chạm và phím vật lý phải phối hợp.** Dự kiến screen actions có affordance rõ và mapping hiển thị khi đã xác minh. Chưa gán L/R, joystick hay switch cho AUTO/HOLD/RTL. [Android controller events](https://developer.android.com/games/sdk/game-controller/controller-input) mô tả KeyEvent/MotionEvent cho thiết bị tương thích; Hera có thể dùng HID, UART hoặc SDK riêng, cần evidence trước khi chọn adapter.
5. **Tách trạng thái theo thiết bị.** Pin drone khác pin A/B của controller; RTK máy bay khác base; RF/control link khác video, cellular và đường đang active. Trường chưa có dữ liệu phải hiện unavailable. Multi-operator/trainer cần owner/role và handover có trạng thái, không chỉ thêm nút chuyển.
6. **Video theo nhiệm vụ.** Một stream chủ đạo và lựa chọn stream/phần quan sát khác là đề xuất UX; không mặc định sáu view bằng nhau. Số luồng, decoder, memory/thermal và latency cần đo theo codec thật. Chưa bật các feed giả để thể hiện capability.
7. **Chạy cài đặt được trên Android là bước tích hợp riêng.** Kiểm lifecycle, foreground/background/reconnect, permission, signed APK/update/rollback, lưu mission/log offline và khôi phục sau lỗi. Web workbench hiện tại phục vụ review logic/UI; chưa là APK cài Hera. Theo ADR-008, dùng kiến trúc mới độc lập và kiểm SDK/native services của HeraHub, chưa thay stack production bằng browser.

## Contract bước tiếp theo

| ID | Kết quả cần có | Trạng thái hiện tại |
|---|---|---|
| HERA-01 | Profile có source locations, conflicts và unknowns; intent target trong SOT | Implemented; byte/location integrity được kiểm |
| HERA-02 | Touch reference Plan/Fly ở 1280×800: cơ bản/kết quả/hành động không bị clip; file/camera/zoom dùng chạm | Browser reference QA; không phải emulator/Hera |
| HERA-03 | Android window thật: resolution, density, insets, font scale, keyboard và lifecycle | NOT_CHECKED |
| HERA-04 | Device input inventory/mapping, calibration, hot-plug, held/repeat/debounce; flight ownership không phụ thuộc focus UI | NOT_CHECKED |
| HERA-05 | Installed RF/RTK/payload/video adapters, throughput/latency/thermal, lỗi link và pin hot-swap | NOT_CHECKED |
| HERA-06 | Signed APK và diễn tập SITL/HIL trên đúng hardware revision | NOT_CHECKED |

Đầu vào hữu ích tiếp theo: BOM board/screen/RF/I/O có part-number và revision; firmware/Android build và SDK; key/axis/channel map; log A/B từ RAGAS; log điều khiển/video. Đây là danh sách làm rõ tích hợp, không phải yêu cầu mua thiết bị hay phát hành ứng dụng.

## HERA02 · cập nhật nghiên cứu phần mềm

Nguồn công khai tách nền Intel và HeraHub v2 Android; manifest RAGAS 4.0.14 build 111 dùng arm64-v8a. Manual có RC mapping/calibration, MAVLink signing/forwarding, NTRIP, offline và payload OTA; chưa cung cấp wire-level SDK. Độ sáng đủ theo chủ việc, không chặn phát triển. Runtime discovery xử lý storage, density và decoder; không ghép phiên bản/brochure thành cấu hình đo được. Xem `HERAHUB-SOFTWARE-RESEARCH.md` và `HERAHUB-INTEGRATION-BACKLOG.md`.

## BOM supplied after HERA02

0.BOM26.xlsx now supplies component-level internal PN/drawing/quantity/unit context across 41 sheets; the previous NOT_FOUND statement applies only to the original RTR-Specification set. HeraLink V1.1-DDL/DTC lists Getac and legacy radio variants. No automatic merge into HeraHub v2/QCS8550 profile: installed revision still UNKNOWN. SOT entrypoint: `../sot/README.md`; workbook errors and hidden masters preserved.

Owner update 2026-10-12: source RAGAS không còn là dependency; ứng dụng độc lập, RAGAS là đối chứng A/B.
