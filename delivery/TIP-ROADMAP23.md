# ROADMAP23 · Rà soát khoảng trống và thứ tự ưu tiên

Ủy quyền: người dùng ngày 13/10/2026 yêu cầu rà soát khả năng thay RAGAS trên Hera nhiều payload, cập nhật ưu tiên và giữ nguyên soak/candidate. Đây là công việc tài liệu; không triển khai adapter, phát hành, chạy lại SITL hay đổi lịch heartbeat trong lượt này.

Đầu ra: `docs/RAGAS-REPLACEMENT-GAPS-20261013.md`, `docs/ROADMAP-PRIORITIES-20261013.md`, receipt tại `evidence/roadmap23`, completion report. Tài liệu ưu tiên mới bổ sung cho roadmap lịch sử đang fingerprint; không ghi đè `docs/ROADMAP.md`, PAYLOAD21, PROTOCOL22, SOT hoặc TIP tích hợp đã được duyệt.

| AC | Điều kiện kiểm |
|---|---|
| R23-01 | Khoảng trống có bằng chứng hiện tại, phạm vi còn thiếu và tiêu chí đóng; tách host/SITL/corpus khỏi hardware/A/B. |
| R23-02 | Ưu tiên trước/sau, phụ thuộc, vai trò chủ trì, việc dời và các gate thay thế được ghi rõ; không bịa tiến độ phần trăm/ngày/capacity. |
| R23-03 | ENDURE20 và PROTOCOL22 Fly vẫn đúng gate đã duyệt; các đề xuất tiếp theo không trở thành quyền triển khai/phát hành tự động. |
| R23-04 | Hash nguồn gốc/candidate/slot/controller/PAYLOAD21/PROTOCOL22/SOT giữ nguyên trước–sau; PID/lock/manifest/trạng thái live được kiểm chỉ đọc. |
| R23-05 | Tài liệu ngoài có URL/thời điểm/raw/hash, link nội bộ tồn tại; failed probes và giới hạn kiểm được lưu. |

Một agent tách bước rà soát → soạn → đối chiếu; không phải audit độc lập. Các ngưỡng tài nguyên/video/flight/A/B thực cần được chốt trong TIP của increment tương ứng trước thu thập kết quả. Không cần hỏi lại về SDK đã được xác nhận chưa có.
