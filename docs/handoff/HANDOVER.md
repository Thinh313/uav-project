# Anh gửi các em: tiếp nhận AERIS / UAV Project

Anh gửi các em bản source và bộ hồ sơ ở đúng trạng thái nghiên cứu hiện tại.
Mục tiêu là để các em hiểu hệ thống, tái lập phần đã có chứng cứ, rồi tiếp tục
hoàn thiện một sản phẩm điều khiển UAV cao cấp. Anh muốn các em giữ hai việc
song song: phát triển nhanh, và biết chắc điều mình đang báo cáo đã được kiểm đến đâu.

Bản này có nhiều năng lực và nhiều revision thử nghiệm, nhưng beta tích hợp vẫn
chưa đạt. Các em không cần bảo vệ những lựa chọn cũ chỉ vì đã tốn công; hãy sửa
đúng pipeline và vòng đời nhiệm vụ khi có bằng chứng. Đừng đổi guard, bỏ frame
hay lấy UI đẹp để thay cho một hành trình vận hành đầy đủ.

## Các em bắt đầu như sau

1. Clone repo public theo tag bàn giao, chạy verify source và bộ mock ở README.
2. Đọc `STATUS.md` và `ARCHITECTURE.md`, vẽ lại được ba đường web, native/control
   và media. Chỉ rõ nguồn nào là mock, replay, SITL và nguồn nào chưa có thiết bị thật.
3. Nhận gói private từ anh, kiểm checksum trước khi giải nén. Giữ BOM và tài liệu
   khách hàng ngoài working copy public. Không gửi nguyên raw/log lên issue public.
4. Chọn một cấu hình máy để tái lập; ghi Node/Python/SDK/WebView/image/AP/profile.
   Không thay cấu hình rồi dùng lại kết luận của máy cũ.
5. Khi mock đã đạt và admission cho phép, kiểm một lượt thực ngắn. Chưa đạt
   video-measure hoặc closure thì ghi đúng NOT READY và giữ primary evidence.

## Việc ưu tiên đầu tiên

Anh đề nghị nhóm tập trung một hành trình duy nhất: khảo sát -> preflight -> Fly
manual/assisted/AUTO cùng payload/video -> mất link/reboot -> review -> SAF/receiver.
Mỗi lần chạy phải giữ source, APK, profile và artifact rõ ràng. Mốc beta simulator
là cùng một release đi hết hành trình, chạy 10 phút không can thiệp, không mất frame,
không phục hồi quyền ngầm và có receiver kiểm lại bằng chứng.

Điểm chặn hiện tại không phải thiếu một nút UI. Cadence đã được chứng minh,
nhưng navigation/EKF cold-start và video-measure chưa đi hết. R02 đã qua mock;
ngân sách artifact phải được quyết định minh bạch trước lượt mới. Các em đọc
raw trước, tránh tiếp tục một chuỗi vá chỉ dựa vào lỗi timeout sau cùng.

## Cách anh muốn nhận báo cáo

Các em gửi một kết quả theo outcome: source/tag nào, máy/profile nào, lệnh nào,
ca nào pass/fail/chưa chạy, raw và SHA ở đâu, nguyên nhân nào đã chứng minh,
nguyên nhân nào mới là giả thuyết, và bước nhỏ tiếp theo sẽ phân biệt điều gì.
Một báo cáo tốt có thể ghi NOT READY. Một báo cáo thiếu bằng chứng không được
đổi thành DONE bằng cách cộng số test xanh hoặc số tính năng đã có trong code.

Anh mong các em tiếp nhận chủ động. Phần nào đơn giản hóa được thì đề xuất
thẳng; phần liên quan quyền, dữ liệu, an toàn, ngân sách hay phát hành thì chốt
contract trước. Trước khi đưa lên tay cầm và bay thật, nhóm còn cần bench,
HIL, hiệu chuẩn và field qualification theo đúng cấu hình thực tế.

## Hồ sơ đi kèm

PDF trình bày chi tiết nằm tại `output/pdf/UAV-PROJECT-HANDOVER.pdf`.
README là lối vào nhanh; các file dưới `docs/handoff/` là tài liệu có thể chỉnh
sửa; manifest và validation dưới `handoff/` dùng để kiểm máy.

## Công cụ tiếp nhận r1

Anh đã kiểm lại bằng một clone sạch từ GitHub và bổ sung đường bắt đầu một lệnh:
`node tools/handoff/intake.mjs`. Các em đọc `INTAKE01.md` để thấy phần đã chạy,
phần đã sửa và phạm vi chưa nghiệm thu. Gói private gốc vẫn nguyên byte ở mốc
handoff ban đầu; dùng helper r1 từ clone public để kiểm và dựng workspace riêng,
không ghép dữ liệu private vào clone sẽ push.
