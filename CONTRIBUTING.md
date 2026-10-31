# Làm việc trên bản chuyển giao

- Tạo nhánh `research/<chủ-đề>` từ tag bàn giao. Mỗi PR giải quyết một outcome
  kiểm được; ghi source/profile/platform, ca đã chạy, ca chưa chạy và log liên quan.
- Đọc `AGENTS.md`, README và status hiện tại trước khi chạy script. Script dưới
  `planning/` có thể tạo evidence, mở Android hoặc gửi lệnh trong SITL; không chạy
  tất cả harness chỉ vì chúng có tên test.
- Tách sửa source, mock và kiểm thực. Không mô tả ACK là thực thi, ảnh tổng hợp là
  ảnh camera hay một prefix journal là bản ghi đã đóng đủ.
- Giữ source/candidate/ENDURE lịch sử nguyên byte. Sửa trong namespace thử mới,
  định danh đúng dependency và tạo gate mới sau review. Không dùng một chữ PASS
  trong báo cáo cũ để cấp quyền cho cấu hình mới.
- Giữ freshness250ms và guard của profile hiện hành. Thay đổi policy là quyết
  định được review riêng, không phải cách làm test xanh. Ghi budget artifact,
  metadata, disk và shutdown reserve trước khi mở actor.
- Không commit BOM, dữ liệu khách hàng, khóa ký, token, APK, VM image hoặc raw
  private. Giữ giấy phép thành phần bên thứ ba. Một PR không tự cấp quyền bay thật.
- CI hiện chỉ kiểm source/mock trên Linux. Android, đồ họa, video, HIL và máy bay
  thật có ma trận nghiệm thu riêng.
