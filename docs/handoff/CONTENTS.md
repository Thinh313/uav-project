# Phạm vi public/private và tính toàn vẹn

## Source public H10

Repo public có lịch sử riêng và tag `research-handoff-2026-11-02-h10`. Bản gốc tiếp tục phát triển ở repo private với tag `development-handoff-2026-11-02-h10`. Không nhập lịch sử private vào public và không di chuyển các tag bàn giao cũ.

Mã nguồn sản phẩm, adapter, Android, compiler, simulator và các revision cô lập được xuất theo policy đã chốt. Manifest `handoff/SOURCE-MANIFEST.json` ghi các file public. Verify chứng minh byte/kind của danh sách đó; không chứng minh mọi file thêm vào workspace là hợp lệ hoặc runtime đã được nghiệm thu.

98 đường dẫn thiếu ở checkout tác giả có từ trước. Snapshot Git giữ blob cũ; chúng không bị stage thành deletion để cập nhật mốc này. Việc tái dựng vào bản nhận không khẳng định đường dẫn gốc hiện diện liên tục. Những nhãn khách hàng đã được ẩn danh vẫn có bản gốc private và kê khai riêng.

## Gói riêng

BOM, dữ liệu khách hàng, context nội bộ, raw evidence, candidate pools, engineering APK, AP executable và image đã khai báo được giao riêng qua kênh kiểm soát truy cập. Gói private gốc 410.224.640 B giữ nguyên SHA:

`52fd3330c64c327cc5827be61ff4f9cda20dd1a5bede1d20c08ee4dd0a92fd28`

Supplement MILESTONE05 cũ vẫn là lịch sử. Mốc H10 có `UAV-PROJECT-H10-SUPPLEMENT-2026-11-02.tar.gz`, kèm manifest và SHA256 riêng do anh cung cấp; không coi gói gốc cũ tự chứa source và raw mới. Nhóm cần nhận đủ các thành phần được kê khai của đúng mốc.

Không upload gói private, manifest có chi tiết khách hàng, credential hoặc khóa ký vào issue/PR/release public. Không giải nén overlay private vào clone dùng để push. Public hóa code không đồng nghĩa công bố BOM hay quyền cấp lại license cho thành phần bên thứ ba.

## Phần không có trong Git public

Raw/candidate/APK/image/SDK/AVD và cache không đi trong repo public. Các bản chụp web nghiên cứu và snapshot provenance mới cũng được giữ trong supplement H10 private. Một số liên kết trong ghi chú nghiên cứu lịch sử có thể trỏ tới dữ liệu riêng; không coi clone public chứa đầy đủ raw nghiên cứu. Gói engineering không bao gồm Android SDK/system image/AVD userdata, toàn bộ ổ đĩa hoặc mọi log lịch sử không kê khai. Các source mock gốc có thể đọc fixture private và đường dẫn host cũ; clone public không tự tái lập 34 kiểm host-coupled của H10.

Không có phần cứng HeraHub, MCU/radio, camera/gimbal, dữ liệu hiệu chuẩn đầy đủ hay một universal installer. Checksum đủ không tự chứng minh runtime đúng, simulation đúng vật lý hay sản phẩm đủ điều kiện bay thật.

## Luồng tiếp nhận

Clone/tag -> verify source -> mock public -> đọc status -> nhận và kiểm gói private -> workspace riêng -> intake môi trường -> mock/replay theo contract -> admission -> lượt thực ngắn. Biên bản tiếp nhận ghi đúng phần đã nhận/kiểm và phần thiếu.
