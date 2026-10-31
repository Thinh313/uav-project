# NATIVE31 — bàn giao APK development NATIVE30

**Trạng thái: PARTIAL_DEVELOPMENT_SIGNED_HOST_VERIFIED_ANDROID_NOT_RUN.** Người dùng đã cho phép ký APK development riêng, sau đó chọn giữ dung lượng hiện tại và nhận APK cùng phần kiểm đã đạt. Không khởi động emulator trong lần này.

## Đã bàn giao

- APK: `native/runtime31/dist/aeris-native30-development.apk`,66,441 byte; SHA-256 `b442b3ed1ad2ff171a6cbcde55ba513d45a484260cac1e9fc2f492b5d5aba221`.
- Package `vn.rtr.aeris.shell30`, versionCode31 / `0.3.1-native30-development`. Manifest khai báo min API26 / target33; chưa chứng minh tương thích bằng runtime.
- Chữ ký APK v2/v3 kiểm đạt. Certificate development riêng: SHA-256 `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`. Không dùng khóa phát hành, không ký/chọn software candidate mới. Private key không nằm trong gói bàn giao.
- Manifest development bật debug cho QA cục bộ, không yêu cầu permission, tắt backup và cleartext. Không có SDK/radio/lệnh bay. Nội dung APK sau ký khớp payload trước ký.
- Bản dẫn xuất đọc source NATIVE30, giữ nguyên tất cả source/receipt cũ; overlay Activity bật WebView debugging và gửi focus khi resume, chỉ để cho phép tạo lại gate mới, không khôi phục preflight/run. Nhãn UI chuyển từ unsigned sang development. Hash source/overlay/assets: `evidence/native31/build02.json`.

## Kiểm đã chạy và giới hạn

77 kiểm host chạy lại đạt:31 journal Java và46 editor. Đã đối chiếu APK/certificate/manifest/assets cùng hash bảo vệ3547 file cũ. Chi tiết và kết quả cuối: `evidence/native31/verification.json`, `preservation-after.json`, `final-signature.txt`.

Lỗi ART cũ `getFileStore SecurityException` và receipt FAIL vẫn giữ nguyên. APK development chứa bản sửa N30 dùng `File.getUsableSpace`, nhưng **chưa kiểm lại bản sửa trên ART**. Chưa cài APK, chưa kiểm Activity/bridge, persistence app-private sau force-stop/reboot, SIGKILL trên Android, SAF nhập/xuất, keyboard/window hoặc focus thật.77 kiểm host không thay các gate này. Không có nghiệm thu HeraHub/input/video thực hay điều khiển drone.

## Sự cố dung lượng và dọn dẹp

Admission sparse ban đầu chưa dự toán đủ cấp phát cuối: quan sát19,783,680,000 byte còn trống (khoảng18.43GiB), thấp hơn sàn20GiB. Tôi đã dừng, xóa riêng scratch tạo trong lần thử và bảo toàn receipt `resource-attempt01.json`; không tuyên bố giữ sàn suốt lần giải nén đó. Phép thử compression/lean runtime tiếp theo không khởi động emulator. User chọn bàn giao tại dung lượng hiện tại.

Đã xóa `native/runtime31/.runtime` (archive/image/emulator/probe), `.host-tests`; `.build` được helper dọn trong finally cả khi lỗi ký. Không sao chép toàn bộ dự án, không xóa dữ liệu khác, không tạo Docker image. APK/public certificate và bằng chứng nhỏ giữ lại; khóa development giữ local riêng với mode600 trong thư mục700. Dung lượng cuối ghi chính xác trong `verification.json`; phải còn≥20GiB để nhận bàn giao.

Lần chạy Android sau cần admission ít nhất28GiB free, ngân sách archive + toàn bộ uncompressed image + emulator + AVD + host margin; không dựa vào zero-seeking để giả định giảm cấp phát. Chỉ target emulator sở hữu rõ ràng, giữ20GiB dự phòng khi theo dõi dung lượng thực. Sau đó mới đóng gate ART/UI/persistence/reboot.

Source/candidate/software trust, các attempt ENDURE20 và ENDURE27 được đối chiếu byte; không chạy lại soak, không cộng interval, không thay monitor hoặc tích hợp Fly. ENDURE27 vẫn là lần thất bại đã ghi nhận, không được nâng thành PASS vì APK development này.

## Đối chiếu yêu cầu

| Yêu cầu | Kết quả |
|---|---|
| REQ31-01 APK development/chữ ký/provenance riêng | PASS |
| REQ31-02 ART/SIGKILL sau sửa lỗi | NOT_CHECKED;31 host PASS |
| REQ31-03 installed UI/private persistence/reboot | NOT_CHECKED |
| REQ31-04 focus/window/keyboard/SAF Android | NOT_CHECKED |
| REQ31-05 sàn dung lượng xuyên suốt | FAIL tại lần giải nén; đã dừng/dọn, sàn cuối kiểm riêng |
| REQ31-05 không đổi frozen/ENDURE, không project copy, dọn scratch | kiểm hash/cleanup trong verification |

Một agent thực hiện tuần tự Contractor/Builder/Verify; không gọi đây là audit độc lập hay nghiệm thu sản phẩm bay.
