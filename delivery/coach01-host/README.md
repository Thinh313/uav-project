# AERIS Debrief: COACH01

25/10/2026. Bộ phân tích replay cục bộ, là baseline xác định cho AI Assisted Training & Inspection. Chưa có mô hình học máy/LLM và không kết nối điều khiển drone. Chưa đưa vào native shell hay APK.

## Mở và sử dụng

1. Mở **Start Debrief.command** trong thư mục này hoặc chạy `node pilot/coach01/server.mjs` từ checkout AERIS.
2. Mở http://127.0.0.1:8897. Chọn **Xem chuyến bay SITL mẫu** để đọc lại gói Beta05 đã lưu, không khởi động SITL mới. Hoặc **Mở hồ sơ** để chọn gói raw SAF Beta05 JSON, tối đa 32 MiB.
3. Sau khi kiểm toàn vẹn và dựng lại nhiệm vụ: dùng **Phát lại**, timeline hoặc các mốc sự kiện. Bản đồ cục bộ hiển thị đường đã ghi và dải khảo sát. Nút dẫn chứng raw đưa tới mẫu quan sát gần mốc; không phải vị trí chính xác tại thời điểm sự kiện.
4. Đọc nhận xét cùng giới hạn. **Độ cao / Home** không tự đồng nghĩa AGL. Khoảng cách tới dải gần nhất không phải sai số bám waypoint đang hoạt động. AUTO không dùng để chấm kỹ năng phi công.
5. **Xuất báo cáo** tải JSON có checksum. Danh sách **Hồ sơ đã lưu** giữ qua restart. Gói nguồn được giữ trong evidence/coach01/workspace02; không tự dọn hoặc trả lại quyền điều khiển.
6. Dừng bằng Ctrl+C. Server cũng tự đóng sau 30 phút; chỉ bind localhost8897. Không dùng cho LAN/điện thoại/production hoặc máy sạch chưa có checkout/cache.

Receiver recompute từ report và gói gốc:

```sh
node pilot/coach01/receiver.mjs /duong/dan/bao-cao.json /duong/dan/goi-SAF-Beta05.json
```

Receiver kiểm checksum, raw/WAL, nguồn model KML và tính lại báo cáo; không xác thực danh tính nguồn bằng chữ ký. Gói Beta04 hay định dạng khác chưa hỗ trợ. Gói thiếu hỏng không được gọi là kết quả hợp lệ.

## Giới hạn được giữ rõ

- Camera trong gói mẫu là tổng hợp; ảnh thực0. Độ phủ/GSD/nhòe/chồng phủ ảnh thực UNKNOWN. Không thay ảnh tổng hợp bằng chứng camera vật lý.
- Mẫu vị trí lấy từ wire MAVLink RX đúng target/session; CRC chỉ áp dụng message thuộc dialect hiểu được. Message chưa biết không dùng để suy tình trạng cảm biến.
- Không nối đường/tính gia tốc qua gap; clock guest và host giữ riêng. Yaw/heading chưa biết hiển thị không hướng. Chưa có phân tích stick/IMU hay huấn luyện reinforcement learning.
- Lưu source/report/receipt theo digest, quota256MiB; pending không có receipt không được công bố. Khi hết quota/dung lượng phải xử lý có chủ đích, không tự xóa bằng chứng.
- Admission20GiB; sàn ghi10GiB +256MiB reserve. Không cài dependency hay tải model.
- Backend/restart/receiver và toán đã kiểm. **Kiểm trực quan browser/touch/keyboard/pixel chưa chạy vì Local browser use đang bị tắt**. Không coi UI đã nghiệm thu chỉ từ kiểm HTML/CSS/JS.

Bản này gắn với workspace Mac hiện tại. Không phải APK/installer độc lập, bản ký production hay phi công AI. Không thay Beta05, candidate hoặc ENDURE.
