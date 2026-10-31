# BETA-STABILITY02 · NOT READY

Cập nhật 2026-10-26T03:13:02.397806+00:00. Phạm vi: Android emulator + ArduPilot SITL, payload/video tổng hợp.

## Kết luận

BETA-STABILITY02 chưa đạt nghiệm thu Beta. Đã triển khai đo từng chặng, sửa các điểm nghẽn và kiểm được các thành phần độc lập; chưa hoàn tất bộ 3 polygon + 3 corridor cùng video/payload trên một bản cố định. Không chọn bản phát hành hoặc ký production.

## Đã thay đổi

Nguồn H.264 tổng hợp chạy bằng VideoToolbox trên host, có đo render/encode/IPC/publish. Network, decode và vẽ canvas được tách sang DedicatedWorker/OffscreenCanvas trên Android. Ghi đầy đủ span có định danh frame/config/session/boot/clock, đối chiếu theo frame thực sự hiển thị; lưu chuỗi hash và đóng/fsync đuôi. Công việc đóng gói/receiver được chuyển khỏi vòng xử lý nóng sang worker có giới hạn. Sửa alias dữ liệu clock, xác nhận prefix bền vững và đồng bộ quota giữa companion với tiến trình con. Gộp block trace tối đa 1.024 dòng để giảm số file; không lược dòng hay viết lại hash.

## Chứng cứ video

Probe nguồn host 360 frame: P95 request→packet 16,199 ms, lớn nhất 74,093 ms; nền tảng báo dùng encoder phần cứng. Đây là nguồn tổng hợp và timestamp trước render, không phải thời điểm phơi sáng camera. Các số trung bình tốt không chứng minh hết giật. Lượt pins04 đạt riêng video nhưng thiếu điều kiện trace. Pins05 có trace hợp lệ nhưng gap 257,861 ms vượt 250 ms. Pins06 có gap chẩn đoán 280,888 ms và hồ sơ gốc bị ngắt do quota; không được nâng lên ca bay đạt. Pins07 yêu cầu prefer-software và nhận lỗi “Unsupported configuration”; decoded/displayed bằng 0. Chỉ cấu hình yêu cầu này không được hỗ trợ ở emulator hiện tại; không suy ra toàn bộ H.264 hay mọi Android đều không hỗ trợ.

## Lỗi vận hành còn mở

Nguồn vẫn sinh/truyền khi viewer không giải mã được. Lượt cuối nhận 1.073.787.066 byte và chạm giới hạn tổng thân truyền 1 GiB: BODY_OR_RUN_BYTE_BOUND. Guard đóng host/emulator, giữ hồ sơ; exit code 0 của tiến trình không phải nghiệm thu thành công. Không tăng giới hạn, tự xóa log hoặc mở lại campaign. Ngưỡng đĩa vẫn 20/10 GiB và 256 MiB dự phòng; không đổi speedup 1, cap 500 ms, ngưỡng FPS/latency/gap.

## Mất link, reboot và quyền

Hai lượt độc lập trên ArduPilot SITL thực đã quan sát aircraft đang bay AUTO, quyền payload mock từ 1 về 0 sau ngắt link hoặc reboot, và hồ sơ gián đoạn không tự khôi phục quyền. Không có video/capture hợp lệ trong hai lượt này; không thay thế được nghiệm thu fault đồng thời với video/payload.

## SAF, persistence và UI

Đã xuất hồ sơ pins05 qua Android SAF, đọc lại 24.191.962 byte khớp từng byte và SHA-256 với gói gốc, rồi kiểm bằng receiver riêng. Kết quả video FAIL trong gói giữ nguyên. Restart tiến trình Android giữ workspace 2.248 byte và 5 review cùng raw head; không tự kích hoạt client hay phục hồi quyền. Bước nhập lại workspace cuối chưa chạy vì host đã đóng. Đã kiểm hình học và xem 10 ảnh: bốn màn hình và modal workspace, cả sáng/tối, trên emulator 1280×800. Còn hai lỗi P2: panel video che một phần nhãn nguồn bản đồ; input file còn giao diện tiếng Anh mặc định. Chưa chứng minh độ mượt chuyển động, ngoài trời hay thiết bị HeraHub.

## Sửa harness và giới hạn bằng chứng

UIAutomator có thể thoát 0 dù không lấy được trạng thái mới, hoặc lỗi AccessibilityNodeInfoDumper. Harness nay chỉ đọc đường dẫn XML duy nhất sau thông báo dump thành công, dùng cây accessibility compressed và giữ toàn bộ lỗi trước đó. Đã tiếp tục một picker đang mở dựa trên quan sát mới, không gửi lại thao tác xuất đã chấp nhận. Không tuyên bố hai chu kỳ hủy/mở picker đã đạt. Kiểm lạnh xác nhận 345,687 event trace được chấp nhận trong 344 block giữ đúng chuỗi/hash và đuôi đã đóng. Đây không phải bằng chứng mọi frame đã sinh đều tới màn hình: viewer pins07 không giải mã được frame nào. Cả 5 gói lưu đều qua receiver ở tiến trình riêng, nhưng receiver tái sử dụng một phần core toán; không phải đối chứng thuật toán hoàn toàn độc lập, không xác thực nguồn vật lý. Payload, JPEG và thermal-look là tổng hợp; ảnh camera thật bằng 0, không đo nhiệt, không đo photon/exposure, decoder backend chưa biết.

## Bảo toàn và tài nguyên

Đối chiếu không drift: 17,117 identity legacy, 4,269 mục tiền nhiệm, 1,063 file thực thi; bản sao revision05/06 khớp byte. Các tập này chồng lấp, không cộng thành số file độc nhất. 165 đường dẫn thiếu từ trước giữ nguyên; không phục hồi trong task này, không tuyên bố hiện diện liên tục hay ENDURE 24 giờ đạt. Dùng 5/12 AP, 7/8 host; giữ mọi container và bằng chứng lỗi. Đã dọn cache build Android, cache Swift khoảng 48 MiB và __pycache__ riêng. Docker image prune thu hồi 0 B, không xóa container/volume hay dữ liệu khác; không cài dependency/SDK mới, không sao chép cả dự án vào thư mục tạm.

## Bước tiếp theo

VIDEO-CAPABILITY-LIFECYCLE: (1) thương lượng isConfigSupported cho đúng codec/config trong worker trước khi chạy nguồn liên tục; cấu hình thay thế phải có profile và chứng cứ riêng; (2) nguồn tạm dừng rõ ràng khi viewer không hợp lệ, giữ đầy đủ bộ đếm, frame đã sinh, clock và hồ sơ chuyển trạng thái, không giấu drop; (3) kiểm riêng video dưới tải và xác định decode/presentation jitter, đánh giá đường Android MediaCodec nếu WebView không đáp ứng. Chỉ sau khi đạt ngưỡng video mới khóa một bản để chạy lại đủ 3 polygon + 3 corridor, fault đồng thời và SAF. Không dùng thêm lượt bay để tìm kết quả may mắn.

## Đối chiếu các lượt thực

| Build | FPS | P95 upper (ms) | Gap max (ms) | Kết luận |
| --- | --- | --- | --- | --- |
| pins04 | 29,928 | 74,970 | 204,769 | Video đạt riêng; điều kiện trace chưa đạt |
| pins05 | 29,865 | 56,888 | 257,861 | FAIL gap; trace khoảng đo đạt |
| pins06 | 29,993 | 52,942 | 280,888 | Chẩn đoán; hồ sơ gốc FAIL quota |
| pins07 | 0 | Không có | Không có | Cấu hình decoder không hỗ trợ; 0/6 |

## Hồ sơ đối chiếu

- [Nghiệm thu máy đọc](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/acceptance.json>)
- [Đối chiếu nguồn đóng băng](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/preservation-final-final07.json>)
- [Trace lạnh đầy đủ](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/full-trace-cold-verification07.json>)
- [Receiver tất cả hồ sơ](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/receiver-history-final07.json>)
- [SAF raw](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/saf-raw-verification07.json>)
- [Persistence Android](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/workspace-restart-verification07.json>)
- [QA ảnh UI](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/android-visual-review07.json>)
- [Tổng hợp lượt chạy và ngân sách](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/evidence-summary-final07.json>)
- [Lỗi đóng host cuối](</Users/os/Downloads/AI technique/aeris/evidence/betastability02/final-evidence-addendum07.json>)
- [TIP và giới hạn đã chốt](</Users/os/Downloads/AI technique/aeris/planning/betastability02/TIP.md>)
