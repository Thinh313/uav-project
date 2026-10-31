# AERIS · Thứ tự ưu tiên từ 13/10/2026

Đây là **bản cập nhật ưu tiên** cho [roadmap lịch sử](ROADMAP.md) và [PAYLOAD21 slice](PAYLOAD21-ROADMAP.md), theo yêu cầu chủ việc. Các trạng thái/exit gate lịch sử vẫn giữ nguyên. Tài liệu này được bổ sung ngoài inventory đang đóng băng, không đổi candidate9/generation04, source/corpus/trust hoặc kế hoạch tích hợp PROTOCOL22 đã duyệt. Danh sách khoảng trống và chứng cứ: [replacement gaps](RAGAS-REPLACEMENT-GAPS-20261013.md).

Mục tiêu: AERIS trở thành GCS vận hành trên HeraHub cho một cấu hình Hera nhiều payload được xác nhận, trước hết với hành trình khảo sát → nhiệm vụ → bay/payload → media → bàn giao. Sau đó mới mở rộng đến toàn bộ workflow RAGAS. Không có lịch hoàn thành hardware khi chưa có SDK/thiết bị; không ước lượng capacity, số payload hay lợi thế A/B từ marketing/simulation.

## Thay đổi thứ tự

| Trước | Sau cập nhật | Lý do / đánh đổi |
|---|---|---|
| Chuỗi host storage/security/load/endurance | Hoàn tất ENDURE20; chỉ sửa reliability mới khi gate cụ thể thất bại | Nền dữ liệu đã có nhiều increment; tiếp tục thêm hạ tầng tổng quát sẽ không đóng đường điều khiển Hera. Các lỗi bảo toàn chứng cứ vẫn ưu tiên xử lý. |
| Payload simulation rồi chờ SDK cho native | PROTOCOL22 Fly → live transport contract/SITL responder → native shell/input/video chuẩn bị song song | Có thể giảm rủi ro trước khi có SDK; từng lớp vẫn giữ nhãn simulator/emulator và gate thực riêng. |
| Broader missions, AI/accessories và native cùng backlog | Khảo sát/payload/capture/input/UX trước; patterns chuyên dụng và runtime AI/phụ kiện sau | Tránh dàn trải trước khi một hành trình vận hành đầy đủ được kiểm. Full replacement vẫn giữ các mục mở. |
| A/B preparation | Chốt rubric/binary/configuration sớm; đo sau bench/HIL và trên cùng thiết bị | Tìm được lỗi usability thực trước release; chưa có phép đo thì không tuyên bố thắng RAGAS. |

## Now — việc hiện được phép

| ID | Trạng thái / kết quả | Vai trò chủ trì và phụ thuộc | Gate |
|---|---|---|---|
| RM-01 ENDURE20 | RUNNING_NOT_FINAL; ưu tiên nghiệm thu đang chạy | Agent theo heartbeat hiện có; không sửa run/candidate | Continuous24h generation04/signed9; raw timing/hash, 27 gói/664 file, trust/signature/selected9/phase/supervision, restart/browser. Đủ giờ đơn lẻ không PASS. Sớm nhất 13:11 ngày 14/10/2026 giờ Việt Nam, chưa phải giờ nghiệm thu cam kết. |
| RM-02 PROTOCOL22 vào Fly | WAITING_ENDURE20; đã được ủy quyền tự triển khai khi gate đạt | Agent; RM-01 và [TIP tích hợp](../delivery/TIP-PROTOCOL22-FLY-INTEGRATION.md) | Đóng preview/writer sạch; offline inspector trong Fly, đủ regression, new engineering package/bootstrap/staged canary/preservation rồi selection. Không nối raw replay sang lệnh thật/SITL. Version/sequence dựa high-water mới kiểm, không hardcode seq10. |
| RM-03 chuẩn bị cấu hình/acceptance | Rà soát tài liệu hoàn tất; intake/rubric có thể chuẩn bị ngoài vùng frozen | Agent soạn contract; chủ việc/RtR cung cấp SDK/configuration/binary khi sẵn có | Configuration tree và checklist evidence cụ thể, unknown giữ null. Không yêu cầu phân xử độ sáng. Không tự liên hệ vendor hoặc thu thập trên thiết bị chưa có. |

ENDURE20 thất bại: giữ raw/attempt/module riêng, báo dependency thất bại; không ký lách gate, không tự nối interval hoặc retry flight. RM-02 không thay đổi thành live payload control vì tên “Fly integration”.

## Next — ưu tiên đề xuất sau RM-02

Các ID dưới đây là hạng mục roadmap, chưa là milestone mới đã build, không tự mở rộng heartbeat thành quyền triển khai chúng. Mỗi increment cần TIP/ADR theo mức thay đổi và ủy quyền triển khai tương ứng.

| Thứ tự / ID | Deliverable và gate ra | Việc không cần Hera SDK | Phụ thuộc thực / chủ trì dự kiến |
|---|---|---|---|
| 1 · RM-04 aircraft/payload transport và mission routing · P0 | Broker tách inspector/live; protocol discovery và route component/proxy/manager; authority/freshness/ACK quarantine; explicit camera mission targets. Real autopilot SITL + responder payload giả lập, negative routing/reboot/loss/duplicate, không unintended command. Bao gồm phần còn thiếu record/stream/storage/camera definition theo capability, không tự gán universal support. | Contract transport/auth/signing, independent simulator adapter, camera/gimbal responder, pinned QGC/ArduPilot fixtures và fault tests. Flight profile vẫn simulator. | RM-02; maintainer AERIS phụ trách phần mềm. Firmware/radio/payload API thực do kỹ thuật RtR xác nhận ở RM-07. |
| 2 · RM-05 GCS native shell + input ownership · P0 | ADR chọn stack/bridge từ core độc lập; Android artifact chạy operator journey với persistence/lifecycle, calibration/mapping versioned, lost focus/input/process không tái cấp quyền. Không biến APK diagnostic thành production app bằng đổi nhãn. | Host build, emulator nếu sẵn toolchain, input replay, lifecycle/mock bridge. Dừng build lớn nếu disk dưới20GB; không tạo project copy. Emulator không xác nhận HeraHub. | Có thể chuẩn bị song song RM-04. Target OS/ABI/density/input/RC route thực để đóng RM-07. Maintainer AERIS/native; người cụ thể chưa được giao. |
| 3 · RM-06 video/media + operator workflow · P0 | Native decode/stream identity/frame age/switch/record; capture/file/hash/time lineage riêng. Fly một view chính, selectors rõ, lỗi từng feed/control/aircraft, takeover/release; shared control sizing và native touch QA. | File video khai nguồn/mock network, codec/resource/reconnect/clock skew corpus, media-integrity tests và UX walkthrough. Giữ synthetic/imported/physical tách rõ. | RM-05 runtime seam và RM-04 route; actual video endpoint/camera calibration từ RM-07. Không hứa3/6feed đồng thời trước đo. |
| 4 · RM-07 observed Hera/HeraHub bench · P0 | Một cây cấu hình được hỗ trợ: install/window/SDK/input/radio/auth/discovery/three-position mapping nếu thực có/video/storage/thermal/runtime budgets. Bench/disarmed có raw traces và authority review; pairing/signing provisioning theo cấu hình. | Intake templates, endpoint/security contract và failure scripts chuẩn bị cùng RM-03–06. | SDK/device/configuration đang chưa có; kỹ thuật RtR xác nhận as-built, maintainer tích hợp. Dependency cần trước kết luận supported hardware; không gắn ngày giả. Không chờ bench mới bắt đầu phần shell/replay. |
| 5 · RM-08 survey readiness + HIL faults · P0 | Full preflight profile/health/battery/fence/Home/terrain/datum; RTK/NTRIP/PPK nếu yêu cầu khảo sát; mission/readback/camera targeting; radio/payload/video/process/power/hot-swap/loss/overload campaigns không lặp lệnh. Native storage/update/recovery trên máy thực. | Geodata/correction-age/mission corpus và HIL test plan có thể làm sau RM-04; field-calibration không giả lập thành kết quả. | RM-04–07; kỹ thuật/autopilot/payload và người vận hành phụ trách hardware/HIL. Failsafe acceptance theo installed firmware; thiếu mục P0 thì chưa field-alpha. |
| 6 · RM-09 controlled survey + real media · P0 | Bay có kiểm soát trên tổ hợp đã qua HIL; manual/mission transitions, payload/video/capture đúng thiết bị, logs/media bàn giao nguyên vẹn; achieved coverage/GSD/blur/accuracy có dữ liệu và checkpoint. | Receiver/review rubric và processing intake chuẩn bị trước. | RM-08, camera calibration/launch/geoid tie, khu vực và người vận hành phù hợp. Flight authority chưa được cấp bởi roadmap này. |
| 7 · RM-10 RAGAS A/B + replacement acceptance · P0 | Cùng thiết bị/firmware/payload/source/mission, binary hashes, task order counterbalanced và rubric đã chốt: completion/errors/recovery/time/workload/video latency; raw failures và missing samples giữ đủ. Chỉ kết luận theo workflow/configuration đã đo. | Rubric/measurement schema, black-box documentation/binary metadata khi có. Không dùng RAGAS source. | [A/B protocol](PAYLOAD21-AB-PROTOCOL.md), RM-07 bench usability trước và RM-09 cho operational comparison; chủ việc quyết threshold, operator chạy. |
| 8 · RM-11 production release readiness · P0 | Supported configuration matrix và operator acceptance, SBOM/license/SDK terms, official signing/ownership/key custody, native install/update/recovery, training/support và release checklist. Không có flight-critical P0 tồn tại trong phạm vi phát hành. | Inventory/reproducibility và contract chuẩn bị được; host engineering trust không đóng official/native gates. | RM-10 và người có quyền nghiệm thu/phát hành RtR; không có external release ủy quyền trong lượt này. |

Critical path là RM-01 → RM-02 → RM-04/05/06 → RM-07 → RM-08 → RM-09 → RM-10 → RM-11. RM-03/intake/A/B rubric đi sớm; RM-04–06 có các seam dùng chung nên phải thống nhất contract, không ba implementation rời nhau. Khi chưa có phần cứng, tiếp tục phần không phụ thuộc; trạng thái hardware vẫn blocked/NOT_CHECKED, không đổi scope để bỏ gate.

## Later — vẫn thuộc full replacement

RM-12 · P1: corridor/structure/orbit/LiDAR và QGC complex regeneration theo từng corpus; RTK/PPK nâng cao, camera definition/extended config, commissioning/calibration/maintenance/payload firmware với quyền riêng. Hạng mục nào cần cho pilot khảo sát được chuyển lên P0 trước pilot.

RM-13 · P2: AI inference/detection/tracking, LRF/light/drop/speaker, PTT/chat, Remote ID/weather và multi-operator/trainer. Mỗi mục cần source/API, authority/safety contract, dataset/latency/quality và operator acceptance; nhận diện AI không tự có quyền điều khiển gimbal/flight. Để sau survey pilot không đồng nghĩa đã đạt full RAGAS replacement.

## Điều kiện tuyên bố thay thế

Survey replacement chỉ đạt khi RM-01–11 đóng trên một cấu hình observed và một bộ nhiệm vụ xác định, A/B/rubric đạt và chủ việc nghiệm thu. SDK/device/HIL/physical media/field quality hiện vẫn NOT_CHECKED. Full replacement còn cần RM-12/13 và inventory chức năng đo từ binary, hoặc phạm vi excluded được chủ việc chấp nhận rõ. Không tuyên bố “cạnh tranh DJI” là phép đo đã đạt.

Không có nhân sự/capacity cụ thể được cung cấp nên dùng vai trò chủ trì, không bịa tên/effort/delivery date. Thứ tự dùng gate và critical dependencies thay RICE định lượng vì reach/impact/effort thực chưa có. Heartbeat hiện có tiếp tục RM-01/RM-02 theo ủy quyền cũ; không thay prompt/lịch/notification trong đợt rà soát này.
