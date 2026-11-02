# Hiện trạng H10 tại ngày 02/11/2026

**Engineering alpha; beta tích hợp NOT READY.** Cả G1, G2, G3, G4 của BETA-RC01 đều chưa được nghiệm thu. Nguồn H10 đã qua source/mock và QA độc lập; chưa chạy lại seal/normal-close của hành trình G1 Android bằng H10.

## Năng lực sản phẩm đã có trong source

| Nhóm | Phạm vi hiện có | Giới hạn |
|---|---|---|
| Khảo sát | KML, polygon/corridor, compiler, Home/cao độ và QGC semantic | Corpus/SITL theo revision, chưa chứng minh chất lượng ảnh thực |
| Điều khiển | Preflight, geofence/failsafe, manual/assisted/AUTO, thu hồi quyền | Nghiệm thu beta cùng một release còn mở |
| Payload | Discovery/routing camera/gimbal, nhiều payload, dual-operator | Contract/mock/replay; Hera, Phase One, RGB/thermal thực còn gate riêng |
| Video/media | Host source, decoder/clock/FPS, geotag/review, xuất/nhận gói | H10 chưa nghiệm thu nhiệm vụ đồng thời video/payload |
| Hồ sơ | Journal, checkpoint, restart, quota, SAF và receiver | Byte hợp lệ không tự chứng minh recording hoàn chỉnh hoặc nhiệm vụ thành công |
| Giả lập | SITL vòng kín, physics, viewer 3D và âm thanh tổng hợp | Chưa hiệu chuẩn Hera bằng số đo thực, chưa phải digital twin xác thực |
| Android | Native shell/cockpit, bridge/input/storage, APK development và emulator | Chưa nghiệm thu Xiaomi/HeraHub hay radio/MCU/payload thực |

## Bằng chứng mới nhất

H8 m601/m602 và H9 m701/m702 là bốn lượt SDK cold boot đã kiểm thực, dữ liệu private được đối chiếu và SDK đóng bình thường. Chúng là qualification SDK của từng candidate, không phải G1 hoặc chuyến bay.

g104 FAIL trước Activity vì Node không phân giải alias theo graph source. H9 đã sửa loader; g105 đã qua companion READY, đăng ký native và rollover. g105 vẫn FAIL: SEAL_PRODUCT đã có tác động nhưng toàn bộ kết quả COMMAND_COMPLETE vượt progress 4 KiB. Kết quả quá lớn không được lưu đủ, nên không biết chính xác số byte của payload cũ.

H10 sửa chung đường kết quả và đóng writer. **34 phương thức kiểm tập trung đạt trên máy tác giả**, gồm Node client -> Python writer Unix RPC/fsync -> Root reader với metadata budget mock. QA độc lập kiểm source và các ca tập trung. Không cộng các lượt kiểm trùng nhau thành tỷ lệ trưởng thành.

m801 là một lượt emulator thực chỉ đọc. Đã thu đủ raw 250.880 B và SDK đóng bình thường. Đây là forensic capture, không phải SDK qualification hay G1. Root và QA đối chiếu được 83 file/9 thư mục: thêm đúng hai AJ02 và sáu STATUS DTO; các dữ liệu cũ khác giữ nguyên, registry chỉ append.

Registry hiện tại có lifetime generation 10, record 0, hai journal mới đóng/rỗng lưu trực tiếp, tám journal trong archive và không pending. Head cuối được quan sát từ raw m801 mới, không phải ACK cuối đã giữ trước lỗi g105. Không suy ra tính liên tục đường dẫn hoặc chống rollback toàn filesystem.

## Trạng thái bốn cổng

| Cổng | Trạng thái | Cần hoàn tất |
|---|---|---|
| G1 | NOT ACCEPTED | Contract tiếp tục từ 83 file, qualification đúng candidate, hai phiên native và full cold export, seal/ref/normal close |
| G2 | NOT RUN với H10 | Polygon/corridor Android-SITL, upload/readback, manual/AUTO, video/mock payload, review và SAF |
| G3 | NOT RUN với H10 | Mất link, AP reboot, app restart, thu hồi quyền và persistence |
| G4 | NOT RUN | 600 giây bay tích hợp liên tục, chỉ sau các cổng và lượt ngắn đạt |

Raw về GPS/EKF/clock của VIDLIFE12 và runtime máy nhận R2 là lịch sử được giữ riêng. Không dùng kết luận của revision cũ làm kết luận navigation hoặc video của candidate H10. Chưa có benchmark chứng minh vượt DJI, chứng nhận compliance hoặc qualification bay thật.
