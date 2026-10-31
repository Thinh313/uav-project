# RUNTIME-EVIDENCE05

Đã hoàn tất phần sửa source và kiểm mock/replay cho pipeline ACK/DTO, cùng gate từ chối trước launch. **Chưa đạt Android–SITL hay beta 30 phút.** Không mở campaign mới, build APK, ký mới hoặc chọn candidate.

## Kết quả có bằng chứng

| Hạng mục | Kết quả | Phạm vi |
| --- | --- | --- |
| Observer và lưu ACK/DTO một lần | PASS mock | 46/46 kiểm độc lập trên source 69 file |
| Đọc lại bằng tiến trình mới | PASS replay | 313 snapshot gốc, tổng 2.066.711 byte, phục hồi đúng byte/SHA |
| Admission từ chối trước thực thi | PASS mock | 14/14 kiểm độc lập trên source 71 file |
| STATUS/Android–SITL mới | CHƯA KIỂM | Chưa đủ contract toàn pipeline |
| Bay 30 phút, mất link, restart thực | CHƯA KIỂM | Không dùng mock làm chứng cứ nghiệm thu bay |

Observer dùng một luồng logcat có marker xác nhận sẵn sàng trước Intent; ACK/DTO lưu với tham chiếu, SHA, nonce, tiến trình, context và clock gốc. Kiểm lỗi bao gồm dữ liệu mới chưa thấy, ACK phân mảnh, sai nguồn/nonce/PID, fsync lỗi, hết quota, ghi đồng thời và đóng luồng thiếu EOF. Lỗi phải từ chối, không khôi phục quyền.

Envelope observer thử nghiệm được khai báo chặt hơn: 32 request, 128 command mỗi vòng đời, tối đa 128 KiB cho từng luồng stdout hoặc stderr của mỗi command (tổng hai luồng có thể là 256 KiB). Quá giới hạn thì giữ prefix lỗi và từ chối, không coi là capture hoàn chỉnh. Trần protocol gốc 2.048 request vẫn còn; envelope mới không đủ để công bố hỗ trợ session 30 phút hay mọi thao tác screenshot/export. Chưa kiểm screenshot lớn hơn 128 KiB qua đường mới.

Gate mới đối chiếu Inventory hiện tại, source và vị trí ghi đã pin, lưu lý do từ chối trước khi đăng ký case, tạo thread, chuẩn bị native hay dispatch tiến trình con. Đã kiểm N/N+1, ghi đồng thời, fsync các thư mục mới, lỗi fsync, traversal và source/site/policy drift. Bản ghi từ chối chỉ được xác nhận bền vững khi còn quota cho entry và fsync thành công; nếu không, gate báo lỗi UNDURABLE và không launch. Registry có 15 nhóm owner và 119 vị trí IO/FD/print tiềm năng; việc liệt kê này **chưa chứng minh mọi writer đã được tích hợp**.

## Vì sao chưa mở lượt bay

Tổng các mức dự phòng tối đa đã biết là **126.894.080 byte (121,02 MiB)**, vượt trần metadata **67.108.864 byte (64 MiB)** trước khi cộng dữ liệu hiện có và những writer chưa có giới hạn. Đây là tổng mức cho phép trong contract, không phải lượng dữ liệu audit thực tế đã đo. Một audit đang được phép tới 64 MiB nên không thể đồng thời dành chỗ cho observer, lifecycle và đóng hồ sơ dưới cùng trần 64 MiB.

Các khoảng trống còn phải đóng:

1. Áp ngân sách trước ghi cho toàn bộ writer, giới hạn capture/pipe và đường drain; làm báo cáo audit gọn bằng tham chiếu tới raw được giữ nguyên.
2. Đóng lỗi sau CONNECTED với bằng chứng ground, journal và quyền sở hữu đầy đủ. Đóng observer không chứng minh AP an toàn hay đã đóng hết owner; trạng thái connected/unknown/armed vẫn bị chặn.
3. Tạo observer/bridge mới khi Android restart, liên kết hồ sơ trước/sau. `supervisor.verify_restart` hiện dùng lại bridge cũ, trong khi bridge đúng quy tắc phải từ chối process epoch mới; đây là lỗi tích hợp đã xác định.
4. Sau các gate trên mới kiểm STATUS và SITL ngắn. EKF `0xa7`, quota frame và chứng cứ đóng native từ lượt trước vẫn là các gate riêng chưa được giải quyết trong task này.

## Diễn giải phép đối chiếu

Trace cũ có 49.546 lần xuất hiện JSON nhưng chỉ 315 dòng JSON duy nhất. Replay phục hồi đúng các dòng và 313 snapshot khớp được; hai dòng không ghép snapshot vẫn được giữ. Marker replay là dữ liệu tổng hợp, không phải readiness Android thật. Các nhóm replay tối đa 32 request không chứng minh một session dài 313 request được phép chạy.

Bộ biểu diễn offline mới chiếm 5.390.336 byte cấp phát. Thư mục cũ 52.772.864 byte còn chứa nhiều loại output khác nên **không dùng hai số này để công bố tỷ lệ tiết kiệm toàn pipeline**. Chưa đo latency/FPS/pacing hay dung lượng khi chạy live. Kiểm thêm 32 blob mới không nén được, mỗi blob 131.072 byte, đã phục hồi nguyên vẹn. Công việc này là sửa deterministic IO; không dùng LLM làm baseline cho phép kiểm byte.

## Source, bảo toàn và bàn giao

Hai biến thể cô lập được giữ riêng, chưa chọn làm candidate:

- Observer 69 file: `200f532b8761480aea0aa747b779c214555352ad7334fb19d4ed9f9652d8892c`.
- Gate từ chối 71 file: `aac335f8b7c8dd272f45eb77f3bcfd06ccae0e29f568021967a9b12b2f967768`.

Root kiểm độc lập toàn bộ pin của hai biến thể, parse Python và 20 tham chiếu bằng chứng. Kiểm bảo toàn lúc 02:10 UTC đối chiếu 17.117 đường dẫn legacy, 29 inventory niêm phong, native source 50 file và cây nội dung OBSERVE04: không có drift mới; 165 đường dẫn thiếu từ trước giữ riêng. OBSERVE04 thay đổi 65.536 byte cấp phát vật lý nhưng cây byte/path/size/mode vẫn khớp; không sửa seal cũ hoặc suy ra hiện diện liên tục. Không sửa source/candidate gốc hay lịch sử ENDURE; không tuyên bố ENDURE đạt.

Đã xóa scratch của mock, replay, integration và QA trong thư mục task. Không có bản sao cả dự án, dependency install, build hay Docker mới.

Bằng chứng chính: `evidence/runtime-evidence05/ROOT-VERIFY01.json`, `qa/SOURCE-MOCK-GATE01.json`, `qa/NEGATIVE-INTEGRATION-GATE01.json`, hai checkpoint của Builder và `preservation-final01.json`. Báo cáo cũ có lỗi được giữ làm lịch sử, không cộng dồn số test qua các lượt.

**Trạng thái bàn giao: source/mock và gate từ chối đã đạt; toàn runtime NOT READY.** Bước kế tiếp cần là một thay đổi thống nhất về writer budget, audit và vòng đời owner/restart, rồi nghiệm thu lượt ngắn trước khi cho phép 30 phút.
