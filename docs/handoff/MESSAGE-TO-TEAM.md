Anh gửi các em bản AERIS ở mốc H10 ngày 02/11/2026:
https://github.com/nclamvn/uav-project/tree/research-handoff-2026-11-02-h10

Các em clone đúng tag, đọc README và PDF trong repo, verify source rồi chạy mock public. Anh giữ bản phát triển private để tiếp tục song song. BOM, dữ liệu khách hàng, raw, candidate và APK anh gửi riêng kèm manifest/checksum; các em giữ chúng ngoài clone public.

Bản này vẫn là engineering alpha, beta chưa đạt. H10 đã sửa đường kết quả lossless và đóng writer, có kiểm Node-Python wire thật bằng mock budget. Lượt forensic Android m801 đã giữ được dữ liệu hiện tại nguyên vẹn; nó không phải G1 hay một chuyến bay được nghiệm thu.

Việc đầu tiên là tiếp nhận đúng trạng thái 83 file/lifetime generation 10, lập contract tiếp tục có đối chiếu độc lập, rồi chạy G1 mới. Không dùng lại decoder 75 file, tự gửi lại APPLY, xóa evidence hoặc khôi phục quyền. Sau đó mới kiểm nhiệm vụ Android-SITL, video/payload, mất link/reboot, SAF và 10 phút bay tích hợp.

Anh mong nhóm chủ động nghiên cứu và báo theo kết quả: tag/commit, cấu hình, lệnh, phần đạt/lỗi/chưa kiểm, raw/SHA và quyết định tiếp theo. Giữ rõ điều đã chứng minh và điều còn là giả thuyết. Các em có thể nhận source để bắt đầu R&D ngay; phần runtime và phần cứng phải giữ gate riêng.
