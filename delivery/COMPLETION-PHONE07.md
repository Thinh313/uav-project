# PHONE07: hợp nhất nhiệm vụ và Payload Gateway trong native shell

Ngày21/10/2026. **Hoàn tất code/build và kiểm host/mock; sẵn sàng kiểm thiết bị. Nghiệm thu Android và phần cứng: NOT_CHECKED.** Một agent thực hiện lần lượt Contractor, Builder, Verify theo Vibecode Kit6.3; không có tuyên bố phản biện độc lập bởi người/agent khác.

Đã tạo package cô lập `vn.rtr.aeris.phone07`: giữ compiler KML của PHONE06, thêm preflight replay → Fly mock từng điểm → discovery/chọn RGB hoặc IR → quyền camera/gimbal có hạn → readback → JPEG tổng hợp + sidecar tọa độ UAV tại exposure mock → review và journal bất biến. SAF export đã viết và compile; chưa chạy trình chọn/provider Android thật. Không tích hợp vendor SDK hoặc tạo production release.

| Phạm vi nghiệm thu | Kết quả và bằng chứng |
|---|---|
| AC1 model KML, Home/cao độ, compiler | Host PASS: polygon và corridor biên dịch/replay cùng model; không suy ra terrain/camera Hera đã hiệu chuẩn |
| AC2 hành trình và restart | Host PASS: thiếu freshness/điểm bị chặn, hoàn tất chỉ là MOCK; mở lại giữ phiên gián đoạn, không tự khôi phục quyền |
| AC3 Gateway nhiều payload |22/22 nhóm policy trên core được port; RGB/IR capture UI đã chạy, gimbal readback, IR không ISO/radiometry; chưa phải driver Sony/Phase One |
| AC4 native journal/media |24 assertion I/O trên host JVM đạt;13/13 nhóm JS/JVM đạt. CAS, fsync faults, quota, symlink, tamper, PENDING được giữ. Android ART/JSI/epoch bridge thực: NOT_CHECKED |
| AC5 gói và receiver |3 gói host được receiver Python riêng kiểm integrity/toán;9 ca replay/sai receiver/hỏng byte bị từ chối. Android SAF/provider/callback và TAR do Java export trên điện thoại: NOT_CHECKED |
| AC6 APK development |Compile toàn bộ Java, aapt2, d8, zipalign, apksigner PASS. Payload unsigned/signed khớp.131 asset UI trong APK khớp stage đã kiểm; fixture host không có trong APK |
| AC7 UI và bàn giao |Host UI kiểm luồng corridor, readback,2 ảnh RGB/IR, hoàn tất và reload;2 layout1280×800 và900×500. Panel giữa header/footer, không overflow ngang ở900, nút xuất48px cuộn tới được. Không chứng nhận mọi màn Android hay hiệu suất thương mại |

APK: [`aeris-phone07-development01.apk`](../native/phone07/dist/aeris-phone07-development01.apk),3.853.554byte. SHA256 `02d1fcf9929603f9da81cb22294b7ad162a8d78c44ac314f22da06bcc8c5befd`. Source ID `e0c18fa2fad9d2852005cebcea4010f4b9e551f9a1d3f71030d79df0c1ce7e93`. Development certificate SHA256 `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`; chỉ quyền INTERNET, không xin camera/microphone/location Android.

Kiểm cuối cùng đúng source ID của APK: [`host-verification03.json`](../evidence/phone07/host-verification03.json), [`build01.json`](../evidence/phone07/builder/build01.json), [`apk-ui-equivalence01.json`](../evidence/phone07/apk-ui-equivalence01.json), [`receiver-verification01.json`](../evidence/phone07/receiver-verification01.json). Ảnh kiểm: [`review-media-1280x800.png`](../evidence/phone07/review-media-1280x800.png), [`review-media-900x500.png`](../evidence/phone07/review-media-900x500.png). Đây là receiver có triển khai riêng, không phải nguồn ảnh được xác thực bởi phần cứng.

Các lỗi/giới hạn được giữ công khai: lượt journey-test01 có12/13 nhóm đạt vì xin ticket khi preflight chưa ready; đã sửa, journey-test02 và kiểm cuối03 đạt13/13. Envelope kiểm đầu có thêm gateway.json nên receiver từ chối đúng allowlist3 file; TAR wire đúng3 file được chấp nhận. UI đầu có nút dưới footer và painter lịch sử SITL tranh quyền; đã tách owner theo mode, sửa safe area và kiểm lại. Có một timeout CDP khi đóng mock; đọc lại journal/UI xác nhận đã hoàn tất, không gửi lại lệnh. Không xóa các hồ sơ lượt đầu.

**Giới hạn sản phẩm:** video/IR, GNSS, ±5ms, readback và chuyến bay ở đây đều tổng hợp. Không có ảnh camera thật, EXIF thật, geoid/lever-arm calibration, radio link, thermal radiometry, simulator physics coupling hoặc chứng cứ bay Hera. Codec relay mới ở trong process, không đại diện đường RF hoặc phép đo HTTP trước. Storage bridge đồng bộ có thể gây stall; cần đo Android trước kết luận mượt. Payload store mới96 records/8 thư mục/12MiB, chưa có rotation/archive; quota dừng ghi, không tự dọn. Direct-SITL path cũ được giữ có guard, chưa tái nghiệm thu trên APK mới.

ADB chưa có thiết bị ở lượt kiểm; không chạy emulator/SITL hoặc tải SDK. Build admission thấp nhất22,43GiB, giữ sàn20GiB.308 đường dẫn được chọn trong preservation baseline khớp SHA, không thiếu/thay đổi trong phạm vi này; đây không phải audit mọi đường dẫn lịch sử hoặc nghiệm thu ENDURE24h. Không sửa PHONE06/source/candidate/ENDURE/canonical SOT. Preview/tab/JVM thuộc lượt kiểm đã dừng, stage/build/unsigned và cache Python do lượt này tạo được dọn; APK và bằng chứng được giữ.

Thứ tự tiếp: kiểm APK trên Xiaomi theo [runbook](../planning/phone07/RUNBOOK.md), xử lý ART/SAF/lifecycle và stall codec/storage; sau gate thiết bị mới thay mock bằng media/camera thật. Chưa đủ căn cứ gọi phần mềm sẵn sàng điều khiển Hera hoặc vượt một sản phẩm thương mại.
