# BIG-02: chuẩn bị media và ảnh gắn định vị trên laptop

Ngày 21/10/2026. **Đã triển khai và kiểm phần host; toàn bộ BIG-02 còn NOT READY.** Không cần chờ điện thoại để làm phần này. Nguồn camera, GNSS và sự kiện chụp đều tổng hợp; `actualImages=0`. Không có Android, camera, drone hay liên kết vô tuyến thật trong lượt kiểm này.

## Kết quả dùng được

Một overlay cô lập dùng lại chính cockpit PHONE06: mã hóa H264 → relay HTTP nhị phân localhost → giải mã → canvas; chọn RGB/thermal-look, xem tuổi khung, đo và lưu trace, chụp JPEG từ đúng khung đã giải mã, mở review và xuất JPEG gốc + sidecar + manifest. Không sửa APK BIG-01 hay thêm một ứng dụng demo rời.

JPEG được giữ nguyên byte/SHA. Sidecar liên kết run/aircraft/camera/boot/feed/frame, thời điểm khung và cặp mẫu GNSS tại thời điểm đó. Vị trí là **GNSS của aircraft**, không phải tọa độ mục tiêu hoặc vị trí camera đã bù lever arm. Chuẩn ngang WGS84; cao độ ellipsoid được ghi riêng, không gán nhầm thành MSL/relative Home. Thiếu dữ liệu, sai kiểu/clock/boot/datum hoặc ACK đơn lẻ bị QUARANTINE. Sai số thời gian trong fixture là giả định tổng hợp, không phải phép đo độ chính xác đồng bộ camera thật.

Thermal-look chỉ là hình thử có màu nhiệt; không radiometry và không có nhiệt độ °C. Không truyền lệnh bay, không nối media vào C2/WAL/physics và không thay chính sách giữ raw frame.

## Đo thực tế trên browser, nguồn thử tổng hợp

Profile chốt trước: H264 1280×720, mục tiêu 30 fps, bitrate cấu hình 4 Mbps, realtime, yêu cầu prefer-software. Backend thực tế vẫn UNKNOWN. Laptop MacBookPro18,2, Apple M1 Max, RAM 32 GiB; Chrome 155. Không đo tải CPU, nhiệt, mạng ngoài hoặc camera glass-to-glass. Thời gian dưới đây là proxy **timestamp nguồn tổng hợp → lệnh vẽ canvas cùng browser**, không phải phơi sáng → photon màn hình.

| Cửa sổ / nguồn | Thời lượng | Khung hiển thị | FPS | Latency p50 / p95 / p99 | Khoảng cách khung lớn nhất | Phục hồi |
|---|---:|---:|---:|---:|---:|---|
| live01 / source01 RGB | 30,002 s | 836 | 27,865 | 8,8 / 14,1 / 27,8 ms | 64,3 ms | Không thử |
| live02 / source02 RGB | 30,004 s | 838 | 27,930 | 9,2 / 12,8 / 15,4 ms | 59,8 ms | Không thử |
| live03 / source03 thermal-look | 30,002 s | 823 | 27,432 | 8,6 / 12,7 / 20,0 ms | 544,7 ms | 511,2 ms sau yêu cầu ngắt relay 500 ms |

Các cửa sổ đạt mục tiêu engineering đã chốt: FPS≥24, p95≤300 ms, p99≤500 ms, không có khoảng ngừng≥1 s; lượt ngắt đạt phục hồi≤2 s. Đây là mục tiêu do assistant đề xuất, không phải chuẩn DJI. Không gộp phiên hoặc gọi elapsed time ngoài cửa sổ là nghiệm thu dài hạn. live01 không có start/end tường minh nên QA ghi rõ phần duration/foreground là browser self-report; live02/03 đã có mốc và kiểm membership từng sample.

Trong lượt ngắt có **14 chunk video bị chặn có chủ đích**, tương ứng 14 khoảng trống frame ID. Không diễn giải các counter drop khác bằng 0 thành “không mất khung”. Source03 đổi thermal → RGB trực tiếp, tạm khóa chụp khi chưa có khung mới rồi nhận RGB mới; đó là smoke test, không phải cửa sổ benchmark RGB mới. Các số đo gắn đúng source02/source03. Source04 chỉ sửa CSS nhãn số ảnh; 24 pin còn lại không đổi so source03. Kiểm bố cục 1280×720 xác nhận nhãn rộng 56 px, nằm trong rail và không tràn chữ; không được quảng cáo như benchmark mới. Source04 ID: `e862a0bffb76f067c5158000ab809192f429ca09b72efe7b0827e75e3d9254ed`.

Trace gốc và kiểm tính lại độc lập: [live02](</Users/os/Downloads/AI technique/aeris/evidence/big02/live02/report-01.json>), [live03](</Users/os/Downloads/AI technique/aeris/evidence/big02/live03/report-01.json>), [QA live02](</Users/os/Downloads/AI technique/aeris/evidence/big02-qa/live02-metrics-independent.json>), [QA live03](</Users/os/Downloads/AI technique/aeris/evidence/big02-qa/live03-metrics-independent.json>). Các receipt giữ riêng theo source và phiên kiểm.

## Kiểm độc lập và sửa lỗi

Builder, QA và Contractor được tách vai theo Vibecode Kit v6.3. Corpus giữ trước khi chạy gồm geotag/capture và relay; receiver Python không nhập core hoặc hàm verify của sender. Receiver tính lại nội suy qua kinh tuyến 180°, kiểm schema, SHA, byte size, run/boot/feed/receiver và chống replay. Process receiver mới từ chối gói đã nhận, giữ nguyên SHA state khi từ chối. Không coi bookkeeping này là xác thực nguồn/PKI production.

QA độc lập chốt **PASS_SCOPED cho phần engineering tổng hợp**, không còn P0/P1 mở trong phạm vi source HOST01 đã kiểm. Biên bản: [verification-final01.json](</Users/os/Downloads/AI technique/aeris/evidence/big02-qa/verification-final01.json>). Chín hàng yêu cầu ở bảng dưới gồm năm hàng có bằng chứng scoped và bốn hàng còn gate; đây không phải phần trăm hoàn thành sản phẩm.

Lỗi tìm được và sửa có bằng chứng: JSON tải về bị bọc thành Buffer; sai Content-Type chunk; tương quan frame đến sau phản hồi relay; thiếu sample của timing bị coi là 0; giới hạn body không đủ trace; replay set bị khởi tạo lại; task/timer/callback cũ tác động lên phiên mới; report cũ ghép sai config/feed; phản hồi resync cũ làm reset decoder mới. Ca phản chứng resync FAIL trước sửa và PASS sau sửa đều giữ lại. Không viết lại kết quả cũ thành PASS. Nhãn số ảnh dài bị cắt trên rail được sửa riêng bằng CSS và kiểm lại bố cục.

JPEG browser tổng hợp đã qua GET HTTP thật, so từng byte với bản lưu, rồi receiver độc lập xác nhận. Hai gói source03: RGB 108.049 byte và thermal-look 111.925 byte. Frame ID và thời gian được ghi cả trong ảnh và sidecar. Metadata không chứng minh camera thật hoặc chất lượng khảo sát.

**Download qua UI browser chưa nghiệm thu:** CUA downloadMedia bị timeout/reset session; cách đợi download event có giới hạn 8 giây cũng chưa trả kết quả. Đã giữ hồ sơ sự cố, không retry vô hạn. GET backend và receiver PASS không được thay cho PASS của thao tác tải bằng UI. Android SAF cũng chưa kiểm.

## Phạm vi đạt và phần còn thiếu

| Yêu cầu | Trạng thái bằng chứng |
|---|---|
| Overlay cô lập; nguồn/candidate/ENDURE giữ nguyên trong phạm vi kiểm | PASS theo fingerprint, có sự cố thiếu đường dẫn cũ được ghi riêng |
| Encoder/relay/decoder/canvas, timing và xuất raw report | PASS scoped browser laptop, profile/version ở bảng |
| Queue có giới hạn, đúng identity/GOP/keyframe, lỗi clock/boot | PASS mock/receiver; phục hồi relay 500 ms đã thử browser |
| RGB ↔ thermal-look, chụp đúng khung, review trong cockpit | PASS synthetic host; không PiP hoặc payload thật |
| Original SHA/sidecar, đúng thời điểm và cao độ, gói thiếu/hỏng/sai receiver/replay | PASS corpus + HTTP + receiver độc lập |
| UI download browser, Android SAF, native/WebView và điện thoại/tablet | NOT CHECKED |
| Camera thật, exposure clock, EXIF tương thích công cụ ngoài, GNSS/lever arm thực | NOT CHECKED; hiện chỉ sidecar tổng hợp |
| Nhiều viewer/thiết bị, Wi-Fi/radio/Starlink, RTSP/WebRTC, CPU/RAM/heat dài hạn | NOT CHECKED; relay hiện một viewer |
| Radiometry/định vị mục tiêu, điều khiển payload/Hera, production | NOT CHECKED |

**Giá trị:** có đường đo và bộ kiểm toàn vẹn có thể chạy lại trước khi mua thời gian thiết bị. Chưa xác định đoạn gây giật trong hệ thống khách hàng, chưa chứng minh cải thiện vận hành hoặc ưu thế với DJI. Đối chứng LLM không thích hợp cho thuật toán transport/hash/địa lý xác định; lợi ích người dùng vẫn phải đo khi nối thiết bị và camera thật.

## Bảo toàn và vận hành tiếp

Không build/ký APK mới, không chạy SITL/emulator/soak, không dùng SDK hay quyền camera/location. PHONE06 source07 248 pin và APK01 giữ nguyên SHA. Đối chiếu 58.089 đường dẫn được chọn không có lỗi mới hoặc SHA mismatch mới; 562 đường dẫn thiếu từ trước trong phạm vi này vẫn thiếu. Phạm vi khác với 597 lỗi/68.915 đường dẫn lần BIG-01, không phải phục hồi 35 file hoặc PASS toàn bộ lịch sử. Không khôi phục/xóa lịch sử ENDURE hoặc dữ liệu người dùng.

Ba phiên đo và một phiên kiểm bố cục đã đóng server/tab; stage `.local/big02/stage` được dọn sau mỗi lượt. Các receipt, trace, ảnh tổng hợp và bản source trước sửa được giữ. Không tải dependency hay tạo cache build. Sàn 20 GiB được giữ; số cuối và fingerprint hiện hành nằm trong `evidence/big02/final-verification01.json`.

Lượt kiểm mới phải dùng evidence root chưa tồn tại, ví dụ:

```sh
python3 -B planning/big02/serve.py --evidence-root evidence/big02/operator-preview01
```

Xem [TIP](</Users/os/Downloads/AI technique/aeris/planning/big02/TIP-HOST01.md>), [ADR](</Users/os/Downloads/AI technique/aeris/planning/big02/ADR-HOST01.md>) và [runbook](</Users/os/Downloads/AI technique/aeris/planning/big02/RUNBOOK-HOST01.md>). Không dùng lại thư mục live01/02/03 đã có bằng chứng.

Bước tiếp theo khi Android sẵn sàng: qualify codec/WebView và USB/network trên Xiaomi; đồng thời chốt model/firmware/API camera RGB/thermal và topology stream. Sau đó nối adapter camera thật, đo từng chặng nguồn/encode/link/decode/display/fanout, hiệu chuẩn clock chụp với GNSS, kiểm ảnh gốc và SAF. Chỉ khi các gate này đạt mới đóng BIG-02.

Tham chiếu giao diện kỹ thuật, không phải chứng nhận: [W3C WebCodecs Working Draft 19/10/2026](https://www.w3.org/TR/2026/WD-webcodecs-20261019/), [MDN VideoEncoder](https://developer.mozilla.org/en-US/docs/Web/API/VideoEncoder), [MDN VideoDecoder](https://developer.mozilla.org/en-US/docs/Web/API/VideoDecoder), [MAVLink CAMERA_IMAGE_CAPTURED](https://mavlink.io/en/messages/common.html#CAMERA_IMAGE_CAPTURED).
