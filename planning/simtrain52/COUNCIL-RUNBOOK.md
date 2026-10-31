# Kịch bản trình diễn simulator trước hội đồng

Mục tiêu18 phút, live trên laptop xuất máy chiếu. Kế hoạch, chưa có kết quả rehearsal. Điều kiện mở buổi: G6 nghiệm thu tích hợp và G7 rehearsal đạt, đúng manifest/version/profile. Tất cả mode và sensor chỉ dùng instance mô phỏng được cấp quyền.

## Trước buổi

- Khóa bản chạy, laptop/GPU/power mode, camera/scene/seed và input mapping; kê khai profile reference/Hera engineering/calibrated đúng mức.
- Kiểm offline cold start, asset/license, disk reserve, màn hình extended và mirror, âm lượng loa/limiter, màn hình đọc được từ cuối phòng.
- Khởi động instance mới, kiểm heartbeat/firmware/sim identity, clock/recording/telemetry; joystick calibration, neutral và abort của giáo viên.
- Chuẩn bị mission ngắn đủ thời gian1×, gói dữ liệu/KML đã kiểm, một fault chính; không xem script sự kiện là chuyến bay đã chạy.
- Ghi record-only backup trên cùng workload sau khi nghiệm thu; nhãn backup luôn hiện. Presenter nói, operator điều khiển, instructor chèn fault; một người có thể kiêm vai nếu rehearsal chứng minh được.

## Trình tự live

### 00:00–01:00 Định vị sản phẩm

Thao tác: Mở cockpit và màn world trên máy chiếu; chỉ rõ profile reference/Hera calibration status.

Bằng chứng hội đồng thấy: Một session live, clock và trạng thái mô phỏng nhìn thấy.

### 01:00–04:00 Bay bằng tay

Thao tác: Gamepad điều khiển takeoff, tiến/lùi/yaw, giữ vị trí và hạ cánh; show stick overlay ngắn.

Bằng chứng hội đồng thấy: Mode thực, response liên tục, đồ họa và âm bám motor.

### 04:00–06:00 Tải thay đổi cảm giác

Thao tác: Mở hai lượt fresh cùng bài empty/loaded đã chuẩn bị, cho hội đồng điều khiển đoạn ngắn.

Bằng chứng hội đồng thấy: Compare input-normalized và graph; nếu dùng trace chuẩn để A/B thì ghi rõ recorded comparator.

### 06:00–08:00 Bán tự động

Thao tác: Guided takeoff, chọn điểm do hội đồng chỉ, hold rồi đổi yaw/độ cao.

Bằng chứng hội đồng thấy: Target yêu cầu khác actual trajectory; không snap pose.

### 08:00–12:00 AUTO khảo sát

Thao tác: Nhập KML đã kiểm, review camera/GNSS, mission readback, AUTO và sinh ảnh mô phỏng.

Bằng chứng hội đồng thấy: Mission ngắn được thiết kế để đủ thời gian thực1×, không speedup giấu.

### 12:00–14:00 Gió và tiếp quản

Thao tác: Giáo viên thêm gust theo seed, pause AUTO, người học tiếp quản và hold/RTL.

Bằng chứng hội đồng thấy: Mối liên hệ disturbance→attitude/motor→audio và ownership rõ.

### 14:00–16:00 Lỗi có kiểm soát

Thao tác: Chọn một lỗi camera/CORS phù hợp policy; đánh giá nhận biết và xử lý.

Bằng chứng hội đồng thấy: Fault event, phản ứng đúng miền, không auto retry hay báo ảnh đã có.

### 16:00–18:00 Review và câu hỏi

Thao tác: Land/disarm/đóng; xem timeline, vùng thiếu, điểm và bundle; nhận challenge target/seed cho vòng sau.

Bằng chứng hội đồng thấy: Tách planned/executed/captured; evidence mở được và không khẳng định accuracy Hera thật.

## Challenge và câu trả lời phải có bằng chứng

- “Có phải animation không?”: hội đồng chọn điểm Guided hoặc seed mới, xem request/observed mode/actual trajectory và input overlay. Replay được ghi rõ, không nhập quyền.
- “Có tải khác gì?”: mở paired traces cùng input và seed; so acceleration/hover power/motor reserve. Cho thử live riêng, không lấy cảm giác chủ quan thay số đo.
- “Mưa thật đến đâu?”: chỉ rõ model nào ảnh hưởng lực, model nào ảnh hưởng visibility/sensor và phần unsupported.
- “Đã giống Hera chưa?”: mở profile/version/provenance và validation status; không dùng silhouette/CAD để chứng minh lực đẩy hoặc latency.
- “Tự động làm được gì?”: mở original KML→compiled plan→mission readback→executed path→image inventory. GSD/dataset mô phỏng không phải chất lượng đo đạc thật.

## Khi gặp lỗi

Operator giữ quyền hoặc abort theo policy simulator; giữ raw/incomplete, không reset phiên cũ để xóa lỗi. Presenter nêu hiện tượng ngắn gọn. Nếu cần, chuyển sang backup với nhãn và nói rõ đây là recording; không tính là live PASS. Chỉ mở session mới sau review lỗi; không gửi lại mutation do mất phản hồi mà chưa reconcile.

## Sau buổi

Đóng phiên/recorder có kiểm, xuất manifest/metrics/raw index/timeline/scoring/camera inventory và giới hạn model. Checkpoint và SHA của gói dùng cho kiểm lại; không phải chữ ký mới. Giữ mọi run thất bại. Không coi3×18phút rehearsal là ENDURE24h hay chứng nhận đào tạo bay thật.
