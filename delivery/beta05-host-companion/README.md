# AERIS Beta05 host companion: gói kiểm nội bộ cho Mac hiện tại

Chỉ simulator được sở hữu, video/payload tổng hợp. Đây là launcher pack gắn với checkout AERIS và cache công cụ trên Mac này; không phải installer độc lập cho máy mới. Không cần HeraHub/Xiaomi. APK development riêng, chưa production.

1. Chọn `Doctor.command`: kiểm source pins, Node, ADB/emulator/AVD đã cache, binary ARM ArduPilot/image đã cache, cổng trống và dung lượng. Không tải/cài dependency hoặc dọn bằng chứng.
2. Chọn `Start Beta.command`: chờ gate31mẫu/30s, mở host và emulator riêng. Giữ cửa sổ Terminal chạy. `Start Mock.command` chỉ mở giao thức mock để xem UI; không mở ArduPilot.
3. Mở `http://127.0.0.1:8895/publisher`, chọn VP8-720P30-V1 rồi bật nguồn tổng hợp. Mở `Android.command` để cài APK riêng lên emulator-5582, reverse8895/8896 và mở shell. Không dùng ADB với điện thoại thật.
4. Trong Android: Workspace → Mẫu sân thử SITL → xác nhận mặt phẳng/datum → tạo phương án → preflight → duyệt. Sang Fly, kích hoạt phiên → xác nhận Home tổng hợp → kết nối giả lập. Chờ GNSS/EKF/Home ổn định rồi kiểm preflight, cấp quyền, upload/readback, arm, kiểm Home sau arm.
5. Nhận video → Đo xuyên AUTO → kiểm Home đang hiển thị → Bắt đầu AUTO. Phép đo tự lưu3cửa sổ30s liên tiếp, không tự phát lệnh bay. Trong AUTO có thể tìm/chọn/cấp quyền payload tổng hợp, đặt gimbal và chụp JPEG tổng hợp. Giữ nguồn laptop và video Android hiển thị trong90s. Không mở picker hay chuyển theme/màn khi đang đo.
6. Khi nhiệm vụ quan sát đủ navigation + đất/disarm và3báo cáo đã lưu, đóng vào Review → Kiểm video suốt AUTO → xuất raw/media qua SAF. PASS yêu cầu phủ toàn khoảng AUTO từ raw AP, FPS>=24, mỗi5s đủ>=24FPS, P95 upper<=300ms, gap<=250ms, không mất coverage/clock/counter. Gói nhận phải kiểm lại, không chỉ đọc nhãn PASS. Dùng `Verify Package.command`, dán đường dẫn JSON SAF đã lấy về Mac; receiver tính lại SHA, raw/WAL và kết quả video từ từng mẫu.
7. `Status.command` đọc trạng thái; `Stop Beta.command` hoặc Ctrl+C yêu cầu đóng sạch host/emulator/AP được sở hữu. Không tự resume/ARM/retry. Nếu lock stale, dừng và giữ log; không xóa lock tùy tiện.

Gate20GiB admission/10GiB floor +256MiB reserve, forecast15s, quota bằng chứng1GiB, runtime45phút, tối đa3APrequest trong một host session và tối đa3container Beta05 được giữ trong đợt kiểm hiện tại; các lượt mới có thư mục evidence/launches mới và authority luôn chưa cấp. Không tự xóa evidence. Các container/state AP được giữ để chẩn đoán; khi tổng quota hết cần xuất/kiểm và chính sách dọn được duyệt riêng.

Nguồn: http://127.0.0.1:8895/publisher. Cockpit host: http://127.0.0.1:8896/mock (bridge MOCK, không chứng nhận Android). Luồng kiểm chính trên Android. Không mở cổng ra mạng LAN/Internet. APK không tự chạy được khi thiếu host companion.

Chưa chứng minh phần cứng Hera, Phase One/Sony/thermal, radio, pin thực, phơi sáng/GNSS thực, photon latency hoặc UI production. Không dùng dữ liệu mô phỏng làm bằng chứng khảo sát thực địa. Không khởi động ENDURE, thay candidate hay ký production.


APK development: `native/betaworkbench05/dist/aeris-beta05-development02.apk` trong checkout; ZIP cũng giữ bản APK để đối chiếu. Không mở gói này như một installer độc lập ngoài checkout. `Start Mock Android.command` kiểm UI native mà không mở AP. Nếu preflight chưa đạt do EKF/Home đang khởi tạo, giữ disarmed và chờ dữ liệu sẵn sàng rồi kiểm lại, không bỏ guard. Gói chỉ đủ90s đo liên tiếp cho nhiệm vụ sân thử ngắn; nếu không phủ trọn AUTO thì phải báo chưa đạt. Chọn tên SAF mới thay tên đề xuất legacy workspace02; không ghi đè tài liệu đã có.
