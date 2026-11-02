# Anh gửi các em: bản bàn giao H10

Anh gửi các em mã nguồn AERIS ở mốc H10 ngày 02/11/2026 để tiếp nhận và tiếp tục nghiên cứu. Anh giữ bản phát triển riêng tại repo private `nclamvn/aeris`; các em làm việc tại repo public `nclamvn/uav-project`. Hai repo có lịch sử độc lập và các tag cũ được giữ nguyên.

Mốc các em nhận là `research-handoff-2026-11-02-h10`. Bản gốc tương ứng dùng tag `development-handoff-2026-11-02-h10`. Đây là bàn giao nghiên cứu, **beta tích hợp NOT READY**. Anh không muốn các em hiểu một bộ mock xanh là một bản cài đã đủ điều kiện vận hành drone thật.

## Điều anh muốn nhóm làm được ngay

Các em clone đúng tag, kiểm manifest, chạy đường mock public được nêu trong README và ghi môi trường thực tế. Sau đó đọc trạng thái H10, phân biệt source/mock, replay, SDK/emulator thực và bay SITL. Bộ private nhận riêng giúp đọc lại raw và artifact; nó không thay việc intake máy nhận.

Nhóm ưu tiên một hành trình sản phẩm: lập nhiệm vụ -> preflight -> Fly cùng video/payload -> mất link/reboot -> review -> SAF/receiver. Trước mắt phải nối lại đúng trạng thái dữ liệu sau g105. Không dùng lại decoder 75 file khi native đã có 83 file và lifetime generation 10.

## Cách anh muốn các em phát triển

Giữ một cấu hình source/APK/profile có định danh rõ. Khi lỗi, đọc raw và kiểm giả thuyết bằng ca nhỏ trước khi sửa. Với lỗi lặp lại, sửa ranh giới pipeline và vòng đời thay vì chỉ tăng timeout. Không bỏ frame, reset counter, xóa evidence hay đổi guard để đạt một nhãn PASS.

Anh muốn nhận báo cáo ngắn theo kết quả: tag/commit nào, máy nào, lệnh nào, phần pass/fail/chưa chạy, raw và SHA ở đâu, điều gì đã chứng minh và điều gì còn là giả thuyết. Một kết quả NOT READY có bằng chứng vẫn hữu ích; một chữ DONE thiếu bằng chứng thì không.

BOM, tài liệu khách hàng, khóa và raw không đưa vào issue/PR public. Bản gốc của dữ liệu riêng được giữ trong gói kiểm soát truy cập. Các em chủ động đề xuất đơn giản hóa, nhưng chốt thay đổi về quyền, dữ liệu, an toàn, ngân sách hoặc phát hành trước khi áp dụng.
