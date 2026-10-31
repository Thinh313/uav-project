# PHONE06: kịch bản nghiệm thu trên điện thoại Xiaomi và drone giả lập

Tài liệu kiểm, chưa phải kết quả. Mọi dòng bắt đầu NOT_CHECKED. Ghi chính xác model Xiaomi/Android/HyperOS/WebView, APK/source SHA, host/APbinary/firmware/config, runID/planSHA và loại kết nối. Người dùng đang chuẩn bị kết nối USB; không có thiết bị không được ghi phonePASS.

## Bố trí và bằng chứng

Điện thoại ngang chạy APK development PHONE06. Laptop chạy ArduPilot SITL và viewer3D/audio tổng hợp; host observer không điều khiển AP. Có thể xuất màn laptop lên thiết bị chiếu. USBloopback là đường đầu tiên, không tự mở LAN. Không nối aircraft/Hera/payload thật. Có nhãn giả lập trên mọi màn liên quan.

Từng bước ghi expected/observed/PASS/FAIL/NOT_CHECKED, timestamp/clock-domain, ảnh hoặc video ngắn nếu được phép, native rawhead và AP observer prefix tương ứng. ACK chỉ chứng minh phản hồi giao thức; mode/chuyển động/hạ cánh dựa telemetry. Map/3D/camera mô phỏng và âm thanh tổng hợp luôn được phân biệt với ảnh/media thật. Không ghi phần trăm hoàn thiện từ số checkbox.

## Trước khi cài

1. Kiểm SHA toàn bộ frozenbaseline/source/candidate/ENDURE, source mới và APK certificate/payload; chỉ chọn PHONE06 development. Không gỡ app khác hay xóa dữ liệu cá nhân.
2. Kiểm diskfloor20GiB và ngân sách build/runtime trong TIP. Không dùng lại threshold Androidemulator29GiB như proof forecast phone; cũng không tự hạ sàn20GiB. Thiếu tài nguyên: hoàn thiện mock/APK, để actual NOT_CHECKED.
3. Chọn đúng serial Xiaomi đã cho phép USBdebugging; ghi model/OS, chỉ thao tác package PHONE06 và các file xuất thuộc tác vụ. Không root điện thoại. Nếu Xiaomi hỏi quyền cài USB, người dùng xác nhận trên máy; không tìm cách lách.
4. Cài APK, kiểm package/version/signature và SHA file APK đã cài nếu đọc được qua đường hợp lệ. Nếu không đối chiếu được phải ghi giới hạn; không dùng emulator receipt thay cho Xiaomi.

## Phiên chỉ đọc

5. Mở app: landscape/safearea đúng; nav/logo/telemetry align, nút48dp, font Việt đọc rõ, themeicon đổi đúng; mở/đóng từng pane không che controls. Không tự connect, không tự cấp quyền.
6. Khởi động duy nhất simulator sở hữu sau resource/source/ports gate. Ghi ownedCID, APpid/logs/guestlisteners. Cấp fresh run/admission cho đúng APK/session qua USBloopback, không dùng ticket cũ.
7. Bấm kết nối: phải thấy read-only, firmware4.7.1/dbe79216 và sys42/comp1 đúng; telemetry tuổi, mode, Home/altitude datum và vị trí. Sai loại/target/boot/stale hoặc ticket hết hạn phải chặn. Trước cấp quyền, observer xác nhận0mutation.
8. Laptop hiện đúng drone, cùng run/plan/pose. Ngắt feed quan sát: viewer phải UNKNOWN/đóng băng, không tiếp tục bay theo dữ liệu cũ. Audio chỉ phát sau thao tác bật, ghi rõ synthetic.

## Lập nhiệm vụ và bay AUTO

9. Tạo nhiệm vụ mẫu nhỏ quanh Home giả lập; nhập KML polygon rồi corridor riêng, chỉnh điểm/độ cao/tốc độ và xem bản đồ. Invalid/mixedunsupporteddata phải từ chối rõ; không im lặng đổi chuẩn độ cao. Lưu và mở lại workspace trước khi nối phiên bay mới.
10. Preflight: kiểm firmware/capability, tham số đúng kiểu/freshness, GPS/EKF, Home và độ cao, failsafe/profile, lượng dự phòng ở phạm vi mô hình được công bố. UNKNOWN phải chặn bước phụ thuộc.
11. Explicit pilot authority; upload rồi readback đối chiếu semantic với plan đã chốt. Không coi MISSION_ACK là readback. Không sửa plan trong lúc phiên đang hoạt động.
12. Arm theo thao tác riêng có xác nhận; duyệt Home sau arm nếu hợp đồng yêu cầu; explicit AUTO. Quan sát AParmed/mode, takeoff, waypoint reached, camera command route, ground/disarm. Ghi actual Home/cao độ khác request nếu có; không dùng animation để bù thiếu telemetry.
13. Review chỉ accepted nếu các điều kiện nhiệm vụ đã được receiver kiểm. Abort/mấtlink hoặc manualtakeover giữa survey phải giữ trạng thái interrupted/UNKNOWN tương ứng, không tự hoàn thành.

## Bay cảm ứng và bán tự động

14. Fresh training run/grant: bật manual từ neutral, đúng pilot và đủ freshness. Không có implicitarm từ cần ảo. Hai pointer riêng: trái ga/yaw, phải pitch/roll; chuyển finger ngoài vùng/nhấc/cancel được xử lý xác định. Mapping thống nhất label/axes/MAVLink; rate<=20Hz và nativelease<=250ms.
15. Sau mode observed phù hợp, kiểm từng trục nhỏ, tiếp theo pitch+yaw phối hợp. Quan sát RC/axis telemetry và pose drone. Cùng giá trị cần nhưng fresh liveness snapshot hợp lệ phải được nhận; replay seq/receipt cũ không được kéo dài lease.
16. Giữ ngón nhưng cố tình dừng JS/UI producer theo fault harness: native phải tự hết hạn. Ngừng chạm phải neutral/release theo mode-policy đã chốt. Đo thêm AP giữ lệnh bao lâu/RCfallback và mode an toàn, không kết luận từ cần vẽ về giữa. Độ trễ input/native/AP phải khai báo clockmapping+uncertainty.
17. Chuyển manual→Hold/RTL/Land hoặc quay về AUTO chỉ khi policy cho phép, explicit intent và mode thực được xác nhận. Không gửi lại mutation sau UNKNOWN. Giữ nút thu hồi/quay về nhìn thấy; popup không ăn mất touch-release.

## Payload và sự cố

18. Discovery syntheticcamera/gimbal: chọn đúng payload, deniedunsupported, góc/zoom/capture đúng target/transaction. CameraACK không tạo ảnh thật; actualImages phải0. Nếu có operatorB riêng, xác thực/join/consent/handover và mất quyền trên phiên độc lập; một phone đổi tab không phải chứng minh dualoperator.
19. Trên fresh fault run, lần lượt kiểm rút USB thật, đưa app nền/khóa màn hình, stale feed và restart session/AP khi các gate cho phép. Ghi fault thực nào đã làm; flagmock không thay cableunplug. APfailsafe/RTL/ground dựa observer; pending intentUNKNOWN, quyền thu hồi, mở lại không tự nối/cấp quyền/arm. Không gộp các loại lỗi thành mộtPASS.
20. Thử dữ liệu cũ/wrongtarget/wrongrun/bootregression qua mock/replay độc lập trước khi actualfault. Không thử gây lỗi bằng nối thiết bị thật hoặc sửa byte của evidence cũ.

## Hồ sơ và khởi động lại

21. Sau ground/disarm, đóng phiên và giữ nguyên native raw/diagnostics/observer/controller exit+seal. closure.json đơn lẻ không đủ đóng sạch. Ghi từng thành phần seal/receiver khác nhau, không giả mã hóa/chữ ký phần mềm từ fileSHA.
22. Chọn đúng run, xuất qua AndroidSAF tới file do người dùng chọn; đọc lại provider và kiểm bytes/SHA, receiver độc lập kiểm mission/raw/run/context. Thử bản sao corruption/wrongrun, giữ bản gốc. Không yêu cầu đọc /data/user bằng root.
23. Processrestart rồi người dùng reboot điện thoại khi sẵn sàng: workspace/review giữ nguyên, không phục hồi authority/connection/lease. Kiểm nhập lại gói trong workspace mới, không ghi đè evidence cũ.
24. Dừng có kiểm soát đúng ownedPID/container/ports/adbreverse của task. Không kill ADBserver hoặc container/app khác. Dọn compile/unsigned/scratch do task tạo; giữ APK kýdevelopment và toàn bộ evidence. Đối chiếu frozenSHA sau cùng.

## Điều kiện bàn giao

PASS_SCOPED chỉ cho cấu hình/scenario thực đã làm; mock, host, physicalAndroid, AP-SITL và human cảm nhận là các lớp khác nhau. PHONE06 chưaDONE nếu cài/USB/actualjourney/fault/restart bắt buộc chưa kiểm. M1/phần cứngHera/PhaseOne/video/AIbay/calibratedphysics và24hENDURE vẫn có gate riêng. Chưa hiệu chuẩn Hera không quảng bá tải/gió/mưa/âm thanh là giống aircraft thật. Không nói mọifeature AERIS đã nghiệm thu từ một buổi demo.
