# RUNTIME-OBSERVE04

**Trạng thái: NOT READY cho nhiệm vụ Android–SITL hoàn chỉnh.** Nguồn AC và admission đã đạt. Bản APK development cô lập đã sửa đường STATUS qua Activity; Android giữ accessibility và vào CONNECTED. Lượt ngắn dừng vì metadata vượt 64 MiB trước khi preflight đạt, chưa cấp quyền hay đến bước ARM.

| Hạng mục | Kết quả thực tế |
|---|---|
| STATUS-only trên APK cũ | Bốn mục điều hướng còn nguyên. Không tái hiện được lỗi mất accessibility cũ. |
| STATUS-only trên APK mới | Đạt: PID ổn định; ACK/snapshot khớp process/view và nonce/SHA; bốn mục điều hướng hợp lệ; ảnh trước/sau giống byte. Android nhận → phát ACK 8,46 ms; vòng host 146,28 ms. |
| CONNECT sau sửa | Đã vào CONNECTED, owner hiện diện, không còn lỗi CONNECT_ACTIVITY_PAUSED trong đoạn đã quan sát. |
| Preflight | Chưa đạt: EKF_FLAGS_UNKNOWN_OR_UNQUALIFIED:0xa7. Không nới tiêu chí EKF. |
| Bay manual/assisted, thả cần/BRAKE/cấp quyền mới/LAND | Chưa được nghiệm thu. Lượt mới dừng trước các bước này. |
| Review, restart, export native cuối | Chưa kiểm được ở lượt mới. Emulator đã bị guard dừng. |
| Bằng chứng frame/journal và đóng nhiệm vụ | Không đạt để công bố hoàn chỉnh; giữ nguyên mọi prefix lỗi. |

## Nguyên nhân và thay đổi

Lượt đầu ghi CONNECT_ACTIVITY_PAUSED ngay sau một STATUS dùng am start vào Activity. Đây là nguyên nhân gần được hỗ trợ bởi source và thời điểm quan sát; chưa có trace Android đủ để loại trừ mọi tác nhân pause khác. Đã chuyển riêng STATUS sang receiver chỉ đọc, giữ BOOTSTRAP ở Activity, giữ toàn bộ guard khi app thật sự pause/mất focus. APK mới đã qua mock, typecheck, kiểm độc lập source, manifest và chữ ký development; sau đó STATUS và CONNECT thực tế đã hoạt động.

Lượt ngắn thứ hai chạm quota metadata 64 MiB. Hai lượt tạo 313 subscription logcat, giữ 49.546 dòng JSON nhưng chỉ 315 dòng khác nhau. 99,36% byte JSON bị lặp; riêng các bản logcat chiếm 41.226.240 byte được cấp phát. Admission kiểm dung lượng đang dùng, nhưng chưa dự trù metadata còn phát sinh cho việc polling. Đây là lỗi cần sửa trong pipeline observer/ghi bằng chứng, không được giải quyết bằng nới quota hoặc xóa log cũ.

Sau metadata failure, cleanup từ chối đường dừng dành cho trường hợp chưa có owner vì native đã CONNECTED. Backend tiếp tục rồi dừng bằng FRAME_ADMISSION_QUOTA; AP parent dừng theo HOST_BACKEND_FAILED. Root không kill AP/backend để giả lập bằng chứng ground. Khi hai tiến trình con đã chết và container đã biến mất, chỉ tiến trình lab treo được dừng để thu hồi observer. Không có receipt đóng nhiệm vụ hợp lệ.

## Giới hạn bằng chứng

- Backend ghi 152.785 frames/completed frames; stageRows là 152.784. Không kết luận đủ frame hoặc mission PASS từ các bộ đếm này.
- QA kiểm prefix gồm 10.316 frame CRC thụ động; đây không phải kiểm toàn bộ nhiệm vụ.
- Lượt đầu có bằng chứng fence/ground/drain trước owner, nhưng journal thiếu SESSION_FAILED. Nguyên nhân thiếu append cũ vẫn chưa rõ; không viết lại ledger.
- Trạng thái CONNECTED ở lượt mới chỉ chứng minh đã vượt điểm lỗi cũ. Không suy thành bay, điều khiển payload, beta hay chứng nhận an toàn.
- Quyền DUMP có trong manifest và receiver đã nhận từ engineering observer root. Chưa thử từ app Android không được cấp quyền; guard pause thật sau sửa mới được kiểm bằng mock/source.
- Thời gian guardian chạy không phải thời gian bay và không được cộng thành 30 phút.

## Phạm vi bảo toàn

Mọi thay đổi nằm trong evidence/runtime-observe04. Bản thử mới có 65 file runtime và 50 đầu vào native; 47/50 đầu vào native giữ nguyên. Candidate mới d4eb9c3c… và APK development 47208ec0… chưa được chọn vào trust/global release, không ký production.

Đối chiếu cuối: 17.117 định danh bảo vệ, 29 inventory niêm phong và 50 file native gốc không có drift. 165 đường dẫn thiếu từ trước vẫn ghi riêng. Không phục hồi mới, không sửa source/candidate gốc hay lịch sử ENDURE; không khẳng định hiện diện liên tục hoặc nghiệm thu ENDURE. Không chạy riêng lại bộ 838 pin bổ sung ngoài các baseline/inventory đã kiểm.

Guard giữ nguyên: freshness 250 ms, input 200 ms, speedup 1, cap 500 ms, fsync trước sensor, không cho phép bỏ frame; metadata 64 MiB và artifact 4 MiB. Cả hai lượt ngắn trong ngân sách đã dùng; không khởi động lượt khác trong campaign cũ.

Scratch native/betaintegrated01/.build/native-development đã được dọn. Không copy toàn dự án, không tải SDK/venv mới. Docker image prune đã chạy, thu hồi 0 byte. Các PID thuộc lượt kiểm đã dừng. Dữ liệu app giữ nguyên qua install -r; chưa kiểm cuối lại 541 file private của các APK cũ do emulator đã bị guard đóng.

## Bước tiếp theo

Sửa một lát cắt pipeline hoàn chỉnh: một luồng ACK/DTO gốc bền vững, receipt tham chiếu SHA/offset thay vì thu lại lịch sử cho từng STATUS; barrier subscribe và xử lý mất link/restart phải chống mất hoặc nhận nhầm ACK. Dự toán và kiểm ngân sách metadata còn lại trước launch/từng lần ghi, chừa ngân sách ghi lỗi và đóng hồ sơ. Khi quota lỗi, vòng đời observer/native/AP phải dừng phối hợp và giữ trạng thái không đủ bằng chứng.

Kiểm lại bằng trace đang có và fault injection trước. Chỉ mở campaign mới sau gate mới; lượt ngắn trọn vẹn phải đạt trước lượt 30 phút. Không tăng quota, tái phân loại log, cắt frame hay sửa hồ sơ cũ để có PASS.

## Hồ sơ

- [Contractor Verify](../evidence/runtime-observe04/ROOT-VERIFY01.json)
- [QA STATUS Android](../evidence/runtime-observe04/qa/ACTUAL-STATUS04-AUDIT01.json)
- [QA lượt SITL ngắn](../evidence/runtime-observe04/qa/ACTUAL-SHORT02-FAILURE-AUDIT01.json)
- [Đo nguyên nhân metadata](../evidence/runtime-observe04/host/METADATA-CAP-ANALYSIS01.json)
- [Kiểm bảo toàn cuối](../evidence/runtime-observe04/preservation-final01.json)
