# AERIS Beta Campaign 01

26/10/2026 · Kế hoạch của kiến trúc sư trưởng · Revision 1

**Đích: một bản beta Android hoàn chỉnh trong phạm vi giả lập được công bố, có thể cài lại, vận hành nhiều nhiệm vụ và bàn giao cho nhóm chuẩn bị HeraHub.** Đây là kế hoạch, chưa phải lệnh chạy campaign, kết quả nghiệm thu hay quyền bay thật. Trạng thái ban đầu của mọi gate mới là NOT_STARTED. Các bản source/candidate đóng băng, canonical SOT và ENDURE giữ nguyên.

## 1. Cam kết sản phẩm và cách chốt beta

Người nhận được APK engineering, host companion, cấu hình simulator, corpus nhiệm vụ, hướng dẫn và receiver độc lập. Từ một máy đã đáp ứng prerequisite, họ tự cài, ghép đúng simulator, lập nhiệm vụ, kiểm trước bay, bay manual/bán tự động/AUTO, điều khiển payload, xem video, xử lý sự cố và nhận hồ sơ review có thể kiểm lại. Không cần người phát triển sửa file hoặc gọi lệnh terminal giữa từng bước của nhiệm vụ.

Một release ID ràng buộc commit, APK/certificate, host, firmware và cấu hình AP, model vật lý, bộ nguồn bản đồ/địa hình, topology payload, version WebView/codec, schema và dữ liệu thử. Không cộng PASS của OPERATOR01, MissionBeta01, BETA-VIDEO03 và SIM-STABILITY03 để gọi một APK mới hoàn tất. Sửa thành phần ảnh hưởng gate nào phải kiểm lại gate đó trên release cuối.

Ba mức ra khỏi chiến dịch:

| Mức | Ý nghĩa | Điều kiện |
|---|---|---|
| BETA-SIM | Beta trên Android emulator và host simulator tham chiếu | Tất cả yêu cầu MUST của campaign PASS trên cùng release/config; corpus, fault, hiệu suất, UX, lưu/nhập và bàn giao đạt |
| BETA-DEVICE | Cùng beta đã kiểm trên điện thoại/controller Android xác định | BETA-SIM + model/OS/WebView/GPU/input/thermal thực, cài đặt/mạng/lifecycle/SAF và workload trên thiết bị đó |
| HERA-BENCH-READY | Hồ sơ và adapter sẵn để nhóm bench Hera tiếp nhận | Contract input/transport/payload có thể thay provider, unknowns có chủ xử lý, test/HIL kit và checklist; chưa đồng nghĩa HERA-FLIGHT-READY |

Chiến dịch có thể đạt BETA-SIM khi chưa có HeraHub. Không gọi BETA-DEVICE đã đạt nếu chỉ có emulator. Cài được APK không chứng minh điều khiển máy bay thật an toàn. Khả năng thiết bị vật lý được thêm vào supported-configuration matrix sau quan sát thực, không từ `minSdk` hay BOM.

## 2. Tình trạng đầu vào và quyết định kiến trúc

Codebase đã có nhiều nền tảng dùng lại. SIM-STABILITY03/AP04 hoàn tất manual Android–SITL, RTF 1,000696× với 116.815 frame; replay model gốc khớp byte. Nhưng recorder của lượt dài tràn, elapsed tiếp tục tăng sau closure, UI harness có thể dừng vì template trang không khớp, và xóa ADB reverse không tạo đúng một vụ mất socket. MissionBeta01 có polygon điều hướng đạt nhưng fail video maximum gap; BETA-VIDEO03 có một lượt video đạt và còn lỗi niêm phong. Đây là nguyên nhân phải hợp nhất, không phải lý do viết lại toàn bộ.

Quyết định:

1. **Một product line tích hợp**, dự kiến `native/betaintegrated01` + `pilot/betaintegrated01`, manifest dependency rõ. Dừng sinh thêm một ứng dụng riêng cho mỗi patch. Tận dụng module hiện có qua adapter; không sao chép toàn repo, không rewrite Java sang Kotlin/Compose hay thay engine 3D chỉ để đổi stack.
2. Android tiếp tục dùng shell/bridge native hiện có và giao diện đã duyệt. Native sở hữu socket, clock/boot identity, vòng đời input, durable I/O cần thiết và giải mã khi cấu hình phù hợp. UI không làm authority source và không scan toàn history/geometry trên mỗi telemetry tick.
3. Host simulator sở hữu AP SITL, physics, cảm biến/môi trường, camera tổng hợp, instructor fault và scene. Companion là hạ tầng mô phỏng, không phải một dependency bắt buộc cho app GCS khi sau này nối radio/drone thật.
4. Một flight domain và một mission model dùng chung cho Workbench/Fly/review; một owner vẽ mỗi vùng UI. Bản kế hoạch, bản đã upload/readback và tiến trình bay là các state riêng.
5. SIM provider và hardware provider dùng contract chung nhưng capability/transport binding khác nhau. SIM phải hiện rõ; không có nút chuyển ngầm từ simulator sang máy bay thật. Thay provider không giữ lease/session/approval cũ.
6. Renderer/audio chỉ nhận pose/motor/camera ground truth đã kiểm tuổi. Không tự viết pose ngược vào flight control; replay phải có nhãn và clock riêng. Tham chiếu kiến trúc FDM/SITL của [ArduPilot](https://ardupilot.org/dev/docs/simulation-2.html) và [JSON backend](https://ardupilot.org/dev/docs/sitl-with-JSON.html).

```text
ANDROID A / ANDROID hoặc CLIENT B độc lập
  Workbench → Preflight → Fly + Camera → Review
                 │
  Mission / Flight / Payload / Authority / Evidence domains
                 │
  Native I/O + clock + input + decoder + durable workspace
                 │  simulator endpoint có identity + quyền
HOST COMPANION   Transport / session broker / fault proxy
                 ├── ArduPilot SITL ↔ physics 6DOF tham chiếu
                 ├── camera/gimbal/sensor peers và camera-file pipeline
                 ├── environment / obstacles / instructor
                 └── 3D/audio observer + independent replay/receiver

SAU CHIẾN DỊCH: thay provider bằng radio/MCU/camera thật đã bench/HIL.
```

### Ranh giới bắt buộc

- Mỗi intent mang aircraft/session/boot/operator/resource/sequence/clock/capability context. Mất session, stale, background, thu hồi hoặc reboot phải làm quyền cũ vô hiệu; không tự tái dispatch lệnh chưa rõ kết quả.
- Tách ACK, reported state, observed execution và file ảnh. ACK camera không được cộng vào actualImages. Đối chiếu [camera v2](https://mavlink.io/en/services/camera.html), [gimbal v2](https://mavlink.io/en/services/gimbal_v2.html) và [mission protocol](https://mavlink.io/en/services/mission.html).
- Retry giao thức phải được phân loại theo thao tác. Read request và mission transfer có bounded retransmission đúng phiên; non-idempotent capture/flight action có intent ID, uncertainty và reconciliation. Không blanket retry HTTP POST; cũng không tắt toàn bộ reliability của MAVLink. [Command protocol](https://mavlink.io/en/services/command.html) là tham chiếu, còn execution được xác nhận riêng bằng state.
- Native flight/raw, media và UX diagnostics dùng budget/channel riêng. Backpressure không được làm optional renderer hoặc scan quota chặn heartbeat. Có thể giảm chất lượng graphics/video theo profile được công bố, nhưng không bỏ physics/control frame, bỏ fsync hay che tuổi dữ liệu để lấy PASS.
- Firmware/model/profile và cấu hình failsafe đều pin. Chỉ đọc/đối chiếu trước khi cấp quyền; mọi ghi tham số nếu cần nằm trong thao tác mô phỏng rõ ràng, lưu before/after. Không dùng config simulator như cấu hình Hera thật.

## 3. Phạm vi beta: đa năng nhưng có ranh giới

**MUST:** một aircraft mỗi mission; hai operator độc lập; tới bốn payload peer mô phỏng; manual, Hold/RTL/LAND, assisted POI/orbit và AUTO; survey polygon, corridor, waypoint/inspection, tìm kiếm theo lưới; Home/cao độ và KML/QGC subset; offline map/terrain đã pin; preflight/failsafe; RGB/thermal tổng hợp; file ảnh gắn vị trí drone tại exposure; review/replay/SAF; 3D/audio/môi trường; fault/restart/quota; APK/companion cài lại được và kit bench.

Các tính năng beta phải có trong hành trình sử dụng, không chỉ contract CLI. Màn hình radio/camera thật chưa có provider phải ghi capability chưa hỗ trợ, không để thao tác trông như đã kết nối.

**Gate riêng sau BETA-SIM:** Phase One/Sony/thermal/LiDAR thật, RTK/NTRIP/PPK thật, HeraHub MCU/radio/HID vật lý, mô hình Hera hiệu chuẩn, data nguồn vùng trời vận hành, bay đêm/tầm xa thực địa, production signing/update custody và NDAA/vendor compliance. Contract và emulator cho các mục này có trong beta; claim phần cứng thì chưa.

**Sau beta:** fleet/multi-UAV/deconfliction, GNSS-denied/VIO, AI target tracking/autonomous replanning, 3D mission editing nâng cao, radiometric thermal và tọa độ vật thể từ LRF. Không dùng nhãn AI để gộp các năng lực chưa kiểm. Danh sách 48 nhóm yêu cầu gốc được ánh xạ đầy đủ trong `campaign.json`, gồm phần beta và phần gate riêng.

## 4. Bảy milestone thực sự

| Mốc | Kết quả người dùng | Gate ra | Phụ thuộc | Dự toán kỹ thuật* |
|---|---|---|---|---|
| M0 · Release baseline | Có đúng một nhánh/source/config và lối cài/chạy rõ | Dependency closure, giấy phép/pins, manifest, prerequisite, lỗi tồn, missing-file disposition, corpus và target chốt; không đụng frozen | Không | 1–2 ngày |
| M1 · Flight runtime bền vững | Bay manual/assisted, dừng và mở phiên mới đúng cách | Sửa recorder/closed clock/UI state; neutral handoff; full-frame fsync; actual socket loss/AP reboot; 30 phút vòng kín không tràn | M0 | 3–5 ngày |
| M2 · Mission workbench | Kỹ sư lập và bay nhiều loại nhiệm vụ ngay trong app | Shared mission model; KML/QGC semantic oracle; geo/Home/terrain; upload/readback; AUTO/Hold/resume/RTL; review | M1 | 3–5 ngày |
| M3 · Payload, video và crew | Hai người vận hành nhiều payload và nhận ảnh có tọa độ | 4 peer/đúng route, ownership riêng; camera files/ground truth; video xuyên nhiệm vụ; revoke/partition/reboot; SAF receiver | M1; release tích hợp dùng M2 | 4–6 ngày |
| M4 · Simulator và cockpit | Trải nghiệm mô phỏng có thể dùng để diễn tập và trình diễn | Physics/sensor/environment corpus, 3D/audio bám state; UX toàn màn/theme/popup/input; instructor và debrief | M1; chạy tích hợp với M2/M3 | 4–6 ngày |
| M5 · Qualification release | Một APK/host vượt toàn bộ chiến dịch | Cùng release: nominal lặp, fault corpus, perf/endurance, receiver, restart, cài lại; independent QA; zero P0/P1 trong beta scope | M2,M3,M4 | 4–6 ngày + thời gian soak |
| M6 · Handoff và bench kit | Nhóm khác tự cài, chạy bài và chuẩn bị thay provider thật | Người nhận cài sạch, chạy mission/fault, kiểm gói; supported matrix, giới hạn, adapter API, bench/HIL plan và demo hội đồng | M5 | 2–3 ngày |

*Đây là dự toán engineering, chưa phải cam kết ngày giao hay năng suất agent. Tổng effort khoảng 21–33 ngày-người theo gói công việc trên, chưa tính chờ máy/SDK và tái kiểm khi fail. Với 2 builder chủ chốt + 1 QA, các lane M2/M3/M4 có thể chồng một phần; dự kiến ban đầu 4–6 tuần lịch bao gồm qualification, không suy từ tổng effort thành lịch tự động. Sau M0 phải ước tính lại bằng cycle time thực. Nếu một người thực hiện toàn bộ, thời gian tăng; không hứa ngày hoàn tất từ số LOC. Không giảm gate để giữ lịch.

**Critical path:** M0 → M1 → tích hợp M2/M3/M4 → M5 → M6. Khi chưa có M1, chỉ làm mock/oracle/design độc lập; không mở nhiều runtime để che lỗi nền.

## 5. Work package đầu tiên và quản trị lỗi

M0 phải hoàn thành: bảng retain/adapt/retire theo module; chọn nguồn MissionBeta/Native98/Workbench và 9 file overlay SIM-STABILITY03 bằng digest; danh sách lệnh launcher duy nhất; kiểm serial/port/owner, namespace workspace, fonts/definitions và toàn dependency được chọn. 97 tracked missing paths phải được phân loại. Nếu cần file từ Git/backup, phục hồi đúng byte vào intake của beta cô lập; không reset hoặc viết vào đường dẫn đóng băng.

M1 làm theo thứ tự:

1. Tái hiện recorder full, activeAPSeconds sau close và navigation mismatch bằng replay/fault nhỏ. Giữ receipt cũ làm regression. Lưu thời điểm closed monotonic/UTC đúng một lần, không dựng lại elapsed từ now sau đóng.
2. Xác định capacity theo frame/event thực; preflight phải từ chối duration vượt khả năng capture. Thiết kế chunk/spool có sequence/head SHA/CRC/commit và failure seal, không overwrite unread trace. Nếu cần sửa instrumentation AP, tạo artifact riêng, pin source/compiler/binary và kiểm differential; không thay binary đã pin hoặc thuật toán bay âm thầm.
3. Đóng writer, journal và process theo state machine, không bỏ cleanup khi logging fail. Correlate host/guest clock bằng bracket và báo uncertainty. No fresh data → UNKNOWN, không suy LAND từ pose cũ.
4. Kiểm mock trước, một actual manual ngắn rồi mới tăng 5/15/30 phút. Mỗi mutation uncertain dừng để quan sát/reconcile, không tự thử lại takeoff.
5. Fault transport phải chứng minh socket bị cắt tại proxy/FD được sở hữu, có last RX/first timeout, byte counter và clock. Không dùng việc xóa port mapping làm bằng chứng mất link.

Mỗi lỗi có severity, reproduction, first domain failure, owning module, affected gates, proposed repair và raw refs. Sau hai lượt cùng chữ ký lỗi không có evidence mới, dừng live rerun và chuyển replay/instrumentation. Không mở một namespace sản phẩm mới cho mỗi patch. Budget mỗi work package/actual campaign phải khai báo trước; hết budget giữ nguyên outputs và báo blocker, không chạy vô hạn.

## 6. Thiết kế corpus và chiến dịch kiểm

### Sáu lớp kiểm, không thay thế nhau

1. **Unit/property/semantic oracle:** parser, math/geo, typed parameters, mission semantic roundtrip, authority races, clocks, writer faults. Sinh held-out seed sau khi khóa implementation; không sửa fixture để lấy PASS.
2. **Protocol peers/replay:** real framing/CRC/sequence, wrong target, duplicate/late ACK, boot/session, 4 payload peer, mTLS/operator identity, reliable transfer và uncertainty.
3. **Headless AP + physics:** AP thật, ground truth, deterministic model oracle, constraints/load/wind/sensor/collision, recorder integrity và timing. Scene không nằm trong control loop.
4. **Android UI + AP + media + 3D:** dùng APK thật; thao tác giao diện đã quan sát, log native input và event; foreground/background, IME, popup, SAF và OS lifecycle. DOM mock không thay tầng này.
5. **Candidate qualification:** tất cả workload/fault/endurance trên cùng release ID, dữ liệu đóng được receiver process riêng kiểm lại sau khi runtime dừng.
6. **Receiver/operator acceptance:** người nhận khác cài lại, tự làm bài theo tài liệu, nhận diện UNKNOWN, takeover và package thiếu/hỏng. Review của agent không thay human usability.

### Bộ bài thực tế

Nominal gồm: manual hold/pitch+yaw/takeover; polygon đồng bằng/địa hình/no-data boundary; corridor thẳng/gấp khúc/đổi datum hợp lệ; inspection orbit/waypoints; lưới tìm kiếm ban ngày/đêm; low-battery RTL/alternate trong mô phỏng. Polygon3 + corridor3 chạy tối thiểu 3 lần với seed/profile đã khóa: 18 mission, thêm manual/inspection/search. Seed held-out thuộc cùng supported envelope, không chọn lại ca dễ sau failure.

Corpus danh nghĩa hướng tới polygon khoảng1/5/20ha và corridor0,5/2/5km, có cao độ/tốc độ/overlap/battery reserve phù hợp model được chọn, không ép mission vượt envelope để có màn demo dài. Đây là kích thước mục tiêu của corpus cần compiler/physics đáp ứng hoặc được xử lý rõ ở M0. Phép chiếu phẳng hiện giới hạn khoảng cách phải được thay bằng geodesic/local-frame chuyển đổi có oracle hoặc từ chối vùng ngoài miền; không coi5km đã hỗ trợ chỉ vì vẽ được đường. Một mission đơn lẻ vẫn cần đủ thời gian active và capture budget; không cắt đầu/cuối để tránh recorder.

Fault gồm: mất link khi giữ cần tiến, high latency/loss/jitter/reorder, AP reboot khi airborne, host chết, app background/force-stop/rotate, wrong target/gimbal device, stale camera/RGB↔thermal, mất operator B/tranh chấp/late grant, ENOSPC/EIO/short write/fsync fail, gói thiếu/hỏng/replay/sai receiver, DEM/geoid/clock/Home không hợp lệ, GPS/EKF/obstacle sensor dropout, motor fault/payload swing. Các ca vật lý không nhất thiết phải hạ cánh thành công: PASS có thể là dự đoán mất kiểm soát/collision và hồ sơ thất bại đúng; không giả khả năng giữ bay với 2–3 motor hỏng của một quad.

Mỗi case lưu preconditions, input/model/seed/config, injection thật, oracle độc lập, expected behavior, timeout/quota, raw closure và verdict. Mức mô phỏng gắn trên từng trường hợp: scripted mock, real protocol peer, actual AP, Android emulator hoặc physical target. `campaign.json` liệt kê case IDs và requirements tương ứng; đây là thiết kế corpus, chưa phải test executable hay kết quả.

### Video, ảnh và geotag

Đo source/generate → encode → host queue/send → Android receive → decode → canvas submit/present proxy, không chỉ FPS trung bình. Ghi clock uncertainty và giữ toàn khoảng AUTO; đo p95/p99, max gap, min5s FPS, rejected/dropped/recovery counts. Không gọi canvas timestamp là photon latency. RGB/thermal simulation có nguồn, seq, frame age, resolution/FOV/calibration version riêng; đổi feed không đổi quyền.

Camera peer phải tạo file ảnh từ camera view của simulator, không lấy ảnh màn observer làm ảnh camera. Image index, exposure event, raw file SHA, session/payload/position/quaternion và time-sync bracket đi cùng file. EXIF chỉ ghi trường có datum/định nghĩa phù hợp; sidecar giữ WGS84, relative/Home, AMSL/ellipsoid/geoid và uncertainty rõ. Mất dữ liệu đồng bộ thì đánh GEOTAG_UNCERTAIN, không gắn vị trí mới nhất như exposure. Beta đếm simulated files riêng; actual hardware photos luôn 0 khi chưa có camera thật. Khách cần tọa độ drone/camera lúc chụp, không tự suy ra tọa độ vật thể.

## 7. Vật lý, đồ họa và âm thanh: chân thực có thể giải thích

Profile gồm frame/rotor geometry, mass/inertia/CG, thrust/torque curves, motor lag, drag, battery/voltage sag, wind/gust, sensor/FOV/noise và contact model. Đơn vị/trục ENU-NED-FRD/quaternion và altitude datum phải có oracle. Model tham chiếu hiện có là baseline; model khác được version riêng, không thay đồng thời model và performance rồi gọi là đối chứng.

Mức độ chân thực:

- FID1: model tham chiếu, có phương trình/unit/seed và oracle; tham số có thể là giả định R&D.
- FID2, bắt buộc cho beta: AP vòng kín, frame/clock/raw đầy đủ, corpus động lực học/sensor/collision qua differential và envelope được công bố; chưa là Hera calibrated.
- FID3, sau khi có dữ liệu RtR: đối chiếu log Hera ở tải/gió/nhiệt/pin khác nhau, fit trên calibration set và kiểm held-out flights. Camera/gimbal/âm học cũng cần dữ liệu riêng.
- FID4: HIL và bay kiểm soát, thiết bị/hardware faults và operational envelope được RtR chấp nhận.

Mưa/gió/đêm phải tách phần vật lý, suy giảm cảm biến/link và hiệu ứng nhìn thấy. Không đưa con số derating hoặc battery-vs-altitude như sự thật Hera khi chưa có data. Dây treo dùng model pendulum/tension và contact có test conservation/timestep, không chỉ animation. Va chạm khác avoidance: sensor phát hiện, AP giảm tốc theo cấu hình, còn contact giải quyết va chạm nếu tránh thất bại.

3D ưu tiên model có license, PBR, scale/thrust axes đúng, terrain/environment có nguồn, ánh sáng/shadow ổn định và camera follow/ground/payload. Chất lượng giảm có profile rõ khi GPU không đủ; physics, raw và fidelity envelope giữ nguyên. WebGL2 hiện có là baseline; chỉ chuyển WebGPU/engine khi benchmark cùng scene/workload chứng minh lợi ích và có fallback. Không cài engine/asset pack lớn chỉ vì tên công nghệ.

Âm thanh tổng hợp đi từ RPM/load/distance/direction và environment, có limiter; bật bằng gesture rõ. Armed/stale/background/ended phải gate đúng, có kiểm PCM/loopback hoặc audio capture thật. Active audio track không chứng minh có tiếng. Không công bố SPL/timbre Hera cho đến khi có recording/RPM/thrust/distance reference. Hội đồng xem projected scene nhưng pose vẫn từ flight loop, không chạy video kịch bản thay cho điều khiển.

## 8. Chuẩn UX của cockpit cao cấp

Giữ RtR trắng/đen, vàng nhấn ít; font tiếng Việt đủ weight, số tabular và đơn vị/datum sát giá trị. Fly ưu tiên video/map, actual mode, source/age, ownership, battery/link/GNSS và cảnh báo có thứ tự. Header/footer thấp hợp lý; hai rail độc lập cùng trục Y, thống nhất grid/spacing/hitbox. Blur glass thích nghi nền sáng/tối, có scrim khi cần đọc; không hy sinh contrast để trong suốt.

Một design-token system dùng chung cho Plan, Preflight, Fly, payload panels, Review, file dialogs và lỗi. Icon đúng chức năng/state và accessible label; sun/moon đổi đúng, battery không cần text thừa. Nút có enabled/pending/denied/unknown rõ; slider chỉ đổi requested value, Apply/capture intent riêng khi hợp đồng yêu cầu. Critical action không bị IME/popup che; emergency Hold/RTL/LAND luôn truy cập được trong state được phép.

Đo ở 1280×800 tablet/controller và landscape phone profile thật được chọn, font scale1.0/1.3/1.5, insets/IME, 2 theme và bright/dark camera backgrounds. Hitbox ≥48dp theo [Android](https://developer.android.com/guide/topics/ui/accessibility/views/apps-views); glove mode56–64dp là mục tiêu dự án cần người dùng thử. Contrast text thường ≥4.5:1, text lớn ≥3:1 theo [W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html); không coi đó là chứng nhận toàn bộ cockpit WCAG.

Human gate: ít nhất 5 người thuộc vai pilot/survey/payload, làm 5 task chuẩn; ≥90% task hoàn thành không có developer cứu, 0 unintended critical action, severity P0/P1 bằng0. Đây là formative pilot để tìm lỗi, không phải mẫu thống kê chứng minh ưu thế thương mại. Ngưỡng gesture/time/workload khóa trước buổi thử. Chưa có người tham gia thì human gate NOT_CHECKED.

## 9. Quality/performance contract

Tất cả số mục tiêu bên dưới là **đề xuất engineering của AERIS**, trừ tham chiếu UI đã dẫn. M0 khóa target profile, method và ngân sách; thay đổi phải có lý do/ADR trước lượt kiểm mới, không hạ ngưỡng sau khi fail. Gate cũ nghiêm hơn trên một slice được giữ cho slice đó.

| Nhóm | Beta target / cách đo |
|---|---|
| Control identity | 0 accepted stale/wrong aircraft/operator/boot/route intent; sequence/clock/lease checked; HB guard1500ms và input lease200ms hiện hành không nới |
| Physics | speedup1, pacing cap500ms, fsync-before-sensor, không mất frame; aggregate RTF≥1.000 trong cửa sổ nominal đã khai báo; clock uncertainty không đủ thì INCONCLUSIVE, không PASS |
| Renderer | Foreground full-quality1280×800: RAF p95≤33.4ms, p99≤100ms, đo cùng SITL/video; RAF không thay GPU-present/photon metric |
| Video RGB | 720p30 source, decode/display ≥24FPS ở mọi bin5s đầy đủ, p95 upper source→canvas≤300ms, conservative max gap≤250ms xuyên toàn AUTO; cold-first-frame≤1500ms trên profile chính |
| Thermal simulated | Rate/resolution khác RGB phải ghi profile, không kéo FPS RGB thành thermal claim; frame age/clock/route luôn kiểm |
| Local UI | Touch-to-visible-feedback p95≤100ms trên target; tách ACK latency; không ANR/crash trong mandatory corpus |
| State/review | Closed elapsed bất biến; không stale pose thành state sống; review status và file completeness độc lập; receiver từ chối mọi tamper/missing/foreign context trong corpus |
| Geometry/control | Trên calm reference profile: cross-track RMSE≤1m, max≤3m và altitude RMSE≤0,5m trong đoạn đã định nghĩa; ground truth/estimations đo riêng. Với wind/load khác, envelope/tolerance khóa theo profile trước khi chạy |
| Simulated exposure/geotag | Index/route/fileSHA khớp100%; position error≤1m và altitude≤0,5m so exposure ground truth, time-bracket uncertainty≤50ms trên profile chính; không áp thành accuracy ảnh Hera thật |
| Model oracle | Static force/acceleration và charge integration sai số≤1%, pendulum natural frequency≤5% so analytical fixture; exact old-model byte oracle giữ khi thuật toán không đổi; timestep/noise/contact tolerances khóa riêng trước test |
| Storage | Admission20GiB, runtime floor10GiB +256MiB reserve, forecast15s; thêm ngân sách cho raw/video/clone/export/checkpoint, không dùng free disk một thời điểm như toàn ngân sách |
| Long run | Sau nominal/fault đạt: 30min → 2h → 8h cùng bộ phiên bản; 24h là gate endurance cuối trên host/storage phù hợp. Không cộng interval, không thay actual-loop soak bằng replay để báo PASS |
| Resource stability | Không unbounded queue; sau warmup không tăng retained heap/RSS theo số mission. M0 đặt absolute ceilings từ baseline; 2h/8h/24h report phân biệt heap, RSS, GPU, guest và workspace |

WAL AP04 đo 215.851.544 byte/97,2773s, ngoại suy khoảng7,44GiB/giờ và178,55GiB/24h, **chỉ WAL**. Đây không phải số đo soak/compression. Long run cần storage bên ngoài/host chuyên dụng hoặc lossless storage đã chứng minh byte-equivalence; phải tính trace/video và bản sao. Không tự xóa raw đã nghiệm thu để nhường chỗ. Nén/segment không được đổi ordering/barrier hay bỏ frame. Chuẩn bị nguồn điện/lid/sleep supervision và owner PID/port bằng observer thật. ENDURE cũ chỉ đọc, campaign beta có evidence root mới.

## 10. Quy trình phát hành và mức tin cậy

Các vai: Chief Architect chốt scope/seams/gates; integration builder giữ product line; flight/simulation builder và media/payload builder xử lý lane; QA adversarial độc lập kiểm raw/oracle; pilot/payload users làm usability; release owner giữ key/artifact. Có thể một người kiêm vai theo giai đoạn nhưng phải công bố self-review; không gọi là independent QA. Chỉ giao agent khi được phép và có work package rõ, không thêm reviewer cho mỗi file.

CI nhẹ cho parser/types/schema/model/authority/journal và headless protocol. Nightly/host lane chạy corpus AP/Android theo admission; renderer/perf lane trên đúng target. `run-manifest` chứa releaseID/configID/scenarioID/seed/data source hashes/start clocks/owner/budget/expected outcomes. Verifier không được đọc chính summary PASS làm oracle. Fresh receiver kiểm lại source records, chain, sequence, media SHA, temporal/geo consistency và completeness.

Release freeze: tag candidate, source/SBOM/licenses, exact APK signing cert, host digest, protocol dialect/XML, AP artifact và config, model/assets. Cài trên profile sạch, không phụ thuộc đường dẫn home của developer; package kiểm path traversal/symlink/duplicates, version/schema và wrong receiver. Dùng development/beta signing riêng, không kèm key; production signing/custody là gate riêng. Update/migration phải giữ original workspace và không tự phục hồi quyền khi rollback/restart. Lỗi candidate giữ evidence; bản sửa tạo release mới, ảnh hưởng gate nào chạy lại gate đó.

Severity áp cho lỗi trong beta scope: P0 là sai aircraft/quyền/dữ liệu critical hoặc thao tác bay ngoài ý định; P1 là mất chức năng lõi, crash/ANR, mất hồ sơ hoặc vượt performance gate bắt buộc; P2 là lỗi không chặn task có workaround rõ. Priority của feature tương lai không được nhầm với severity của defect. P2 chỉ được deferred khi không vi phạm bất kỳ MUST nào và được ghi trên handoff. Không cho fail P0/P1 bằng điểm tổng hoặc tỷ lệ case pass.

Định nghĩa DONE: mọi MUST PASS trên same final release/config; không P0/P1 mở trong beta scope; không required NOT_CHECKED; raw/review/receiver/preservation đối chiếu; runtime đóng sạch; người nhận cài/chạy được và limits rõ. Handover README, APK+checksum/cert, companion, supported matrix, corpus, sample reports, diagnostic export, troubleshooting và known limitations cùng version. Hoàn tất kế hoạch không phải hoàn tất sản phẩm.

## 11. Mục tiêu vượt DJI: đo khác biệt có giá trị

DJI công bố các năng lực cao cấp như terrain-follow, POI/Smart Track và route automation trên [Matrice400](https://www.dji.com/matrice-400). Đó là publisher claims làm nguồn yêu cầu tham khảo, không phải benchmark AERIS đã thắng. Nhiều năng lực phụ thuộc cảm biến/aircraft, không thể giải quyết chỉ bằng UI.

AERIS chọn bốn trục lợi thế để kiểm: (1) workflow khảo sát/inspection ít công hơn, (2) payload nhiều hãng và hai operator có quyền rõ, (3) simulator/replay giải thích và tái tạo sự cố, (4) offline-first/data provenance và khả năng tự triển khai. Mục tiêu đề xuất: giảm ≥20% thời gian hoàn thành một tác vụ lặp so baseline thao tác thủ công hiện tại, 0 lỗi critical và cùng chất lượng đầu ra. Nếu có DJI/Pilot2 đúng cấu hình, chạy crossover cùng task/input/người/hardware; thiếu thiết bị thì ghi benchmark DJI NOT_MEASURED, không lấy mock làm đối chứng.

UI/UX phải đẹp và đọc được nhưng không bù cho lost control, media stale, geotag sai hay recorder thiếu. AI runtime không nằm trên critical path beta. Sau beta có thể thêm plan/preflight copilot theo proposal→deterministic validation→operator consent, so LLM/agent trực tiếp về chất lượng, thời gian, công người và quyền riêng tư; không cấp autonomous flight từ chat.

## 12. Chuyển sang Hera thật

Bench intake cần: HeraHub model/OS/MCU firmware/protocol, Android input/key/axis/calibration, radio topology/QoS, AP frame/firmware/dialect/parameters, flight-control ownership với RC độc lập, camera model/serial/lens/SDK, gimbal controller/limits/extrinsics, thermal radiometry, battery/thrust/mass/CG/payload envelope và timestamp/GNSS source. Unknown giữ UNKNOWN và giao đúng người RtR xác nhận.

Thứ tự sau beta: controller no-prop/bench → MCU/HID/calibration/input loss → radio/serial/telemetry read-only → payload/gimbal có tải giả và nguồn an toàn → HIL với failsafe/ownership → flight test do RtR phê duyệt và pilot thực hiện → khảo sát/inspection có ảnh thật/checkpoints. Không chạy thật vì cùng sysid hoặc cùng MAVLink. Night/range/obstacle avoidance/45+min/PhaseOne/NDAA là claim cần gate thiết bị và dữ liệu của RtR, không được giải phóng chỉ từ BETA-SIM.

## 13. Rủi ro và checkpoint quản trị

Rủi ro lớn: (a) module chồng chéo/2 owner UI, (b) recorder/capture và quota không tương thích long run, (c) unknown timestamp/ACK/device routing, (d) host scheduling làm video/control cạnh tranh, (e) simulator đẹp nhưng model chưa hiệu chuẩn, (f) thiếu hardware/human UX, (g) lặp live test khi chưa có evidence mới. Mỗi rủi ro có owner/trigger/mitigation trong dữ liệu campaign.

Báo cáo theo milestone: outcome đã dùng được, MUST pass/fail/not checked, raw/perf/config, regressions và gate còn lại. Có blocker về authority/integrity hoặc ngân sách thì báo ngay; không gửi DONE cho từng patch. Không chạy lại 24h cũ, không sửa hồ sơ lịch sử, không công bố ra ngoài hoặc ký production từ kế hoạch này.

Kế hoạch dùng Vibecode Kit6.3 và khung PRD; đây là đề xuất kiến trúc của assistant, chưa qua independent engineering/human flight review. `campaign.json` là bản máy đọc cho milestones, requirements, mapping48features, corpus, metrics, tasks và risks. `PLAN-VALIDATION.json` chỉ xác nhận tính nhất quán của kế hoạch, không xác nhận sản phẩm PASS.
