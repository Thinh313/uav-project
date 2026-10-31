# M1: hoàn tất phần hardening offline lifecycle05

20/10/2026. **Phần kiểm và sửa lifecycle offline đã đạt; M1 toàn sản phẩm vẫn NOT READY.** Thực hiện trong lúc người dùng dọn dung lượng, đúng giới hạn chỉ sửa và kiểm mock/replay. Chưa chạy Android/SITL, build APK, ký, sửa ENDURE hoặc chọn candidate mới.

## Kết quả có ích

Đã dùng harness chạy trực tiếp top-level controller thực dưới các boundary được inject, thay vì chỉ kiểm helper hoặc AST. Ba lỗi của runtime04 được tái hiện và sửa riêng trong runtime05:

- Tạo peer thất bại sau khi mở console có thể để file mở và trả exit0. Nay console được đóng độc lập với việc đã gán được peer hay chưa.
- BOOTSTRAP_EOF đã xuất hiện trước có thể bị lỗi probe đến sau ghi đè trong closure. Nay giữ lỗi được latch đầu tiên và các lỗi phụ riêng, có nguồn và timestamp.
- Ghi closure/fsync lỗi vẫn có thể in CLOSED None và trả exit0. Nay trạng thái ghi bền chưa đạt không được coi đóng sạch và caller nhận verdict thất bại.

QA còn phát hiện lỗi trong bản sửa đầu: sys.exit trong finally có thể che BaseException. Đã tái hiện trước/sau sửa; bản cuối không phát seal thành công khi ngoại lệ nghiêm trọng đang truyền ra. Giữ các phiên bản và trace trước sửa. Hai vấn đề của harness (thời điểm khôi phục API quá sớm, một JSON hỏng làm mất các receipt khác) cũng được sửa trước khi chốt QA, không tính thành lỗi sản phẩm.

## Kiểm chứng và phạm vi

| Lớp kiểm | Kết quả |
|---|---|
| Builder | 20 input được khai báo,28 lần thực thi controller gồm ca trước sửa, lỗi fixture và lượt kiểm nhắm đích |
| Bản05 lịch sử 7b977a… |19 ca được chọn đạt, có pin đúng phiên bản, không gắn lại thành kết quả chạy bản cuối |
| Bản cuối 586a0d… | Ca fatal nhắm đích đạt; QA độc lập12/12 ca đạt, đi đúng predicate cần kiểm |
| Tổng khai báo |32 input,40 lần thực thi, có phần giao nhau về hành vi; không phải32 tính năng hoặc32 chứng nhận độc lập |
| Phạm vi TIP offline |6/6 yêu cầu kiểm đạt; không chuyển thành tỷ lệ hoàn thiện phần mềm |
| Mã nguồn |4 tệp mới,39.870byte; APcommand construction và resource/deadline900s/ground-stop giữ nguyên |
| Bảo toàn |71.158 đường dẫn trước/sau khớp SHA,0 sai lệch tại checkpoint;192 native source pin và APK04 không đổi |
| Dung lượng |Trên sàn20GiB; chỉ dùng source/evidence nhỏ, không tải dependency hoặc tạo bản sao project |

Harness chỉ rebind root R sang scratch được đánh dấu; chạy các branch thật dưới fake Docker/process/socket/clock và lịch thread có kiểm soát. Digest firmware sentinel và parser HB/land/position là synthetic. Kết quả không chứng minh firmware, CRC, độ bền filesystem thật, mọi race thread, tốc độ hay động lực học bay. QA là agent độc lập với Builder, chưa phải human/hardware review. Các lỗi fixture và lần kiểm preflight QA dừng trước controller được giữ, không tính thành lỗi source hay PASS nhánh chưa đến.

Bằng chứng chính: `evidence/integration03-lifecycle05/qa/verification-final01.json`, `builder/source-ready02.json`, `root-verification-final01.json`; sourceId `bc50dfa5bdca8bcdd8de1f8a82bdbbfc128defc6ac7ef559dd90facd0f4c503d`. Runtime cũ/bootstrap04/source/candidate/canonicalSOT và hồ sơ ENDURE giữ nguyên.

## Quy tắc dùng bản sửa và phần còn thiếu

closure.json riêng lẻ không chứng minh phiên đóng sạch. Caller phải có exit0 của đúng process, seal CLOSURE05 đúng run/CID với CLOSED_SUCCESSFULLY và closurePersisted=true, cùng hồ sơ/raw vượt các receiver liên quan. Thiếu seal hoặc fatal phải giữ UNSEALED/UNKNOWN/FAILURE. Đã ghi overlay trình tự tiếp theo ở `planning/product-standard01/M1-ACCEPTANCE-SEQUENCE05.md`; runbook04 không bị ghi đè.

M1 còn các gate thực tế I01-I10: phiên dài và cohort đúng kiểu/freshness, nhiệm vụ KML→upload/readback→AUTO→review, hai operator độc lập/nhiều payload/partition/pilotloss, observer3D airborne30s, SAF đúng selectedrun và receiver, process/coldboot/preservation, UI và managed closure. P1 OPERATOR01 đã đạt scope riêng vẫn được giữ. Không chuyển acceptance đó sang cấu hình tích hợp mới. Nguyên nhân EOF thực tế trước đây vẫn UNKNOWN.

**Bước kế tiếp:** chỉ khi người dùng cho phép kiểm thực tế trở lại và tài nguyên đạt admission mới (29GiB ổn định trước boot,26,25GiB sau boot, guard21GiB giữ sàn20GiB), kiểm Android–SITL theo overlay05. Dung lượng tăng không tự kích hoạt chạy. HeraHub/PhaseOne/video thật và production còn gate riêng.

Đã dọn toàn bộ scratch mock trong repo; không xóa bằng chứng, không tạo scratch ngoài repo hay dùng Docker trong task này. Giá trị đã chứng minh là phát hiện/sửa cách ghi nhận lỗi và đóng phiên trong mock. Lợi ích runtime/performance chưa đo; không đưa ra tuyên bố vượt DJI hoặc phần trăm trưởng thành từ số ca kiểm.
