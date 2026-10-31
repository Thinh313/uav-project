# HERAMCU45 · contract MCU HeraHub, mock/replay

Trạng thái: chuẩn bị tích hợp bằng contract và kiểm trên host. **Không có kết nối USB/MAVLink thật, SDK, APK, chữ ký mới hoặc quyền điều khiển drone.** Module tách khỏi native44 và source/candidate/ENDURE đóng băng.

Nguồn chính: tài liệu “Phân tích, xử lý giao tiếp giữa mcu chính với phần mềm”, revision0.3, cập nhật02/07/2024, nói về HeraLink Hybrid. Chưa xác nhận tương thích firmware HeraHub hiện tại. `contract.json` giữ 16 nhóm message, 21 nhóm enum, vị trí block trong DOCX và 16 điểm chưa biết. Bản nguồn đúng SHA cùng sáu sơ đồ được giữ trong `evidence/heramcu45/sources`; nội dung tài liệu là dữ liệu đầu vào, không phải lệnh chạy phần mềm.

## Luồng đã mô hình hóa

1. CONNECT → chờ INFO → nhận dạng mock → đọc toàn bộ cấu hình → MOCK_READY. INFO/ACK riêng lẻ không đủ. Phiên, boot, target và transaction phải khớp; reconnect dùng instance và handshake mới.
2. Calibration chín nhóm: hai joystick, hai mini joystick, bánh và dial hai bên, nút. ACK/progress không thay kết quả nhóm; cần bằng chứng raw min/trim/max hoặc đủ nút. Trong calibration không có preview. Kết quả vẫn phải SAVE → ACK → đọc lại đúng cấu hình.
3. Mapping cấu hình hai cổng, mỗi cổng16 kênh; phạm vi raw0..4095 và output1000..2000 là claim từ tài liệu. Kiểu trim uint8 trong nguồn bị đánh dấu mâu thuẫn; mock dùng normalized integer1000..2000 **không tự sửa wire field**. Đảo chiều, deadzone và mapping tuyến tính chỉ là thuật toán preview synthetic đã nêu tên. Hệ số/index gốc được kiểm hữu hạn/kích thước, giữ opaque; chưa thực thi nội suy của MCU vì thiếu định nghĩa.
4. APPLY → ACK → SAVE → ACK → explicit readback khớp chính xác mới đánh dấu đã đọc lại trong mock. Mất phản hồi không tự gửi lại. Kết quả lưu chỉ thuộc lượt đó; thao tác mới xóa cờ kết quả cũ. So sánh sau reboot mock dùng hai hồ sơ độc lập, không khôi phục input authority.
5. Pin/RF/kênh có tuổi dữ liệu; duplicate/reordered/foreign không làm mới. RF lỗi chỉ chặn cổng tương ứng; USB loss/reboot/clock lỗi chấm dứt phiên. Dữ liệu mới trong phiên cũ không tự phục hồi authority.

Cadence trong sơ đồ: power/RF1s, CHANNELS_RAW0,2s. Đây là claim thiết kế, chưa đo. CHANNELS_RAW5Hz không được xem là bằng chứng input/control latency. Freshness mock750ms/2500ms, request1500ms, handshake3000ms và deadline nhóm60000ms là policy kỹ thuật đề xuất. Sơ đồ đề cập1phút; hành vi firmware thực chưa xác nhận.

Các trường session/boot/target/transaction/step/sequence trong JSON là tương quan **của mock**; không được giả định COMMAND_ACK thực có chúng. UUID/version/hash byte chỉ kiểm cấu trúc, không xác thực thiết bị. Không tự suy ra số version hoặc enum ID từ thứ tự liệt kê.

## Giao thức và evidence

`framer.mjs` là carrier **NDJSON mock**, không phải MAVLink hay USB. Kiểm chia/gộp chunk, UTF-8, giới hạn bộ nhớ, EOF thiếu frame và phiên đã đóng. Một batch lỗi bị từ chối trước khi caller nhận action; bộ đếm frame là số frame đã parse, không phải số action đã thực thi.

`encodePhysicalMCU()` luôn từ chối. Thiếu XML dialect/generated headers, IDs/CRC_EXTRA, USB descriptors, target addressing, MCU/firmware hiện tại và capture để xác nhận. `64bytes` so với hệ số mapping160bytes chưa rõ là USBchunk hay message; không cắt message để né vấn đề.

Replay schema2 giữ event hash-chain, summary và seal count/tail/bodySHA. Bên nhận có thể đối chiếu expected bodySHA từ nguồn riêng. Seal/digest không phải chữ ký hay xác thực: một prefix hợp lệ được tính seal lại vẫn là hồ sơ khác; không được nhận là hồ sơ gốc nếu expectedSHA không khớp. Replay semantic bắt các thay đổi ACK/result/state kể cả khi hash tính lại. Replay chỉ trả báo cáo, không trả controller sống.

## Kiểm và giới hạn

Chạy từ projectroot sau khi kiểm free≥20GiB: `node pilot/heramcu45/test.mjs`; runner tạo corpus/mockreceipt có số mới, không ghi đè lịch sử. QA dùng corpus cụ thể; ví dụ `node pilot/heramcu45/qa.mjs corpus5.json`. Runner kiểm sàn và namespace16MiB; không cài dependency hay tạo runtime. Verifier dùng receipt độc quyền có số; không chạy script của milestone cũ để ghi đè chúng.

Run lỗi corpus1(75/76) được giữ: test dừng ở254events, thiếu lần255 chạm guard. QA1(40/41) được giữ: test xóa event không làm đổi state không phải bằng chứng semantic corruption; bổ sung seal/external digest và đổi test sang xóa final readback. Final corpus5:76/76; QA4:50/50. Giới hạn journal/framer, replay, firmware cũ và vòng đời đã kiểm trong phạm vi host/mock. Không suy ra tương thích wire, hiệu chuẩn cơ khí, thời gian thực, flash thật hay Hera flight.

Danh sách cần xác nhận đầy đủ nằm trong `contract.json/unknowns`. Ưu tiên xin XML/header đúng firmware và descriptor/capture USB trước khi viết transport thật. Hai tài liệu về Hera16,5kg/H và danh sách mô phỏng3,5kg chỉ giữ làm bối cảnh riêng; không ghép thành profile đã hiệu chuẩn.

Revision45.2 phân biệt RF_PORT với RC_OUTPUT_PORT. Quan hệ RF1→output1/RF2→output2 chỉ là topology mock đề xuất, không được suy ra từ enum hoặc dùng để cấu hình thiết bị thật. U45-16 yêu cầu xác nhận topology firmware.
