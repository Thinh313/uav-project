# ROADMAP sau NATIVE94

18/10/2026. Đã gỡ phụ thuộc laptop cho inspect/compile/import semantic của khâu lập nhiệm vụ Android. Hai E2E nominal trên SITL được nghiệm thu engineering; chưa thay Ragas trên Hera thực.

1. P1 — Native MAVLink transport trực tiếp Android → owned ArduPilot SITL: bỏ bridge điều khiển host, discovery firmware/typed parameters/freshness chỉ đọc trước; tiếp đó preflight, explicit grant, upload/readback, Home sau arm và AUTO/review. Giữ một model và authority volatile, không tự nối lại hoặc resume.
2. P1 — Fault tại ranh giới upload/readback/commit: mất link/reboot/sai boot–session–HEAD, unknown outcome, journal pending; kiểm no auto retry/regrant/resume. Corpus khách hàng và toán–địa lý độc lập về corridor/coverage/ảnh/thời gian trước mở rộng envelope bay.
3. Bench khi có thiết bị/API — HeraHub MCU/HID/calibration/deadman/radio/video; PhaseOne/gimbal và nhiều payload; hai operator thật. Chuẩn bị contract đã có nhưng không suy mock thành tích hợp thực.
4. Gate triển khai — thermal/resource/performance/pacing/24h, đóng gói và ký production, tích hợp candidate có kiểm soát; không mở khóa source/candidate/ENDURE trong94.

Trọng tâm: nối hoàn chỉnh lõi native tới autopilot, sau đó bench phần cứng; không mở thêm nhánh mock để thay cho hai gap này. Không đưa tỷ lệ hoàn thành toàn dự án khi chưa có ma trận nghiệm thu phần cứng và triển khai.
