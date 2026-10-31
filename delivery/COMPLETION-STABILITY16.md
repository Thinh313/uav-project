# STABILITY16: ổn định heartbeat, UI và kiểm kê quota

Ngày 24/10/2026. Phạm vi: module cô lập, kiểm mock/fault injection và đối chiếu log cũ. Không thay ứng dụng hoặc chiến dịch đang đóng băng.

**OVERALL STATUS: READY-with-deferred trong phạm vi source/mock. Android–SITL và beta tích hợp: NOT READY / NOT RUN.** Nguyên nhân khởi phát độ trễ UI/heartbeat cũ vẫn UNKNOWN; không tuyên bố bản vá đã sửa được lỗi đó trên Android.

## Kết quả có ích

- Có adapter kiểm kê quota chạy một worker, một công việc đang xử lý, không hàng đợi, không cache bỏ kiểm SHA. Worker gọi đúng scanner G15 đóng băng, giữ kiểm đầy đủ metadata và SHA theo phase. Có hook resource guard cô lập để ghép vào một entry mới; chưa được ghép vào G15.
- Deadline 10 giây tính từ dispatch, gồm phần startup còn lại sau dispatch, đọc inventory và nhận kết quả. Freshness 15 giây lấy mốc dispatch của parent một cách bảo thủ; kết quả đến muộn không làm hồ sơ cũ thành mới. Lỗi, stale, đóng hoặc worker chết đều vô hiệu hóa mẫu, không tự thử lại/khôi phục worker.
- Có bộ đọc chẩn đoán UI tách tuổi snapshot, timer lag, queue wait, send/header/body và các pha server. Chỉ ghép đúng lifecycle document/request/action; không trừ timestamp khác clock, không coi server trả 200 là client đã nhận. Module không thay lịch heartbeat hay quyền điều khiển.
- Đã sửa và kiểm lỗi đóng file: dù fsync và close cùng lỗi, vẫn thử đóng worker, trả lỗi đầu tiên và giữ close idempotent. Đã giữ ca phản chứng của QA về tổng lịch sử giả; bản cuối buộc tổng khớp tuple của inventory đã pin.

## Chẩn đoán dựa trên bằng chứng

G15 từng từ chối UI age 1564,706 ms so với 1200 ms. Heartbeat 367 có queue wait 0 ms, timer lag trước đó 419,6 ms, header 1067,8 ms và thất bại 1070,8 ms so với deadline 1000 ms. Trong clock server riêng, xử lý 106,143 ms, journal barrier 105,929 ms. Không có phép đo đủ để chia phần còn lại cho mạng, host hoặc Android; không đổi queue khi chưa có căn cứ.

Log macOS hiện còn ghi Clamshell Sleep lúc 15:54:43 và DarkWake 16:04:37 ngày 23/10, cách 594 giây. Điều này phù hợp với loop gap 592,9 giây và lần host dừng quota stale lúc 16:04:38. Guard đã từ chối đúng; đây là sự kiện sau lỗi UI/heartbeat, không giải thích thay cho lỗi trước đó. Log được thu hồi sau sự kiện, không phải native observer chạy liên tục trong campaign.

Đo trực tiếp scanner trên kho hiện có: metadata 301,78 ms; full SHA 1240,84 ms, đọc 306.022.057 byte lịch sử; timer lag tối đa 2,67/3,61 ms ở hai lượt. Inventory read/hash/parse đồng bộ khoảng 0,39/0,83/5,95 ms vốn nằm ngoài duration mà scanner cũ báo. Đây là đo cục bộ, chưa chứng minh bottleneck gây lỗi G15.

## Đối chứng và nghiệm thu

| Phép kiểm | Kết quả và giới hạn |
|---|---|
| Healthy, cùng inventory đầy đủ | Tổng entries/bytes/hash khớp. Một cặp full SHA: cũ 1122 ms, worker 1008 ms; không suy ra lợi thế tốc độ từ một cặp đo. |
| Tiêm quota FS block 1250 ms | HTTP mock handler cũ quá hạn khoảng 1004 ms; worker trả heartbeat 10,60 ms. |
| Tiêm quota CPU block 1250 ms | Cũ quá hạn khoảng 1004 ms; worker 9,57 ms. |
| Chính heartbeat fsync hoặc host bị chặn 1250 ms | Vẫn từ chối khoảng 1004 ms; không bỏ barrier/nới deadline. |
| UI độc lập | 25 ca PASS: identity, dữ liệu sai, thứ tự clock, late header/body, giữ lỗi qua vòng retention, clone và close. |
| Quota độc lập trên source cuối | 35 ca PASS: full SHA parity, tuple, phản chứng đã sửa, delayed delivery, 10 s/15 s, clock lùi, crash/exit 17, tamper, malformed, late result và cleanup. |
| Source/mock Builder | UI 8 nhóm; quota healthy parity + 6 ca HTTP có kiểm soát; resource guard 3 nhóm. Giữ riêng số của Builder và QA, không cộng thành chứng nhận sản phẩm. |

HTTP mock dùng handler G15 thật, ClientSession/Store/journal/fsync gốc và client worker có clock riêng. Fixture đổi root ghi sang STABILITY16, vô hiệu hóa transport bay và không kiểm admission vật lý trong constructor. Guard được kiểm riêng với dung lượng thật và đã từ chối đúng. Không có MAVLink/SITL/Android hay lệnh bay trong thử nghiệm này.

Lượt localhost đầu tiên bị sandbox EPERM đã được giữ; lượt mock có quyền localhost chạy sau đó được lưu riêng. Bản đối chứng timing chạy trước bản vá tuple; proof source xác nhận delta chỉ là ràng buộc policy/inventory/tổng, QA 35 ca chạy lại trên source cuối. Không gọi timing trước sửa là phép đo lặp trên source cuối.

## Bảo toàn và giới hạn

QA đầu lượt đối chiếu đúng 12.671 mục bảo vệ, 7 literal symlink, 1.414 pin, 26 helper và 8.385 entry lịch sử; không thiếu/đổi SHA trong các tập này. Cuối lượt kiểm lại 204 đường dẫn G15 đã đóng và các dependency được tải, đều khớp; không lặp toàn bộ audit lớn. Git có 95 đường dẫn thiếu từ đầu lượt, đều ngoài baseline bảo vệ; danh sách được giữ trong receipt, không khẳng định toàn repository nguyên vẹn và không tự khôi phục.

Không sửa source/candidate/ENDURE, pin, lock hay lịch sử G15. Bốn proof cuối G15 chưa từng được ghi vẫn được ghi nhận là chưa có; không tạo lại ở đây để lách writer gate 28 GiB. Không build/cài/ký APK, tải dependency hay dọn dữ liệu người dùng.

Đã dọn 17 thư mục scratch trong repo do tác vụ tạo: 13 của Builder và 4 của QA, danh sách đầy đủ cùng kiểm tra không còn tồn tại nằm trong `evidence/stability16/qa-final01.json`. Sáu listener HTTP mock và các worker đã đóng. Không tạo scratch ngoài repo. Phạm vi ba thư mục STABILITY16 lúc QA chốt gồm 45 file, 257.666 byte, dưới ngân sách 32 MiB; báo cáo/manifest bàn giao bổ sung vẫn rất nhỏ.

Dung lượng khoảng 26 GiB: cao hơn sàn 20 GiB nhưng thấp hơn admission 29 GiB. **Android–SITL NOT RUN**, không mở campaign mới hay nối tiếp campaign đã thất bại. Không có bằng chứng mới về AUTO/video/payload hoặc persistence trên Android trong milestone này.

## Handover

Code: `pilot/stability16/{quota-worker,quota-scanner,quota-resource,ui-timing}.mjs`.

Hợp đồng và cách ghép: `planning/stability16/TIP.md`, `ADR.md`, `quota-HANDOVER.md`, `ui-integration.md`. Hook resource guard là async, entry mới phải await construction và closure; đổi một dòng import trong G15 là chưa đủ. Tuple hiện ràng buộc riêng inventory G15; generation khác phải có tuple được kiểm riêng.

Bằng chứng: `evidence/stability16/qa-final01.json`, `qa-preservation01.json`, `qa-power-review01.json`, `qa-ui01.json`, `qa-quota01.json`, `builder-quota-02-comparison01.json`, `builder-quota-source-proof01.json`, `builder-quota-guard-tests02.json`, `builder-ui-proof01.json`, `runtime-disposition01.json`. Giữ nguyên cả counterexample và failure receipt. Manifest bàn giao gắn SHA của source, báo cáo và receipts; đây là kiểm toàn vẹn cục bộ, không phải chữ ký phát hành.

Bước tiếp theo: khi đủ admission ổn định, ghép đúng các hook vào một bản thử cô lập mới, kiểm Android–SITL AUTO/video/payload, mất link, reboot và persistence. Chỉ kết luận lỗi tích hợp đã sửa khi có bằng chứng từ lượt đó; chưa nâng trạng thái beta.
