# Beta desk: đọc hồ sơ và bàn giao

Mở `Open Beta Desk.command`, giữ Terminal rồi truy cập http://127.0.0.1:8900/. Ctrl+C đóng host; tự đóng sau 30 phút. Không cần Android, SDK, Docker, build hoặc tải dependency. Đây là entrypoint gắn với checkout trên Mac hiện tại, chưa là installer độc lập.

- “Mở hồ sơ SITL mẫu” tính lại gói SAF Beta05 đã lưu, không mở SITL mới. Không tự nạp mẫu lúc mở trang.
- “Nhập gói hồ sơ” nhận JSON SAF Beta05 hoặc manual02, giữ đúng byte gốc. Các loại khác từ chối. Nguồn SITL, mock giao thức, scripted hoặc bàn phím được ghi riêng, không tự nâng thành ảnh/drone thật.
- Thư viện tìm theo tên/run/SHA, lọc AUTO/manual. Chọn hồ sơ để xem kết quả nguồn và tính toàn vẹn ở hai mục riêng. Mỗi lần xuất chạy lại receiver từ raw trước khi chuyển gói cho browser.
- Lịch sử còn sau restart. Gói pending hoặc lỗi hiển thị issue, không tự sửa/dọn/resume. Danh sách kiểm receipt và SHA nguồn, chưa tính lại toàn bộ mỗi lần refresh; có nút kiểm lại rõ ràng.
- Các lượt khởi chạy Beta05 là metadata đọc tại chỗ; closure chỉ nói về việc đóng runtime được ghi nhận. Không khẳng định runtime đang chạy hoặc nhiệm vụ PASS. Không xóa lock, kill PID, retry hoặc khởi động lại từ desk.
- Link Cockpit (8896), Debrief và Manual (8897) cần dịch vụ tương ứng mở riêng bằng launcher đã có. Desk không tự mở hoặc cấp quyền điều khiển.

Receiver CLI: `node pilot/betaops01/receiver.mjs /absolute/path/package.json`. SHA/replay là kiểm nhất quán, không phải chữ ký hoặc xác thực nguồn. Đây là mock/replay bổ trợ beta, không production.

Giữ gate20/10 GiB +256 MiB khi ghi; inbox64 MiB,16gói, input32MiB, một verifier/30s. Quota gồm pending, không tự xóa bằng chứng. Source fsync trước receipt commit. Nếu write/response chưa rõ, đọc lại lịch sử; không tự gửi lại. Browser đã hoạt động trong lượt này: đã kiểm desktop sáng/tối, mẫu SITL, tìm kiếm, panel giới hạn và thao tác xuất. Mobile/cảm ứng/file picker thực và hiệu năng dài hạn chưa nghiệm thu; xem completion report để phân biệt từng loại bằng chứng.
