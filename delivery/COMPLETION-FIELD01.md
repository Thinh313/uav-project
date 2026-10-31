# FIELD01: hoàn tất tích hợp và kiểm thử trên host

Ngày chốt: 21/10/2026. Phạm vi: các phần của FIELD01 không cần Xiaomi, SDK hoặc thiết bị Hera. Quy trình Vibecode Kit 6.3; triển khai trong `pilot/field01`, kế hoạch trong `planning/field01`, hồ sơ mới trong `evidence/field01`.

**Kết quả: PASS cho phạm vi kỹ thuật trên host được liệt kê dưới đây. Chưa nghiệm thu Android hoặc phần cứng, chưa đủ căn cứ kết luận sản phẩm thương mại sẵn sàng.** Không tạo APK, không ký phần mềm, không chạy emulator hoặc chiến dịch ENDURE mới.

## Giá trị đã chạy xuyên suốt

Cùng cockpit nhận KML polygon/corridor, lưu model nhiệm vụ dùng chung, biên dịch trên Node, kiểm trước bay, cấp quyền rõ ràng, upload/readback, arm, duyệt Home sau arm, bay AUTO bằng ArduPilot SITL và lưu review. Payload mock chạy đồng thời với chuyến bay; nguồn video riêng được mã hóa, truyền qua HTTP/TCP và giải mã trên trình duyệt. Ảnh JPEG từ khung đã giải mã gắn tham chiếu vị trí SITL, được lưu bền vững, xuất qua HTTP và kiểm lại ở receiver độc lập.

Đây là GCS chạy trên host với ArduPilot internal quad. Không phải bản native Android đã được nghiệm thu, không phải mô hình động lực học Hera đã hiệu chuẩn, không phải demo 3D photorealistic. RGB và thermal-look là ảnh tổng hợp; số ảnh camera thực bằng 0.

## Ma trận nghiệm thu

| Phần | Kết quả đã có chứng cứ | Giới hạn |
|---|---|---|
| AC1: model và biên dịch | 6 ca Node: polygon, corridor, giữ byte KML/QGC nguồn và semantic camera, từ chối datum chưa hỗ trợ/complex survey/Home chưa duyệt | Không tuyên bố hỗ trợ mọi file QGC; compiler Node là chuẩn của milestone này |
| AC2: bay SITL cùng cockpit | 1 chuyến AUTO được kiểm raw, 16 mission item, 32 item readback trong 2 chu kỳ, 6 camera command truyền lên AP, 0 ghi tham số; kết thúc ground/disarm và đóng sạch | Không suy ra ảnh thực hoặc camera đã thực thi từ ACK; mất link/reboot được kiểm bằng mock ở milestone này, chưa có lượt fault SITL mới |
| AC3: video | 2 cửa sổ foreground 30 giây, nguồn và canvas đều hiện; RGB và thermal-look đạt khoảng 27,60 fps, p95 upper bound 21,54/22,66 ms; phục hồi sau ngắt relay 500 ms là 538,6/530,6 ms | Đo source-to-canvas localhost có clock bounds; không phải photon latency, Wi-Fi, điện thoại hoặc video camera thật; chưa có soak video dài hạn |
| AC4: payload và quyền | Discovery, chọn payload, lease, camera/gimbal mock, thu hồi quyền, sai target, timeout, stale/link/boot fence; JPEG không nhận tọa độ từ phiên bay khác | Không có driver Phase One/Sony/gimbal/thermal thực; không có radio hoặc hai tay cầm thật |
| AC5: hồ sơ và bàn giao | WAL intent/commit async, quota/pending, restart không trả quyền; 4 JPEG tổng hợp giữ SHA; bộ bàn giao actual HTTP được receiver nhận bền vững và đối chiếu ảnh với raw đúng chuyến | SHA chứng minh toàn vẹn byte, không chứng minh danh tính nhà sản xuất hoặc độ chính xác cảm biến |
| AC6: cùng giao diện | Khảo sát → preflight → Fly → review; 1280×720 và hành trình corridor trên iframe thực 900×500; đổi theme, loading, quyền và trạng thái UNKNOWN được kiểm | Chưa bao phủ toàn bộ màn Android, GPU, accessibility và mọi độ phân giải |

## Chứng cứ được chọn

- [Kiểm tổng hợp cuối](../evidence/field01/final-verification01.json): tính lại fps/p95/fault window từ mẫu gốc, kiểm raw, receiver, dung lượng và 327 file bảo vệ.
- [Raw chuyến SITL được chấp nhận](../evidence/field01/flight02-raw-verification-sb5d91f31ba82446984dc.json): run `sb5d91f31ba82446984dc`, 7.294 raw record, 529 tham chiếu vị trí. Firmware quan sát 4.7.1, binary được pin SHA; speedup 1. Receiver raw riêng xác nhận gói nhiệm vụ và raw duplex.
- Video được chọn: [RGB report-01](../evidence/field01/app07/media/report-01.json), [thermal-look report-02](../evidence/field01/app07/media/report-02.json). Không dùng report sơ bộ để kết luận hiệu năng.
- [Bộ nhận qua HTTP](../evidence/field01/http-receiver-set01/index.json), [receipt bền vững](../evidence/field01/http-receiver-state01/delivery-receipts.jsonl): index SHA `0bc99d4bc10c84603ad13c16c7b583b6e72f44e9694ab83bd8b6ea526276336c`, 4 file, 4.589.321 byte, 2 JPEG thuộc đúng chuyến SITL. Receiver từ chối replay và gói sai ngữ cảnh trước khi ghi ledger.
- [Restart](../evidence/field01/restart-after-final01.json): revision 6, model/plan SHA và KML nguồn giữ nguyên, 4 ảnh giữ SHA, 4 review phục hồi; quyền bay và phiên chạy không tự phục hồi.
- [UI geometry](../evidence/field01/ui-verification01.json): logo và metric đầu cùng x=24 px, lệch 0 px; hai rail cùng tâm Y=348 px, lệch 0 px; hai panel cùng đỉnh và chiều cao.

### Chất lượng vị trí ảnh

Hai ảnh liên kết SITL lấy tọa độ tham chiếu tại lúc host nhận telemetry, theo phương pháp `NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC`. Chúng giữ riêng MSL và cao độ tương đối Home. Sai lệch ghép tham chiếu là khoảng 30,46 và 33,58 ms; đó không phải sai số thời điểm phơi sáng. Thời điểm phơi sáng vật lý, độ chính xác GNSS, đồng bộ clock cảm biến, geoid/ellipsoid và chất lượng khảo sát vẫn UNKNOWN. Thermal-look không có dữ liệu nhiệt bức xạ. Ảnh không được công bố là ảnh chụp thực hoặc ảnh đạt chuẩn mapping.

### Nhóm kiểm bổ sung

| Nhóm kiểm | Kết quả cuối | Hồ sơ |
|---|---:|---|
| Store + Python receiver | 14/14 | `evidence-tests-2026-10-21T12-16-05-371Z/results.json` |
| Gateway, actual store + flight/media giả | 17/17 | `evidence-gateway-tests-2026-10-21T12-59-30-349Z/results.json` |
| HTTP app không gửi lệnh bay | 11/11 | `evidence-app-http-tests-2026-10-21T12-57-10-204Z/results.json` |
| Combined delivery set + receiver | 12/12 | `evidence-delivery-set-tests-2026-10-21T12-45-01-016Z/results.json` |
| Media HTTP/TCP fault groups | 19 PASS | `media-http-test-result.json` |
| Clock renewal/recovery | 5 PASS, gồm 95 giây HTTP/3 lần renew | `media-clock-recovery-test-result.json` |
| Compiler | 6 PASS | `mission-tests01.json` |

Các đường dẫn tương đối ở bảng nằm dưới `evidence/field01`. Số ca kiểm mô tả phạm vi đã chạy, không chứng nhận chất lượng tổng thể. Builder cũng viết một phần test; receiver Python là implementation riêng, không phải phản biện độc lập của con người. Raw flight receiver dùng lại decoder canonical nên không phải decoder thứ hai được viết độc lập.

## Những vấn đề phát hiện và đã xử lý

1. **TAKEOFF không có MISSION_ITEM_REACHED số 1:** lượt SITL thứ hai đã bay và hạ cánh nhưng bị từ chối nghiệm thu. Giữ nguyên kết quả đó. Flight02 bổ sung quy tắc hẹp: baseline GUIDED/armed trên mặt đất, AUTO/current 1, chuỗi leo cao liên tục tại Home, ít nhất 2 mẫu đạt ngưỡng trước chuyển current 3, cùng REACHED 2. Các NAV khác vẫn bắt buộc REACHED; upload/readback/Home/RTL/ground/disarm giữ nguyên. Lượt thứ ba đạt quy tắc mới, không tạo REACHED giả.
2. **Video offscreen và clock:** report sơ bộ không bảo đảm nguồn/canvas thực sự hiện; source renewal gặp sai số floating point ở mốc 60 giây. Đã thêm visual coverage và marker clock lưới nhị phân, giữ bounds đầy đủ. Report cũ được giữ, không dùng làm nghiệm thu.
3. **Recovery race:** số 110 ms ở report app06 không hợp lệ cho ngắt 500 ms. Đã gắn recovery với cấu hình, ACK/resume bound của server và khung nguồn mới; chỉ hai report app07 được chọn.
4. **P1 tham chiếu vị trí sai phiên:** reconnect có thể tìm trúng vị trí cũ. Đã fence theo run/boot/model/plan/session; mismatch giữ ảnh không định vị, ghi lý do, không gắn tọa độ cũ.
5. **Persistence:** WAL canonical hóa thứ tự key JSON. Semantic document, model/plan SHA, KML nguồn và byte ảnh giữ nguyên; không hứa toàn chuỗi JSON byte-identical. Hồ sơ so sánh ban đầu không đạt được giữ cùng ghi chú sửa kết luận.
6. **UI:** bỏ writer HUD cũ cạnh tranh, không nháy số placeholder trước khi tải workspace, giữ DOM nút review khi dữ liệu chưa đổi, bố cục compact không đo fps khi video bị che.

Tổng cộng có đúng 3 lượt SITL mới theo ngân sách: lượt đầu dừng ở preflight/EKF warmup, lượt thứ hai chưa đạt quy tắc TAKEOFF, lượt thứ ba đạt. Không cộng hoặc viết lại kết quả các lượt trước. Mất link/reboot/mock không được diễn giải thành bằng chứng AP reboot thực.

## Toàn vẹn, tài nguyên và bàn giao

- 327 file thuộc baseline bảo vệ của FIELD01: **0 khác biệt SHA** khi chốt. Đây là tập bảo vệ được khai báo, không phải chứng minh toàn bộ repository hoặc mọi đường dẫn lịch sử luôn hiện diện. Các đường dẫn thiếu đã có trong trạng thái repo được giữ nguyên; không tự khôi phục hoặc thay lịch sử.
- Không sửa source/candidate đóng băng, PHONE07, lịch sử ENDURE hoặc canonical SOT. Không ký mới, không tải SDK/image/dependency.
- Evidence FIELD01 khoảng **203,6 MiB** tại kiểm cuối, dưới ngân sách 512 MiB. Host còn khoảng **31,93 GiB**, cao hơn sàn 20 GiB.
- App11 đóng sạch, không khôi phục quyền; cổng 8870/8871 không còn listener của tác vụ. Container `aeris-field01` không chạy. Docker image prune thu hồi 0 byte, không dọn volume/container khác.
- Đã xóa đúng cache mới của tác vụ: `pilot/field01/.stage` (4.716.318 byte) và `pilot/field01/__pycache__` (3.114 byte). Không xóa evidence; lock của test crash được giữ làm chứng cứ. [Receipt dọn dẹp](../evidence/field01/cleanup01.json).
- [Hướng dẫn chạy lại có kiểm soát](../pilot/field01/README.md). Stage có thể dựng lại từ nguồn được pin, dùng thư mục output mới; không tự chạy SITL thứ tư hoặc mở lại chiến dịch soak. Bản bàn giao hiện tại là mã nguồn, báo cáo và hồ sơ tĩnh, không phải dịch vụ đang chạy.

Phần này chủ yếu deterministic, không dùng LLM lúc vận hành nên không lập benchmark LLM giả tạo. Chưa đo lợi thế thương mại, tổng công kỹ sư hay mức giảm thao tác người dùng so với baseline khác; không dùng kết quả một host để kết luận vượt DJI.

## Gate tiếp theo

Khi Xiaomi sẵn sàng: kiểm runtime/ART, lifecycle foreground/background, input, persistence, Android SAF export/import và hiệu năng video trên thiết bị thật, với sàn dung lượng giữ nguyên. Sau đó mới kiểm camera/gimbal thực, clock phơi sáng/GNSS, thermal, radio, link loss và an toàn bench Hera. Bay đêm/tầm xa, dual-operator phần cứng, hiệu chuẩn Hera và phát hành production là gate riêng. Không cần kết nối Xiaomi để xem, replay hoặc kiểm receiver của bộ chứng cứ host đã bàn giao.

![Cockpit đang bay AUTO SITL với video và payload tổng hợp](../evidence/field01/cockpit-sitl-capture01.png)
