# AERIS COACH02: huấn luyện manual bằng mô hình tham chiếu

Mở COACH01 bằng launcher hiện có `delivery/coach01-host/Start Debrief.command`, hoặc từ thư mục AERIS chạy `node pilot/coach01/server.mjs`. Host chỉ nghe trên 127.0.0.1:8897, tự đóng sau 30 phút. Truy cập `http://127.0.0.1:8897/manual/` hoặc chọn “Huấn luyện manual” ở debrief. Host cần ít nhất 20 GiB trống để khởi chạy; khi ghi giữ 10 GiB và dự phòng 256 MiB. Không tự xóa hồ sơ.

## Thực hành

1. Nhập tên operator, chọn bài giữ vị trí / bay thẳng và dừng / xoay hướng và ổn định. Chọn đáp ứng tham chiếu có tải hoặc không tải và nguồn bàn phím hoặc bảng trục mock.
2. Bấm “Tạo bài và đồng bộ clock”. Thả tất cả phím, đưa các trục về 0.
3. Bấm “Nhận quyền và bắt đầu”. Đây là một thao tác để tránh lease 200 ms hết hạn giữa hai lần bấm. Nếu clock/quyền hết hạn, đồng bộ và xin quyền lại một cách rõ ràng; chương trình không tự khôi phục quyền.
4. W/S tiến/lùi, A/D trái/phải, R/F lên/xuống, Q/E xoay. Với nguồn bảng trục, dùng các slider. Mất focus/background dừng lấy mẫu và yêu cầu thu hồi quyền khi host còn truy cập được. Không retry POST tự động nếu kết quả chưa rõ.
5. Bài kết thúc khi đủ bước hoặc chạm giới hạn tham chiếu. Muốn kết thúc sớm, thu hồi quyền rồi “Kết thúc và lưu”. Bài thiếu bước có trạng thái INCOMPLETE.
6. Chọn hồ sơ trong lịch sử, kéo timeline, xem sai số/quyền/clock, xuất gói raw, nhập lại để đối chiếu. Reload/host restart chỉ cho xem hồ sơ, không phục hồi phiên/quyền. Dùng “Đóng phiên cũ sau reload” nếu host còn giữ phiên cũ trước khi tạo bài mới.

Receiver CLI kiểm SHA, chuỗi journal, từng kết quả/state và đánh giá đã tính lại:

```sh
node pilot/coach02/receiver.mjs /absolute/path/manual-package.json
```

## Phạm vi bằng chứng

Ba bài kéo dài 18–20 giây mô phỏng, bước 50 ms. Đầu vào là vận tốc thân/tốc độ xoay chuẩn hóa, không phải PWM hay attitude. Hai profile chỉ đổi hằng số đáp ứng 0,55 / 0,95 giây. Gió là offset vận tốc tham chiếu, không phải khí động học hoặc thời tiết Hera đã hiệu chuẩn. Mô hình không có 6DOF, collision, cảm biến tránh vật cản hoặc ArduPilot. Không dùng để chứng nhận kỹ năng bay thật.

Clock input và host có danh tính riêng, được đối chiếu bằng khoảng offset và độ bất định; không ghép clock hoặc đổi speedup. Thời gian callback bàn phím không phải thời gian vật lý HID. Mỗi bước được fsync trước khi công bố; raw ghi cả action bị từ chối. Hồ sơ chứa phím, snapshot phím đang giữ, trục, operator/boot/session/profile, lease và clock. Receiver nhận biết gói pending, thiếu closure, sửa state/grade và không biến dữ liệu AUTO thành chứng cứ manual. SHA/replay chứng minh nhất quán nội bộ, không xác thực danh tính nguồn hoặc chữ ký.

Các kiểm UI dùng Node VM và DOM/network/timer giả. Chưa kiểm hình ảnh, pixel, chồng đè, tương phản thực, cảm ứng, FPS, âm thanh, HID, Android hay HeraHub. Mô hình controller tự động dùng trong corpus mang nhãn SCRIPTED_MOCK, không phải người lái hoặc AI học máy. Host preview là mock, không có đường gửi lệnh UAV.
