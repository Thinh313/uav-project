# COMPLETION — NATIVE97

18/10/2026 · PASS engineering trong phạm vi TIP · 6/6 REQ, 16 kiểm nghiệm thu cuối · APK development07. Đây không phải tỷ lệ hoàn thiện toàn sản phẩm hay nghiệm thu bay thật.

SPEC → BUILD → VERIFY do một agent thực hiện. Parser MAVLink upstream Python đối chiếu riêng với Java native; đây là công cụ kiểm độc lập về cách tính, không phải nhóm QA độc lập.

## Đã triển khai

Adapter payload nằm trong Java native, giữ socket, arbiter quyền và tạo byte MAVLink tại biên gửi. WebView chỉ gửi yêu cầu có kiểu; không có API tiêm byte payload. Mỗi payload là một bundle camera + gimbal; chọn payload để xem không tự cấp quyền. Hai vai trò local `pilot-a` và `payload-b` phải tham gia rõ ràng. Sequence/revision/generation, lease và heartbeat chặn yêu cầu cũ. Bàn giao đóng băng lệnh cho đến khi người nhận đồng ý; release/mất operator/timeout/boot/clock/lifecycle thu hồi quyền, không tự cấp lại hay gửi lại.

Workbench trong Workspace dùng cockpit glass, hai thẻ operator, nút chọn rõ front/center/rear, discovery và trạng thái phản hồi. Station heartbeat15s, lease30s và transfer15s là chính sách fixture engineering, chưa phải chính sách được khách hàng/Hera phê duyệt.

## Kiểm thực tế Android → ArduPilot

APK07 trên Android13 ARM64, WebView101,1280×800, emulator-5582. Native GCS255/190 kết nối trực tiếp AP SERIAL0. ArduPilot4.7.1 binary được pin SHA; synthetic camera/gimbal peers nằm trên hai bus SERIAL1/2. Host không phát lệnh GCS. Observer riêng thấy410 heartbeat AP đều disarmed; runtime đóng sạch.

Hai phiên native mở có chủ ý trên cùng AP run04, có raw và generation riêng; không ghép thành một chuyến bay hay một lượt UI liền mạch:

- Camera `f7607a0e-ca71-48df-bc05-cf4683632dbd`: discovery100/102/101/154; capture cả ba camera, zoom center, focus front bởi operator payload sau bàn giao. Lệnh zoom front nhận ACK sai component/sai recipient và phản hồi sai camera vẫn `UNKNOWN_TIMEOUT_UNCERTAIN`, quyền được thu hồi. Bốn lần lệnh khi không có quyền, trong lúc bàn giao, sau chuyển chủ và sau release bị từ chối. Không có TX trái quyền trong replay.
- Gimbal `3f95baf5-82d0-4e3a-96a4-0a4dd8584e9b`: manager authority và góc20°/yaw0° của device1 trả phản hồi khớp; parser riêng đối chiếu quaternion. Thử device2 cùng manager bị chặn trước gửi bởi `AMBIGUOUS_ACK_KEY`. Mất pilot thu hồi mọi bundle; đóng phiên không khôi phục quyền.

Parser riêng xác nhận3.518 record native,360 TX_INTENT/TX_WRITTEN ghép đủ;16 lệnh đi đúng bus và không xuất hiện ở bus còn lại (8 discovery +8 lệnh điều khiển/thử lỗi). Kiểm CRC, target/recipient/device, tham số, quyền hiện hành, lease, ý định và phê duyệt gửi đã fsync. ACK hoặc phản hồi nhất quán chỉ là `OBSERVATION_CONSISTENT_UNATTRIBUTED`; executionProven=false, actualImages=0.

## Mock, persistence và toàn vẹn

55 ca Java native có mục tiêu:41 arbiter/framer/protocol,14 biên gửi/lifecycle. Bao gồm CRC, byte phân mảnh, signed frame không hỗ trợ, stale/boot/clock, sequence/revision cũ, tranh chấp/consent, mất heartbeat, lease/transfer expiry, phản hồi sai mục tiêu/giá trị, late ACK và thu hồi giữa prepare–write. Code core/wrapper/test liên quan khớp SHA giữa lần kiểm và source APK07. Build07 chạy lại169 ca file-gate/archive kế thừa cùng regression workspace/history/bundle/journal; không cộng các lần chạy lặp thành ca mới.

Force-stop/relaunch process Android giữ nguyên8 file payload/workspace, không tạo phiên socket/raw mới và không khôi phục quyền. Đây là kiểm restart process, chưa phải reboot Android OS trong increment này.396 file private Native90–96 giữ nguyên SHA. Năm raw payload được giữ nguyên:4 CLOSED,1 hash-chain prefix chưa có closure, không sửa/trim hay kết luận hoàn tất cho prefix.

Diagnostic UI giữ7 generation, tổng7.890.313 byte, lớn nhất2.095.803 byte, dưới bound2MiB/generation và16MiB tổng. Một số driver trước dừng vì diagnostic đã đầy/stale hoặc thao tác dropdown/IME không tới đúng control. Giữ toàn bộ receipt FAIL và ảnh; không dùng hitbox cũ, không tính thao tác thiếu native intent là PASS. Đã đổi target thành ba nút rõ ràng, dedup render và chỉ báo controls của modal đang mở. Ca gimbal08 cuối đạt cả5 kiểm UI. Camera và gimbal được nghiệm thu bằng raw riêng; không tuyên bố toàn bộ driver UI duy nhất đã đạt.

## Bảo toàn và bàn giao

65.935 đường dẫn bảo vệ qua NATIVE96 khớp SHA; source/candidate/ENDURE không đổi. Đây là xác nhận byte hiện tại, không khẳng định đường dẫn hiện diện liên tục trong quá khứ. Không chạy ENDURE mới, không ký production hay đổi selected candidate.

Dung lượng runtime thấp nhất36,25GiB, trên sàn20GiB. Đã dừng emulator và bốn run AP sở hữu; không còn listener ở các cổng thử. Đã dọn sáu APK unsigned, `.host97` và `native97/__pycache__`; giữ sáu APK development và toàn bộ evidence. Docker image prune thu hồi0B, không prune volume/container; không cài thêm dependency hoặc tạo bản sao toàn dự án trong tmp.

- [APK development07](../native/native97/dist/aeris-native97-development07.apk) · SHA `eb0a32f02564a8e7c12a883a6392a16145fe9b6588276ccb96414862340a161a`.
- SourceID `641f7503f8fc77eccbc47a33a903869d8bc4f3626880283de9f57e3024e211cd`; cert development v2/v3 `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`.
- [VERIFY](../evidence/native97/final-verification.json), [camera replay](../evidence/native97/independent-camera97.json), [gimbal replay](../evidence/native97/independent-gimbal97.json), [restart](../evidence/native97/restart97.json), [pin/extents](../evidence/native97/final-pins97.json), [preservation](../evidence/native97/preservation-final.json), [TIP](TIP-NATIVE97.md), [ADR112](../docs/ADR-112-NATIVE97-PAYLOAD-AUTHORITY.md).

## Gap và bước tiếp

Chưa có Phase One thực: model/firmware/API/lens/calibration và tương thích gimbal còn chưa biết. Peers đang là generic protocol fixture. Hai vai trò chạy local trong một Activity, chưa phải hai tay cầm/radio có xác thực; remoteAuthentication=false.

Native flight và payload đang loại trừ kết nối lẫn nhau trong APK lab. Chưa nghiệm thu điều khiển nhiệm vụ bay và payload đồng thời. Mỗi endpoint+command ACK key chỉ được dùng một lần/generation; repeated/continuous control và device2 cùng manager chưa được mở. Discovery quan sát thông tin không chứng minh đã tìm đủ mọi thiết bị, không xác thực nguồn.

Bước hợp lý tiếp theo: hợp nhất session/arbiter flight–payload dưới một transport native, kiểm chỉ đọc trước, rồi nhiệm vụ SITL có payload và thu hồi quyền khi mất link; tiếp theo kiểm hai phiên operator độc lập. Giữ hàng rào với ACK không có transaction ID, không mở điều khiển lặp bằng suy đoán. HeraHub/HID/video/PhaseOne thật, HIL, bay thực, Hera physics/pacing1×/24h và production vẫn NOT_CHECKED trong NATIVE97.
