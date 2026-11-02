# NAVFIX13: đã chạy Android–ArduPilot, beta chưa đạt

**PARTIAL / NOT READY.** Báo cáo này cập nhật trạng thái sau khi anh cho phép artifact 9 MiB. Các biên bản cũ giữ nguyên, kể cả báo cáo trước đó đang chờ phê duyệt.

## Kết quả dùng được

Đã đồng bộ trần artifact mới 9 MiB ở candidate, preview, guardian, HostHealth và monitor, vẫn tính đủ sáu pool cũ. Tổng thực 8.876.032/9.437.184B. Dự toán artifact tăng đúng 1 MiB; trần metadata 64 MiB, floor 10 GiB, reserve 256 MiB và mọi freshness/physics/authority guard khác giữ nguyên.

Đã sửa chuyển tiếp cấu hình: guardian nhận đúng spec được chọn, có kiểm SHA trước khởi chạy và giữ pin AVD index. Bản thân spec/cache/AVD không reset hoặc sửa cấu hình.

Đã xử lý thận trọng trường hợp mất phản hồi `adb root`: không gửi lại root, không biến receipt thất bại thành thành công. Chỉ trường hợp lỗi/capture/argv/ref chính xác mới được quan sát chỉ đọc; phải thấy UID0 và cùng kernel boot UUID trong deadline 30 s cũ. 24 ca mock mục tiêu đạt; 6 budget, 5 spec và 23 probe/disposal regression đạt. Policy 27 và wire 5 không đổi, đã kiểm trước và giữ đúng SHA. S02 chứng minh đường bình thường rootexit0, UID2000→0/cùngboot; **nhánh mất phản hồi chỉ mới kiểm mock**, chưa được nghiệm thu live.

## Hai lượt thực tế

| Lượt | Kết quả | Giới hạn bằng chứng |
|---|---|---|
| S01,41,08s host | Android boot; rootRPC đóng kết nối, exit1; giữ nguyên log | Chưa cài/kiểm APK, chưa companion/AP; UID sau root không quan sát được |
| S02,93,70s host | UID0/cùngboot đạt; APK, companion, ArduPilot thực chạy; khảo sát/compile/lưu đã đi qua | Guard HostHealth 100 ms dừng tại UI trước consent/connect, chưa tới preflight |

Không chạy lại S01, không reset slot/lock/quota, không chạy lượt thứ ba. Không ARM, RC manual hoặc AUTO. Không có ảnh/video thật, không có APK/chữ ký mới.

## Blocker hiện tại: độ trễ host, chưa phải bằng chứng GPS sai

Nonce, 95 byte request và PID client/guardian khớp trong raw IPC. Từ lúc client gửi xong đến khi server bắt đầu ghi trace mất 119,693 ms, đã vượt guard 100 ms. Xử lý sau entry đến sendend chỉ 0,596 ms; server sendall xong ở 120,391 ms tính từ clientbegin. Client không nhận byte phản hồi nào. `sendall` thành công không chứng minh bên nhận đã nhận/chấp nhận.

Request server trước đó chỉ 0,440 ms. Trong tail giữ lại không có request dài giải thích hàng đợi. Có span `pmset` Popen 234,912 ms, 2,15 ms threadCPU và toàn query 349,060 ms chồng khoảng lỗi trong cùng guardian. Đây là tương quan đã đo, **chưa chứng minh OS/GIL/spawn là nguyên nhân**. Không có interval inventory guardian giữ lại chồng thời điểm lỗi; không quy sai cho việc parse lại 92 module.

Có lỗi phụ khi đóng monitor: `IPC10_FROZEN_NO_NEW_ACCEPTANCE`. Nó giữ trạng thái từ chối sau lỗi IPC đầu tiên; không được xóa latch để tạo closure PASS. Các tiến trình/container thuộc lượt đã thoát và cổng đã đóng, nhưng không tuyên bố monitor/recording đã đóng hợp lệ như nhiệm vụ hoàn thành.

## GPS/Home/clock và tính toàn vẹn

Raw trước đây xác nhận GPS/Home nhất quán, 37.279 frame và EKF flags167 thiếu vị trí ngang tuyệt đối; không có căn cứ ép tọa độ/Home hay tắt kiểm EKF. Modelclock khi đó tăng đúng nhưng tiến độ chỉ khoảng 0,65× host; thời gian owner bao gồm startup không là thời gian EKF hội tụ.

S02 mới giữ khớp 12.838 nhóm RX/INTENT/SENT/STAGE, unknown-send 0; 54 heartbeat quan sát đều disarmed. Atomic clock age lớn nhất 145,913 ms, dưới 250 ms. Recording là INCOMPLETE_RECORDING; AP-stage là COMPLETE_BYTES_UNATTESTED, không chứng minh execution. Lượt dừng trước b-connect nên **chưa kiểm được EKF/preflight mới**, không kết luận nguyên nhân gyro-bias/delayed-GPS.

## Bảo toàn và storage

Source/candidate cũ, ENDURE, repo public và hai gói bàn giao private giữ nguyên byte. 3.870 entry files và 2.307 file thuộc sáu pool được kiểm theo hai phạm vi riêng, không cộng thành tổng duy nhất. Hai case mới giữ 36 và 122 file theo baseline sau đóng. Hai candidate chẩn đoán mới được nạp/kiểm trong process tươi, không thay release/trust selection hay ký mới. 98 đường dẫn thiếu từ trước trên checkout gốc không phục hồi hoặc stage thành deletion.

Đã dùng nén filesystem trong suốt của macOS cho QA, metadata và một số bản sao working copy mới: path, byte/SHA, mode/mtime không đổi; inode/flags/physical allocation có thể đổi và đã ghi receipt. Candidate thực thi/oldsource/rawcase không nén hoặc sửa. Inventory nguyên bản vẫn tính mọi file bằng allocation thực, df/forecast vẫn theo filesystem thật; không loại dữ liệu khỏi domain hay tăng cap 64 MiB. Mọi fixture tạm đã dọn; không có copy cả dự án trong/tmp. Docker image prune thu hồi 0 B; không prune container/volume.

## Bước kiến trúc hợp lý tiếp theo

Kiểm A/B việc cô lập thao tác spawn/đọc power khỏi đường phục vụ guardian/owner 100 ms, bằng mock/fault injection và raw đang giữ; đồng thời sửa cơ chế đóng monitor khi đã fault để drain bằng chứng thất bại mà không hỏi lại authority đã frozen. Giữ 100 ms và mọi guard, không dùng cache cũ như dữ liệu mới. Đây là hướng cần kiểm chứng, **chưa triển khai hoặc nghiệm thu** trong lượt này. Sau đó mới mở probe disarmed mới để đo chuyển trạng thái EKF rồi xét workflow nhiệm vụ đầy đủ. Chưa mở kiểm 10 phút hoặc tuyên bố beta stable.

Bằng chứng có SHA và trạng thái từng yêu cầu trong COMPLETION-NAVFIX13-REV03.json cùng thư mục.
