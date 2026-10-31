# GCS34 — phần mềm UAV cao cấp: chức năng, khoảng trống và UI/UX

14/10/2026 · Scope: khảo sát/inspection dân dụng trên Hera, thay Ragas bằng kiến trúc AERIS độc lập; hướng tới vượt hệ thống DJI tương đương qua đối chứng. Đây là nghiên cứu và đề xuất sản phẩm, không thêm tính năng vào candidate đang đóng băng.

## Kết luận hiện trạng

AERIS chưa có toàn bộ các chức năng người dùng vừa nêu. AUTO với ArduPilot thật đã được quan sát trong SITL; NATIVE33 chỉ Fly mock. Chưa có airspace dataset pháp lý đã tích hợp/nghiệm thu, geofence đầu-cuối, runtime AI detection/tracking, avoidance/VIO trên Hera thật hoặc live video thật. Mục tiêu cần bao trùm toàn bộ GCS, không dừng ở mission editor hay hạ tầng lưu hồ sơ.

Đọc `aeris-source-status.json` và `feature-catalog.json` để đối chiếu SHA/scope. `app/core/qgc.mjs:34` từ chối geofence không rỗng trong execution adapter mission-only; nhận/giữ một file `.plan` không chứng minh có fence upload/enforcement. Các service SITL có GUIDED/AUTO/HOLD/RTL/ARM, upload/readback và reconciliation; không đồng nghĩa tất cả mode/RC/failsafe Hera đã nghiệm thu. Native33 phát hành APK development riêng nhưng actual ART/Activity/private persistence/force-stop/reboot còn NOT_CHECKED. ENDURE27 vẫn FAILED do HOST_EXTERNAL_POWER_LOST; chưa có24h acceptance. Không chạy lại hay sửa các gate này trong nghiên cứu.

## Nguồn và mức tin cậy

19 trang primary chụp raw có SHA,39 assertion trích vào Refinery từ18 trang. Các origin cùng hãng không được tính thành nguồn độc lập. Registry chỉ xác nhận tài liệu **nói gì**, không chứng minh tính năng vận hành hay hiệu suất. `independent_performance`/scope không có dẫn chứng giữ honest-null. Không cho điểm Strong/Weak từ quảng cáo.

- [DJI Matrice4/Pilot2](https://enterprise.dji.com/matrice-4-series): nhà sản xuất công bố nhận diện, tracking, FlyTo/POI và sensing. Smart3D Explore gắn Matrice4E với Manifold3; không suy phần mềm UI tự cung cấp thị giác/compute. Firmware, payload và phụ kiện quyết định khả năng.
- [DJI FlightHub2](https://enterprise.dji.com/flighthub-2): tham chiếu cho planning, remote operations, collaboration, review/private deployment và AI workflow. Đây là platform/backend/edition riêng; không gom thành mọi tính năng đều có trong Pilot2 hoặc mọi aircraft.
- [Skydio X10 FAQ](https://www.skydio.com/x10/faqs) và [autonomy ecosystem](https://www.skydio.com/skydio-autonomy): tham chiếu cho tích hợp perception/navigation/data acquisition. Không suy một capability của X10/R10/F10 hoặc gói3DScan thành khả năng mọi UAV. Tính chính xác khảo sát phụ thuộc setup và reference data.
- [QGC5.1 Plan](https://docs.qgroundcontrol.com/Stable_V5.1/en/qgc-user-guide/plan_view/plan_view.html), [Fly](https://docs.qgroundcontrol.com/Stable_V5.1/en/qgc-user-guide/fly_view/fly_view.html): tham chiếu planning patterns, fence/rally, payload/map/video và sự khác biệt continue/resume; firmware-dependent.
- [ArduPilot AUTO](https://ardupilot.org/copter/docs/auto-mode.html), [fences](https://ardupilot.org/copter/docs/common-geofencing-landing-page.html), [GCS failsafe](https://ardupilot.org/copter/docs/gcs-failsafe.html), [BendyRuler](https://ardupilot.org/copter/docs/common-oa-bendyruler.html), [terrain](https://ardupilot.org/copter/docs/terrain-following.html): capabilities của autopilot còn phải đối chiếu bản firmware pinned, sensors và cấu hình thật. Không tự áp defaults hiện tại lên Hera.
- [RAGAS public](https://www.rtrobotics.com/defense/ragas): tham chiếu cho geographic operational picture và nguồn video hai chiều; chưa có A/B binary/runtime nên không đánh giá chất lượng. Chưa dùng mã nguồn ứng dụng Ragas.
- [HeraHub Intel](https://www.rtrobotics.com/commercial/herahub) tách riêng controller Android/v2 trong nguồn dự án. Tám stream quảng cáo trên trang Intel không chứng minh decoder/thermal của Android v2. Nguồn GitBook/HeraHub-v2 hiện không truy cập được qua web tool; reuse nghiên cứu12/10 phải gắn ngày và scope, không gọi là refresh thành công.
- [Android accessibility](https://developer.android.com/guide/topics/ui/accessibility/views/apps-views): minimum native touch target48dp; không suy từ52CSSpx trong minh họa. [NASA crew interfaces](https://www.nasa.gov/reference/10-0-crew-interfaces-vol-2/) cung cấp nguyên tắc mode-awareness/decision clarity/recovery **dùng bằng phép tương tự**, không phải chứng nhận hay tiêu chuẩn pháp lý UAV áp trực tiếp.

## Ba lớp thường bị nhầm

**Bay tự động:** máy bay thực thi mission lập trước, AUTO/navigation và lệnh camera trên autopilot. Không cần một neural model để là AUTO. **AI hỗ trợ người vận hành:** nhận diện, giải thích rủi ro, kiểm chất lượng ảnh, đề nghị plan/refly; không tự có quyền gửi lệnh bay. **AI tự chủ có perception:** sensor→model→bounded planning→controller, avoidance/VIO/tracking/return behavior, có freshness/uncertainty/authority và fallback. Lớp cuối cần aircraft-side sensors/compute/integration; thêm nút “AI bay” không tạo ra nó.

Kiến trúc đề xuất: autopilot giữ stabilization/failsafe; onboard companion cung cấp perception/autonomy theo capability; native GCS giữ owner/mission/payload/video/review; AI copilot xuất proposal có cấu trúc. Safety admission kiểm schema, geography, mode, owner, link, energy và dữ liệu trước khi proposal được phê duyệt. LLM không được gửi trực tiếp arbitrary MAVLink/arming/flight outputs. Đây là ranh giới thiết kế đề xuất, không là tính năng đã có hay nhận định chung về tất cả sản phẩm đối thủ.

## Airspace warning khác geofence và giấy phép

Một sản phẩm cần ba lớp riêng:

1. **Geo-awareness:** dữ liệu không phận có nguồn, revision, phạm vi phủ, khoảng hiệu lực, altitude reference và quy tắc vùng. Đối chiếu tuyến dự kiến, các đoạn chuyển tiếp, đường về/nơi đáp; hiển thị lý do và đoạn xung đột.
2. **Operational geofence:** vùng bao/loại trừ trên autopilot với semantics/policy thực. Edit→upload→readback→quan sát breach/action bằng corpus và SITL trước hardware. Fence tiếp tục nằm trên autopilot khi GCS mất link; phải kiểm configured behavior, không giả định universal RTL.
3. **Authorization/operator policy:** ghi scope, thời gian và điều kiện chấp thuận thực. Acknowledge cảnh báo hay vendor-unlock không tạo giấy phép. Không có dữ liệu hoặc dữ liệu cũ phải UNKNOWN, không “safe” từ một map trống.

[Thông báo DJI17/11/2025](https://www.dji.com/media-center/announcements/dji-expands-geo-system-update-to-remaining) mô tả phased rollout chuyển remaining NFZ thành Enhanced Warning và phân biệt advisory với authority data. [Trang GEO legacy](https://www.dji.com/flysafe/introduction) vẫn mô tả blocking/unlock cho các dòng cũ. Không xóa một nguồn, không gom phạm vi/thời gian khác nhau thành một sự thật universal; behavior thực phải chốt model/firmware/market. Không dùng bài legacy làm yêu cầu “mọi DJI phải hard-lock”.

[Cổng Chính phủ](https://xaydungchinhsach.chinhphu.vn/huong-dan-thuc-hien-thu-tuc-cap-phep-bay-doi-voi-tau-bay-khong-nguoi-lai-va-cac-phuong-tien-bay-khac-119250616123043064.htm) chỉ tới `cambay.mod.gov.vn`. Nghiên cứu này xác nhận entry point được công bố, chưa ingest polygon/map/API và chưa kiểm quyền tái sử dụng, cập nhật hoặc coverage hiện hành. Không scrape/bypass protected databases. Chưa có căn cứ để vẽ vùng sân bay thật hoặc đặt bán kính cấm chung trong AERIS.

## Blueprint chức năng đề xuất

47 candidate requirements ở9 nhóm trong `feature-catalog.json`; đây là selected set cho sản phẩm khảo sát/inspection, không là “toàn bộ mọi tính năng trên thị trường”. Các nhóm:

1. Flight modes/ownership/manual takeover; mode thực khác requested/ACK, physical input và flight/payload owner riêng.
2. Airspace/geofence/preflight/failsafe; GNSS/EKF/link/battery, Home/datum, energy reserve và return viability.
3. Survey/mission; grid/camera/GSD/overlap, terrain, offline, RTK/PPK, corridor/structure/orbit và nhiều sortie.
4. Payload/video; discovery/identity/camera/gimbal, EO/thermal, frame age/sync, capture/media, radiometry/LRF với sai số.
5. AI/autonomy; plan assistance, detection/tracking, quality/refly, avoidance/replanning; VIO/night theo phần cứng. Mỗi tính năng có limitation/fallback riêng.
6. Records/offline data; event/media/mission timeline, dataset/handoff/resume/integrity, quota/dọn dẹp có preview.
7. Fleet/collaboration; remote handover, role access, shared video/annotations, multi-UAV deconfliction. Multi-payload không chứng minh multi-aircraft.
8. Native/security/maintenance; lifecycle, authentic transport, package updates, calibration/diagnostics, overload/thermal/power/endurance.
9. Training/validation; simulator có provenance/calibration, operator scenarios và đối chứng cùng workload.

P0/P1/P2 trong catalog là thứ tự **đề xuất**: P0 cho first operational survey product; P1 cho advanced professional capability; P2 cho fleet/high-autonomy extensions. Không ấn định deadline hay tuyên bố đã approve release.

## UI/UX cần đạt

Cockpit của người điều khiển là trung tâm. Bốn giai đoạn Khảo sát/Preflight/Fly/Review chung một mission context, thêm Workspace/Setup/Diagnostics riêng khi cần. Khi bay, hiển thị ổn định aircraft identity, bên giữ quyền, **mode quan sát**, altitude datum, GNSS/RTK, energy reserve, link/video freshness. Requested→ACK→observed phải phân biệt; lost/stale không giữ nhãn xanh/AUTO giả.

Bản đồ và video cùng hiện; đổi vùng chính bằng một thao tác, giữ đúng payload/stream identity và dấu thời gian. Camera selection không âm thầm đổi target gimbal; unknown capability bị unavailable có lý do. Thermal visualization khác radiometry. Độ phủ planned khác captured/usable; AI box gắn frame và hết hiệu lực khi frame cũ.

Giữ vị trí/Về Home/Tiếp quản ở vị trí ổn định; nghĩa và khả dụng theo mode/sensors/owner/transport thực. Xác nhận nguy cơ phải hiện đích, hành động và hậu quả; không modal cho mọi thao tác nhỏ. Mất GCS không chứng minh physical RC cũng mất; UI chỉ vô hiệu hóa các đường điều khiển không còn được xác minh và chỉ dẫn đường takeover đã kiểm. Không restore owner sau reconnect/restart.

Cảnh báo theo consequence và urgency, có lý do/nguồn/thời gian/hành động phù hợp. Acknowledge không resolve underlying fault. Audio/haptic bổ sung khi API được kiểm; không giả âm thanh là bằng chứng. Alert mới không làm toolbar/critical buttons nhảy hoặc che mất video/map quan trọng. Kiểm mode confusion và alarm overload bằng operator scenarios, không chỉ screenshot.

Trắng/đen là nền; vàng nhấn phụ cho selection/route. Đỏ/amber reserved cho nguy cơ khi cần; nghĩa không dựa riêng màu. IBM Plex Sans hiện có, typography/data units rõ, ít decoration. Native touch≥48dp và khoảng cách/size tăng theo thử glove; CSS checks không thay native/operator acceptance. Advanced options hiện theo ngữ cảnh, tránh cockpit đầy nút và AI chat chiếm chỗ thao tác bay.

`operator-cockpit.html` là **bản minh họa tương tác độc lập**, tất cả số, map, video, polygon và lời gợi ý là giả lập; không gọi radio/SDK/SITL hoặc endpoints bay. Sáu scenario cho bình thường/vùng giới hạn/video cũ/mất telemetry/pin thấp/airspace cũ. Header/footer ghi provenance; bản đồ giả không dùng để quyết định bay. Đây không phải tính năng mới của APK hay Fly candidate.

## Điều gì có thể tạo lợi thế vượt trội

Đề xuất khác biệt: capability-aware multi-payload với ownership rõ; offline mission-to-media-to-handoff; giải thích đúng vì sao không thể tiếp tục; AI assistance có evidence/uncertainty; refly dựa quality thực; workflow nhất quán VN/EN; fault recovery không nhân đôi lệnh hoặc mất hồ sơ. Đây là hypotheses cần thử, không khẳng định đối thủ thiếu chúng.

Đạt parity phải hoàn tất core control/video/airspace/native trước. Chứng minh superiority bằng named DJI aircraft/controller/Pilot/FlightHub/payload và Ragas binary/version trên workload so được; đo completion/time/errors/mode-confusion, end-to-end input/control/video latency+jitter+frame age, recovery, usable coverage/GSD/blur/geographic error, resources/heat/power và data integrity. Giữ failed/missing/aborted samples; không dùng vendor latency numbers không rõ boundary hoặc FPS host làm baseline thắng.

## Thứ tự tiếp theo đề xuất

1. Chốt full-product capability/mode/authority/alert contract và UX state map, gắn47 requirements vào gates; tránh triển khai hàng chục màn riêng không chung context.
2. Làm module **geo-awareness + operational geofence** riêng bằng synthetic/authorized offline corpus: polygon holes/concavity/boundary/intersections/time/altitude datum/stale coverage/authorization, rồi AP fence upload/readback/breach trên SITL khi được phép và đủ tài nguyên. Không cần SDK cho contract/geometry/replay.
3. Bổ sung FlightOps cockpit/state/alert/input/video descriptors theo capability bằng mock/replay, nối cùng native journey trong module riêng. Giữ nguồn/video/AI là unavailable khi chưa có thực.
4. Nghiệm thu actual Android khi gate dung lượng đạt; sau đó bench/HIL HeraHub/Hera với input/radio/video/payload thật. Đóng performance/journal/endurance open gates theo kế hoạch hiện hữu, không ký lách hoặc tự restart.
5. Thêm AI perception/quality/tracking có corpus và metric độc lập; chỉ mở quyền autonomous control khi sensor/compute/fallback và closed-loop gates đã đạt. Field survey/media → A/B → production release; fleet/VIO/night theo scope riêng.

Nguồn/candidate/ENDURE vẫn đóng băng. Đây là nghiên cứu đề xuất; cần quyết định scope triển khai tiếp, không tự tích hợp vào release.
