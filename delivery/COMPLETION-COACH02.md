# COACH02: bài tập manual, input và bằng chứng quyền/clock

Ngày 25/10/2026. **READY trong phạm vi code + mock/replay đã yêu cầu. Nghiệm thu trực quan: NOT_CHECKED.** Không có bằng chứng huấn luyện Hera thật, Android/HID hoặc bay SITL trong milestone này.

Đã tích hợp “Huấn luyện manual” vào COACH01: ba bài giữ vị trí, bay thẳng rồi dừng, xoay hướng rồi ổn định; bàn phím và bảng trục mock; hai đáp ứng tham chiếu có tải/không tải. Truy cập [manual](http://127.0.0.1:8897/manual/). Host preview có giới hạn 30 phút; hướng dẫn mở lại và thao tác ở `delivery/coach02-manual/README.md`.

## Hành vi đã thực hiện

- Clock nguồn và host riêng; handshake bốn timestamp tạo khoảng offset, kiểm tuổi/độ bất định/drift. Không dùng thời gian callback làm thời gian HID vật lý. Snapshot phím và trục phải nhất quán; phím đối nghịch vẫn là phím đang giữ, không được dùng thay điều kiện thả hết phím.
- Đồng bộ → trung tính → cấp quyền rõ ràng. Nút “Nhận quyền và bắt đầu” gộp thao tác để không tiêu hết lease 200 ms giữa hai lần bấm. Input sai operator/session/boot/profile/clock/sequence, hết quyền hoặc stale không tiến mô hình. Mất focus/background dừng gửi; sau restart hoặc nhập gói không tự khôi phục quyền. Không tự retry mutation có kết quả chưa rõ.
- Journal SHA-chain append/fsync trước khi công bố state. Lỗi writer làm phiên ngừng tiếp tục; closure thiếu khiến gói INCOMPLETE. Gói đã đóng không nhận append muộn. Quota có giới hạn, không tự dọn dữ liệu. Lịch sử, nhập/xuất và receiver đọc lại sau restart mà không phục hồi quyền.
- Replay tính lại mọi action/state và kết quả đánh giá. Hiển thị sai số vị trí/cao độ/hướng, độ phủ bài tập, biến thiên trục, các gate input/quyền/clock, tỷ lệ thời gian mô phỏng/nguồn và các raw row liên quan. Không tạo điểm kỹ năng phi công tổng hoặc suy ra khả năng bay thật từ controller scripted.

## Kiểm chứng

| Lớp kiểm | Kết quả | Phạm vi chứng cứ |
|---|---:|---|
| Engine, journal và fault injection | 17/17 nhóm | mock/scripted, writer/closure/pending/tamper/cold receiver |
| Client và lỗi mạng | 6/6 nhóm | mạng/clock logic giả, không browser/HID |
| Hành vi UI hiện hành | 10/10 nhóm | mã UI thật chạy trong Node VM, DOM/fetch/timer giả |
| Validation và correlation bổ sung | 5/5 nhóm | prototype/path, phím-trục, resync, SHA cũ |
| Tích hợp host HTTP | 7/7 nhóm | HTTP localhost thật, disk/restart, 4 bước model; input Node tạo |
| Đối chiếu toán độc lập bằng Python | PASS | 6 corpus scripted / 2.320 frame; sai số component tối đa 5,97×10⁻¹³; clock bound sai số 0; 100 trường hợp offset bất đối xứng |
| Cấu trúc/syntax | PASS | 8 module, 30 ID duy nhất, tham chiếu ID và asset route |

45 nhóm ở các lớp trên không phải 45 lượt bay hoặc chứng nhận sản phẩm. Sáu trường hợp exercise/profile thuộc corpus scripted, không phải kết quả người lái. Receiver là tiến trình độc lập; người viết và người rà soát là cùng assistant, không phải QA con người độc lập. So sánh hiệu quả đào tạo với người lái/LLM trực tiếp: NOT_MEASURED; tính toán quyết định dùng code, không gọi mô hình AI.

Các lần kiểm chưa đạt được giữ: tests01 có phép sửa giá trị grade bằng chính giá trị cũ nên ca tamper không thật sự làm biến đổi; đổi mutator và tests02 đạt. UI01 có hai lỗi helper tra sai ID file, được sửa trước các lượt đạt UI02–05. Một lần ghi lại receipt UI02 bị EEXIST và không ghi đè hồ sơ. Static checker ban đầu quên prefix `m-` của helper UI; sửa checker, không suy ra lỗi sản phẩm từ assertion đó. Kết quả hiện hành được định danh trong `evidence/coach02/verification-final01.json`.

## Phạm vi chưa đạt / giới hạn

Browser vẫn không truy cập được trong công cụ. Chưa kiểm trực quan, pixel/alignment/chồng đè, màu tương phản trên màn thực, bàn phím/cảm ứng vật lý, FPS, âm thanh, Android hoặc HeraHub. Không dùng ảnh mock hay DOM test để báo PASS các mục này. Chưa đo UI realtime 1× thực; bước model cố định và tỷ lệ source/sim được công khai, không đổi clock hoặc bỏ frame để che chậm.

Mô hình vận tốc bậc một có gió offset, ENU mét/hướng độ; không phải vật lý 6DOF/Hera/ArduPilot, motor, mưa hoặc collision. “Có tải” chỉ đổi hằng số đáp ứng. Giới hạn 3 m/s áp dụng từng trục ngang; không phải giới hạn độ lớn vector đường chéo. SHA-chain/receiver chứng minh nhất quán, không xác thực nguồn hay chứng minh callback là người thật. Không có lệnh điều khiển drone, SDK, APK, SITL/emulator, ký software mới hoặc ký production.

## Bảo toàn

Chỉ hai file host COACH01 được chỉnh để tích hợp: `pilot/coach01/server.mjs` và `index.html`; exact byte trước sửa được lưu ở `evidence/coach02/source-before/`. 34 thành viên khác của handoff UI-repair01 còn nguyên SHA. Handoff cũ không bị viết lại; handoff COACH02 ghi phiên bản tích hợp mới.

Đối chiếu preservation trước/sau xác nhận 17.117 định danh quan sát không đổi, gồm source/candidate/canonical SOT/ENDURE và các baseline được bảo vệ. 165 đường dẫn thiếu từ trước vẫn thiếu, không có phục hồi, không khẳng định sự hiện diện liên tục hoặc nghiệm thu ENDURE mới. Giữ gate 20 GiB admission / 10 GiB khi ghi, thêm dự phòng 256 MiB. Không xóa bằng chứng, không tạo bản copy toàn dự án, cache build, venv, dependency hoặc thư mục scratch cần dọn.

Store training mới `evidence/coach02/workspace01` là dữ liệu sẽ thay đổi khi người dùng thực hành, tách khỏi receipt kiểm thử đã đóng. Preview PID/lifetime chỉ là tình trạng lúc bàn giao, không phải chứng cứ kiểm hình ảnh. Bản kê SHA cuối ở `evidence/coach02/handoff-final01.json` và `.sha256`.
