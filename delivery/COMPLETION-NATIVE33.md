# NATIVE33 — hành trình native bền vững,14/10/2026

**PARTIAL_HOST_VERIFIED_ANDROID_NOT_CHECKED.** Đã triển khai khảo sát → preflight → Fly mock → review trong module riêng, build APK development và kiểm logic/Java/UI/restart trên host. Chưa cài hoặc chạy trên Android/emulator; không gọi đây là nghiệm thu native hay sản phẩm Hera.

Người dùng hỏi phần nào có thể làm ngay không cần dọn thêm dung lượng. Đã tiếp tục toàn bộ phần triển khai và kiểm nhỏ; không tải image/SDK/emulator hoặc hạ gate28GiB. Một agent thực hiện các pha đặc tả, build và verify tuần tự, không phải kiểm độc lập.

## Thay đổi và hành vi

`native/journey33` kế thừa nguyên byte editor/pins/survey/compiler của NATIVE30. Người vận hành sửa tên, vùng WGS84 và tham số khảo sát; draft lỗi vẫn lưu để sửa. Compile tự chuyển preflight; cần đối chiếu mock mới và xác nhận Home/chuẩn độ cao. Fly chỉ là các quan sát mock theo điểm; ACK không tiến tuyến, landing sớm bị từ chối, chỉ đủ tuyến và landing mới kết luận COMPLETED_MOCK. Không radio/SDK/flight output hoặc media thực.

Một workspace atomically gắn draft, nhiệm vụ hiện tại, event chain và các phiên trước vào Java journal bất biến. Mỗi bước mock được lưu trước khi giao diện xác nhận thành công; typing chưa bấm lưu không được coi là đã lưu. Reply mất sau commit làm UI chặn thao tác và yêu cầu đọc lại, không tự retry hay phát lại điểm. Restart append INTERRUPTED_RESTART cho phiên chưa kết thúc, giữ nguyên event prefix/cursor; draft và history trở lại, quyền/compile/preflight không trở lại. Hồ sơ hoàn tất giữ nguyên byte sau restart. Việc sửa draft/tạo nhiệm vụ mới không sửa hồ sơ cũ.

Review kiểm hash lẫn semantic replay: exact mission/form/compiler lineage, session/epoch, clock monotonic, preflight order/freshness, cursor và landing. Rehash một review giả không làm nó hợp lệ. Media luôn rỗng; flightExecutionProven, physicalMediaVerified và authorityRestorable luôn false.

Giới hạn engineering:4 phiên trước,256 event/phiên,512 revision,64MiB journal,262144 byte/workspace. Quota từ chối và bảo toàn hồ sơ; không tự xóa. Event quota/clock/storage unknown chặn tiếp tục. Đây không phải dự toán dung lượng hoặc thông lượng sản phẩm.

## Artifact và kiểm cuối

- APK `native/journey33/dist/aeris-native33-development-02.apk`,70608 byte; SHA256 `1f81c0de6af5fb2b21f1c2708f6f6cbe0116f45e366f3374628e769d5acfc98e`.
- Package `vn.rtr.aeris.journey33`, version33 / `0.3.3-native33-development`, khai báo minAPI26/target33, debug QA, không permission. Chữ ký v2/v3 và certificate NATIVE31 development cũ đã đối chiếu; không tạo software-release signature/candidate hay dùng khóa phát hành.
- **85/85 kiểm logic:**46 editor/compiler regression và39 workspace/mock/recovery/adversarial.
- **31/31 Java journal:** immutable revision/head, token stale, writer lock, fault boundaries, corrupt/pending/quota/symlink.
- **19/19 actual host JVM SIGKILL:** old/old/new tại RECORD_PUBLISHED/HEAD_PENDING/HEAD_COMMITTED, giữ hai revision, công bố pending và không auto-publish.
- **30/30 kiểm UI host:** full journey, invalid draft, new browser runtime/server restart, giữ prefix, completed review byte-exact, export/reverify, link loss, polygon tùy ý, stale tab,6 viewport360–1920px, zero console errors/external requests/flight endpoints. Screenshot là Chromium host, không Android.
- Build/DEX/assets/package/certificate xác nhận khớp. Final receipts: `build02.json`, `logic02.json`, `crash1.json`, `browser5.json`, `verification02.json` trong `evidence/native33`.

## Những lỗi giữ lại

Browser1 chưa chạy vì sandbox từ chối bind loopback. Browser2/3 FAIL vì prepared-page background writer chạy đua với restart writer; giao diện đúng là STORAGE_UNCONFIRMED. Browser3 giữ trang lỗi và immutable journal. Sửa bằng cách prepared background chỉ thu hồi gate trong RAM, không ghi thừa; active-run background vẫn checkpoint và chờ admitted write trước khi ghi interruption. Không sửa FAIL thành PASS; browser4/5 là các lần kiểm mới.

Verifier lần đầu FAIL do thiếu JAVA_HOME cho apksigner và đọc nhầm tên trường aapt2 `minSdkVersion`. Giữ `verification01.json` và incident; sửa harness rồi kiểm lại thực sự đạt tại `verification02.json`.

## Đối chiếu yêu cầu

|REQ|Triển khai/kiểm đã có|Phần chưa nghiệm thu|
|---|---|---|
|R33-01 hành trình4 giai đoạn|PASS_HOST; APK đóng gói|Installed Android UI NOT_CHECKED|
|R33-02 atomic workspace/checkpoint|PASS Java/mock/host|Storage app-private trên Android NOT_CHECKED|
|R33-03 restart và không restore quyền|PASS host JVM/browser restart|Android force-stop/reboot NOT_CHECKED|
|R33-04 review semantic/provenance|PASS_HOST|Không ảnh/media/execution vật lý|
|R33-05 fault/stale/quota/background|PASS mock/host|Lifecycle/concurrent Activity trên Android NOT_CHECKED|
|R33-06 development APK cô lập|PASS signature/package/DEX/assets|Runtime compatibility NOT_CHECKED|
|R33-07 emulator/ART/installed journey|Chưa thực hiện|NOT_CHECKED do admission|
|R33-08 preservation/disk/cleanup|PASS các gate đã quan sát|Không suy ra kết quả endurance hoặc power-loss|

7/8 phạm vi yêu cầu đã triển khai;1 nghiệm thu emulator chưa thực hiện.87,5% là coverage phạm vi triển khai, **không phải tỷ lệ trưởng thành/sẵn sàng sản phẩm** và không đóng các native-aspect gate trong bảng.

## Tài nguyên, bảo toàn và giới hạn

Kiểm trước build/tests và cuối: còn khoảng25,3GiB, trên sàn20GiB nhưng dưới admission28GiB cho full Android runtime. Không tải/khởi động/cài emulator; ART sau sửa lỗi N30, Activity/bridge, native private persistence, force-stop, reboot, SAF, keyboard/window và focus Android đều NOT_CHECKED. Runbook riêng: `native/journey33/ANDROID-RUNBOOK.md`. Không có bằng chứng HeraHub/input/video/payload thật hoặc superiority Ragas/DJI.

**8630 đường dẫn bảo vệ khớp SHA trước/sau**, gồm frozen source/candidate/trust/SOT/ENDURE và các module/evidence trước. Giữ nguyên mọi FAIL và sự cố đường dẫn lịch sử; không suy ra path gốc hiện diện liên tục. ENDURE vẫn thất bại, không relaunch/monitor/selection hoặc cộng interval.

Đã xóa riêng `.build`, `.qa-store-*`, `.crash-qa-*` của NATIVE33 sau mỗi test; browser/server/JVM thuộc test đóng. Không whole-project copy, dependency install, outside-repo scratch, SDK/AVD/Docker/Next output mới. Giữ APK và các bằng chứng nhỏ, kể cả immutable fault journal; không xóa dữ liệu khác.

SIGKILL trên host khi OS hoạt động không chứng minh Android hoặc mất điện/OS crash; fsync không tự xác nhận media vật lý. Quá trình chết sau write có thể để pending/unknown và cần xử lý rõ ràng. Không tự sửa HEAD, xóa lock hoặc retry mutation. Native chỉ được coi nghiệm thu khi runbook chạy trên emulator thực với receipts mới, sau gate dung lượng.
