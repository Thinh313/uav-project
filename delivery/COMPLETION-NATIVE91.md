# Completion NATIVE91

18/10/2026 · **PASS trong phạm vi Android emulator + SITL engineering.** Không phải nghiệm thu Hera/HeraHub hay production. Một agent tách SPEC/BUILD/VERIFY; receiver là tiến trình/đường kiểm riêng, không tự nhận một nhóm QA độc lập. Canonical SOT/source/candidate/ENDURE giữ nguyên; tài liệu này là bổ sung riêng.

Đã triển khai xuất diagnostic trace định dạng Native90 qua Android SAF trong namespace91, receiver kiểm độc lập, rồi ghép cockpit với ArduPilot4.7.1 SITL. Màn Fly nhận vị trí/telemetry thật của simulator; local video là pattern tổng hợp PiP, input chẩn đoán không phát lệnh. Đã sửa island video che thông tin vị trí và bổ sung gate foreground/busy chung cho SAF/workspace/raw và thao tác mutable SITL.

## Ma trận nghiệm thu

|REQ|Kết quả|Hành vi|Bằng chứng trong evidence/native91|
|---|---|---|---|
|91-01|PASS|Trace định dạng Native90, prefix bất biến + workspace/HEAD/manifest/receiver/nonce, không nâng prefix thành toàn phiên.|archive-tests06; receiver06-sitl-final; native90-corpus-provenance|
|91-02|PASS|Android SAF create/write/readback; hủy, kill trước SAVE → UNKNOWN, chọn sai gói không hoàn tất; bản sao khôi phục khớp đúng SHA gốc.|diag-ops03/04/05/06; saf04-recovered; saf06-sitl-final|
|91-03|PASS|Receiver intake độc lập, 20 mutant bị từ chối, raw receiver phân biệt bay hoàn tất và gián đoạn; không khôi phục quyền.|receiver-negative-final; receiver-extra-negative; independent-raw-receiver|
|91-04|PASS|APK06: KML → compile16mục → read-only4.7.1 → preflight → grant → upload/readback → arm → Home mới → AUTO → RTL/ground/disarm → review.|runs/sb0efacd0e4b743668a75; upstream-raw-oracle-final06|
|91-05|PASS|Nominal04 và06; mất foreground05 → revoke/GCS failsafe/RTL/hạ cánh; accepted=false. Update/reboot giữ workspace và SAF; 3review còn nguyên.|android91-history-after-reboot06; final-verification06; interrupted receipt|
|91-06|PASS|59.229đường dẫn bảo vệ +28file sandbox90 khớp SHA; runtime đóng; không tải SDK/image; sàn20GiB được giữ.|preservation-after06; native90-sandbox-preservation06; runtime-closure06|

## Các phép kiểm đã chạy

- Host06:33ca input/video model,15ca journal,13ca archive/prefix,115tổ hợp admission gate. Các suite kế thừa bundleIO8/composite3/fileops12/workspace12/history11 cũng đạt. Không cộng ca JVM/ART hay các lần chạy lại thành chức năng mới.
- Mock trước SITL:24ca bridge,8ca channel,18ca passive observer;31controls,46model,14takeoff guard. Receiver13+7ca phá dữ liệu/semantic/replay đều bị từ chối, gồm thay mission rồi tính lại toàn bộ hash.
- Android33 ARM64/WebView101: SAF thật và đọc lại provider; kill trong picker; wrong artifact; recovery copy đúng gói gốc; update/reboot.33guard model chạy trên ART trong APK06. Snapshot đóng app có11trace/269event, đều qua chain/provenance replay. Đây vẫn là committed prefixes, không có whole-session completion marker.
- Ba SITL run độc lập: `sfca8e3a181054791a9c9` nominal04; `s18177b39963244da9537` foreground-loss05; `sb0efacd0e4b743668a75` nominal06. Mỗi run16mission items,6camera commands,2readback cycles,0parameter writes. Hai run nominal được raw xác nhận NAV/takeoff/RTL/ground/disarm; run sự cố chỉ xác nhận failure, không nghiệm thu nhiệm vụ hoàn tất.
- Nominal cuối06 có4937raw records/3853RX/227TXframes. JS raw verifier và generated Python MAVLink dialect kiểm CRC/target/mission float32/camera độc lập với kết luận UI; receiver raw tái dựng execution. Camera command không chứng minh chụp ảnh, ảnh thực0.
- Mất foreground thử trên05: cắt duplex điều khiển, passive observer không chèn heartbeat ghi GCS Failsafe/RTL/ground/disarm; explicit acknowledgement rồi close interrupted. Lifecycle/transport không đổi trong06; gate bổ sung được kiểm115tổ hợp và nominal06 chạy lại đầy đủ.

## Bản bàn giao

- APK duy nhất để dùng cho vòng này: `native/native91/dist/aeris-native91-development06.apk`. APK02–05 giữ truy vết, không dùng thay06.
- APK SHA256: `ab230364dc22fb92001c504f429e6f65a79ae18ac8b1cc61afa1fe33383e7fec`.
- Source ID: `c8c312a758d4f8875d40e49b35c81601b6cd15289ebda47c52278f4f1640786c`.
- Ký development V2/V3, certificate engineering cũ; APK cài trên emulator được đọc lại sau reboot và khớp SHA. Không ký production hay tạo release candidate mới.
- Workspace `initial`, mock HEAD `5b8fcf960b1e9b70697ceff08516bbdf965bca030befbae6d20fe047e24db84c`; SITL HEAD r6 `a2f3ed1d91c1afd2fbe150a6efdcc3f99997f328746f1494c5248119ec40177b`; mission `212c359032633fb4df8aea3577995ba1161ac701775e96ad9610369ac277bc1e`.
- `receiver06-sitl-final.receipt.json` kiểm prefix + current review HEAD; receipt raw riêng kiểm execution. Hash/source allowlist không phải xác thực nhà sản xuất hay chữ ký hồ sơ.

## Giới hạn và các sự cố được giữ

Corpus Native90 gốc được đọc chỉ đọc và đóng thành **host compatibility fixture** cho receiver. Không tuyên bố tự động di chuyển dữ liệu từ sandbox90 sang91 hoặc fixture gốc đã đi qua SAF. Luồng SAF thực xuất trace/workspace của app91 với định dạng kế thừa90.

Có7giao dịch diagnostic sau reboot:5COMPLETED/1CANCELLED/1UNKNOWN. UNKNOWN là fixture kill-picker03 với nonce đã dùng ở receiver; giữ nguyên, không tự thử lại, không phát receipt thành công. Recovery04 dùng nonce riêng và đúng byte staged gốc, không chụp lại thành gói mới.

02 bị lỗi canonical path Android alias “Symlink ancestor”, đã sửa03. Một bước harness lấy nhầm filename diagnostic khi kiểm raw05; receiver từ chối thiếu MANIFEST88, không phát success receipt; file đúng sau đó được đối chiếu SHA và semantic đạt. UIAutomator WebView đôi lúc rỗng/cached trong chuyển cảnh: dùng ảnh mới, đối chiếu operation ID/staging và raw journal; không dùng DOM injection/debugging. Các raw và incident đều giữ.

Rà soát cuối phát hiện guard busy chưa phủ chéo các writer:06 dùng FileGate91 chung, từ chối background/đang có writer với115kiểm; read-only status/revoke vẫn cho phép. Không quan sát mất dữ liệu trước sửa. Các app/source cũ không sửa.

Cockpit đã có Fly telemetry và panel KML/preflight/SITL trong cùng app; editor mock và mission SITL vẫn là hai contract riêng. Video tổng hợp640×360, chưa video camera thật, HID/MCU thật, dual-operator thật, Hera physics/payload, HIL/field, tránh vật cản thực, NDAA hay secure production enrollment. Cấu hình speedup1 không đồng nghĩa đạt pacing1×; không mở gate ENDURE24h hoặc latency/scanout/thermal/leak/performance từ vòng này. UI chỉ kiểm các màn đã chụp1280×800, không chứng nhận mọi pixel của toàn AERIS.

## Bảo toàn và đóng runtime

59.229đường dẫn bảo vệ khớp SHA;28file workspace/trace sandbox90 đúng byte. Chỉ xác nhận hiện tại, không suy tồn tại liên tục trong lịch sử. Không sửa lịch sử/khởi động ENDURE, source/candidate hay ký production. Hai emulator controller/bridge và3container SITL thuộc task đã đóng; không còn process socket trên5582/5583/5891/5892/8860, kiểm bind với SO_REUSEADDR đạt.

Thấp nhất28.54GiB trống qua hai runtime, cao hơn sàn20GiB. Đã dọn5APK unsigned (`native91-unsigned02..06.apk`) và cache Python riêng, tổng16,763,843bytes. `.build` tự dọn; giữ signed APK/evidence/AVD90. Không copy project sangtmp, tải SDK/dependency/image; Docker image prune cuối không prune volume/container.

Bước tiếp: hợp nhất một model nhiệm vụ KML cho cockpit editor và SITL preflight/upload, đưa review/trace/receipt thành timeline dễ đọc trong cùng ứng dụng; giữ guard và bằng chứng. Bench HeraHub/MCU/HID/Phase One/video thật chỉ mở khi có thiết bị/SDK và cấu hình đích.
