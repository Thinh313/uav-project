# BETA06 G5 · Ghép sửa lỗi kết thúc phiên

22/10/2026 · **Source/mock: đạt trong phạm vi SITL cô lập. Sản phẩm beta: NOT READY.**

Đã ghép hai sửa lỗi R2 vào đường gọi thật của ứng dụng G5 cô lập. Sau khi phát hiện máy dùng pin 6%, người dùng chọn “Chỉ ghép code và kiểm mock lúc này”. Vì vậy phiên này không mở host listener, Android/emulator hoặc AP mới. Mọi kết quả G5 về AUTO/video/payload thực, mất link, reboot, restart, persistence Android và SAF đều **NOT_RUN_USER_DEFERRED**.

## Đã thay đổi

1. Controller dùng completion cùng telemetry mới, đúng run/boot/client/config/model/plan để cho phép Close; không đợi nhãn DISARMED khi stage AUTO còn giữ lại. Vẫn kiểm hình học/UI và gửi nhiều nhất một lần.
2. Sau Close/cut/reboot/abort SITL, ứng dụng đọc review/closure đã seal, kiểm byte/SHA và ghi tham chiếu nhỏ vào journal. Không đưa map 842 khóa vào serializer giới hạn 64 khóa.
3. Khi ghi chỉ mục, lưu outcome hoặc phản hồi sau tác dụng gặp lỗi, UI hiển thị chưa xác nhận và ứng dụng chặn tiến trình tiếp theo. Không báo “chưa thực thi”, không retry tác dụng đã hoàn tất và không khôi phục quyền.
4. Lịch sử review đọc lại tham chiếu đã kiểm, giữ kết quả execution và phân biệt kết quả lưu trữ với nghiệm thu raw. Gate restart yêu cầu chỉ mục bền vững, receipt và raw N1/F1 khớp.
5. Mỗi lượt đọc completion ghi trace theo chuỗi SHA, giữ projection các trường quyết định cùng tuổi dữ liệu và timestamp của từng lần đọc. Đây là các lần đọc tuần tự trong cùng poll, không phải toàn trạng thái nguyên tử. Vượt giới hạn hoặc lỗi writer sẽ chặn input.

## Kết quả kiểm chứng

| Phần | Kết quả |
|---|---|
| Controller → R2 → phase policy → dispatch | PASS SOURCE/MOCK; 12 nhóm kiểm mục tiêu của Builder, được QA đối chiếu thêm. |
| Handler thật → review seal → R2 → Store01 | PASS với tác dụng bay được stub; gồm review 842 khóa, Close và các kết thúc SITL không được nghiệm thu. |
| Lỗi sau tác dụng | PASS các ca quota, fsync, mất receipt, ghi ACTION_END/outcome lỗi, seal thiếu hoặc sai. Không có lệnh bay thật trong các ca này. |
| Lịch sử và tải lại store | PASS SOURCE/MOCK; gồm reload và từ chối tham chiếu bị thay đổi. Chưa kiểm Android restart. |
| UI và asset | PASS kiểm hàm UI trong VM và đường GET của handler không mở listener; bootstrap giữ đúng SHA, UI G5 được trỏ đúng nguồn. Chưa kiểm hình ảnh/FPS trên Android. |
| Guards và replayer | Chuẩn hóa namespace được đối chiếu; thuật toán raw, clock, authority, deadline và ngưỡng tài nguyên giữ nguyên. |
| Dung lượng trace | Projection đại diện: 721 poll và dispatch khoảng 2,46 MB, dưới giới hạn 4 MiB. Đây là dự toán từ fixture đã giữ, không phải số đo runtime G5. |

Gate QA độc lập kết luận PASS trong phạm vi tích hợp source/mock đã đóng băng, không còn P1 chưa xử lý trong phạm vi đó. Đây không phải quyền khởi động runtime hoặc nghiệm thu sản phẩm.

Không cộng số nhóm Builder với những lần QA chạy lại để quảng bá thành số chuyến bay hoặc tỷ lệ trưởng thành.

## Giới hạn quan trọng

G5 là bản engineering cho **SITL**. “Mock/replay” trong báo cáo này chỉ phương pháp kiểm code với tác dụng SITL được thay bằng fixture. Nó khác lựa chọn **mode=mock** của giao diện cũ.

Contract R2 yêu cầu review SITL và closure sở hữu đúng định danh. Chế độ mock giao thức cũ không có bằng chứng tương đương, nên bước đóng sẽ trả UNVERIFIED và dừng. Không tuyên bố hành trình mock UI cũ hoặc mọi chế độ đã tương thích. Trước nghiệm thu sản phẩm cho mọi chế độ, cần contract lưu trữ riêng cho chế độ đó hoặc điều chỉnh phạm vi UI rõ ràng.

Không dùng kết quả N1 G4 trước đây để lấp nghiệm thu G5. Chưa có kiểm mới trên Android, SITL, camera/gimbal thật hoặc HeraHub. Không build, cài lại hay ký APK.

## Bảo toàn

- 6.334 đường dẫn trong baseline trước tích hợp giữ nguyên loại file/link, mode, byte và SHA.
- 700 pin G5 khớp; helper freeze gồm 21 file, trong đó có policy R2 thực sự được import. Các pin G4 và bằng chứng chiến dịch lỗi cũ giữ nguyên.
- Workspace G5 là bản sao riêng gồm 20 file/870.221 byte. Workspace02 G4 không bị ghi thêm; bản sao chưa được mở bởi writer runtime.
- Candidate, ENDURE, lịch sử lỗi/receipt cũ và dữ liệu Android không bị chỉnh sửa. 95 đường dẫn lịch sử đã thiếu trước phiên vẫn được ghi nhận riêng; không có khẳng định toàn repository luôn hiện diện đầy đủ.
- Dung lượng trống ghi nhận lúc lưu nghiệm thu là 38,03 GiB, trên sàn 20 GiB. Không có copy toàn dự án, dependency install hoặc build mới.
- Đã dọn fixture tạm theo receipt Builder/QA và riêng planning/beta06g5/__pycache__ gồm 5 file pyc. Các fixture lỗi được giữ làm bằng chứng trong generation05; không xóa dữ liệu lịch sử.

## Bàn giao

Entry ứng dụng: pilot/beta06g5/app.mjs. Controller và bộ đối chiếu: planning/beta06g5. Kế hoạch chạy tương lai vẫn hữu hạn: một cửa sổ host 2.700 giây, tối đa bốn AP N1/F1/N2/F2, một managed restart; boot thứ hai chỉ kiểm persistence. Không tự mở lại G4, reset latch, tăng ngưỡng hay ký mới.

Khi người dùng tiếp tục phần runtime, kiểm lại nguồn AC, dung lượng ổn định tối thiểu 29 GiB, pin/baseline và quyền browser; sau đó mới chạy các gate thực đã chuẩn bị. Các thao tác SAF phải giữ quota và có bằng chứng provider/byte/journal riêng.

**Giá trị đã chứng minh:** đường tích hợp source/mock xử lý đúng hai nguyên nhân lỗi đã quan sát và không báo sai tác dụng Close. Hiệu năng và hành vi bay G5 chưa đo. Đối chứng LLM trực tiếp không áp dụng cho phần deterministic này.

## Hồ sơ

- [Gate QA độc lập: source/mock đạt, runtime chưa chạy](../evidence/beta06/generation05/qa-source-mock-gate05.json)
- [TIP và phạm vi người dùng đã điều chỉnh](../planning/beta06g5/TIP-INTEGRATED-CLOSE05.md)
- [Handover ứng dụng](../planning/beta06g5/BUILDER-FLIGHT-HANDOVER05.md)
- [Handover controller/native](../planning/beta06g5/BUILDER-NATIVE-HANDOVER05.md)
- [Pin ứng dụng](../evidence/beta06/generation05/flight-pins.json)
- [Freeze source](../evidence/beta06/generation05/builder-source-freeze01.json)
- [Freeze helper](../evidence/beta06/generation05/native-helper-freeze05.json)
- [Đối chiếu bảo toàn của Root](../evidence/beta06/generation05/root-final-source-preservation05.json)
- [Phạm vi chỉ code/mock](../evidence/beta06/generation05/root-scope-disposition02.json)

