# MISSION55 · Đối chiếu nhiệm vụ và oracle toán–địa lý

Module offline triển khai RAGAS54 B1/B2, ưu tiên camera, QGC và Home/cao độ. Không có socket, encoder gửi lệnh, flight authority hoặc tích hợp với app đóng băng. Gói ký, source/candidate, canonical SOT và ENDURE được giữ nguyên.

## Dùng ngay

Chạy từ `/Users/os/Downloads/AI technique/aeris`:

```sh
python3 -B pilot/mission55/cli.py compare app/fixtures/qgc/roundtrip03/simple-relative-input.plan app/fixtures/qgc/roundtrip03/simple-relative-qgc-saved.plan
```

CLI chỉ đọc và in JSON. Exit0: `EQUAL_DECLARED_SCOPE`; exit2: `DIFFERENT`; exit3: `REVIEW_REQUIRED`; exit4: input bị từ chối. Home10→7 ở ví dụ trả exit2. Bản kế hoạch gốc không bị sửa. `groundStation`, thứ tự key và khoảng trắng được ghi rõ là cosmetic; null/0, frame, flags, doJumpId và extension không bị bỏ qua.

`semantic.py` so riêng header/Home, editable Survey design và cached executable items. Có parser typed camera206/2000/2001/2500/2501; ID camera khác stream ID và receiver của mission readback. DO_JUMP, schema/extension chưa hiểu và fence/rally có nội dung giữ REVIEW_REQUIRED; không chuyển đổi ngầm. Survey cache bằng nhau không chứng minh lưới đã tái sinh đúng từ polygon/angle.

`geometry.py` dùng GeographicLib2.1 ghim SHA trong `vendor` để tính tham chiếu geodesic; `compare_geometry` giải thích ảnh hưởng Home/cao độ theo model của file, chưa chứng minh mốc địa hình thực. `compare_measurement` kiểm metric/đơn vị, đổi đơn vị có ghi lại scale; unknown khác0, count phải nguyên và exact. Area ellipsoid khác planar/DEM surface/coverage. Bản tham chiếu area không xác minh polygon đơn/hole hoặc field quality.

`geo.mjs` là implementation toán riêng cho local planar area, WGS84 inverse distance, ETA từng leg, optics/trigger/cadence/count theo endpoint policy tường minh, geoid/cao độ và mẫu ridge. `geo_cli.mjs` nhận mảng JSON qua stdin, trả từng kết quả/lỗi; giới hạn1MiB/2.000ca. So với GeographicLib/vector chính thức và expected analytic trong campaign. Vincenty chỉ dùng khi hội tụ, gần antipodal từ chối; không fallback sang cầu và không coi đây là geodesic engine hoàn chỉnh cho toàn cầu.

## Corpus và kiểm chứng

Đợt nghiệm thu cuối ghi trong `evidence/mission55/run5` và verifier đi kèm. Có50 plan tổng hợp/dẫn xuất và11 fixture QGC có provenance; chỉ11 fixture được ghi là output từ QGC lịch sử. Recipe góc0/35/90/179 chỉ thay thiết kế, chưa regenerate tuyến. Count endpoint policy tổng hợp không được gọi là thuật toán đếm ảnh QGC đã đạt.

Mỗi lần chạy có thư mục attempt riêng, receipt không ghi đè:

```sh
python3 -B pilot/mission55/run.py --attempt run6
```

Lệnh này chạy corpus offline, không khởi động SITL. Gate dung lượng kiểm sàn20GiB và headroom nhỏ trước writer. Không dùng lại tên attempt. Để kiểm pin bảo vệ, `preserve.py <phase-mới>` chỉ đọc pin kế thừa, ghi receipt mới. Không chạy lại capture dependency để ghi đè snapshot.

Readback lịch sử gồm8 cycle19item trong hai journal, ở dạng JSON đã decode; **không có raw inbound để kiểm CRC độc lập**. Có38 raw outbound item được decoder mới kiểm CRC và đối chiếu metadata.95 frame session trước trong journal chuyến sau bị cách ly, không gộp vào chuyến mới. Boot không được ghi trong journal; tuổi dữ liệu dùng context replay tổng hợp, không chứng minh freshness thời gian thực. ACK/capture report/file declaration không thành file ảnh đã kiểm.

run1 giữ lỗi kỳ vọng phân loại antipodal: engine từ chối do không hội tụ, nhưng test chờ nhãn khác. Các run sau ghi expected class chính xác; không đổi speed/giảm độ chính xác/fallback để làm xanh. run2/3/4 là các bước mở rộng, không cộng test của nhiều attempt thành tổng nghiệm thu. Fixture run1 nằm trực tiếp trong `fixtures`, các attempt sau có thư mục con; root `corpus.json` là catalog lịch sử run1. Dùng catalog ở attempt cuối.

## Phụ thuộc và phạm vi chưa kiểm

GeographicLib2.1 chỉ nằm trong module, wheel vàSHA từ PyPI, license/METADATA/RECORD giữ trong `vendor`. Vector kiểm chính thức có commit/SHA; common.xml có snapshot/SHA để kiểm ID và CRC-extra của message73. Không cài vào `.venv` hay môi trường app.

Chưa chạy RAGAS runtime, QGC GUI mới/regeneration, SITL mới, HeraHub/SDK hoặc camera/calibration/ảnh/checkpoint thực; chưa ký. Bất nhất manifest RAGAS112/tên111 còn OPEN. Kết quả chỉ nghiệm thu module offline theo [TIP](../../delivery/TIP-MISSION55.md), không kết luận thay RAGAS hoặc thắng DJI.
