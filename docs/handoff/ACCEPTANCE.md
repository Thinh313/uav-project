# Biên bản tiếp nhận tại mốc H10

Anh đề nghị các em ghi kết quả theo từng mục. Nhận source đầy đủ và chạy được một mock không đồng nghĩa đã nhận một beta đủ điều kiện bay.

## Source và tài liệu

- Ghi repo, tag và commit thực nhận; giữ tag H10 và các tag lịch sử.
- Verify danh sách source SHA/kind; ghi rõ kiểm không bao trùm file lạ ngoài manifest.
- Chạy mock public đúng README, lưu version Node/Python, command và stdout/stderr.
- Đọc trạng thái G1-G4 và các giới hạn source/mock, replay, SDK, SITL, hardware.
- Đối chiếu license, attribution, symlink và các nhãn đã ẩn danh.

## Gói private

- Nhận checksum ngoài gói qua kênh tin cậy; kiểm gói gốc và supplement H10 theo manifest.
- Giữ BOM/context/raw ngoài clone public; không thêm remote public vào workspace private.
- Ghi artifact, raw, image, APK, SDK/AVD nào đã nhận hoặc còn thiếu.
- Đối chiếu SHA byte, mode/hardlink và declared archive members theo công cụ được cung cấp.
- Không coi checksum ở trong chính archive là xác thực người gửi.

## Trạng thái hiện tại

- Đã đọc m801 forensic-only và không đổi nó thành SDK qualification/G1.
- Phân biệt head registry mới quan sát với anchor tổ tiên và antirollback toàn filesystem.
- Không dùng decoder 75 file cho trạng thái 83 file/lifetime generation 10.
- Giữ g103 APPLY, g104 và g105 cùng kết luận lịch sử, không tự retry hoặc reset.
- Ghi rõ G1-G4 chưa được nghiệm thu, không ký nhãn beta simulator hay hardware release.

## Mẫu báo cáo một lượt

Mục tiêu; source/tag/commit; APK/AP/profile SHA; OS/CPU/RAM/Node/Python/Android/WebView; lệnh và argv; thời gian host/AP/clock domain; pass/fail/chưa kiểm; primary cause; secondary cleanup; raw/manifest SHA; frame continuity; authority sau mất link/restart; SAF/receiver; reviewer và quyết định tiếp theo.

Nếu thiếu SDK/artifact hoặc admission từ chối, ghi “đã nhận source, runtime chưa kiểm” cùng nguyên nhân. Khi lỗi, giữ bằng chứng, không dừng phiên khác hay xóa lock để chạy lại. Người tiếp nhận, người kiểm kỹ thuật và người quyết định release là các vai trò riêng.
