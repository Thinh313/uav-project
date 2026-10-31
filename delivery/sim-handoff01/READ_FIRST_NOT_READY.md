# SIM-HANDOFF01 · Gói engineering, chưa nghiệm thu

**NOT READY.** Đây là bản để đội tích hợp rà soát/cài thử trong môi trường mô phỏng. Chưa kiểm chạy AP vòng kín, Android, điện thoại Xiaomi hoặc hình ảnh/âm thanh thực trên bản này. AUTO/KML và payload/video đồng thời chưa tích hợp. Không phải bản khách hàng hay bản điều khiển Hera thực.

## Thành phần

- APK development riêng `vn.rtr.aeris.simhand01`, không đè ứng dụng khác.
- Host launcher/doctor/USB installer, gateway manual, cockpit cảm ứng và observer 3D/audio.
- Physics tham chiếu kế thừa SIMTRAIN53: quad 3 kg, profile tải giữa/lệch 1 kg, gió có seed. Chưa hiệu chỉnh Hera, chưa tái kiểm thực trên bản này.
- Asset 3D/Three.js/HDR/fonts kèm attribution; manifest/hash và receiver kiểm byte.

## Máy host được nhắm tới

macOS Apple Silicon, Python 3.14.6, Node 24.14.1, Android platform-tools và Docker Desktop có sẵn đúng image `sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84`. Archive không chứa SDK hoặc Docker image. Gói chưa chứng minh chạy trên máy sạch; Windows/Linux không được hỗ trợ ở lượt này.

## Trình tự cài thử

1. Đối chiếu SHA256 archive với báo cáo bàn giao; kiểm bằng `archive.py verify` trước khi giải nén. Dùng thư mục nhận mới, không sao chép đè dự án đang làm.
2. Từ thư mục gốc đã giải nén, chạy `python3 -B planning/simhand01/launcher.py doctor`. Thiếu prerequisite thì dừng, không tự đổi cấu hình để vượt gate.
3. Chạy `python3 -B planning/simhand01/launcher.py start --ack-simulation`. Lệnh chủ động của operator tạo ngân sách phiên mới có giới hạn. Không tự mở AP hay ARM khi tải trang.
4. Kết nối điện thoại USB, bật gỡ lỗi USB và chấp nhận máy tính. Dùng `adb devices -l` để lấy đúng serial.
5. Chạy `python3 -B planning/simhand01/install.py install --serial SERIAL_CUA_DIEN_THOAI --launch`. Installer chỉ cài package này và reverse cổng 8896; không root hoặc sửa ứng dụng khác.
6. Điện thoại mở cockpit; laptop mở `http://127.0.0.1:8896/observer`. Nhóm QA cần tự nghiệm thu preflight → điều khiển manual → release/mất focus → LAND/disarm → review/export. Chưa đánh dấu các bước này PASS.
7. Dừng bằng `python3 -B planning/simhand01/launcher.py stop`; giữ toàn bộ log và biên bản closure. Không tự xóa container/volume/hồ sơ để tiếp tục.

Gate dung lượng: admission 20 GiB, floor 10 GiB + 256 MiB dự phòng, theo dõi forecast. Ngân sách tác vụ phát triển đã hết và không dùng lại để chạy; chỉ bộ nhận đã kiểm byte, do operator chủ động khởi động, mới tạo ngân sách phiên tương đối. Chính sách này không phải nghiệm thu tính vận hành của gói.

## Phần phải hoàn tất trước chuyển giao sử dụng

- Doctor/start/stop trên thư mục nhận và cấu hình host thực.
- Kiểm vòng kín trên đúng code cuối, đối chiếu pose/RPM/clock, failsafe và nguyên trạng hồ sơ.
- Xem và nghe output 3D/audio; kiểm camera ground/follow/payload đúng phần đã hỗ trợ.
- Kiểm Xiaomi thật: input, DPI/safe area, ra nền, mất cáp, restart và SAF.
- Bổ sung AUTO/KML/upload/readback và camera/video cùng phiên, không thay bằng hoạt ảnh hoặc mock PASS.

Hướng dẫn chi tiết ở `planning/simhand01/README.md` trong archive. Hash bảo đảm toàn vẹn byte; không phải chữ ký phát hành production hay chứng nhận độ giống Hera.
