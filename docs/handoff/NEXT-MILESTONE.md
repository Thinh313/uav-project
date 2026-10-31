# Chiến dịch tiếp theo: beta simulator tích hợp

Anh đề nghị nhóm gom việc thành một milestone sản phẩm, không tiếp tục báo DONE
cho từng bản vá mà chưa đi hết hành trình. Tên làm việc: BETA-SIM-STABLE.
Mục tiêu là một cấu hình source/APK/profile xác định chạy đủ nhiệm vụ và đóng
bằng chứng, trước khi nối tới phần cứng thật.

## Giai đoạn A: tiếp nhận và khoanh đường chạy

Các em chốt source/tag và machine profile, xác minh mọi input cần cho đường selected,
đọc primary/secondary causes trong kit, tái lập mock và ghi thiếu prerequisite.
Đầu ra là sơ đồ luồng, danh mục dependency có SHA, quyết định ngân sách artifact
và một lệnh kiểm chỉ đọc có log. Không thêm tính năng mới trong giai đoạn này.

## Giai đoạn B: cold-start và media

Kiểm R02 trên lượt ngắn sau gate. Đo AP boot time và host wait riêng, chỉ đi tiếp
khi health thực đạt và dữ liệu đủ tươi. Theo dõi source/viewer/collection riêng;
đo encode, gửi, nhận, decode, warm frame và display. Khi sourceAGE250 từ chối,
ghi đúng substage và qualified clock interval, không suy ra do UI hoặc onPause.

Đầu ra phải có video-measure dispatch/ack và frame proof thực. Một nút hết disabled
hoặc một timeout được đổi thành lỗi nhanh chưa là kết quả chức năng.

## Giai đoạn C: hành trình 10 phút

Dùng cùng release đi từ lập nhiệm vụ tới preflight, upload/readback,
AUTO, HOLD/manual/assisted, chủ động LAND và review. Chạy đồng thời payload/video,
kiểm quyền hai operator và phản hồi sai target. Thử mất link, AP reboot,
app restart và nhận gói SAF ở receiver độc lập.

Mỗi lần gián đoạn phải giữ hồ sơ và thu hồi quyền. Khôi phục record không tự
cấp lại authority. Không cộng hai khoảng chạy bị ngắt thành một lượt liên tục.
Không giữ joystick cuối khi input mất freshness.

## Giai đoạn D: lặp và chốt beta

Lặp ít nhất 3 polygon và 3 corridor, gồm hình nhỏ/lớn, trường hợp góc hẹp,
Home/cao độ khác nhau và tải host được công bố. Giữ các ca âm: stale input,
sai receiver, sai payload target, thiếu/méo gói, quota và closure không đủ.
Dùng tiêu chí đã chốt trước lượt; không đổi ngưỡng sau khi biết kết quả.

Chỉ chốt beta simulator khi không còn lỗi chặn P0/P1 trong profile đã công bố,
đủ frame, không journal gap chưa giải thích, video/payload đạt tiêu chí được đo,
quyền thu hồi đúng, restart/receiver không kết luận sai và shutdown sạch.
Các em phải công bố cả cấu hình, số lượt, denominator, percentile và failure.

## Giai đoạn E: phần cứng

Sau beta simulator mới chốt SDK/transport/input của controller, thông số aircraft
và payload thật. Bench trước, tiếp theo HIL, rồi flight test được phê duyệt riêng.
Mô hình Hera cần dữ liệu khối lượng/quán tính, thrust/RPM, pin, tải và gió thực;
không hiệu chỉnh bằng cảm giác hoặc dùng hình 3D đẹp làm bằng chứng vật lý đúng.
Phase One, RGB, thermal, gimbal và media gốc có contract/qualification riêng.
