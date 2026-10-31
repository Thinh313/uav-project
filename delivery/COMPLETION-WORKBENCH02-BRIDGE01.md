# Workbench02: hai bản vá bridge

Ngày 24/10/2026. **READY trong phạm vi hai bản vá bridge và mock; Workbench02 native tích hợp vẫn NOT READY.** Một assistant chuyển pha Contractor, Builder và Verify theo Vibecode 6.3; không có review độc lập.

## TIP bổ sung và kết quả người dùng

Yêu cầu: kiểm dung lượng, ghép hai lỗi bridge khi đủ sàn 20 GiB; mock trước, Android–SITL chỉ sau admission. Giữ source/candidate đóng băng, ENDURE và guard. Phạm vi sửa source có sẵn chỉ `pilot/workbench02/native-bridge.mjs`; thêm bộ kiểm và bằng chứng nhỏ ở Workbench02. Ngân sách hiện hữu 8 MiB không đổi. Không build hoặc ký APK.

1. Ràng buộc nhãn platform của phản hồi với environment lúc gửi request. Mock không thể trả nhãn Android; receipt export phải dùng đúng loại bằng chứng SAF của platform đó.
2. EMPTY chỉ nhận head ROOT và body null. COMMITTED phải có head 64 ký tự hex thường; load kiểm body/SHA, save kiểm previousHead và SHA trước khi tiến head. Receipt không hợp lệ không được báo đã lưu.

SHA bridge trước: `d38ab19f41703f5871e6b0079c01be86db7d1ba8f4efdd57988f9b1f6117e7c8`.
SHA sau: `cb5c9511970cf388f09a888e2c25b73162983aea9a920237d4fcc2b2706572f7`.

## Verify

- Hai yêu cầu sửa: 2/2 đã ghép và có đối chứng. `bridge-regression01.json` tái dựng bản trước trong RAM, kiểm đúng SHA gốc, tái hiện hai lỗi; bản sau từ chối cả hai. Không ghi đè source hoặc lịch sử gốc để làm baseline.
- `node planning/workbench02/bridge-tests01.mjs 03`: 25/25 nhóm PASS trong `bridge-mock03.json`. Có kiểm save/load qua provider mới, CAS, head/body/SHA, nguồn phản hồi, nhãn SAF, UTF-8/bounds, session/id/action, timeout, không retry, foreground, picker hủy, receipt lỗi và không khôi phục quyền. Nhãn ANDROID trong ca kiểm cũng là phản hồi giả lập Node, không phải thiết bị Android.
- Projection UI giữ inverse equality với Workbench01, 8 thay thế đúng số lượng, không có localStorage fallback ở native mode; generated module qua kiểm cú pháp. Kiểm cú pháp 6 module Workbench02 đạt. Không có kiểm giao diện tương tác mới.
- Chuỗi model nhiệm vụ synthetic chuẩn bị được; Home/datum/camera/range sai bị từ chối ở planner hoặc adapter. Đây không phải upload hay thực thi bay.
- Kiểm trước/sau đạt 14.025 identity bảo vệ, 65 file Workbench01 và native reuse pins. Chỉ một source có sẵn thay đổi, đúng bridge trên; 12 source khác giữ SHA. Xem `preservation-resume-before01.json`, `preservation-resume-after01.json`, `resume-verification01.json`.

Không cộng lại các lượt thất bại thành kết quả cuối: lần runner đầu exit 13 do tiêm receipt trước khi async SHA tạo request; log ở `bridge-runner-attempt01.json`. `bridge-mock01.json` và `bridge-mock02.json` giữ nguyên kết quả 24/25: harness thiếu energy, sau đó đặt assertion quá muộn khi planner đã từ chối datum. Sửa harness chờ request quan sát được, bổ sung energy chuẩn và bao cả chuỗi tạo plan trong negative assertion; không sửa planner hoặc nới tiêu chí. Không lấy các kết quả này làm bằng chứng Android.

## Admission và giới hạn

Dung lượng lúc vào 28,76 GiB; kiểm cuối 28,65 GiB (30.760.960.000 byte). Đủ sàn 20 GiB cho sửa/mock nhỏ, nhưng dưới ngưỡng khởi chạy 29 GiB. Physical precheck từ chối; chưa bắt đầu 31 mẫu ổn định, chưa qua full admission, không mở Android/emulator/AP/SITL và không dùng campaign G17 cũ làm chứng cứ giao diện mới. Guard giữ nguyên.

Java store/ART, SAF thật, UI Android, persistence/restart Android và AUTO cùng video/payload chưa nghiệm thu. Hai candidate Java từ lượt trước vẫn chưa ghép; StoreTest đang chờ overload constructor tương ứng nên chưa thể coi bộ Java là buildable/đã kiểm. Không tạo APK hay chữ ký mới, không dispatch lệnh bay và không chạm HeraHub.

Value evidence: chứng minh sửa hai lỗi integrity/provenance bằng mock; lợi ích thời gian/công người so với CLI chưa đo. Không có runtime AI hay cơ sở tuyên bố đạt DJI hoặc sẵn sàng bay thật. Kết quả phù hợp để tiếp tục hoàn thiện source native rồi qua admission mới.

Không tạo scratch ngoài repo, không cài dependency hoặc tạo build cache. Không xóa bằng chứng hay dữ liệu; không có artifact tạm mới cần dọn. Sự cố ghi hai file kiểm sau guard ở lượt trước vẫn được giữ nguyên trong lịch sử bàn giao NOT READY, không viết lại thành tuân thủ hoàn toàn.
