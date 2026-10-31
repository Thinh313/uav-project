# COCKPITVIDEO04: video host trong cockpit Android

Ngày 22/10/2026. **PARTIAL / NOT READY cho nghiệm thu đồng thời nhiệm vụ, video và payload.** Code cô lập đã có và mock đã kiểm; không ký APK mới. Các phép kiểm riêng lẻ đạt không thay thế phép kiểm kết hợp còn thiếu.

## Kết quả dùng được

Cockpit khảo sát → preflight → Fly → review dùng APK development02 đã cài, giữ nguyên SHA. Laptop Chrome phát nguồn RGB/thermal-look tổng hợp; Android chỉ nhận/giải mã video liên tục. Panel vẫn hỗ trợ chụp một frame JPEG tổng hợp theo contract cũ, đây là thao tác mã hóa ảnh đơn chứ không phải encoder video trên Android. Không có publisher iframe hoặc VideoEncoder trong receiver panel mới.

Đã thêm trạng thái nguồn/freshness, start/stop rõ ràng, stop khi lifecycle đổi, xử lý lỗi chụp và hồ sơ đối chiếu riêng gắn SHA của báo cáo video với danh tính nguồn, phiên AP, boot, model và plan. Chọn video không cấp quyền bay hoặc payload. Giữ camera/gimbal mock, ảnh thực bằng 0, thermal không đo nhiệt. Đây là cấu hình host companion: phần điều khiển MAVLink chạy Node trên laptop, không chứng minh một APK điều khiển Hera độc lập.

## Kiểm đã chạy và giới hạn

| Phạm vi | Kết quả thực tế | Kết luận |
|---|---|---|
| Contract mock và regression | Builder kiểm các nhóm contract, HTTP mock, helper, panel; QA độc lập 8 ca mock và 4 ca capture/UI. Generation02 kiểm 5 nhóm static và 4 nhóm pin độc lập. Không cộng các nhóm có thể trùng thành một tỷ lệ sản phẩm. | PASS trong phạm vi từng báo cáo |
| Android | Android 13/API33, emulator-5582, 4 CPU/2 GiB, WebView101. APK SHA `df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d` không đổi. Cockpit và receiver tải/chạy thực. | Đã kiểm trên emulator; chưa HeraHub/Xiaomi |
| Nhiệm vụ SITL lượt01 | Run `s48d15d007cba435b87c9`: 12 lệnh upload đúng trường, 24 mục readback qua hai chu kỳ, bốn lệnh camera206, AUTO/navigation/RTL/ground-disarm, review accepted. Không PARAM writes. | PASS nhiệm vụ generic quad; camera upload không phải exposure |
| Video lượt01 | 897 frame / 30.001,8 ms: **29,8982 FPS**; P95 upper **59,2769 ms**; explicit viewer start → fresh **261,1 ms**. 0 consumer drops, decoder errors và API failures trong cửa sổ đo. | PASS các ngưỡng này trong một cửa sổ; không phải độ tin cậy mọi thiết bị |
| Đồng thời video/payload khi bay | Sidecar lượt01 hợp lệ về SHA/clock, nhưng có **0 điểm lệnh payload AUTO đủ điều kiện**. Fault relay500ms nằm ngoài cửa sổ video. Lượt02 guard từ chối capture vì đã hạ cánh. | NOT CHECKED cho nghiệm thu kết hợp/recovery |
| Generation02 thực | Run `s6b9520caba1c4186833e`, request10: kết nối và preflight chỉ đọc READY; không grant/upload/readback/arm/AUTO. Viewer từng nhận frame rồi báo `CLOCK_CALIBRATION_UNKNOWN`; publisher kết thúc `SOURCE_CLOCK_RECOVERY_BOUND`. Không có báo cáo30s. | PARTIAL; không thay thế lượt01 |
| Reboot khi payload lease còn hiệu lực | Chưa chạy được kịch bản yêu cầu. Không có request11. | NOT CHECKED, chặn nghiệm thu |
| Persistence | Ba cold boot giữ dữ liệu native. Cohort03 giữ đúng SHA của 14 artifact/mirror cũ; journal cũ giữ nguyên prefix và thêm một `MIRROR_COMMITTED` 470 byte. Tổng file15→16. QA kiểm đúng chain27 record; không khôi phục quyền. | PASS bảo toàn/mirroring đã quan sát; không chứng minh mọi fault storage |

Nguyên tắc hoàn tất takeoff của lượt01 dùng verifier Takeoff01 đóng băng: CURRENT/climb/transition thay cho thông điệp MISSION_ITEM_REACHED của seq1 không xuất hiện. Raw và quy tắc suy ra được lưu rõ; không giả thông điệp bị thiếu. Dữ liệu AP dùng ArduCopter4.7.1 internal quad, speedup1, không phải vật lý Hera đã hiệu chuẩn.

## Hai lỗi chặn cần xử lý tiếp

1. **Clock/source lifecycle:** viewer không tìm được probe clock hợp lệ; publisher hết ngân sách khôi phục freshness. Tab Chrome khác từng được quan sát đang foreground, nhưng thứ tự visibility/calibration/rejection chưa đủ để kết luận nguyên nhân. Không khẳng định đơn giản là hết hạn clock hoặc do background. Cần journal chẩn đoán có giới hạn cho từng probe, rejection, epoch/config và visibility; kiểm race giữa renewal định kỳ với reactive recovery bằng mock trước. Giữ nguyên các ngưỡng và không tự reconnect.
2. **Harness UI theo tọa độ chưa ổn định:** checklist/profile và nội dung panel làm nút dịch chuyển. Một số tap không tạo action điều khiển nào; timeout và lần ngắt helper được giữ. Cần nhận diện nút từ trạng thái UI hiện tại, kiểm action receipt sau từng bước trước khi chạy kịch bản airborne. Không thay bằng control POST ẩn.

Đã chuẩn bị fixture corridor dài hơn và adapter test riêng generation02, nhưng chưa nghiệm thu nó khi bay. Offset ngang3× quanh Home không cho thời gian tuyến3×: compiler thực cho80,6867m /2m/s =40,3434s. Cap9/pin gốc không đổi; adapter mới giới hạn tổng11 request, lưu chín request trước và từ chối request12. Request10 đã được tiêu thụ dù chưa arm. Không tự mở thêm phiên trong tác vụ này.

## Bảo toàn và tài nguyên

QA rehash: protected baseline1486, native7, old FIELD02 evidence1496, frozen current source93 đều **0 sai lệch**. Generation02 source19/pin101 và archive13 file generation01 cũng đúng SHA. Chỉ thêm ba thư mục SITL mới theo lịch sử của tác vụ; không sửa dữ liệu run cũ. Baseline có95 đường dẫn Git đã thiếu từ trước, nên không tuyên bố toàn repo không thiếu file. Bảy symlink fixture được đối chiếu đúng semantics dereference của baseline; không chứng thực literal link target.

Hai admission generation02 bị từ chối vì dung lượng dao động trước khi tạo emulator/process/AP request. Sau dừng host,31 mẫu độc lập đã ổn định rồi mới admission lại bằng cùng gate. Lỗi sandbox listen EPERM và mọi refusal được giữ; không sửa controller để lách gate. Cuối tác vụ các PID/cổng riêng đã đóng, container `aeris-field02` không còn. Mức trống thấp nhất được log emulator là khoảng30,03GiB; số đo và guard không chứng minh mọi thời điểm không được lấy mẫu. Không có soak, selection, trust, source/candidate hay lịch sử ENDURE bị thay đổi.

Đã dọn riêng stage132 file/4.716.332 byte và cache/binary QA OCR262 file/258.104.562 byte do tác vụ tạo. Giữ source và toàn bộ evidence. `docker image prune -f` thu hồi0B; không prune container/volume. Cuối dọn còn khoảng35,48GiB.

## Hồ sơ và cách tiếp tục

- [TIP và ranh giới](</Users/os/Downloads/AI technique/aeris/planning/cockpitvideo04/TIP.md>), [bàn giao Builder](</Users/os/Downloads/AI technique/aeris/planning/cockpitvideo04/BUILDER-HANDOVER.md>).
- [QA độc lập cuối](</Users/os/Downloads/AI technique/aeris/evidence/field02/cockpitvideo04/qa-final-independent-supplement02.json>), [raw nhiệm vụ đạt](</Users/os/Downloads/AI technique/aeris/evidence/field02/cockpitvideo04/qa-raw-nominal01.json>), [đối chiếu media](</Users/os/Downloads/AI technique/aeris/evidence/field02/cockpitvideo04/qa-media-nominal01.json>).
- [Chẩn đoán clock và phép kiểm kế tiếp](</Users/os/Downloads/AI technique/aeris/planning/cockpitvideo04/BUILDER-MEDIA-CLOCK-SUPPLEMENT.md>), [disposition generation02](</Users/os/Downloads/AI technique/aeris/evidence/field02/cockpitvideo04/generation02-disposition01.json>).
- [Đóng runtime](</Users/os/Downloads/AI technique/aeris/evidence/field02/cockpitvideo04/closure-final01.json>), [dọn dữ liệu sinh](</Users/os/Downloads/AI technique/aeris/evidence/field02/cockpitvideo04/cleanup01.json>).

Code/stage có thể dựng lại từ nguồn và manifest, nhưng không nên chạy thêm cohort trước khi sửa harness/đo clock và chốt ngân sách kiểm mới. Bước nghiệm thu còn lại là một cửa sổ video30s đủ ngưỡng có camera/gimbal mock trong AUTO thật, fault relay trong chính cửa sổ đó, rồi một run riêng reboot với lease còn hiệu lực và kiểm từ chối quyền cũ. Chưa ký mới, chưa thiết bị thật, chưa production.

**VERIFY:** user outcome triển khai được receiver host vào cockpit nhưng chưa chứng minh toàn hành trình đồng thời; requirement coverage theo bảng trên; giá trị đo được là hiệu năng một cửa sổ và nhiệm vụ SITL riêng, chưa có benchmark ngang điều kiện để tuyên bố hơn topology cũ. Baseline LLM không áp dụng cho công việc transport xác định này. **OVERALL STATUS: NOT READY.**
