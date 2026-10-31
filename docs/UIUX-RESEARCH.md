# Nghiên cứu và phương pháp thiết kế UI/UX RtR · UX01

Ngày nghiên cứu: 12/10/2026. Phạm vi đợt này: giao diện điều khiển cho workflow khảo sát và lập nhiệm vụ; prototype Plan/Fly cục bộ. Yêu cầu trực tiếp của chủ việc: bỏ chất lượng thiết kế M0, dùng trắng/đen làm chủ đạo, vàng làm màu phụ ít. Nghiên cứu chuyển thành giao diện chạy được và tiêu chí kiểm, không dừng ở moodboard.

## Cách cào và lọc

Chọn nguồn chính thức theo ba câu hỏi: người điều khiển cần nhìn thấy gì; thao tác có đo được không; đánh giá trải nghiệm bằng phương pháp nào. Giữ URL, thời điểm lấy, bytes và SHA-256 trong `research/uiux-20261012/sources.json`; claim có đoạn chứng cứ đối chiếu với snapshot, nguồn gốc và giới hạn áp dụng. Registry do Refinery tái dựng tất định; không cộng nhiều trang W3C hoặc ISO thành nhiều nguồn độc lập.

Kho có 12 hồ sơ thu thập cho 10 URL, gồm hai lần lấy HTTP ISO bị 403 và hai bản trích xuất qua web thay thế. Có 10 captures lưu được: tám HTML, hai bản trích xuất web. Trang DJI cockpit trả về shell ứng dụng, giữ để ghi nhận nhưng không dùng làm chứng cứ nội dung. 12 claims dùng chín captures nội dung thuộc bốn nhóm nguồn NASA/DJI/W3C/ISO. Hai trường `aeris-compliance` và `operator-superiority` để null. Các bản trích ISO là abstract công khai; chưa có toàn văn tiêu chuẩn trả phí. Không tuyên bố bao phủ hết tiêu chuẩn hoặc sản phẩm cạnh tranh.

## Căn cứ → quyết định thiết kế

| Căn cứ chính thức | Điều rút ra trong phạm vi nguồn | Quyết định của dự án |
|---|---|---|
| [NASA crew interfaces, Vol. 2](https://www.nasa.gov/reference/10-0-crew-interfaces-vol-2/) | Thông tin quan trọng cần nhìn đồng thời; dữ liệu thiếu/cũ phải được nhận biết; đơn vị nhất quán; màu có dấu hiệu bổ trợ | Giữ plot, kết quả, validation và hành động trong một workspace. Khi telemetry cũ, đổi số thành `—`, thêm chữ, khóa thao tác phụ thuộc dữ liệu. Nêu đơn vị cạnh giá trị |
| [DJI Primary Flight Display](https://enterprise-insights.dji.com/blog/dji-primary-flight-display) | Ví dụ sản phẩm tích hợp thông tin bay để giảm việc chuyển vùng nhìn | Dải telemetry và khu lệnh ổn định. Chỉ hiển thị trường có dữ liệu; không vẽ attitude/heading/GNSS giả. Đây là suy luận thiết kế từ ví dụ sản phẩm, chưa là so sánh hiệu suất |
| [WCAG 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) | Ngưỡng tương phản chữ và tín hiệu giao diện có thể tính được | Kiểm các cặp token dùng cho chữ, viền, selection và focus; kiểm thêm ảnh render. Kết quả token không thay thế audit toàn bộ giao diện |
| [WCAG 2.5.5, AAA](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html), [2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) | Vùng đích tăng cường 44×44 CSS px, có ngoại lệ; focus không bị che hoàn toàn | Chọn sàn vùng chạm 44px, nút chính 48px; next/previous thay thế chọn tuyến mảnh; sheet có focus trap, Escape và trả focus |
| [ISO 9241-210:2019](https://www.iso.org/standard/77520.html) | Abstract đề cập thiết kế lấy người dùng làm trung tâm trong vòng đời hệ thống | Định nghĩa bối cảnh, dựng task, thử, ghi lỗi và sửa; lặp với người điều khiển thật. Quy trình dưới đây là đề xuất dự án, không phải trích toàn bộ ISO |
| [ISO 9241-110:2020](https://www.iso.org/standard/75258.html) | Nguyên tắc tương tác tổng quát; abstract loại thẩm mỹ/nhận diện thương hiệu khỏi phạm vi | Đánh giá thao tác và thẩm mỹ bằng hai câu hỏi khác nhau; branding trắng/đen/vàng đến từ chủ việc |
| [ISO 9241-11:2018](https://committee.iso.org/standard/63500.html) | Usability là kết quả sử dụng; tài liệu định nghĩa khái niệm, không cung cấp một phương pháp thử cụ thể | Đo hoàn thành nhiệm vụ, lỗi, thời gian và đánh giá của operator trong bối cảnh đã ghi. Không coi ảnh đẹp hoặc browser PASS là bằng chứng vượt trội |

NASA thuộc bối cảnh spacecraft; áp dụng ở đây là tham khảo human factors. DJI là tài liệu của nhà sản xuất. WCAG hỗ trợ accessibility web. Không nguồn nào xác nhận độ an toàn bay hay chất lượng cao cấp của AERIS.

## Hệ kỹ thuật thiết kế đã triển khai

Trục thị giác là vùng công việc tối và inspector chỉnh sửa trắng. Vàng chỉ dành cho tuyến đang chọn, định vị workspace và bước chính. Mức ≤5% pixel vàng ở ảnh khởi tạo là ngân sách thị giác nội bộ, không phải quy chuẩn RtR đã công bố. Mã vàng #F2CA30 tạm dùng vì chưa có brand book. Font IBM Plex Sans cục bộ, số tabular, một bộ icon SVG, các nhóm thông tin và vị trí hành động ổn định.

Thứ bậc thao tác: thiết lập cơ bản → kiểm kết quả → xử lý lỗi → diễn tập. Camera nâng cao nằm trong disclosure; lưu/mở/xuất/nhập nằm trong menu. Điều kiện bơm lỗi diễn tập nằm trong drawer. Dirty, invalid, valid; sent, ACK, observed, rejected, timed-out; fresh và stale là các trạng thái có chữ và phản hồi riêng. Reset phiên dùng dialog cho xuất log hoặc hủy. Zoom, fit, lựa chọn tuyến và footprint đều dùng hình học thực của engine cũ.

Vòng kiểm: kiểm core → kiểm luồng browser → kiểm tương tác/focus/viewport → nhìn ảnh desktop/tablet/mobile → sửa điểm không đạt → ghi receipts. Các lỗi nhận diện đã sửa: input có vùng chạm nhỏ hơn viền ngoài; nút tính lại bị khu vực scroll che trên tablet; hàng chồng ảnh bị footer che và nhãn gốc tọa độ chạm dock ở cửa sổ thực cao 720px. Bổ sung kiểm vùng clip, không chỉ kiểm bounding box nằm trong cửa sổ. Chọn đường SVG được kiểm bằng tọa độ chạm thật, vì hộp hình học của đường dọc rộng bằng 0 dù stroke nhận chạm rộng hơn.

## Thử với operator trước khi kết luận vượt trội

Đề xuất vòng formative đầu: 5–8 người có kinh nghiệm khảo sát, gồm người mới với giao diện và người dùng GCS thường xuyên. Đây là cỡ vòng tìm vấn đề do dự án đề xuất, không đủ tự xác lập ưu thế thống kê. Ghi thiết bị, kích thước màn hình, độ sáng, vị trí sử dụng, kinh nghiệm và cách nhập; thử ngoài trời và găng tay khi có controller mục tiêu. Kịch bản bắt đầu ở dữ liệu diễn tập có đáp án, không điều khiển drone thật.

| Task kiểm | Quan sát và dữ liệu cần ghi | Điểm phải sửa khi gặp |
|---|---|---|
| Tạo khu vực, đổi độ cao/chồng ảnh, kiểm GSD và chu kỳ, xuất rồi mở lại | Hoàn thành đúng; thời gian; số lần đi tìm thông tin; tham số/file có khớp | Người dùng bỏ sót dirty/invalid hoặc nhầm đơn vị; kết quả khó tìm |
| Camera không đạt chu kỳ chụp | Có nhận ra nguyên nhân và sửa đúng không; số lần thử sai | Validation không chỉ rõ bước tiếp theo |
| Chọn tuyến, xem footprint, zoom/fit bằng chạm và bàn phím | Chọn đúng; chạm nhầm; mất bối cảnh; quay lại tham số | View operation bị hiểu thành thay đổi mission |
| Mất/cũ telemetry; nhận ACK nhưng chưa có observed state | Thời gian phát hiện; diễn giải trạng thái; thử ra lệnh; lỗi nguy hiểm | Nhầm ACK với thực thi; nhầm dữ liệu cũ với hiện tại |
| Reset, giữ phiên hoặc xuất log | Log được giữ; hủy có trả đúng bối cảnh không | Mất dữ liệu hoặc focus lạc |

Sau task, lấy đánh giá ngắn về độ rõ ràng, mức tự tin và công sức; ghi lỗi theo mức ảnh hưởng và sửa vòng kế tiếp. Đánh giá thẩm mỹ riêng bằng ảnh/trạng thái thật, không dẫn dắt bằng từ “cao cấp”. Nếu so với GCS hiện có, dùng task tương đương, đảo thứ tự trình bày, cùng phần cứng/điều kiện và ghi rõ phiên bản. Chỉ đặt ngưỡng tốc độ sau khi có baseline; ưu tiên không tăng lỗi quan trọng. Chưa chạy thử operator hay benchmark cạnh tranh trong UX01.

Kết quả hiện tại và ảnh kiểm: [COMPLETION-UX01](../delivery/COMPLETION-UX01.md). Tiêu chí triển khai: [UIUX-DESIGN-STANDARD](UIUX-DESIGN-STANDARD.md).
