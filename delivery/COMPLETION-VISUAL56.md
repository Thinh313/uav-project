# VISUAL56 · Bàn giao nâng cấp hình ảnh

15/10/2026. Preview: http://127.0.0.1:8808/. Module độc lập pilot/visual56; server đang phục vụ loopback. Không thay renderer53/physics, source/candidate đóng băng, SOT/trust/ENDURE. Không chạy SITL mới, build APK hay ký mới.

Đã thay hình học UAV đơn giản bằng CesiumDrone GLB của EdMackey/AGI, CC BY4.0; model gốc giữ byte và attribution. Runtime đổi sang graphite PBR, phản xạ HDRI, bóng đổ/SSAO, ACES và sRGB. Môi trường dùng ảnh chụp panorama8K, HDRI2K và asphalt PBR. UI trắng/graphite, vàng phụ, cảnh làm chủ thể; orbit/zoom, camera preset, timeline, phát/dừng, chọn bản ghi và xuất ảnh PNG. Camera tự lùi trên màn hình hẹp để không cắt cánh. Nút phát/dừng đã đồng bộ nhãn khi seek/restart/load/end.

Hai bản ghi bay SITL thật đã giữ từ SIMTRAIN53 cung cấp pose/RPM, gồm tải giữa/lặng gió và tải lệch/gió giật. Kiểm CRC/SHA-chain khi trích; WAL1200Hz không đổi; bản render lấy30Hz rồi nội suy. NED chuyển sang scene[E,-D,-N]. Ảnh render không phải media camera, ACK hay bằng chứng thực thi ngoài đời.

## Kiểm chứng

- 80 kiểm local: SHA asset/derivative, GLB/license/embedded texture, SHA hai WAL và replay, thời gian tăng, quaternion, syntax, budget và dung lượng;0 lỗi.
- Browser CUA kiểm1920×1080,390×844 và857×988; xem ảnh render thật, camera/play-pause/restart/chọn nguồn/xuất PNG. Lượt cuối không console error/warning. Đã reset viewport override. Không có reviewer độc lập.
- Mẫu120 frame ở1920×1080 trên Apple M1Max: median8,30ms, p95 9,10ms; chỉ là mẫu ngắn tại host, không cam kết fps trên tay cầm/máy chiếu.
-5 kiểm HTTP đạt: trang local, không có route lệnh bay, guard export origin/PNG, chặn traversal. Asset chạy local với CSP self.
-20.935 fingerprint bảo vệ trước/sau:0 lệch/thiếu; là đối chiếu từng thời điểm, không chứng minh hiện diện liên tục hay nghiệm thu ENDURE. Cuối kiểm còn38.502.400.000byte, trên sàn20GiB. Asset chính24.132.795byte, dưới100MiB.

## Phạm vi và phần tiếp theo

Đây là bản nâng cấp hình ảnh/replay có thể xem ngay. Model5844triangle, span minh họa1,03m, chưa phải high-poly scan/Hera calibrated; nền ảnh không có geometry địa hình đầy đủ. Chưa nối renderer mới vào điều khiển live/SITL, chưa thêm thời tiết/âm thanh mới. Không gọi chất lượng này là photoreal tối đa hoặc nghiệm thu đào tạo. Bước tiếp sau đánh giá hình ảnh: chọn/duyệt hero model chi tiết hơn nếu cần, rồi ghép read-only renderer với telemetry live của module mô phỏng qua adapter riêng, đo input-to-photon và độ liên tục frame; giữ đúng physics.

Hồ sơ: evidence/visual56/{verification,browser-qa,http-qa,preservation-before,preservation-final}.json; nguồn/license trong credits.html và receipt acquisition. Ảnh thực từ renderer: render-1792050525480-1.png (1920canvas) và render-1792051676380-2.png. Không tạo scratch/dependency ngoài repo, không xóa bằng chứng hoặc dữ liệu người dùng.
