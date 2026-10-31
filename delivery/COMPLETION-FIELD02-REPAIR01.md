# FIELD02 repair01: bàn giao kiểm chứng

**NOT READY. Đã triển khai sửa cô lập và kiểm mock/Android; chưa đóng toàn bộ lỗi chặn.**

Ngày 22/10/2026. Phạm vi: client Android 13/API33 arm64, WebView101, development APK giữ nguyên, companion laptop và dữ liệu mô phỏng. Không có HeraHub, Xiaomi, camera/gimbal thật hoặc ký production. Báo cáo FIELD02 ban đầu và mọi lượt FAIL được giữ nguyên.

## Kết quả theo yêu cầu

| Hạng mục | Kết quả | Bằng chứng và giới hạn |
|---|---|---|
| Video khởi tạo | PARTIAL | Sửa vòng đời decoder: cấu hình một lần sau keyframe mạng hợp lệ, giữ fence epoch/config/timestamp và recovery. Lượt cuối initial-ready 1.337,9 ms đạt sàn 1.500 ms trên emulator đang chạy; chưa kiểm lại cold boot hoàn toàn với source cuối. Lượt cold boot trước vẫn lỗi 2.009,5 ms. |
| FPS và độ trễ video | FAIL | Lượt cuối 239 frame/30.044,8 ms = 7,95 FPS, dưới 24; P95 upper source→canvas 573,08 ms, vượt 300. Không đổi profile, clock bounds hay tiêu chí. |
| Mất relay video | PASS trong lượt cuối | Ngắt 500 ms, phục hồi 708,9 ms, dưới 2.000 ms; kiểm đúng config và timestamp nguồn mới. Đây là hình tổng hợp qua mạng, không phải độ trễ camera thật. |
| Tương phản DAY | PASS vùng lỗi đã kiểm | Pixel Android thực: thông báo lỗi 5,67:1; tuổi video còn mới 7,12:1, trên 4,5:1. Không suy ra toàn bộ giao diện hoặc mọi màn hình đã được chứng nhận. |
| Thu hồi quyền payload | PASS mock/WAL; live NOT CHECKED | Xóa quyền trong RAM ngay, lưu receipt có pre/post, station/client/run/boot/model/plan và seq/hash; đợi ghi bền vững trước tác động fault. Lỗi ghi phải fail closed. Chưa có quan sát lease đang hiệu lực tại reboot ArduPilot thực. |
| Android–SITL và regression cuối | NOT RUN | Chưa thực hiện nominal AUTO cùng media và reboot với lease hiệu lực; chưa kiểm lại persistence/restart/SAF trên source cuối. Bằng chứng cũ không thay regression mới. |
| Bảo toàn dữ liệu | PASS baseline khai báo | 1.486 file bảo vệ, 1.081 file FIELD02 cũ và 7 file native không lệch SHA. Không tuyên bố toàn repository nguyên vẹn: 95 đường dẫn Git-deleted đã có trước task. |
| Tài nguyên | FAIL điều kiện liên tục | Controller ghi mức trống thấp nhất 421.421.056 byte, khoảng 0,39 GiB. Guard đã đóng companion/emulator nhưng không bảo đảm giữ liên tục sàn 20 GiB. |

## Những thay đổi đã có trong source cô lập

Video có chẩn đoán keyframe mạng giữ đúng byte/SHA; đối chiếu decoder với producer hoạt động và đã dừng, đo riêng từng giai đoạn khởi tạo. Bỏ cấu hình/reset dư trước keyframe đầu tiên. Giảm cập nhật bảng trạng thái thường lệ xuống tối đa 10 Hz, giữ xử lý frame, đo lường, lỗi và sự kiện quan trọng theo từng sự kiện. Scheduler nguồn theo pha 30 Hz tuyệt đối, tối đa một capture mới mỗi callback; ghi riêng missed scheduled slots và credit skips, không tạo frame bù hoặc làm giả timestamp.

Trong lượt cuối, snapshot nguồn ghi 900 slot = 817 lần eligible + 83 slot lỡ; 574 lần bị chặn vì đủ credit. Khoảng chờ output encoder trung vị khoảng 212 ms bao gồm queue/callback scheduling, không phải riêng thời gian codec. Dữ liệu cho thấy áp lực đường encode/credit, chưa cô lập được nguyên nhân hoặc phần ảnh hưởng của tải host. Không có bằng chứng cải thiện hiệu suất ổn định, không chọn riêng lượt tốt để công bố đạt.

Receipt quyền payload gắn chính xác phiên và danh tính nhiệm vụ, không chứa bearer token. Thu hồi có thứ tự ghi WAL trước tác động fault, không tự khôi phục quyền sau restart. Validation loại action/context sai trước invalidation. QA độc lập đạt 10 nhóm authority và 4 nhóm handler với mock/real local WAL; đây không phải bằng chứng autopilot hoặc payload thật đã thực thi.

## Các lượt video được giữ riêng

| Lượt | FPS | P95 upper | Initial-ready | Giới hạn |
|---|---:|---:|---:|---|
| app03 | 19,83 FAIL | 222,58 ms PASS | 2.009,5 ms FAIL | Cold boot emulator 4 CPU, không diagnostic trước viewer |
| app04 | 6,90 FAIL | 660,04 ms FAIL | 1.239,9 ms PASS | Process mới trên emulator đang chạy, instrumentation |
| app06 | 22,87 FAIL | 171,98 ms PASS | 490,9 ms PASS | Presentation tối ưu, vẫn dưới 24 FPS |
| app07 cuối | 7,95 FAIL | 573,08 ms FAIL | 1.337,9 ms PASS | Source theo pha; chưa chứng minh cold boot source cuối |

Mọi lượt dùng VP8 1280×720/30 FPS, 4 Mbps do người kiểm chọn rõ; H264 encoder không được WebView này hỗ trợ. Không trộn FPS một lượt với latency của lượt khác. Hai lượt emulator đầu/cuối thực tế lần lượt 2/4 CPU; sai lệch harness 2 CPU ban đầu có hồ sơ hiệu chỉnh, không gắn nhãn lại dữ liệu.

## Sự cố dừng kiểm và phần chưa chạy

Companion app07 đóng lúc 02:48:48 UTC vì RESOURCE_STOP_PROTECT20GIB; emulator đóng lúc 02:49:07 UTC vì GUARD_PROTECT20GIB. Mức trống tối thiểu khoảng 0,39 GiB là vi phạm thực tế, không phải PASS bảo vệ sàn. Dung lượng sau đó phục hồi khoảng 31,4 GiB tại kiểm cuối. Chưa xác định tác nhân tiêu thụ/giải phóng dung lượng; không quy nguyên nhân cho tiến trình khác từ suy đoán.

Thao tác chọn mode cuối không có hiệu lực: GET state xác nhận kết nối MOCK, run m93498c6ac9f741b39d44, không phải ArduPilot/SITL. Đây là lỗi thao tác QA được giữ trong hồ sơ; không đổi nhãn hoặc retry ngầm. Repair01 có **0 lượt AP mới**. Bảy yêu cầu SITL trước đây vẫn giữ nguyên. Hai launch emulator của ngân sách sửa đã sử dụng; không tự mở thêm lượt sau sự cố.

Do đó, còn thiếu kiểm nominal AUTO đồng thời video, reboot thực khi lease còn hiệu lực, từ chối lệnh sau fault trong context thực và regression persistence/restart/SAF trên Android cuối. Các script chuẩn bị chưa chạy không được tính PASS. Kết quả nominal/fault/SAF FIELD02 trước vẫn hợp lệ trong phạm vi lịch sử đã báo.

## Bảo toàn và đóng tài nguyên

Kiểm cuối không có drift trên baseline, native, evidence cũ, 31 đường dẫn freeze media và 57 đường dẫn pin flight. Không sửa source/candidate đóng băng, ENDURE, trust hoặc SOT cũ. Không tạo APK/chữ ký mới. APK development02 vẫn có SHA256 `df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d`.

Đã đóng toàn bộ companion/emulator/observer của repair; không còn listener 8872/8873/5972/5582/5583 hoặc container aeris-field02. Chỉ dọn stage tự tạo 4.716.318 byte, OCR binary 97.400 byte và cache Swift 257.790.450 byte đã dọn trước đó. Docker image prune thu hồi 0 byte; không prune container/volume. Giữ APK, AVD và toàn bộ bằng chứng, khoảng 15 MiB mới trong ngân sách 192 MiB.

## Hướng tiếp tục

1. Giữ FIELD02 NOT READY. Không mở thêm vòng chỉnh timeout hoặc giảm chuẩn FPS để nghiệm thu.
2. Tách bài đo nguồn hình trên host và Android chỉ nhận/giải mã để đối chiếu topology camera thực tế, có source freeze và ngân sách mới; chưa triển khai trong repair này. Giữ profile/clock/identity và cùng cửa sổ đo. Kết quả hiện tại không chứng minh phương án đó nhanh hơn.
3. Khi môi trường dung lượng ổn định và mở ngân sách kiểm mới, xác minh mode SITL từ trạng thái thật trước mọi action; kiểm hai kịch bản nhiệm vụ/reboot, sau đó regression restart/SAF và cold boot source cuối.

Không có runtime AI trong đường chạy này; đối chứng LLM trực tiếp không áp dụng. Chưa đo hiệu quả người dùng, Xiaomi, phần cứng Hera, thermal radiometric, geotag thời điểm phơi sáng, production hay nghiệm thu ENDURE.

## Hồ sơ

- [TIP repair01](../planning/field02/TIP-REPAIR01.md)
- [QA độc lập cuối](../evidence/field02/repair01/qa-final-repair01.json)
- [QA video cuối](../evidence/field02/repair01/qa-media07.json)
- [Pixel Android DAY](../evidence/field02/repair01/qa-day-pixels01.json)
- [QA quyền payload](../evidence/field02/repair01/qa-authority03.json), [QA handler fault](../evidence/field02/repair01/qa-app-fault04.json)
- [Sự cố tài nguyên](../evidence/field02/repair01/resource-incident01.json), [observer closure](../evidence/field02/repair01/observer-closure01.json)
- [Kiểm SHA/closure cuối](../evidence/field02/repair01/final-verification.json)
- [Builder closure](../planning/field02/repair01/authority-ui-builder-closure.md)
- [Báo cáo FIELD02 gốc giữ nguyên](COMPLETION-FIELD02.md)
