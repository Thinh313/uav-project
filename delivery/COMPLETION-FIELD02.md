# FIELD02: Android–SITL và bàn giao SAF

**Trạng thái: NOT READY. Bàn giao phần đã kiểm, chưa nghiệm thu toàn milestone.**

Ngày 22/10/2026. Phạm vi: APK development Android 13/API33 arm64, WebView101, emulator1280×800, cockpit viewport1280×716, companion trên laptop và ArduCopter4.7.1 internal quad. Đây là client Android điều khiển simulator qua companion host; chưa phải bộ điều khiển MAVLink native-direct độc lập trên HeraHub. Không dùng Xiaomi, máy bay/camera thật hoặc ký production.

## Kết quả sử dụng đã chứng minh

- Hành trình chạm trên Android: KML polygon/corridor → lưu model chung → compile → preflight → cấp quyền rõ ràng → upload/readback → arm → xác nhận Home sau arm → AUTO → RTL/hạ cánh/disarm → review. Hai nhiệm vụ nominal đã đạt kiểm raw độc lập, không ghi tham số autopilot.
- Payload mock: discovery, chọn nguồn, cấp/thu hồi quyền, lệnh và readback gimbal, chụp JPEG tổng hợp có liên kết run/boot/model/plan và mẫu vị trí SITL. Ba ảnh được giữ; không phải ảnh camera thật hay tọa độ vật thể.
- Cắt TCP C2 thật trong SITL và restart tiến trình AP trong container riêng: giữ raw, thu hồi quyền bay, đóng hồ sơ gián đoạn, không kết luận bay hoàn tất hoặc tự nối/cấp quyền lại.
- Workspace, KML, ba capture và lịch sử review tồn tại sau restart emulator/process. Native journal cuối có26 record khớp chuỗi SHA; pending được giữ với trạng thái UNKNOWN_AFTER_RESTART, không tự retry.
- SAF Android thực: xuất/nhập workspace; xuất raw của run gián đoạn; xuất bộ bàn giao bốn file qua picker, readback byte và receiver độc lập. Bộ nominal có4.766.473 byte. Receiver kiểm toàn vẹn trước chấp nhận, từ chối replay;14 nhóm phản ví dụ được kiểm trên dữ liệu bàn giao. Hủy picker không báo thành công; nhập wrapper sai SHA giữ nguyên workspace.

## Nghiệm thu chín tiêu chí trong TIP

| AC | Trạng thái | Bằng chứng và giới hạn |
|---|---|---|
| 1. Runtime Android, nhãn nguồn đúng | PASS trong phạm vi emulator | APK chạy ART; giao diện ghi rõ Android/host và nguồn mock. Crash buffer cuối không có package FIELD02; không suy ra không từng lỗi trong mọi thời điểm. |
| 2. KML → AUTO → review | PASS hai fixture | Polygon16 item, corridor12 item; readback hai chu kỳ, camera item giữ đúng semantics. Không đại diện mọi nhiệm vụ hoặc firmware. |
| 3. Video mạng Android | FAIL | Phát được sau restart viewer chủ động; cold-start1500ms vẫn lỗi, FPS chưa đạt24. |
| 4. Payload, quyền và capture | PARTIAL | Mock/replay và lệnh/capture/revoke nominal có bằng chứng. Thu hồi lease đang hiệu lực đúng lúc AP reboot chưa được quan sát độc lập; không có WAL receipt cho invalidate này. |
| 5. C2 cut và reboot AP | PASS fault/quarantine | Cắt thực ở1,836m/Home, lúc LANDING/armed; restart AP ở9,692m/Home. Hồ sơ incomplete đúng. Không có quan sát RTL/hạ cánh sau mất link, không chứng nhận failsafe máy bay thật. |
| 6. Persistence/restart | PASS các ca đã thử | Cùng userdata/model, không phục hồi quyền; pending UNKNOWN đúng một lần. Không phải thử mọi kiểu mất điện/filesystem. |
| 7. Android SAF/receiver | PASS các ca đã thử | Picker/readback/bộ bốn file/receiver/replay/tamper/cancel/pending đã kiểm. Race CAS trên thiết bị chưa chạy; guard có mock. |
| 8. UI cảm ứng ngày/đêm | FAIL | Header/metric căn chỉnh, telemetry chưa biết hiển thị “—”. Video-age và thông báo lỗi trên kính sáng còn thiếu tương phản; không được tuyên bố toàn UI đạt chuẩn. |
| 9. Dung lượng, đóng tiến trình, SHA | PASS baseline đã khai báo | 1.486 file bảo vệ không drift;7 native source và59 host source khớp. Companion/emulator/container/cổng riêng đã đóng. |

**6/9 tiêu chí có kết quả PASS trong phạm vi khai báo;2 FAIL,1 PARTIAL. Đây không phải phần trăm trưởng thành sản phẩm. Các lỗi bắt buộc chặn FIELD02 READY.**

TAKEOFF được xác nhận bằng quy tắc hẹp đã ghi: AP armed/AUTO, current TAKEOFF, lên gần độ cao yêu cầu rồi chuyển NAV tiếp. Không tạo giả MISSION_ITEM_REACHED cho TAKEOFF. Camera command/ACK không chứng minh camera đã phơi sáng. Hai ảnh polygon được lấy gần mặt đất (một ảnh sau disarm); ảnh corridor ở9,133m trong LANDING. Không quảng cáo các ảnh này là bộ ảnh khảo sát trên không đạt chất lượng.

## Video: số đo giữ đúng từng lượt

| Lượt Android | FPS / sàn24 | p95 source→canvas / trần300ms | Mất relay | Kết luận |
|---|---:|---:|---|---|
| app05,2CPU, cùng polygon AUTO | 23,480: FAIL | 178,261ms: PASS | Không nằm trong cửa sổ đo | Chưa đạt FPS; không có recovery acceptance |
| app09,4CPU, không AP, sau restart viewer | 18,063: FAIL | 255,485ms: PASS | 500ms, phục hồi708,7ms: PASS≤2000ms | Cold-start đầu vẫn FAIL |

Lượt cuối có542 frame trong30.006,7ms, foreground có151 kiểm bao phủ. Ngắt relay ở8.652,5ms trong cửa sổ; frame phục hồi đúng config và có cận timestamp nguồn sau resume42,257ms. Không bỏ thời gian outage ra khỏi mẫu số FPS. Không ghép latency tốt của một lượt với FPS lượt khác.

Profile VP8 720p30 được người kiểm chọn sau khi H264 encoder không được WebView này hỗ trợ; không đổi ngầm profile. Mốc cold-start1500ms không bị nới để đạt. Số đo là nguồn hình tổng hợp qua HTTP/TCP→Android canvas với clock bounds, không phải độ trễ photon/camera thật. Backend codec thực chưa xác định. Thêm CPU không đủ chứng minh nguyên nhân hay giải quyết cold-start.

## Ngân sách, bảo toàn và bản cài

- Hai build development đã dùng: build01 lỗi hằng ART/API, build02 đạt. Bản APK cuối giữ nguyên xuyên suốt các lần kiểm.
- Bảy yêu cầu SITL được giữ đầy đủ, gồm một yêu cầu bị gate29GiB từ chối trước khi AP chạy; sáu lần AP thực. Các quyết định02–05 ghi rõ sửa lỗi harness, điều chỉnh số yêu cầu và cấu hình emulator. Không xóa lượt lỗi, tự retry POST hay mở thêm AP.
- Source/candidate/ENDURE/trust/SOT cũ không sửa. Kiểm cuối1.486 file baseline không drift;95 đường dẫn Git-deleted đã có trước task vẫn được ghi là ngoại lệ, không tuyên bố toàn repository nguyên vẹn.
- Controller Android02 ghi mức trống thấp nhất khoảng33,02GiB; Android01 khoảng24,97GiB. Đều trên sàn20GiB. Kiểm cuối còn khoảng33,30GiB; bằng chứng khoảng351,30MiB, dưới ngân sách512MiB (kích thước logic).
- Đã đóng sạch9 companion session và2 emulator session; không còn container `aeris-field02` hoặc listener các cổng riêng8872/8873/5972/5582/5583. Docker image prune thu hồi0byte, không prune volume/container khác.
- Đã xóa riêng cache Swift257.790.450byte, OCR binary97.400byte và curated stage4.716.318byte. Giữ APK, toàn evidence và own AVD có thể tái sử dụng; không xóa dữ liệu người dùng.

APK: [aeris-field02-development02.apk](../native/field02/dist/aeris-field02-development02.apk),41.363byte. SHA256 `df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d`. Cert development SHA256 `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`. Không phải bản cài standalone cho thiết bị hiện trường; cần companion và cấu hình loopback/ADB của môi trường thử nghiệm.

## Việc tiếp theo để đóng gap

1. Giữ gate video FAIL. Chẩn đoán có giới hạn: giữ đúng byte và SHA của một network keyframe, đối chiếu decoder khi producer ACTIVE/STOPPED trên cùng cấu hình; đo thời gian từng đoạn. Chưa biết căn nguyên cold-start, không mặc định đổ lỗi emulator hay tăng timeout.
2. Sửa tương phản error/age theme sáng và kiểm pixel thực trên kính sáng/tối; giữ metric/source/freshness đúng.
3. Bổ sung receipt quan sát quyền payload trước/sau fault, rồi thử lease còn hiệu lực khi mất link/reboot. Không thay phép kiểm bằng TTL hết hạn hoặc bằng đọc code.
4. Chỉ sau sửa và mock đạt mới mở ngân sách lượt Android–SITL mới; kiểm lại đồng thời AUTO + media outage + WAL. Thiết bị HeraHub/camera/gimbal, radio, geotag thời điểm phơi sáng và production là gate riêng.

Không có runtime AI trong lát cắt này; so với LLM trực tiếp không áp dụng. Hiệu quả thao tác khách hàng, điện thoại thật và lợi thế thương mại chưa đo. Workflow theo Vibecode Kit6.3: Builder thực thi, Contractor và QA độc lập kiểm đầu ra; các vòng sửa dừng theo ngân sách thay vì đổi tiêu chí.

## Hồ sơ kiểm chứng

- [TIP và chín AC](../planning/field02/TIP.md)
- [QA độc lập](../evidence/field02/qa-final-independent01.json), [video cuối](../evidence/field02/qa-final-media09.json)
- [Polygon raw](../evidence/field02/qa-sitl-nominal-independent01.json), [corridor raw](../evidence/field02/qa-sitl-corridor-independent01.json)
- [C2 cut](../evidence/field02/qa-cut-independent05.json), [AP reboot](../evidence/field02/qa-reboot-independent07.json)
- [SAF bốn file và receiver](../evidence/field02/qa-saf-delivery-independent02.json), [pending restart](../evidence/field02/qa-pending-independent03.json), [tamper/cancel](../evidence/field02/qa-native-saf-negative-independent01.json)
- [Kiểm cuối SHA/dung lượng/closure](../evidence/field02/final-verification01.json)
- UI cuối: [Fly DAY](../evidence/field02/android-final-ui09-restart-result.png), [review DAY](../evidence/field02/android-final-ui09-review-day.png), [preflight NIGHT](../evidence/field02/android-final-ui09-preflight-night.png).
