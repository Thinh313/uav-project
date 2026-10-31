# Biên bản tiếp nhận và giao việc

Anh đề nghị các em đánh dấu theo kết quả đã kiểm, không ký một nhãn tổng quát
“clone thành công, nhận đủ, chạy được” khi còn thiếu bộ private hoặc runtime.

## Tiếp nhận source

- Đã ghi URL repo, tag và commit thực nhận.
- Đã chạy verify SHA; số file khớp với manifest của bản đó.
- Đã kiểm source links, giấy phép và các mục public/private.
- Đã nhận đúng BOM/context qua kênh riêng; không có chúng trong public working copy.
- Đã ghi các file được phục dựng từ Git và các nhãn được ẩn danh.

## Tiếp nhận artifact

- Đã pin SHA gói ngoài bằng kênh tin cậy, kiểm 24 thành phần và các manifest trước giải nén.
- Đã tạo workspace private ngoài Git, giữ receipt và phân biệt 9 overlay gốc với public snapshot.
- Đã kiểm manifest từng file và preserved hardlinks/modes trong engineering tar.
- Đã xác định SDK/AVD, image architecture, AP executable, APK/certificate và profile.
- Đã ghi rõ artifact/log nào chưa có; không tạo dữ liệu giả thay thế.
- Đã phân biệt kiểm byte với kiểm chữ ký/trust, clock/PID và runtime thực.

## Kiểm môi trường mới

- Đã ghi OS/CPU/RAM, Node/Python, Docker, Android/WebView và nguồn input.
- Đã chạy mock không nối thiết bị; giữ log stdout/stderr và source SHA.
- Đã ghi admission, quota, nguồn điện và cổng/actor sở hữu trước lượt thực.
- Đã đóng đúng actor thử nghiệm; không dừng hoặc dọn phiên của người khác.

## Mẫu báo cáo một lượt

Các em dùng các trường sau: mục tiêu; source/tag; APK/AP/profile SHA;
platform; command; started/ended; host elapsed; AP elapsed; pass/fail/not-checked;
primary cause; secondary cleanup errors; raw/manifest SHA; receiver result;
frame/clock continuity; quyền sau mất link/restart; phần chưa chứng minh;
quyết định tiếp theo. Tên người review và phạm vi review cần ghi rõ.

## Chấp nhận có điều kiện

Một nhóm có thể nhận source đầy đủ nhưng chưa chạy được Android-SITL vì thiếu
SDK hoặc artifact. Khi đó ghi đúng “đã nhận source, runtime chưa kiểm”.
Tương tự, có thể chấp nhận bộ byte của một hồ sơ lỗi mà không chấp nhận nhiệm vụ
bay hoặc chất lượng khảo sát. Người tiếp nhận, người kiểm thử và người chốt
release là các vai trò khác nhau; ghi đúng ai chịu trách nhiệm phần nào.
