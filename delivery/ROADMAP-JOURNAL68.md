# JOURNAL68 — phần bổ sung roadmap

16/10/2026. Overlay mới; không sửa canonical SOT hay roadmap đóng băng.

Đã đóng gate host/mock: journal intent/outcome, fsync, catalog/source binding, replay lịch sử DUAL67 sau crash hoặc restart sạch, quyền luôn rỗng, quota không tự xóa, UI tách lịch sử và quyền hiện tại. Chứng cứ: COMPLETION-JOURNAL68.md và evidence/journal68/final-verification.json.

Thứ tự tiếp theo:

1. Kiểm persistence trên Android/emulator khi có ngân sách dung lượng; sau đó kiểm mất điện và storage HeraHub thực. Kiểm process crash host chưa thay cho các gate này.
2. Xác thực hai operator và enforce quyền ở phía nhận transport thật; kiểm mất phiên, reboot, ACK sai mục tiêu và fencing trước khi nối hardware. Mock không xác nhận quyền trên thiết bị.
3. Retention/archive/quota có duyệt và kiểm nhập lại; tuyệt đối không tự thu hồi bằng chứng. Thử storage đầy, lỗi IO dài hạn và schema migration có khả năng quay lui.
4. Nếu yêu cầu chống rollback hoặc provenance đối kháng: thiết kế anchor/replica ngoài store và quản lý khóa; không dùng SHA chain nội bộ làm thay thế chữ ký hoặc anchor.

Các gate ENDURE, AUTO63, SDK/HeraHub, ký/phát hành và tích hợp source/candidate giữ nguyên. JOURNAL68 chưa mở bất kỳ gate vận hành bay thật nào.
