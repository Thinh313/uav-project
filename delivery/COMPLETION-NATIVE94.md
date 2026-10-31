# COMPLETION — NATIVE94

18/10/2026 · PASS engineering · APK development05. 29 kiểm cuối đạt; R94-1..6 đạt trong phạm vi TIP, không phải phần trăm hoàn thành toàn dự án.

## Kết quả sản phẩm

Android tự chọn file KML qua SAF, đọc đối tượng, lập tuyến polygon/corridor, chỉnh chiều rộng corridor, biên dịch và lưu bằng một model92. Khâu này không cần parser/compiler của laptop hoặc token bridge. Bản nhập phải được local-recompile trước khi xác nhận kích hoạt. Lịch sử review vẫn đọc được khi bridge đã tắt.

SITL vẫn dùng bridge trên host cho transport/control. Kết nối chỉ đọc đòi host biên dịch độc lập và khớp toàn bộ plan đã commit; không thay thế âm thầm bản nhiệm vụ và không tự cấp quyền/upload/arm/AUTO.

## Kiểm chứng

- 126 mock assertions: 60 ca XML/KML đối chiếu Python; 24 cặp toàn bộ plan/hash đối chiếu AUTO63, kèm camera spacing, lineage, sai datum/Home và host attestation. Thuật toán hình học được tái dùng, không gọi đây là chứng minh toán độc lập.
- Android13 ARM64 / WebView101.0.4951.61 / 1280×800: SAF KML → compile offline → save; export/readback → nhập/recompile → xác nhận activation; force-stop và reboot giữ nguyên byte journal/CURRENT.
- Mutant đổi camera206 rồi rehash record/plan/archive đầy đủ: cấu trúc archive được nhận để staging, semantic replay chặn activation. Thế hệ bị từ chối được giữ để audit, không tự dọn. KML có thuộc tính __proto__ bị chặn bằng KML_ATTRIBUTE, workspace không đổi.
- Hai vòng Android–ArduPilot4.7.1 SITL (build04 và cuối05): preflight → upload/readback → Home sau arm → AUTO → mặt đất/disarm → review. Mỗi vòng 12 item,4 camera command,2 readback;0 PARAM_SET,0 ảnh thực. Raw JS và dialect Python upstream đối chiếu CRC/target/item/camera; receiver độc lập nhận gói đóng với receipt. Không xác thực nguồn thương mại từ receipt này.
- Source/candidate/ENDURE và lịch sử trước:62.732 đường dẫn khớp SHA; sandbox Native90–93 không đổi. Dung lượng tối thiểu 32.71GiB, trên sàn20GiB. Tất cả runtime thuộc tác vụ đã đóng, token đã gỡ.

## Artifact cuối

- APK: [aeris-native94-development05.apk](../native/native94/dist/aeris-native94-development05.apk)
- APK SHA256: `27e904cc75a496ee9173a0c03118413cec580b4c842a85735f711d2c2bad8673`
- SourceID: `9485a61a8e24bbc426d96d271e3474bf6a2db6c55158d312b809850d44a0ed6b`
- Development certificate SHA256: `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800` (khóa engineering hiện có, không ký production).
- [VERIFY](../evidence/native94/final-verification.json), [corpus/mock cuối](../evidence/native94/mock05/mock94.json), [lineage](../evidence/native94/compiler-lineage.json), [ADR109](../docs/ADR-109-NATIVE94-OFFLINE-PLANNING.md), [TIP](TIP-NATIVE94.md).

## Sửa lỗi trong quá trình kiểm

Timeout chọn KML trước đây dùng thông báo commit-unknown của writer dù chưa ghi workspace. Bản cuối phân biệt KML_SELECTION_TIMEOUT_NO_COMMIT và chờ tối đa300s, không áp dụng kết quả đến muộn. Positive SAF/negative KML đã kiểm; chưa chờ hết300s theo đồng hồ thực. Rà soát cuối chặn thêm thuộc tính __proto__; build05 chỉ thay đúng KML reader so với04, toàn bộ mã điều khiển và storage giữ nguyên byte. Toàn bộ run/receipt04 được giữ, không ghi đè.

## Giới hạn và gap còn lại

Chưa phải bản điều khiển Hera được nghiệm thu. Native transport bay vẫn qua host trong bài SITL này; chưa có bench HeraHub/HID/radio/video/PhaseOne hoặc payload vật lý và dual-operator thực. Chỉ camera tổng hợp, Home cố định và flat-world minh thị;10–30m,0.5–2m/s,100m,64KiB KML. Không suy từ ca này rằng DEM/địa hình, RTK/PPK thực hay chất lượng bản đồ khách hàng đã đạt. Chưa mở lại ma trận fault giữa upload/readback/commit trên94; giữ nguyên bằng chứng93. Không có ENDURE24h/pacing/thermal/production qualification mới và chưa tích hợp source/candidate đóng băng.

## Dọn dẹp

Đã xóa5 APK unsigned và cache Python thuộc94; .build tự dọn. Không tạo scratch ngoài repository, không copy toàn dự án. Giữ APK ký development01..05, evidence và AVD dùng lại. Docker image prune đã chạy, không prune volume/container.
