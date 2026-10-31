# RUNTIME-REPAIR03: nguồn/mock đạt, runtime chưa nghiệm thu

**Trạng thái tổng thể: NOT READY.** Đã hoàn tất phần sửa và kiểm nguồn/mock trong phạm vi cho phép khi nguồn điện chưa đủ. Chưa chạy emulator, ADB hay Android–SITL trong lượt này.

## Đã thay đổi

Bản cô lập giữ 65 file nguồn, chỉ sửa 4 file: factory, supervisor, resources và telemetry. Một đường xử lý lỗi chung nay bao phủ lỗi lúc chuẩn bị, sau READY và khi hoàn tất nhiệm vụ; giữ nguyên lỗi gốc và phân biệt lỗi dọn dẹp thứ cấp.

Trước khi đóng AP trong trường hợp chưa kết nối native, runtime dùng cơ chế cắt ingress một chiều hiện có. Nó kiểm chuỗi raw đã fsync của request → accepted → closed, nonce và ngữ cảnh; từ chối nếu từng có kết nối/dữ liệu/pending native, có CONNECT đang chờ, trạng thái không rõ hoặc bằng chứng không còn mới. Chỉ sau bằng chứng ground CRC và prefix phù hợp mới dừng AP rồi backend. Observer tiếp tục hoạt động trong lúc đóng; không giữ khóa đọc raw trong thời gian chờ tiến trình.

Nếu AP/backend đã được đóng đúng quy trình trước khi lỗi review xuất hiện, runtime tái dùng đúng receipt đã xác minh, không gửi stop lần nữa và không biến lỗi thành nhiệm vụ thành công. Với connected/armed/unknown, đường dọn dẹp tự động vẫn bị chặn; đây không phải chứng nhận khôi phục drone đang bay hoặc giữ quyền qua khi client chết.

## Kiểm chứng

| Phạm vi | Kết quả |
|---|---|
| Mock của Builder cho xử lý lỗi | 40 ca đạt |
| Mock đóng tiến trình đã hoàn tất | 6 ca đạt |
| Kiểm độc lập trên phương thức runtime hiện tại | 23 ca đạt |
| Diagnostic STATUS-only | 7 kịch bản và 15 kiểm ranh giới của Builder đạt |
| Kiểm độc lập diagnostic | 13 ca đạt |
| Cú pháp Python | 63 file đạt; 65 file nguồn được đối chiếu |
| Snapshot và packet | 65 nguồn đóng băng, 144 pin khớp; dưới ngân sách artifact 4 MiB |
| Android–SITL / nhiệm vụ bay thực trong giả lập | NOT RUN |

Các con số trên thuộc các phạm vi khác nhau, không cộng thành tỷ lệ trưởng thành hay chứng nhận sản phẩm. Mock có raw CRC tổng hợp và fsync thật; NativeBridge, tín hiệu tiến trình và thiết bị trong các ca này là mô phỏng, không phải bằng chứng thiết bị mới.

## Accessibility còn phải đo

Nguyên nhân WebView mất node sau READY vẫn **UNRESOLVED**, chưa có bản sửa native được chứng minh. Đã chuẩn bị công cụ chỉ gửi một STATUS, khóa đúng emulator-5582, kiểm PID/nguồn/guardian/quyền và giới hạn dữ liệu. Nó chụp AX, PNG, trạng thái accessibility, focus và phiên bản WebView trước/sau truy vấn. Công cụ không tạo BOOTSTRAP/provider, không chạm điều khiển, không cài/xóa dữ liệu và không dùng tọa độ hay JavaScript để lách điều kiện.

Packet đã gắn với snapshot nguồn cuối và kiểm đủ 144 pin, nhưng chưa thực thi. READY render không được coi là bằng chứng nút actionable.

## Bảo toàn và giới hạn

Giữ nguyên APK development `43318d48…5961`, Native50 và chữ ký cũ; không build hay ký mới. Kiểm cuối đối chiếu 17.117 mục lịch sử, 28 manifest niêm phong gồm handoff 848 file của lượt trước, 838 pin nguồn/metadata và Native50: không có drift mới. 165 đường dẫn thiếu từ trước được tách riêng. Không phục hồi file mới trong lượt này và không khẳng định các đường dẫn hiện diện liên tục. Không sửa lịch sử ENDURE hay suy ra ENDURE đã đạt.

Freshness 250 ms, input 200 ms, speedup 1, cap 500 ms, fsync trước sensor, không bỏ frame, sàn 10 GiB và dự phòng 256 MiB được giữ nguyên. Không tạo đồng hồ campaign hay cộng thời gian cũ.

Ghi chú audit: một số mock đầu đã bị cập nhật tại cùng đường dẫn trước khi chốt quy tắc bằng chứng. Checkpoint đầu được giữ nhưng không khẳng định còn đủ byte của các mock đó. Bản final06 và các receipt QA được giữ bất biến, có SHA; không tái tạo lịch sử để che khoảng trống này.

## Bước kế tiếp

Khi admission nguồn điện đạt: chạy phép đo STATUS-only không AP, xác định lỗi ở ranh giới Activity/Intent/accessibility hay sau bootstrap, rồi sửa đúng nguyên nhân. Sau kiểm độc lập mới thử lỗi preowner với AP thật trong SITL và chạy trọn lượt ngắn manual/assisted → LAND → review → restart. Chưa mở lượt 30 phút và chưa thêm tính năng.

Snapshot nguồn: `d56da2d8288d92c5d7fa7acd0a00071a53ad7b03ef4d65b2aa8020b9a58e49e0`.

[Root verification](../evidence/runtime-repair03/ROOT-VERIFY01.json) · [QA nguồn](../evidence/runtime-repair03/qa/HOST-FREEZE-GATE02.json) · [QA diagnostic](../evidence/runtime-repair03/qa/DIAGNOSTIC-GATE01.json) · [Kiểm bảo toàn](../evidence/runtime-repair03/preservation-final01.json)
