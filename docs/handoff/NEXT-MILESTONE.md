# Milestone tiếp theo: tiếp tục đúng trạng thái, đóng G1 rồi mới vào SITL

## Một mục tiêu có thể nghiệm thu

Nhóm cần một release chạy trọn khảo sát -> preflight -> Fly manual/assisted/AUTO cùng video/payload -> review -> SAF/receiver, có mất link/reboot và persistence. Điều kiện beta simulator là cùng cấu hình source/APK/profile, đủ raw và frame, không tự phục hồi quyền, không còn lỗi chặn P0/P1 trong phạm vi công bố.

## Bước 1: tiếp nhận và nguồn dữ liệu

Clone đúng tag H10, verify source và chạy mock public. Nhận gói private, kiểm SHA qua kênh tin cậy và dựng workspace ngoài Git. Ghi cấu hình máy, source/pins và các prerequisite thiếu. Không sửa candidate/raw lịch sử hoặc ghép ngầm các revision.

## Bước 2: contract trạng thái đã thay đổi

Dùng raw m801 và các STATUS gốc để ràng buộc index 83 file/9 thư mục, lifetime generation 10, hai journal mới đóng/rỗng và tám archive. Chứng minh bảo toàn dữ liệu cũ, mode/UID/GID, workspace, counter và registry prefix. Kiểm âm với snapshot 75 file, thiếu journal/STATUS, sai SHA/head/counter, thêm file hoặc thay mode/UID/GID.

Không dùng decoder trạng thái ban đầu và không gửi lại APPLY của g103. m801 chỉ là observation anchor mới, không tự cấp quyền archive hoặc resume. Tạo contract tiếp tục có source pin, receiver đối chiếu độc lập và admission mới trước chạy G1.

## Bước 3: G1 thực bằng bản sửa

Dùng candidate xác định kiểm qualification, hai phiên native, full cold export và lossless seal/ref. Phải kiểm normal closure thực sau ACK cuối, lỗi writer/observer/thread và restart/persistence. Kết quả mock của H10 chưa thay bước này. g105 giữ FAIL dù dữ liệu còn bảo toàn.

## Bước 4: G2 và G3

Chạy ngắn polygon rồi corridor Android-SITL, kiểm KML/mission model, preflight, upload/readback, manual/AUTO, video/payload và SAF receiver. Ghi từng chặng encode/gửi/nhận/decode/display và clock qualified; không lấy nút hết disabled hoặc ACK làm bằng chứng execution/ảnh thật.

Sau đó thử mất link, AP reboot và app restart. Quyền phải bị thu hồi, hồ sơ được giữ và record khôi phục không tự cấp lại authority. Mỗi ca âm có primary cause, cleanup/disposal và byte inventory riêng.

## Bước 5: G4 và mở rộng corpus

Chỉ khi các cổng thực tế trước đạt mới chạy 600 giây bay tích hợp liên tục. Không cộng các interval gián đoạn hoặc thời gian idle. Tiếp tục corpus rộng hơn gồm ít nhất ba polygon và ba corridor, trường hợp Home/cao độ, hình nhỏ/lớn/góc hẹp và tải host được khai báo.

## Sau beta simulator

Controller/input/video, SDK/MCU/radio, Phase One/RGB/thermal/gimbal thật cần bench riêng, sau đó HIL và field qualification. Mô hình Hera cần số đo mass/inertia/thrust/RPM/pin/payload/gió; hình 3D hoặc cảm giác điều khiển không thay dữ liệu hiệu chuẩn. Đây là gate riêng, không được suy ra từ simulator.
