# ARCHIVE69 — roadmap overlay

16/10/2026. Không sửa canonical SOT, source/candidate hoặc roadmap đóng băng.

Đã triển khai lưu trữ các snapshot-generation JOURNAL68 trong module cô lập: export có hash, receiver kiểm byte+catalog+semantic, quota có reserve, exact confirmation trước cleanup hot và HOLD sau interruption. Original68, ENDURE, exports, receiver và audit được giữ. Không còn yêu cầu SDK để kiểm luồng mock này.

Ưu tiên tiếp theo:

1. Thiết kế rotation live68 có closure/generation marker và migration có rollback; phải nghiệm thu riêng trước khi cho live runtime chuyển thế hệ. ARCHIVE69 hiện không giảm quota live68.
2. Nhập gói trên máy nhận/ổ độc lập với danh tính tin cậy, kiểm offline và chính sách custody. Hiện receiver chỉ là namespace riêng trên cùng host; checksum chưa là chữ ký hay anchor ngoài host.
3. Kiểm disk-full/IO/storage Android và mất điện vật lý sau khi đủ headroom; định cỡ quota/retention thật theo thời lượng nhiệm vụ. Không dùng test SIGKILL làm thay thế powercut.
4. Tích hợp native cockpit có gate firmware/hardware, xác thực hai operator và enforce quyền ở bên nhận. Review/archive tuyệt đối không cấp lại quyền hoặc tự retry lệnh pending.

ENDURE/AUTO/SDK/ký/phát hành vẫn có các gate trước đây, không mở gate từ archive mock. Đối chiếu COMPLETION-ARCHIVE69.md và evidence/archive69/final-verification.json để biết những phép kiểm thực sự đã chạy.
