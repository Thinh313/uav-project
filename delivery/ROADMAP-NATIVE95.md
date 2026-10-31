# ROADMAP sau NATIVE95

18/10/2026. Android direct MAVLink → AP4.7.1 internal-quad SITL đã qua E2E với APK development03; không còn GCS/control HTTP bridge host. Chưa nghiệm thu Hera thật.

1. P1 — NATIVE96: fault ngay trên APK direct: disconnect/reboot/Android lifecycle/kill ở ranh giới upload, readback, arm/Home và AUTO; bảo toàn unknown outcome, không retry/reconnect/regrant/resume. Observer nguồn khác chỉ đọc. Xuất raw native qua SAF, độc lập verify/receipt, restart ở bên nhận. Sửa diagnostic generations và quota UTF-8 đúng byte; không tự xóa bằng chứng.
2. P1 — Contract payload và quyền vào native: PhaseOne discovery/settings/capture correlation, gimbal/camera routing nhiều target, hai operator và thu hồi quyền khi mất link. Giữ unknown cho thiếu SDK/hardware; mock không thành bench PASS.
3. Hardware gate — HeraHub MCU/HID/calibration/deadman/radio/video, model/firmware/SDK payload cụ thể, bench props-off rồi HIL và flight có quy trình. Đây là phụ thuộc còn thiếu để thay Ragas trên Hera.
4. Qualification — field survey/corridor/DEM/RTK/PPK, geometry/customer quality, resource/pacing/thermal/24h trên cấu hình triển khai; release trust/signing/rollout được nghiệm thu trước khi tích hợp candidate hoặc ký production.

Không dùng số milestone làm tỷ lệ hoàn thành thương mại. Ưu tiên luồng native bay và payload có chứng cứ, tránh tăng thêm nhánh mock rời rạc. Giữ source/candidate/ENDURE và sàn20GiB cho các bước tiếp theo.
