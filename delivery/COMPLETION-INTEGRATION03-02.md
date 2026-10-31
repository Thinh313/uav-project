# AERIS Integrated Alpha: bàn giao kiểm chứng 02

**NOT READY.** Người dùng chọn bàn giao phần đã kiểm, không mở thêm lượt Android–SITL. Đây là checkpoint phát triển, chưa nghiệm thu trọn milestone và chưa phải bản phát hành sản phẩm.

## Kết quả dùng được

Đã có APK development04 của cockpit Android cô lập, tích hợp đường lập nhiệm vụ KML/corridor, nhập QGC SimpleItems, preflight/mission transport và hợp đồng hai operator/nhiều payload. Màn 3D trên host chỉ đọc dữ liệu native; có tài sản 3D được cấp phép và âm thanh rotor tổng hợp opt-in. Sự có mặt của các thành phần này không chứng minh hành trình tích hợp đã đạt.

APK04 đã kiểm chữ ký development, cài cập nhật giữ UID và đối chiếu đúng SHA trên emulator-5582. QA độc lập đối chiếu 192 pin nguồn, 112 asset cockpit trong APK và 9 pin observer, không có asset dư hoặc trùng. Kiểm coldboot đổi cấu hình emulator xác nhận toàn bộ 35 file riêng của app khớp SHA trước khi mở Activity. Phép kiểm này chưa thay thế nghiệm thu persistence/restart cuối nhiệm vụ.

APK: `native/integration03/dist/aeris-integration03-development04.apk`  
SHA256: `9218acc3b71ad271b3ee9b7ba291d76fe1f97cd714e962ec34630fb6eb6f4ddf`  
Native source: `7784d45e8ba42e654e0a8f15a87476febf8145f0f70d30d88cefb261ed9edab3`  
Observer source (9 pin): `3894481d2de04f8be796343896bee451fdf829b85e1aecf3f5149ece808e2d1c`

## Bao phủ yêu cầu bắt buộc

| Tiêu chí | Trạng thái | Đã kiểm và phần còn thiếu |
|---|---|---|
| I01: preflight, freshness, phiên dài | PARTIAL | Mock độc lập xác nhận vòng đệm giữ đúng 10.000 frame cuối, thứ tự/snapshot/reset qua 32.719 record; guard 1.500 ms vẫn đúng. Phiên APK03 thực có 28.152 frame CRC-decoded nhưng dừng vì stale trước ba cohort sau 20k. APK04 chưa có phiên thực đủ điều kiện này. |
| I02: KML/QGC/Home/cao độ | PASS trong phạm vi | Giữ kết quả semantic/oracle và Android QGC roundtrip đã đạt: 32 item, cao độ riêng 17,25/23,5/14,75 m và tốc độ 1,75 m/s. Intake/compiler không đổi trong bản sửa transport. Complex/fence/rally và ngữ nghĩa thực thi chưa hỗ trợ bị từ chối. Corpus bổ sung sau khi xem dữ liệu không được gọi là unseen. |
| I03: AUTO tới review được chấp nhận | CHƯA ĐẠT | Chưa có lượt final Android AUTO → ground/disarm → accepted review. Các lỗi mới đều xảy ra trước arm; không suy diễn thành nhiệm vụ hoàn tất. |
| I04: hai operator, nhiều payload | PARTIAL | Có contract/mock, mTLS hai phiên và quan sát A điều khiển gimbal −33°/78°. Final B device2, ba camera và capture cùng phiên consent còn thiếu kiểm wire đầu-cuối. |
| I05: partition, thu hồi quyền, pilot loss | CHƯA KIỂM FINAL | Còn kiểm B pending → UNKNOWN, thu hồi ≤3.250 ms, phiên B mới không có quyền, A tiếp tục; mất foreground pilot và AP failsafe. Không thay bằng chứng thành phần cũ cho hành trình final. |
| I06: observer 3D/audio/hiệu suất | PARTIAL | QA độc lập xác nhận vị trí NED/quaternion, prefix/run/source/plan và age proxy của mẫu ground; CLOSED → UNKNOWN không tiếp tục chuyển động. Chưa đạt mẫu airborne toàn chất lượng 30 giây cùng UI/SITL và ngưỡng RAF p95/p99. Chưa có âm học Hera hiệu chuẩn. |
| I07: SAF và receiver độc lập | CHƯA KIỂM FINAL | Có receiver strict và khai báo selected run/receiver/nonce trước SAVE. Chưa xuất/nhập gói final đúng nhiệm vụ rồi kiểm corruption/sai context. |
| I08: process restart/coldboot cuối nhiệm vụ | PARTIAL | Coldboot giữa tác vụ giữ đúng 35 file riêng. Còn kiểm sau nhiệm vụ đã đóng, toàn bộ hồ sơ, không tự nối/kế thừa quyền và đối chiếu private cũ sau cùng. |
| I09: UI toàn hành trình | PARTIAL | Đã kiểm phạm vi cockpit Android và observer ground; còn toàn bộ trạng thái bay/lỗi/review/popup/operator B. P2 còn lại: caption Home dài và mật độ thông tin raw. Không tuyên bố toàn UI đạt từ một ảnh chụp. |
| I10: bảo toàn, pin và đóng tiến trình | PARTIAL | Pin APK/source/observer và đóng runtime riêng đã kiểm. Kết quả đối chiếu baseline bảo vệ cuối nằm trong receipt riêng. Các ràng buộc raw/private/SAF final chưa hoàn tất. |

Chỉ I02 được chấp nhận ở phạm vi đã khai báo. Không chuyển số này thành phần trăm trưởng thành thương mại và không che các gate bắt buộc chưa đạt.

## Lỗi thực tế và cách diễn giải

Phiên APK03 `sd53de50e4918bbc2afe1` dừng unarmed do adapter nhận dữ liệu ở tuổi 1.509 ms, vượt guard 1.500 ms. Đoạn cuối ghi nhận receipt → main-ready 1.105 ms, main-ready → JS-entry 374 ms, proof 19 ms, consumer tiếp 11 ms. Các đoạn này gồm nhiều hoạt động; chưa xác định độc quyền nguyên nhân trễ. Guard đóng là hành vi đúng, không nới ngưỡng để lấy PASS.

Bản sửa thay push/slice lịch sử 10k mỗi frame bằng vòng đệm có nội dung/thứ tự tương đương trong hợp đồng nội bộ. Đối chứng host cho thấy ingest giảm từ khoảng 360–407 xuống 114–163 ms trên 25.050 frame. Đây là microbenchmark host, không chứng minh đã chữa stall 1,5 giây trên Android. Trace lỗi giữ tối đa 64 mẫu timing/pump/listener; phép kiểm domain failure xác nhận lưu trước khi đóng socket. QA từng báo thiếu trace vì đọc phiên bản cũ, sau đó kiểm đúng nguồn và rút phát hiện; không sửa production giả để đáp ứng phát hiện nhầm.

Cấu hình Android mới được khai báo rõ: API33 ARM64, cache AVD cũ, 4 CPU/2 GiB, GPU host, viewport 1280×800. Cấu hình trước là 2 CPU/1,5 GiB. ArduPilot vẫn 2 CPU/512 MiB, speedup 1. Nếu lượt mới thành công, cũng không thể quy riêng cho vòng đệm hoặc gọi là đối chứng phần cứng tương đương.

Phiên APK04 `sb3f198d1ac1f6fb249ef` thất bại ngay bootstrap với `BOOTSTRAP_EOF`, không có bootstrap record, observer record hoặc arm. Console AP dừng ở SERIAL0 “Waiting for connection”. Native sau đó báo CONNECT_FAILED/ECONNREFUSED. Chưa chứng minh nguyên nhân socket cuối cùng; khả năng published port nhận kết nối trước guest sẵn sàng cần được kiểm. Controller dừng container khi nhận EOF; lỗi native sau đó phù hợp với AP đã bị dừng, chưa chứng minh APK04 có regression transport. Không có trace Running/OOM/exit trước khi dừng để kết luận guest tự chết. Không tự retry hay tái sử dụng thư mục run.

Trong cùng khoảng thời gian, free disk giảm từ 27,31 xuống khoảng 21,63 GiB; dữ liệu host của run mới chỉ 19.289 byte. Chưa xác định tác nhân chiếm dung lượng. B và emulator được dừng có kiểm soát trước sàn 20 GiB; không có bằng chứng vượt sàn. Việc dung lượng tăng lại sau khi dừng không xác định được tác nhân.

Raw canonical mới nhất vẫn còn trong AVD, chưa được trích xuất/kiểm seal sau khi emulator dừng. UI có báo CLOSED không đồng nghĩa raw đã được receiver xác nhận. Raw phiên resource cũ đã trích xuất và xác nhận CLOSED/NATIVE_EOF, safeComplete=false; không sửa báo cáo lịch sử để xóa sự bất định đã ghi lúc trước.

## Bảo toàn và giới hạn bàn giao

Đối chiếu SHA cuối đạt 71.158/71.158 đường dẫn baseline, không có sai lệch (`evidence/integration03/preservation-resource-stop03.json`). Đây là quan sát tại checkpoint, không phải chứng minh đường dẫn hiện diện liên tục. Giữ nguyên các run lỗi, APK development cũ, source/candidate/canonical SOT và ENDURE. Không sửa lịch sử, ký production, nối SDK/HeraHub hoặc điều khiển drone thật. PID emulator/controller/operator B và listener riêng 5582–5583, 5937–5942, 8851–8852 đã hết. Container SITL riêng đã dừng; container khác giữ nguyên. Tab observer kiểm thử đã đóng, viewport trả mặc định.

Build staging `.build`, unsigned APK trung gian và scratch kiểm thử do tác vụ tạo đã dọn; giữ APK development có chứng cứ. Docker image prune thu hồi 0 byte; không prune container hoặc volume.

Không có đối chứng thương mại với DJI/Ragas, không có chứng nhận an toàn bay hoặc thiết bị Hera. Công việc này chủ yếu là deterministic transport và kiểm toàn vẹn, không có baseline LLM phù hợp để suy ra ưu thế sản phẩm. Manual/assisted training, physics 1× hiệu chuẩn tải/gió/pin/collision, âm học thật, Phase One/HeraHub và production PKI vẫn là gate riêng.

## Điều kiện tiếp tục

Theo lựa chọn bàn giao hiện tại, không khởi động thêm. Lần tiếp tục cần dung lượng thực ổn định đáp ứng admission, chẩn đoán/fix readiness bootstrap bằng mock trước, và quyết định lại ngân sách hữu hạn vì lượt thất bại đã tiêu một cửa sổ. Sau đó mới tạo run hoàn toàn mới để kiểm ba cohort >20k, nominal + payload + observer, corridor/B partition, pilot loss, SAF/receiver và persistence cuối. Không ghi DONE trước khi toàn bộ 10 tiêu chí bắt buộc đạt.

Các receipt nguồn: `evidence/integration03-qa/source-gate07.json`, `artifact-pins04.json`, `nominal-resume03-freshness-analysis.json`, `observer-ground03c.json`, `observer-terminal03b.json`; runtime: `evidence/integration03-runtime/prearm-failure11.json`, `profile-change-private-after04.json`, `managed-closure12.json`. Báo cáo này thay thế trạng thái checkpoint trước cho việc đọc hiện tại, không ghi đè hoặc làm mất lịch sử checkpoint trước.
