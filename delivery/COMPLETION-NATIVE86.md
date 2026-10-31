# NATIVE86 — COCKPIT85 trên Android

Trạng thái: **PASS trong phạm vi Android/mock đã kiểm, có giới hạn ghi nhận**. 2026-10-17T20:59:46.741302+07:00

Đã đưa mock COCKPIT85 vào shell Android riêng `vn.rtr.aeris.native86`, ký APK development và kiểm trực tiếp trên emulator-5582: Android 33 ARM64, WebView 101.0.4951.61,1280 × 800, density 160. Đây là shell WebView đóng gói Android, chưa phải nghiệm thu trên HeraHub.

[APK development03](/Users/os/Downloads/AI technique/aeris/native/native86/dist/aeris-native86-development03.apk) · SHA256 `8c4d016e5aa8b6c52e86ab3234cccd9ea2602f5b1c1d55478152f9c156559e4a`. Chữ ký v2/v3 đạt; chứng thư development RtR, không phải production. SHA APK đã cài khớp gói host.

## Kết quả chính

- Khảo sát: nhập `Khao_sat_NATIVE86`,31 m/Home,1,1 m/s; lưu và compile polygon mẫu thành2 điểm. Journal draft khớp byte qua restart.
- Preflight: profile mock mới, Home/chuẩn độ cao/tuyến được xác nhận có chủ ý. Profile stale khóa Fly; không kéo dài freshness để vượt kiểm.
- Fly: ACK không tăng cursor;2 điểm quan sát và hạ cánh mock tạo `COMPLETED_MOCK`. Review ghi0 ảnh thực, operational=false, authorityRestorable=false.
- Hồ sơ hoàn tất khớp toàn bộ byte qua force-stop và Android reboot với boot ID mới. SIGKILL đúng PID app khi cursor 1 giữ nguyên prefix và thêm `INTERRUPTED_RESTART`; không tự hoàn tất, tiếp tục bay hay phục hồi quyền.
- SAF: xuất/provider-readback/nhập staging/xác nhận chuyển workspace/restart đạt. Bản nhập có cùng HEAD, thế hệ gốc được giữ. Guard4 snapshot từ chối lần bắt đầu mới, không tự xóa. Tạo workspace mới đòi gói xuất đã kiểm của đúng HEAD hiện tại.
- UI:28 trạng thái chọn lọc,2 theme,4 màn chính,9 điểm mở popup và workspace.160 kiểm UI/package đạt; footer thẳng logo0 CSS px, hai đảo công cụ cùng tâmY0 CSS px. Không thấy nút đang bật trong popup bị che hay tràn chữ ở các trạng thái đo.
- Android WebView thiếu`:has()` được xử lý bằng state mirror; hỗ trợ backdrop-filter được quan sát. Lỗi bàn phím fullscreen che ô nhập ở build01 đã sửa trong build02/03; ô tên và số xuất hiện trên bàn phím, phần biên tập cuộn được.

## Kiểm độc lập và bảo toàn

Replay trên host của dữ liệu thu từ Android xác minh SHA, chain và semantic của30 revision duy nhất và2 gói xuất;4 ca âm kiểm cờ operational/authority và manifest hỏng bị từ chối. Đây là đối chiếu thuật toán riêng với dữ liệu app đã lưu, cùng một agent thực hiện build rồi QA, không tự nhận hội đồng QA độc lập.

Regression:31 controls/icon,46 freshness/history,16 workflow; Java Policy 22,DraftStore 31,ArchiveEdges 4,Workspace 12,History 11;104 kiểm ghép asset tĩnh. Build03 và44 asset trong APK khớp byte nguồn hiện tại.41/42 asset COCKPIT85 được dùng đúng byte; index là thay đổi có ghi nhận, layout86 là lớp mới. Không chạy module fly84 override mock mặc định.

52.432 đường dẫn bảo vệ khớp SHA trước/sau,0 thiếu hoặc lệch. Source/candidate đóng băng và ENDURE được giữ nguyên. Kiểm này chứng minh byte hiện tại; không xóa lịch sử sự cố đường dẫn thiếu hoặc khẳng định đường dẫn luôn hiện diện liên tục.

Emulator/controller thoát sạch, cổng5582/5583 đóng. Dung lượng nhỏ nhất khi runtime chạy: 44.04GiB; sau dọn: 45.78GiB, giữ sàn20 GiB. Đã dọn89file tải/chunk/archive và bytecode tạm riêng của NATIVE86 (~2,03GiB), giữ APK/AVD/appdata/evidence và một SDK cache tái sử dụng có372 file khớp pin. Không xóa dữ liệu khác, runtime cũ hay bằng chứng.

## Giới hạn và phần chưa kiểm

- Một picker SAF thứ hai được giữ mở quá60 giây do quá trình thao tác kiểm, UI báo `NATIVE_COMMIT_UNKNOWN_NO_RETRY`; callback provider đến muộn vẫn có thể ghi file. Đã đối chiếu chỉ đọc toàn bộ manifest/byte trước khi chủ ý tạo workspace mới, không retry tự động. UX timeout này còn cần cải thiện; không suy ra mọi giao dịch chọn tệp kéo dài đã đạt.
- WebView 101/UIAutomator đôi khi thiếu subtree; thao tác dùng screenshot hiện tại khi AX thiếu, không dùng XML cũ.28 ảnh và báo cáo renderer được đối chiếu; renderer là tự quan sát, không phải attestation. Không tuyên bố mọi pixel/mọi trạng thái đều đạt.
- Chưa kiểm HeraHub, joystick/nút cứng thật, video thật, camera/gimbal hay UAV thật. Chưa chạy SITL trong lượt này; chưa benchmark FPS/GPU/độ trễ trên tay cầm hoặc WebView khác. Không có host token, bridge bay hay ký production.
- Các thông số footer và ảnh nền là dữ liệu đặt/minh họa, không phải telemetry hoặc ảnh thực. Bản này đủ cho hành trình diễn tập Android đã nêu, chưa đủ thay Ragas để bay thương mại.

## Bước tiếp theo

Ưu tiên xử lý vòng đời picker SAF dài và thông báo quota/recovery rõ nghĩa cho người dùng; sau đó nối main Fly mới với nguồn SITL chỉ đọc, kiểm freshness/reboot rồi mới mở chuỗi nhiệm vụ có quyền có thời hạn. Không gộp bằng chứng mock với SITL/Hera thật.

## Bằng chứng

[Verification](/Users/os/Downloads/AI technique/aeris/evidence/native86/verification.json) · [UI QA](/Users/os/Downloads/AI technique/aeris/evidence/native86/verification-ui.json) · [Raw replay](/Users/os/Downloads/AI technique/aeris/evidence/native86/captured-replay02.json) · [Preservation](/Users/os/Downloads/AI technique/aeris/evidence/native86/preservation-final.json) · [Crash/restart](/Users/os/Downloads/AI technique/aeris/evidence/native86/crash-restart-verification.json) · [Android reboot](/Users/os/Downloads/AI technique/aeris/evidence/native86/android-reboot-verification.json) · [Cleanup](/Users/os/Downloads/AI technique/aeris/evidence/native86/cleanup.json)

![Review Android](/Users/os/Downloads/AI technique/aeris/evidence/native86/android86-review-completed.png)
