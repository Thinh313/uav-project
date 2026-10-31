# COMPLETION · HERASTORE50

Ngày 15/10/2026 · PASS_SCOPED_HOST_MOCK · 6/6 tiêu chí TIP trong phạm vi host mock/replay.
Một agent thực hiện specification/build/verify tuần tự; không phải đánh giá độc lập.

## Kết quả

Đã bổ sung kho lưu trữ có kiểm nhập lại và thu hồi quota cho định dạng HERASWITCH49 trong module/kho50 riêng. Preview: http://127.0.0.1:8804/; kho operator ban đầu trống, không tự tạo mẫu hoặc tự dọn. Không quản lý hoặc thay đổi dữ liệu preview49 tại8803.

Luồng: chọn workspace chưa hoạt động hoặc lần chuyển đã hủy → xuất theo luồng → nhận lại với SHA-256 toàn gói kỳ vọng → kiểm từng chunk/file và đọc lại bản nhận → replay logic49/47 phù hợp → lập phương án gắn với nguồn, selection và receipt hiện tại → nhập đúng mã đơn vị và đánh dấu xác nhận → dọn riêng bản hot đã được lưu. Giữ nguyên gói lưu, bản nhận, authorization và nhật ký giao dịch. Bản nhập dùng để kiểm hồ sơ, không tự kích hoạt workspace hay khôi phục quyền điều khiển.

Workspace đang chọn, chuỗi lịch sử selection đã công bố, pending switch và dữ liệu không xác định được quan hệ bị chặn. Hồ sơ không hoàn chỉnh được ghi rõ RAW_ONLY_QUARANTINED; lần chuyển hủy là RAW_RETAINED_ATTEMPT_NOT_EXECUTION. SHA là kiểm toàn vẹn, không phải chữ ký hoặc xác thực người phát hành.

Dọn có transaction và intent/result từng file. Ngay trước unlink, kiểm danh tính gói xuất/gói nhận, SHA của file nhận tương ứng và danh tính file nguồn vừa kiểm. Dữ liệu thay đổi sẽ chặn, giữ quota đang tính. Không có rm-rf trong luồng sản phẩm. Mất phản hồi không tự lặp lệnh. Restart không tự dọn tiếp: phải lập phương án và xác nhận lại; chỉ hoàn tác về hot khi chưa có delete-intent. Metadata chưa bắt đầu được giữ bằng thao tác rõ ràng. File mất sau intent được ghi MISSING_AFTER_AUTHORIZED_INTENT, không suy ra nguyên nhân hoặc thời điểm mất.

Chỉ trả quota hot sau khi hoàn tất công bố receipt. Gói lưu và bản nhận vẫn ở cùng host: **không khẳng định đã giải phóng ổ đĩa**; dung lượng tổng thậm chí có thể tăng. Chưa chứng minh lưu bền ở bên nhận ngoài host.

## Kiểm chứng

184 ca kiểm cuối đạt, không cộng lại các receipt cũ:

| Bộ kiểm | Số ca |
|---|---:|
| host2: lưu/nhận/replay/quota/fault |90|
| adversarial1: dữ liệu sai, quota, cold fence, receiver process riêng |23|
| crash3:5 tiến trình riêng bị SIGKILL thực |26|
| browser4: tải/nhập/xác nhận/restart/mất phản hồi/retained attempt/UI |36|
| sourceguard1: thay file nguồn muộn trước unlink |6|
| markup1: HTML đúng và2 biến thể lỗi bị chặn |3|

`verification1.json`:50 kiểm nghiệm thu đạt, kiểm cú pháp13 module JavaScript. Browser thực1280/1024/360 không tràn ngang, nút tối thiểu52px; không lỗi JS/request ngoài. Đã xem ảnh phương án1280 và review360. Backend thực restart với PID khác;5 SIGKILL kiểm các mốc metadata/move/unlink/completion/import. Parser kiểm path traversal/link/duplicate/chunk/SHA/truncation/trailing bytes; quota và thiếu dung lượng kiểm bằng fault injection và hàm admission, không làm đầy ổ thật.

Receipt host2 có trước một số guard bổ sung cuối. Kiểm sau đó tập trung vào cold fence, thay nguồn muộn, browser và crash; không tuyên bố tất cả receipt cũ chạy trên cùng SHA runtime cuối. `final-runtime-pins2.json` đối chiếu bản cuối; `artifact-fingerprints.json` bao gồm mã, test và toàn bộ bằng chứng50. Các receipt trước được giữ, không tính thêm vào184. Lần browser1 lỗi closing option đã được giữ nguyên hồ sơ; sửa và thêm startup markup guard cùng kiểm rendered recovery options để ngăn tái diễn.

Baseline15.796 đường dẫn bảo vệ khớp byte; inventory ENDURE5.051 giữ nguyên. Không sửa source/candidate/SOT/trust/ENDURE hay các milestone trước, không ký mới/SDK/APK/SITL/emulator, không khởi động lại soak. `preservation-final1.json` là đối chiếu cuối; không diễn giải đây là ENDURE24h PASS.

## Giới hạn và tài nguyên

Hot64MiB/4 nhóm/16 lần chuyển; tổng kho50 cap512MiB,16 exports/16 imports/16 cleanup attempts; raw64MiB, package96MiB, chunk256KiB,4096 files/1024 directories, dòng/header2MiB. Ghi theo luồng với buffer có giới hạn, dự phòng16MiB và sàn host20GiB. Không cài dependency hoặc build.

Ngân sách artifact kiểm ban đầu48MiB được điều chỉnh có hồ sơ thành96MiB (`resource-decision1.json`) để giữ các raw receipt trước và kiểm bổ sung; không xóa/ghi đè bằng chứng để vừa ngân sách. Giới hạn sản phẩm và sàn host không đổi. Lúc verification:75.366.400 byte cấp phát (~71,9MiB), host còn24.207.360.000 byte (~22,5GiB). Số cuối nằm trong preservation-final1.

NOT_CHECKED: HeraHub/Android/SDK/MCU thực, mất điện vật lý, ENOSPC toàn volume thực, writer filesystem đối kháng, độ bền lưu ngoài host, tích hợp kho49 đang chạy, hot restore sau delete-intent, thu hồi cold-vault và pruning chuỗi selection đã công bố. Chỉ hỗ trợ một owner hợp tác trên mỗi root. Không có kết luận điều khiển drone thật từ mock/replay.

## Dọn scratch của chính nhiệm vụ

Đã giữ raw proof cần thiết rồi xóa11 root thử nghiệm do nhiệm vụ tạo; không xóa dữ liệu người dùng hay bằng chứng cũ:

- `.local/herastore50-adversarial1`
- `.local/herastore50-browser1`
- `.local/herastore50-browser2`
- `.local/herastore50-browser3`
- `.local/herastore50-browser4`
- `.local/herastore50-crash1`
- `.local/herastore50-crash2`
- `.local/herastore50-crash3`
- `.local/herastore50-qa1`
- `.local/herastore50-qa2`
- `.local/herastore50-sourceguard1`

Không tạo bản sao toàn dự án, dependency ngoài repo, distDir hoặc Docker image. Kho operator50 trống được giữ để người dùng thử có chủ đích; mọi thao tác dọn cần xác nhận trong giao diện.

## Bàn giao

- `pilot/herastore50/README.md`, `delivery/TIP-HERASTORE50.md`, `docs/ADR-063-VERIFIED-ARCHIVE-BEFORE-RECLAMATION.md`.
- `evidence/herastore50/verification1.json`, `preview1.json`, `preservation-final1.json`, `artifact-fingerprints.json`.
- Preview46–49 giữ nguyên PID; preview50 PID71902. Kiểm GET chỉ đọc8800–8804 trả200; preview50 không sample/POST và không có dữ liệu chọn.
