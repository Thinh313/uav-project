# NATIVE88 — Android cockpit, sự cố đang bay và bàn giao raw

**Đạt trong phạm vi Android/emulator + ArduPilot SITL và chuẩn bị bench. Chưa nghiệm thu HeraHub/UAV thật.** Ngày18/10/2026. Triển khai riêng trong `native/native88`, không sửa source/candidate đóng băng, canonical SOT hoặc lịch sử ENDURE.

## Kết quả sản phẩm

- Định dạng hướng bắc000° thay vì360°. Panel khảo sát/preflight có ba hàng sở hữu riêng: tiêu đề, nội dung cuộn, hành động. Sửa tiếp lỗi `display:grid!important` ghi đè `hidden` phát hiện trên development01; development02 chỉ bật grid khi panel hiện. Hai APK có `classes.dex` và mọi asset khác giống byte, chỉ khác CSS này.
- Thông báo thao tác hết hạn/chưa biết kết quả giải thích bước cần làm; không nới hạn Home10giây, grant30giây hay foreground3500ms. Không retry lệnh ngầm. Các mã kỹ thuật vẫn nằm trong hồ sơ.
- Khi liên kết điều khiển mất, Fly xóa trạng thái có thể điều khiển và thu hồi quyền. Kênh giám sát riêng tiếp tục nhận bytes từ AP, không tự gửi heartbeat/lệnh để che mất GCS failsafe. Dữ liệu giám sát không trở thành quyền điều khiển.
- Phục hồi đã kiểm: quan sát mới chứng minh đã hạ cánh/disarm gần Home → người vận hành xác nhận → đóng phiên gián đoạn → phiên mới bắt đầu chỉ đọc. Không tự khôi phục quyền hay tiếp tục AUTO trên không.
- Gói raw đầy đủ khác ZIP workspace: chứa raw điều khiển, raw giám sát, nhiệm vụ, phiên/AP/container, source/pins tại thời điểm chạy và closure. Xuất theo luồng16KiB, giới hạn64MiB, SHA/độ dài và đọc lại provider Android trước COMPLETED.
- Receiver kiểm byte manifest, SHA, chain, CRC/target, nhiệm vụ/camera, hai readback, Home sau arm, cất cánh bằng vị trí, NAV/terminal/hạ cánh hoặc nhánh sự cố. Receipt chỉ phát hành sau kiểm; sai receiver/nonce, replay, thiếu/hỏng/thừa/path/symlink, claim chữ ký/xác thực sai và review mâu thuẫn bị chặn. Đây là kiểm toàn vẹn/ngữ nghĩa engineering; **không chứng minh danh tính nguồn hay chữ ký phát hành**.

## Kiểm Android và SITL thực

Android33 ARM64, WebView101.0.4951.61, owned emulator-5582/AVD88. ArduCopter4.7.1, binary SHA `011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482`; internal quad, speedup1. Không phải mô hình Hera đã hiệu chuẩn hay phép đo pacing SIM32.

| Lượt | APK | Kết quả |
|---|---|---|
| `s02ae8a750700442ab128` | development01 | Nhiệm vụ danh nghĩa hoàn tất;5224raw |
| `sd17f91a4677f4b04bdcf` | development01 | Ngắt duplex đang bay; gián đoạn, đã hạ cánh/disarm và xác nhận riêng |
| `s2240270a7b154a2ab690` | development01 | Android xuống nền trong AUTO; GCS failsafe/RTL/hạ cánh; mở lại không có quyền |
| `s38b4d05f79894d9cadef` | development01 | Ngắt duplex sớm sau cất cánh; GCS failsafe/RTL/hạ cánh, không tự nối lại |
| `se63ba02156e74f1d8d95` | development02 | KML→compile→preflight→upload/readback→arm→duyệt Home mới→AUTO→review;5492raw |

Mỗi nhiệm vụ danh nghĩa có16mission items,2chu kỳ readback,6lệnh camera,0PARAM_SET và0ảnh thực. Hai bộ giải mã JS/upstream Python đối chiếu raw của hai lượt danh nghĩa. Receiver cuối kiểm lại cả5gói;2gói danh nghĩa được xuất thực qua Android SAF và đọc lại đúng SHA.

Ở lượt ngắt đầu, lệnh RTL cuối nhiệm vụ xuất hiện trước GCS failsafe: **không dùng lượt này để kết luận lỗi gây RTL**. Lượt background và ngắt sớm có GCS failsafe/RTL mà chưa đi tới lệnh RTL cuối. Timestamp theo chunk nhận của host; không suy ra thứ tự sự kiện AP bên trong cùng chunk. Bốn tham số failsafe đúng giá trị và đúng kiểu được đối chiếu từ raw. Cả3review gián đoạn giữ `accepted:false`.

APK development02 cũng hoàn tất riêng khảo sát→preflight→Fly mock→review với2điểm quan sát; ACK không tăng tiến độ. Khi quota snapshot chặn lượt mới, đã xuất/readback workspace rồi chuyển thế hệ có chủ ý, giữ mọi file của thế hệ cũ. Không tự dọn hồ sơ.

Journal giữ nguyên SHA/HEAD sau upgrade APK, restart app và reboot Android. Replay độc lập40record duy nhất:34capsule mock,1plan,5review;2review SITL hoàn tất,3gián đoạn. Workspace ZIP xuất ở thời điểm quota có30entries và chưa chứa thế hệ/lượt bay phát sinh sau đó. Các gói raw bàn giao là artifact riêng.

## QA và khả năng truy nguyên

37snapshot renderer chọn lọc bao phủ4màn ×2theme ×2viewport1280×800/640. Đối chiếu ảnh Android, grid rows, hit-test của control trong panel, ba checkbox, thuộc tính hidden và sun/moon. Trong mẫu đo: lệch gutter logo/telemetry0CSSpx, tâm hai đảo cân nhau, không thấy control panel bị footer che. Đây là kiểm mẫu, không phải chứng nhận mọi pixel, FPS hay thermal.

Giữ log lỗi mock clock, helper kiểm thử, CSS hidden và giới hạn chẩn đoán. Log UI đạt hạn2MiB admission đã được đổi tên giữ lại bằng đúng SHA trên Android và host sau khi app dừng; không sửa journal nhiệm vụ. Verifier receiver được gia cố sau4lượt đầu, giữ pin cũ trong từng run; receiver cuối kiểm lại raw gốc. Không viết lại bằng chứng cũ.

Regression:31controls,46freshness/history,14takeoff,24protocol mock,18passive,8loopback channel,16workflow;18package negatives,3real-package false-review rejections,6bench intake cases. JVM:Policy22/DraftStore31/ArchiveEdges4/FileOps12/Composite3/Workspace12/History11/BundleIO8.53module JS và15module Python đạt syntax. Build và QA dùng cùng một agent, các decoder/receiver là đường đối chiếu tách biệt; không tự nhận nhóm nghiệm thu độc lập.

## Bộ bench chuẩn bị

`native/native88/bench/README.md`, `intake.json`, `validate.py`, `qa.py`: danh tính HeraHub/firmware/SDK, radio/transport, input/calibration, video, camera/lens/gimbal, target nhiều payload, hai operator, ngân sách đo và người phê duyệt. Thứ tự: cài đặt → chỉ đọc → input → video → Phase One đơn → dual-operator → tổ hợp payload → HIL/field → receiver.

Người dùng xác nhận chưa có thiết bị/SDK. Intake hiện **BLOCKED_MISSING_INPUTS**, hardwareAcceptance **NOT_CHECKED**. Ngay cả fixture đủ trường cũng chỉ READY_FOR_BENCH_REVIEW_ONLY. Chưa chứng minh HID/radio/video thật, camera Phase One/Sony, gimbal, obstacle avoidance, ảnh mapping, độ chính xác thực địa, thời gian bay hay sản phẩm thay Ragas hoàn chỉnh.

## Bàn giao và bảo toàn

APK cuối: `native/native88/dist/aeris-native88-development02.apk`  
SHA256: `3db42a4fe878d1087a0975ead837484050c4c03789df4b4c362fc515910160cf`  
Cert development: `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`. v2/v3; INTERNET only, không WebView debugging/backup. Không ký production.

`evidence/native88/verification.json` là ma trận nghiệm thu có phạm vi; `module-fingerprints.json` khóa artifact bàn giao.55.417đường dẫn bảo vệ khớp SHA trước/sau; không sửa ENDURE hay suy ra đường dẫn luôn tồn tại liên tục. Không khởi động soak hoặc công bố ra ngoài.

Mọi5SITL,2bridge,emulator/controller sở hữu đã đóng; cổng5582/5583/5889/5890/8850 được giải phóng, token bị loại. Runtime luôn trên20GiB; thấp nhất khoảng37,31GiB. Chỉ dọn2unsigned APK và4bytecode do tác vụ tạo (~6,55MB), `.build` tự dọn; giữ APK ký, raw, receipts,AVD88 và SDK86 tái sử dụng. Docker image prune theo quy tắc chung; không prune volume/container.

Bước tiếp theo là cấp thông tin/thiết bị cho bench đã chuẩn bị, nghiệm thu transport/input/video và một payload trước khi mở rộng tổ hợp. Các chuẩn bị mock hiện có không thay cho phép đo trên HeraHub/Hera thật. ENDURE, pacing dài hạn, bảo mật danh tính receiver và phát hành production có gate riêng.
