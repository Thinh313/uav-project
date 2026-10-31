# AERIS · M1-MOCK: journal, clock và lifecycle

Ngày 27/10/2026. Kết quả: **M1-MOCK FOUNDATION READY**. Đây là phần nền đã kiểm bằng mock/fault injection; **M1 thực và Beta giả lập hoàn chỉnh vẫn NOT READY**.

## Kết quả có ích cho sản phẩm

- Journal phân đoạn giữ thứ tự RX → INTENT → fsync → callback gửi → SENT/UNKNOWN, ràng buộc run/epoch/frame và chuỗi CRC/SHA. Luân chuyển chỉ ở ranh giới hợp lệ; receiver đọc lạnh phát hiện thiếu, đảo, sửa hoặc thêm dữ liệu sau seal.
- Dữ liệu timing/stage được ghi theo luồng; số bản ghi, kích thước, quota và bộ nhớ tổng hợp có giới hạn. Fault injection kiểm short-write, EIO, ENOSPC, file/directory fsync, send không xác định và tiến trình mock bị dừng đột ngột. Các prefix hợp lệ và hồ sơ lỗi được giữ.
- Clock dùng trạng thái pending/recent có giới hạn, không còn phụ thuộc bảng toàn phiên 1.024 phần tử. Bản kiểm độc lập cuối chạy 2.051 trao đổi và giữ 4.104 dòng sự kiện bền vững; kiểm stale, timeout, phản hồi muộn/trùng, sai peer/run/boot và clock regression.
- Lifecycle tách yêu cầu dừng, đóng tài nguyên và commit review; thời gian đã đóng bất biến. Chặn callback thế hệ cũ, lease hết hạn sống lại, khôi phục quyền từ lịch sử và tạo hai phiên kế tiếp từ cùng phiên đã đóng.
- ProviderDescriptor đối chiếu binary/model/config/endpoint theo profile và từ chối candidate thiếu hash. Đây là kiểm cấu trúc dữ liệu đầu vào, chưa phải xác minh runtime hay cấp quyền bay.

## Các lỗi QA đã sửa

Ca quan trọng nhất: close có thể lỗi ở directory fsync sau khi các byte session đã tồn tại, đồng thời không ghi được failure marker. Reader không thể suy ra commit từ chính các byte đó. Kết quả mặc định hiện là COMPLETE_BYTES_UNATTESTED; chỉ anchor do caller giữ sau close thành công mới đối chiếu được commit. Cả hai trạng thái vẫn không cho công bố gói hay kết luận AP đã thực thi. Anchor lấy lại từ chính gói chưa tin cậy không tạo ra bảo chứng độc lập.

Các ca khác đã sửa và kiểm lại: reader chấp nhận policy/eventKind sai kiểu, đọc lịch sử sau lỗi sink bị chặn, clock/lease hết hạn sống lại khi đồng hồ truy vấn lùi, và successor fork. Cho phép phiên mới dùng cùng AP boot khi AP chưa reboot; không tự tạo bằng chứng reboot. Hồ sơ thất bại ban đầu và lỗi helper kiểm thử được giữ nguyên.

## Kiểm chứng và phạm vi

11 tiêu chí đạt trong phạm vi mock. QA độc lập trên source cuối gồm 10 nhóm journal follow-up, 8 nhóm clock, 13 nhóm Java lifecycle/provider và 13 kiểm cold replay. Các nhóm có chồng lấp, không cộng thành số ca độc nhất. Đối chiếu clock → journal hiện tại đạt 48 CLOCK events qua 3 segment; lượt lớn 1.100 trao đổi dùng journal cũ chỉ là tham chiếu, không thay bằng chứng source cuối.

Không mất/trùng frame được chấp nhận trong corpus mock đã kiểm; chưa có kết luận toàn bộ frame của AP thực. Fsync/callback trong kiểm host không chứng nhận chịu mất điện vật lý hay drone đã nhận lệnh. Chưa có kiểm giao diện Android, ART, cảm giác điều khiển hoặc đánh giá người dùng trong nhiệm vụ này.

## Dung lượng và bảo toàn

Admission mock đạt sau 31 mẫu trong 30 giây; chính sách giữ nguyên: entry 20 GiB, floor 10 GiB cộng dự phòng 256 MiB và forecast 15 giây. Kiểm cuối quan sát khoảng 22,8 GiB trống. Bằng chứng trước báo cáo khoảng 13,3 MiB/800 file, trong ngân sách 256 MiB/2.000 file và cửa sổ 4 giờ.

17.117 định danh cũ, 1.620 mục bàn giao SIM-STABILITY03 và 48 file M0 không có sai lệch mới. 165 đường dẫn thiếu từ baseline cũ và 97 file tracked bị xóa từ trước được giữ nguyên hiện trạng; không tuyên bố codebase đầy đủ hoặc đường dẫn gốc hiện diện liên tục. Không sửa source/candidate đóng băng, canonical SOT hay lịch sử ENDURE; không nghiệm thu lại ENDURE.

Không mở AP, Android, emulator hoặc host companion; không build APK/AP/native library, cài đặt hay ký. Có thực thi Python mock và biên dịch/chạy Java thuần bằng JDK có sẵn. Đã dọn class do tác vụ tạo ở clock-lifecycle-unit (16 class) và ba thư mục independent-qa01, independent-edge01, independent-qa02; .build hiện trống. Không tạo bản sao dự án trong /tmp và không xóa bằng chứng.

## Bước tiếp theo

Chuẩn bị M1-BUILD/ACTUAL: ghép adapter journal của AP-stage và native, materialize/pin closure của provider mới, cấu hình clock sender phù hợp freshness, rồi smoke trước kiểm manual/assisted, mất link/reboot và 30 phút đủ frame ở 1×. Default freshness 250 ms không thể sao chép nguyên cadence observer cũ 333 ms; adapter phải chọn và kiểm cadence phù hợp. Chưa đổi speedup, cap 500 ms hay bỏ frame.

## Hồ sơ kiểm chứng

- [Nghiệm thu Contractor](../evidence/betaintegrated01-m1mock/verification-final01.json)
- [QA độc lập, source cuối](../evidence/betaintegrated01-m1mock/qa/FINAL-QA01.json)
- [Đối chiếu bảo toàn](../evidence/betaintegrated01-m1mock/preservation-final01.json)
- [Tiến độ kế tiếp, không ghi đè M0](../planning/betaintegrated01/PROGRESS-M1-MOCK.json)
- [API journal và giới hạn](../pilot/betaintegrated01/journal/README.md)
- [API clock/lifecycle](../planning/betaintegrated01/m1mock/clock_lifecycle/API.md)
