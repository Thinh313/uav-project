# Hiện trạng tại ngày bàn giao

## Kết luận

**Engineering alpha; beta tích hợp NOT READY.** Đã có nhiều năng lực source và
bằng chứng theo từng lát cắt. Chưa có một bản phát hành duy nhất được nghiệm thu
trọn AUTO/manual + video/payload + mất link/reboot + persistence/SAF.
Không quy đổi số milestone hoặc LOC thành phần trăm trưởng thành.

| Nhóm | Hiện có | Mức chứng minh cần phân biệt |
|---|---|---|
| Khảo sát và nhiệm vụ | KML/polygon/corridor, compiler, Home/cao độ, QGC semantic | Nhiều corpus và lượt SITL riêng; chưa tự suy ra chất lượng ảnh khảo sát thực |
| Điều khiển | Preflight, geofence/failsafe, AUTO, manual/assisted, thu hồi quyền | Có kết quả theo revision; beta tích hợp hiện tại vẫn chưa đạt |
| Payload/operator | Discovery/routing, camera/gimbal contract, dual-operator | Mock/replay và SITL; chưa nghiệm thu camera/gimbal Hera thực |
| Video/media | Host source, WebCodecs, qualification, geotag/review pipeline | Chưa chốt cold-start/FPS và hành trình tích hợp cuối; ảnh thật chưa được xác nhận |
| Hồ sơ | Journal, checkpoint, restart, SAF, receiver/integrity | Các lớp đã được kiểm từng phần; không suy ra toàn bộ release đã ổn định |
| Giả lập | SITL vòng kín, physics, viewer 3D, replay, âm thanh tổng hợp | Chưa hiệu chuẩn mô hình Hera bằng số đo thực; rain/wind/payload không là digital twin đã xác thực |
| Android | Source shell/cockpit, APK development, emulator workflow | Có kết quả emulator theo cấu hình; chưa nghiệm thu HeraHub hay Xiaomi thực trong mốc này |

## Kết quả VIDLIFE12 mới nhất

- Target ArduPilot 42/1, firmware 4.7.1; GCS 255/190. Chín yêu cầu cadence được ACK
  chấp nhận; quan sát gap sau ACK: heartbeat 271 ms, id 30/id 33 là 64 ms.
- Discovery 39/39 tham số. Client giữ 42 heartbeat khỏe, không có first fault lifecycle.
- Pin 25,148 đến 25,150 V đạt, nhưng cả 95 bản tin EKF có flags 167 (0xA7), thiếu bit 16
  định vị ngang tuyệt đối. AP báo `Fence enabled, need position estimate`.
- Lượt dừng trước video-start/ARM/RC; không có ảnh thực. Root chạy 129,515 giây host,
  AP boot ở 32,59 giây khi kết thúc. Yêu cầu profile 180 giây không phải thời gian đã đạt.
- 39.239 nhóm RX/INTENT/localSEND/STAGE giữ lại khớp nhau; unknown sends 0,
  max atomic 191,990 ms. Hồ sơ incomplete, không được nghiệm thu bay/media.
- R02 chỉ đổi wait khởi tạo navigation 30 lên 60 giây host.11 mock đạt; chưa kiểm thực.
  Candidate mới bị pure gate từ chối: 8.466.432 B dự toán > 8.388.608 B, vượt 77.824 B.

## Thứ tự nghiên cứu tiếp

1. Xác minh cây source và đọc bộ evidence private, tái lập mock trên máy nhận.
2. Chốt ngân sách artifact cho campaign mới theo review; không xóa evidence để vừa cap.
3. Kiểm navigation/EKF cold-start và viewer/video-measure trên lượt ngắn, giữ guard.
4. Chạy 10 phút Android-SITL không can thiệp, đủ AUTO/manual, video/payload,
   mất link, AP reboot, app restart, persistence và receiver SAF.
5. Lặp polygon/corridor và tải host; chỉ chốt beta simulator khi cùng release đạt.
6. Sau đó mới bench controller/input/video và payload thật, HIL rồi flight test.

Mục tiêu GCS cao cấp là hướng sản phẩm. Chưa có benchmark chứng minh vượt DJI,
chưa có chứng nhận tuân thủ hoặc quyền vận hành thực tế từ các test tổng hợp này.
