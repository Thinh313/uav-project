# BETA06 G6: tích hợp đóng review và kiểm Android–SITL

22/10/2026. **PARTIAL / NOT READY: bản ghép đã kiểm source/mock và AUTO thực trên Android–SITL, nhưng chưa nghiệm thu trọn campaign.**

Đã tích hợp sửa đóng review mock vào entry runtime cô lập G6. APK development hiện có được dùng nguyên byte, không build/cài lại/ký mới và không ký production. Source/candidate đóng băng và ENDURE giữ nguyên. Không có thiết bị Hera, camera/gimbal thật hay SDK.

## Kết quả thực tế

| Yêu cầu | Trạng thái | Chứng cứ và giới hạn |
|---|---|---|
| Cùng ứng dụng xử lý đóng review mock và SITL | PASS source/mock | 57 nhóm QA độc lập trên bộ pin cố định; hành trình MockSocket thực qua handler/Store/history; SITL-shaped fault dùng effect stub. Hai loại hồ sơ riêng, không tạo closure AP giả. |
| N1: Android → preflight → upload/readback → duyệt Home → AUTO → RTL/đất/disarm → review | PASS Android–SITL | Run `sc14d5fb3d17a408a90e0`; 11.160 dòng raw, 8.195 RX/402 TX, 12 item, hai readback, bốn lệnh camera206, không PARAM write. Có 133 heartbeat armed/AUTO; canonical takeoff proof, navigation/RTL/ground/disarm đối chiếu độc lập. |
| Video + payload đồng thời N1 | PASS trong cohort đo | VP8 720p30 tổng hợp; 28,499 FPS/30 giây, P95 upper 50,257 ms, viewer ready 251,5 ms, phục hồi relay500ms trong550,1ms. Startup dùng publisher đã chạy, không chứng nhận cold-start toàn hệ thống. Max display gap940,3ms vẫn phải công khai; không suy ra không giật trong mọi điều kiện. |
| Capture và gimbal N1 | PASS tổng hợp/mock | JPEG54.816byte khớp hash/commit; hai điểm payload cùng lease khi AUTO với telemetry mới. Ảnh thực=0; tọa độ chỉ tham chiếu GNSS SITL lúc nhận telemetry, thời điểm phơi sáng vật lý UNKNOWN. |
| Lưu review N1 | PASS | Compact `FLIGHT_REVIEW_SEALED_REF`, receiptseq114/hash khớp WAL và review/owned closure; không còn run/quyền/lease sau Close. Container N1 dừng exit0/OOMfalse, giữ đầy đủ log. |
| F1: cắt link có chủ ý khi đang bay | NOT_CHECKED; chuẩn bị FAIL | Connect lần hai đã tạo request/AP nhưng host dừng trước grant/upload/ARM/AUTO/cut. Không lấy cleanup TCP/container làm nghiệm thu mất link. |
| Managed restart, N2 đối chứng và F2 reboot | NOT_CHECKED | Không chạy sau lỗi campaign đã latch. Không tạo host2 hay tự khởi động campaign mới. |
| Cold boot13/persistence sau restart | NOT_CHECKED | Chưa chạy. Snapshot cùng boot trước/sau lỗi vẫn19file/34record/13PENDING, SHA/prefix và18artifact cũ nguyên vẹn; điều này không thay cold restart acceptance. |
| Bảo toàn source/candidate/ENDURE và sàn20GiB | PASS phạm vi kiểm | 7.025 đường dẫn bảo vệ giữ nguyên, 750 pin khớp; min runtime quan sát33,226GiB; đã đóng sạch runtime. 95 đường dẫn thiếu từ trước được ghi riêng, không khẳng định toàn repo từng hiện diện liên tục. |

## Lỗi chặn và nguyên nhân có chứng cứ

Guard gốc `pilot/beta06/resource.mjs` duyệt **toàn bộ file và thư mục** dưới `evidence/beta06`. Nó không ghi/trừ baseline lúc khởi động và ném `NEW_EVIDENCE_ENTRY_QUOTA` ở entry4.097, trước phép kiểm200MiB. Tên lỗi nói “NEW”, nhưng bộ đếm thực là toàn bộ bằng chứng đang giữ của nhiều thế hệ.

Trong lúc Connect F1, host ghi `GUARD_OR_EVIDENCE_FAILED:NEW_EVIDENCE_ENTRY_QUOTA` rồi đóng. Tổng byte bằng chứng lúc QA đọc khoảng129,4MiB, free/forecast ở guard cuối khoảng33,31GiB, nên không phải chạm sàn ổ đĩa hoặc quota byte. Tái dựng từ filesystem birthtime cho thấy lúc host bắt đầu có khoảng3.375entry, còn721entry headroom; riêng diagnostics N1 sinh521entry. Đây là tái dựng theo birthtime, không phải snapshot đồng bộ tại guard; đường dẫn đúng entry gây vượt ngưỡng không được log.

F1 run `s77c3f208234b4d918a15` chỉ có24 dòng raw, một TX heartbeat GCS, **không grant, upload, ARM, AUTO, cut hay reboot**. Sau host shutdown, receive-boundary báo mất foreground epoch. Thứ tự code/time phù hợp với việc app.close thu hồi client lúc Connect còn bận; đây là suy luận nguyên nhân thứ cấp, không khẳng định loại hết mọi tác nhân. Container F1 dừng exit137/OOMfalse do cleanup sau Connect lỗi, không phải nghiệm thu fault.

Campaign đã khóa thất bại đúng hợp đồng hữu hạn. Không retry Connect/lệnh bay, không xóa lock/receipt, không reset clock hoặc tăng cap, không đổi code/pin đang chạy. PASS N1 và 57 nhóm source/mock không được dùng thay các gate chưa chạy.

## Thay đổi và định danh

G6 có13 module production mới và bốn transform nguồn G5 với count/SHA chính xác. Tái dùng trực tiếp contract mock r1 đã nghiệm thu; SITL vẫn dùng strict owned-seal G5/R2. Entry giữ guarded listener, parent PID và deadline; mọi thay đổi tách khỏi G5/r1 và candidate. Workspace mới là fork dữ liệu20file/870.221byte, không copy toàn project; runtime chỉ append workspace mới theo lineage. Không mở rộng thuật toán physics, lệnh bay, Home, lease, CRC hoặc serializer.

- Manifest750pin: `426b45aee00bea2bf138b9b867bb5c94e88f44cbaf403dc315fcfc36c2128875`.
- Freeze13production/132stage: `14ae46abb71e3bf1724b8107471119f59a66f5393214271703dd99fa2619205e`.
- Freeze21helper: `616a0dd9c13f22d6439451910a7f8ab07d518cac1eee74b4ae160bf3c2d96b01`.
- APK nguyên byte: `df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d`, Android13/API33, WebView101, emulator5582.
- Qualified ARM4.7.1, speedup1, cap540s, CPU1/256MiB, cùng image/binary/ports đã pin; không dùng physics Hera. Có hai request G6 thực mới: một N1 đạt, một Connect F1 thất bại; 15request lịch sử giữ riêng, G5actual0.

## Dọn dẹp và các ngoại lệ

Root đóng emulator12 exit0/errornull, controller exit0; host tự đóng theo guard. Các PID thuộc task không còn; port8872/8873/5972/5582/5583 trống tại kiểm. Hai container SITL giữ nguyên, không xóa volume/container. `docker image prune -f` trả0B. Builder/QA đã dọn riêng fixture âm tính trong danh mục cleanup của source gate; bằng chứng dương tính và lỗi thật đều giữ. Không cài dependency, không tạo venv/project copy/build cache.

Browser read/close publisher trả “Local browser use is disabled in Work settings” ở cuối campaign; backend/video listener đã đóng, nhưng tabpublisher5 có thể còn mở và chưa xác nhận dừng encoder phía tab. Không dùng công cụ UI khác để vượt hạn chế này. Người dùng có thể đóng tabpublisher còn lại.

Ngoại lệ harness được giữ: setup đầu gọi quá sớm khi ADB offline, dừng ngay phép đọc getprop trước bất kỳ root/reverse/UI effect; setup chỉ thực hiện khi thiết bị online cùng boot. Replay raw lần đầu bị từ chối vì Root đưa WAL đường dẫn tuyệt đối; lần kiểm chỉ đọc với đường dẫn tương đối đã đạt ở raw02. Không chạy lại flight effect. Prefix replay đầu chọn output không bắt đầu `qa` bị từ chối trước ghi, rồi chạy đúng output; không dùng lần từ chối làm PASS.

## Bước tiếp theo cần sửa

Sửa **scope và admission của quota entry** trong một revision mới, giữ nguyên lịch sử G6: công khai đếm file/thư mục nào, baseline bảo vệ nào; tính ngân sách diagnostics/screenshots/receipts/cả bốn AP/restart/closure trước khi mở effect. Kiểm mock với bộ bằng chứng tích lũy vượt4.096entry và số file projected. Giữ aggregate byte guard200/256MiB, sàn20GiB, finite window và provenance; không chữa bằng xóa bằng chứng hay đơn thuần nâng cap vô căn cứ. Sau gate độc lập mới cân nhắc campaign mới với đủ headroom. Chưa có commit/push hay bản ký mới.

Phần đã chứng minh: hành trình nominal thực trong engineering Android–generic SITL và đóng review bền vững. Chưa chứng minh beta trọn luồng, mất link/reboot/restart, hardware Hera, physical media hoặc phục hồi crash/unmanaged standaloneS factory. LLM baseline không áp dụng cho công việc tất định này.

## Hồ sơ và ảnh kiểm

- [Gate source/mock G6](../evidence/beta06/generation06/qa-independent-gate06.json)
- [N1 tổng hợp raw/media/capture/index/closure](../evidence/beta06/generation06/qa-n1-capture-index-closure01.json)
- [Raw N1 đã đối chiếu](../evidence/beta06/generation06/qa-n1-raw02.json), [video](../evidence/beta06/generation06/qa-n1-media01.json), [overlap](../evidence/beta06/generation06/qa-n1-overlap01.json)
- [Nguyên nhân campaign thất bại](../evidence/beta06/generation06/qa-runtime-failure06.json)
- [Root xác nhận runtime đã đóng](../evidence/beta06/generation06/root-owned-closure06.json), [bảo toàn sau runtime](../evidence/beta06/generation06/root-final-preservation06.json)
- [Prefix native cùng boot](../evidence/beta06/generation06/qa-native-prefix-after-failure06.json)
- [TIP](../planning/beta06g6/TIP-INTEGRATED-RUNTIME06.md), [ADR](../planning/beta06g6/ADR-MODE-AWARE-RUNTIME06.md), [thứ tự shutdown đã sửa](../planning/beta06g6/ROOT-RUNTIME-ORDER06.md)

![Android trong AUTO N1, video tổng hợp và payload mock, trước lỗi quota ở lượt tiếp theo](../evidence/beta06/generation06/g6-n1-postlive-payload.png)
