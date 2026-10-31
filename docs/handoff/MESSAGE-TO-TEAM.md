Anh gửi các em bản source AERIS để tiếp nhận và tiếp tục nghiên cứu:
https://github.com/nclamvn/uav-project/tree/research-runtime-2026-10-31-r2

Các em đọc README và PDF chuyển giao trong repo trước, clone đúng tag rồi chạy
bộ source/mock. Công cụ runtime máy nhận, contract mẫu và checklist đã có sẵn.
Anh gửi kèm riêng gói private và supplement; BOM, dữ liệu khách hàng và raw log
không đưa lên Git public.

Bản này đã chạy được Android–ArduPilot SITL tới connect và đọc đủ 39/39 tham số,
nhưng beta chưa đạt: EKF chưa có vị trí ngang tuyệt đối nên preflight dừng đúng
guard. Chưa ARM/AUTO hay nghiệm thu video. Các em ưu tiên tái lập và chẩn đoán
GPS/Home/clock/EKF từ raw trước, rồi hoàn thiện hành trình nhiệm vụ và receiver.
Giữ source/profile/SHA, đủ frame và bằng chứng; báo rõ phần đạt, lỗi và chưa kiểm.
Anh giữ repo phát triển riêng để tiếp tục làm song song với nhóm.
