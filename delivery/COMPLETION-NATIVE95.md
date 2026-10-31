# COMPLETION — NATIVE95

18/10/2026 · PASS engineering trong phạm vi TIP · APK development03 · 27 kiểm nghiệm thu cuối. Có một P2 còn mở ở chẩn đoán UI; chưa phải bản điều khiển Hera thương mại.

SPEC → BUILD → VERIFY do cùng một agent thực hiện. Tính độc lập ở parser/compiler đối chiếu, không phải một nhóm thẩm định riêng.

## Gap đã khép

Android tự biên dịch model KML/corridor và trực tiếp discovery, đọc preflight, upload/readback, arm tại mặt đất, xác nhận Home mới, vào AUTO, quan sát tuyến/RTL/hạ cánh/disarm và lưu review. Transport/control không còn qua HTTP GCS bridge trên laptop. Java sở hữu socket/journal/wire gate; các thuật toán nhiệm vụ và preflight chạy trong APK qua WebView. Laptop chỉ chạy autopilot/physics ArduPilot SITL và observer thụ động không gửi MAVLink payload.

Endpoint engineering cố định 10.0.2.2:5907, chỉ emulator thuộc tác vụ; đây chưa phải adapter radio/UDP/TCP thương mại trên HeraHub. Định danh container được đối chiếu như launch assertion, không phải xác thực mật mã của máy bay thật.

## Chứng cứ cuối

- APK03 trên Android13 ARM64/WebView101.0.4951.61,1280×800 được kéo lại từ Android và đối chiếu đúng SHA. Full E2E cuối: `s095f2c41e36548be9071`.
- Parser Python upstream tách khỏi runtime Java/JS kiểm SHA chain, CRC, target, quyền30s, typed parameters, mission payload và thực thi: 4625 record native, 10753 frame RX, 560 frame TX; 44703 frame ở observer riêng. Hai miền clock được kiểm riêng, không coi host và Android cùng clock.
- 12 mission item,2 readback,4 camera command,23 typed parameter checks,0 PARAM_SET,0 ảnh thực. Có bằng chứng vị trí/độ cao khi cất cánh, NAV, terminal RTL, mặt đất/disarm gần Home. Không suy execution từ ACK hay ảnh từ lệnh camera.
- Compiler đối chứng AUTO63 đã đóng băng khớp toàn bộ plan/model/hash; Home-review và geography digest khớp;862 điểm track giữ đủ trong giới hạn1200, không truncate.
- 34 kiểm mock trong4 suite, gồm đối chiếu3.627 frame nhận và215 frame gửi từ corpus đã nghiệm thu,9 negative wire/profile,6 journal,6 fault clock/CRC/foreign/reboot/stale,7 socket-generation/lifecycle/ack/queue/endpoint. Số34 là top-level checks của các suite, không phải tổng mọi assertion từng frame. Host JVM storage/file gates cũng chạy trong build03.
- Force-stop và reboot cuối giữ nguyên workspace/CURRENT/raw/review, không tự kết nối hay khôi phục quyền. Sandbox Native90–94 giữ nguyên270 file private. Review Android hiện có5 hồ sơ, phân biệt kết thúc và gián đoạn; đây là trạng thái native, không thay chứng nhận QA bên ngoài.
- 63.830 đường dẫn bảo vệ qua NATIVE94 khớp SHA, không có lỗi. Source/candidate/ENDURE không thay đổi. Chỉ xác nhận byte hiện tại, không tuyên bố các đường dẫn đã hiện diện liên tục trong quá khứ.

## An toàn và độ bền trong phạm vi này

Raw RX được fsync trước khi đưa vào JS; TX_INTENT fsync trước khi gửi frame lệnh và TX_WRITTEN ghi riêng. Socket không reconnect/retry/resume hoặc phục hồi quyền. Native gate ràng buộc target, phiên/boot, kiểu tham số, compiled item và quyền tạm thời; JS giữ preflight/mission gates riêng. Các giới hạn32MiB raw,queue,clock,stale và foreground fail closed. Đây chưa phải chứng minh mọi fault native IO/airborne.

## Các lần không được dùng làm PASS đầu-cuối

Docker chưa sẵn sàng ở prelaunch đầu; emulator đầu exit−9, nguyên nhân socket/OS chính xác chưa chứng minh. Giữ receipt, không suy thiếu dung lượng vì sàn vẫn đạt.

Run b có review native hoàn tất nhưng observer chỉ có heartbeat; không nghiệm thu đầu-cuối. Run c/d dừng ở read-only vì thiếu observer stream, không cấp quyền hay arm. Cấu hình per-channel message-intervals đã pin trước launch mới cho đủ dữ liệu; run e (APK02) và f (APK03 cuối) đã qua receiver riêng. Nguyên nhân chính xác vì sao MAV2 defaults chưa có stream chưa được chứng minh; không sửa hồi tố các receipt.

Mock tìm được lỗi pending-open của adapter JS: trả lời open muộn sau close có thể đặt lại writable. APK03 đã sửa, mock fail→pass được giữ và full E2E trên APK03 đã chạy lại. Không phát hiện sự cố này trong hai lần bay live.

## P2 còn mở: chẩn đoán UI

File UI diagnostic đã bão hòa mức cấu hình2MiB; guard cũ tính Java character nhưng ghi UTF-8 nên thực tế dư376B. Receipt cũ không được dùng làm runtime attestation. Phát biểu ban đầu quy do cap180 chưa đủ chứng cứ đã được hiệu chỉnh bằng receipt riêng. Harness nay chặn diagnostic stale; nghiệm thu cuối dùng ảnh UI mới và SHA private journal/raw. Không xóa/truncate bằng chứng. Flight raw journal là tệp khác, có bound theo byte và đã replay độc lập. Cần chuyển diagnostic sang generation/quota đúng byte trong NATIVE96.

## Artifact

- [APK development03](../native/native95/dist/aeris-native95-development03.apk) · SHA256 `dc9500095c4350f1e8e9f184d59c127cac7a4933336c0ace2500dbd8c0f6f405`.
- SourceID `feeaf98efe6e98a42b084b473bf2c515a9163e94b5092ac6c831623cede51724`.
- Cert development hiện có: `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`, v2/v3 đạt; không ký production/candidate.
- [VERIFY](../evidence/native95/final-verification.json), [receiver cuối](../evidence/native95/runs/s095f2c41e36548be9071/receiver95.json), [semantic oracle](../evidence/native95/runs/s095f2c41e36548be9071/semantic95.json), [reboot](../evidence/native95/restart03.json), [preservation](../evidence/native95/preservation-final03.json), [TIP](TIP-NATIVE95.md), [ADR110](../docs/ADR-110-NATIVE95-DIRECT-ANDROID-MAVLINK.md).

## Chưa kiểm và bước tiếp

HeraHub/radio/HID/video thật, PhaseOne/gimbal/nhiều payload/dual-operator thực; ma trận native direct airborne mất link/reboot/kill và unknown outcome; gói raw qua SAF và receipt bên nhận; lỗi native IO/quota/fsync dài hạn; DEM/RTK/PPK và chất lượng photogrammetry; pacing1×/thermal/24h/production. Chứng cứ host-bridge cũ không thay các gate native mới. Internal quad không phải mô hình Hera đã hiệu chuẩn.

NATIVE96 nên ưu tiên fault và bàn giao bằng chứng trên chính APK direct vừa hoàn thiện, cùng quota diagnostic; sau đó mới nối contract payload/quyền vào native và bench khi có thiết bị/API. Không mở khóa candidate đóng băng.

## Dọn dẹp

Đã dừng các runtime/emulator/controller thuộc95, cổng5907/5908/5582/5583 không còn listener. Xóa3 APK unsigned, .host95 và cache Python do tác vụ tạo (kể cả oracle-v2.pyc mới, đã kiểm không thuộc manifest bảo vệ). .build tự dọn; không tạo scratch/copy dự án ngoài repository. Giữ APK development01–03, AVD dùng lại và mọi evidence. Docker image prune đã chạy, thu hồi0B, không prune volume/container. Dung lượng thấp nhất 37.85GiB, trên sàn20GiB.
