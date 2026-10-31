# AERIS: scan codebase và đánh giá khả năng đáp ứng

Ngày 21/10/2026. **Engineering alpha; chưa sẵn sàng thay phần mềm vận hành Hera hoặc phát hành thương mại.**

Đây là scan chỉ đọc mã và bằng chứng giữ lại. Không build, chạy functional test, Android hoặc SITL; không sửa source/candidate/ENDURE. Builder rà code, QA agent riêng phân tầng bằng chứng, Contractor đối chiếu file/hash và tổng hợp. Chưa có human hoặc hardware review mới.

## Tỷ lệ và cách đọc

Mẫu số là 48 nhóm trong feature matrix hiện có. Các nhóm có cùng trọng số, gồm cả tính năng nâng cao chưa chắc cần cho pilot thương mại đầu tiên. Thang đánh giá: 0 chưa tìm thấy implementation phù hợp; 1 có draft/contract nền; 2 có component từng được kiểm trong scope; 3 có hành trình Android–SITL được chứng minh ở cấu hình lịch sử; 4 toàn nhóm đạt trên cấu hình sản phẩm hiện hành và thiết bị mục tiêu. Một nhóm ở mức 2 hoặc 3 vẫn có thể thiếu nhiều subfeature.

| Chỉ số | Kết quả | Ý nghĩa |
|---|---:|---|
| Có nền mã/draft | 38/48 = 79,2% | Chưa nói mã đã build hoặc toàn tính năng dùng được |
| Có component từng được kiểm | 32/48 = 66,7% | Host/mock/SITL cô lập/Android; không phải current product đạt |
| Có journey trong scope lịch sử | 4/48 = 8,3% | F01/F18/F31/F40; không chuyển PASS sang APK mới |
| Đủ gate trên current Xiaomi/Hera | 0/48 = 0% | Chưa nghiệm thu target; không có nghĩa mọi code vô dụng |
| Chỉ số bằng chứng kỹ thuật | 74/192 = 38,5%, khoảng 39–40% | Đánh giá theo thang có QA đối chiếu, không phải % công việc hoàn thành |

Không diễn giải 39% thành còn 61% công việc, độ an toàn 39%, DJI parity 39% hoặc xác suất sử dụng được. Phân bố là 10 nhóm mức 0, 6 nhóm mức 1, 28 nhóm mức 2, 4 nhóm mức 3 và không có mức 4. Các gate bắt buộc quan trọng hơn điểm trung bình.

## Mức độ bằng chứng theo nhóm

| Nhóm | Điểm/tối đa | Chỉ số | Có nền mã | Có component proof |
|---|---:|---:|---:|---:|
| Điều khiển và an toàn | 22/44 | 50.0% | 11/11 | 10/11 |
| Lập nhiệm vụ và địa lý | 10/28 | 35.7% | 6/7 | 4/7 |
| Payload, video và ảnh | 8/28 | 28.6% | 4/7 | 3/7 |
| AI và tự chủ | 5/28 | 17.9% | 3/7 | 2/7 |
| Review và dữ liệu | 9/16 | 56.2% | 4/4 | 4/4 |
| Cộng tác và fleet | 2/12 | 16.7% | 1/3 | 1/3 |
| Nền tảng và phát hành | 11/20 | 55.0% | 5/5 | 5/5 |
| Giả lập và UI/UX | 7/16 | 43.8% | 4/4 | 3/4 |

Các tỷ lệ trong bảng là chỉ số của thang bằng chứng, không phải nghiệm thu toàn bộ tính năng. Điểm cao của storage/runtime không chứng minh độ tin cậy thương mại hay an toàn bay.

## Khả năng đã có và giới hạn

- **OPERATOR01:** APK development06 còn nguyên SHA; P1 đạt 12/12 engineering AC trong cấu hình cũ. Có AUTO 32 item, lệnh camera/gimbal lặp, consent hai vai trong một cockpit, mất link → RTL/UNKNOWN, SAF 2.824.775 byte và restart 23 file. Ảnh thật bằng 0; chưa phải hai operator từ xa hoặc payload thật.
- **INTEGRATION03:** có KML/QGC subset, CREW02 mTLS, writer native dùng chung và PBR observer. Latest integrated acceptance vẫn NOT READY: long-session stale 1509 ms, bootstrap EOF chưa rõ nguyên nhân, nominal/B/airborne 30 giây/SAF/restart final còn thiếu. APK04 khớp SHA nhưng nguồn hiện có một dependency thiếu.
- **PHONE06:** 10 file draft, 73.296 byte; tests rỗng; chưa có build script, dịch vụ host admission, viewer wrapper hoặc APK. Javac từng lỗi ba kiểu String → byte[]; đã sửa source nhưng chưa chạy lại. Khả năng biên dịch chưa được xác nhận.
- **Video và ảnh:** có metadata/routing camera mô phỏng và local VP8 decoder/watchdog. Chưa có camera thật → radio → fanout → thiết bị được nghiệm thu. Chưa có pipeline exposure → file gốc/EXIF → GNSS/time đủ bằng chứng.
- **Simulator:** có physics khối lượng/quán tính/tải/gió/pin tạm tính và thí nghiệm AP pitch+yaw/proximity/sensor loss riêng. Chưa trở thành training Hera hiệu chuẩn. Collision detection/math không thay collision response, sling hoặc lực va chạm.
- **3D:** có asset GLB/HDR/PBR có license, run/plan/native-WAL pose, quaternion, stale handling và rotor audio tổng hợp. RPM còn ước lượng từ armed/speed; chưa phải âm học Hera hoặc gate airborne performance hoàn tất.

## Các gap lớn chặn sản phẩm

1. **Tái lập build:** thiếu `native/crew02/assets/direct95/vendor/pilot/apstream40/definitions.mjs`, expected SHA `b881e15a33e92634ded232fc25b43693e558b662a36dd82571300899d261da7d`. Source07 hiện khớp 191/192 pin, PHONE06 khớp 159/160 dependency. Có bản sao đúng SHA tại `native/crew02/assets/workflow/preflight/definitions.mjs`. Scan không phục hồi file. APK cũ khớp SHA không chứng minh nguồn rebuild đầy đủ.
2. **PHONE06 chưa SOURCE_READY:** còn gap ép kiểu số, lease trước lần chạm đầu, thu hồi khi neutral/input lỗi, admission cũ còn hiệu lực sau lỗi mạng và nguy cơ khóa writer khi verify lại. Cần sửa và kiểm trước khi tạo bản cài.
3. **Tích hợp và acceptance phân mảnh:** nhiều package/prototype và overlay nguồn khác nhau. Cần một active manifest, build và luồng vận hành hiện hành; giữ lịch sử chỉ đọc, không xóa hoặc refactor đại trà.
4. **Media khách hàng:** thiếu live EO/IR, geotag ảnh thật, model/API camera, clock và đường truyền. Đây là gap trực tiếp của buổi họp.
5. **Hardware và production:** chưa qualify HeraHub input/radio, Phase One, ảnh thật, field đêm/tầm xa, hiệu chuẩn training, production key/update hoặc ENDURE 24 giờ.

## Bốn phản hồi buổi họp

| Yêu cầu | Đã có | Nghiệm thu vận hành |
|---|---|---|
| Streaming mượt nhiều thiết bị | Local decoder/watchdog; chưa rõ chặng gây giật | Chưa đạt |
| Ảnh có tọa độ camera/drone lúc chụp | Contract capture/metadata tổng hợp | Chưa đạt |
| RGB/thermal | Generic routing/capability nền | Chưa đạt |
| Bay đêm và tầm xa | Dark UI, preflight và failsafe component | Chưa đạt |

Chưa có outcome nào trong bốn yêu cầu được chứng minh đã giải quyết đầu-cuối trong vận hành AERIS thực. Điều này không kết luận airframe Hera thiếu khả năng tương ứng. Tọa độ đã chốt là camera/drone lúc chụp; thermal viewing, radiometry, bay đêm có người lái và VIO/night autonomy là các phạm vi khác nhau.

## Đề xuất task lớn

1. **BIG-01 Operator Alpha:** sửa pin/build và PHONE06, khép một APK Xiaomi → USB → KML/preflight/readback → AUTO/LOITER → operator/payload → 3D → review/SAF/restart. Là critical path nên làm trước.
2. **BIG-02 Live Media & Geotag:** đo đường video, network decode/fanout, RGB/IR, exposure → file → GNSS/EXIF → map/review/export trong cùng cockpit. Adapter/corpus có thể chuẩn bị song song sớm.
3. **BIG-03 Hera Bench/Field/Release:** exact hardware/SDK/radio/camera, night/range/energy margin và operational failsafe, production update/key/endurance/customer acceptance.
4. **BIG-04 Training fidelity:** nhánh physics 1×, tải/gió/pin/collision/motor fault, 3D/audio và instructor có dữ liệu hiệu chuẩn. Tái dùng BIG-01; AI/fleet/VIO chưa vào critical path inspection.

Work package, dependency, budget và Definition of DONE: [MILESTONES.md](</Users/os/Downloads/AI technique/aeris/planning/scan-20261021/MILESTONES.md>). Không có số đo đủ để cam kết ngày hoàn tất hoặc tổng công từ LOC.

## Quy mô và giới hạn scan

Quét 3,323 file nguồn, 149,367 dòng vật lý. Loại bản trùng byte còn 2,343 file/117,332 dòng; có 980 đường dẫn trùng nội dung byte. Phạm vi: app/services/native/pilot/tools/tests/deployment. Loại build, .local, runtime binary, vendor và evidence. Có generated bindings, historical fork, test/harness và mã minify; không gọi đây là production LOC hoặc dùng để tính hoàn thành. Hash dedup cũng không nhận ra hai bản logic giống nhau nhưng đổi package.

Chi tiết inventory: `inventory.json`. Đánh giá 48 nhóm và lý do: `feature-assessment.json`. Input pins, hai APK và dependency thiếu: `provenance.json`. Scan không chạy lại toàn bộ 71.158 đường dẫn bảo vệ; các full-baseline check trước là lịch sử. Không sửa source/candidate/ENDURE.

## Ma trận 48 nhóm

| ID | Yêu cầu | Mức 0–4 | Phạm vi được ghi nhận |
|---|---|---:|---|
| F01 | Mode thực, mode yêu cầu, chủ quyền điều khiển | 3 | P1 observedmode/authority journey; historicalconfiguration only |
| F02 | Joystick, nút/roller và tiếp quản | 2 | MCU logical/input Android components; physicalHID andphone stickpath unqualified |
| F03 | Arm, takeoff, AUTO, Hold, RTL, land | 2 | AUTO/arm/takeoff/ground/lossRTL subset; broadmanual/Hold/Land transitions not jointlyqualified |
| F04 | Pause/continue/resume nhiệm vụ | 1 | Snapshot/reconcile substrate; actualpause/resume flow missing |
| F05 | Hai operator độc lập và bàn giao quyền | 2 | mTLS separateB components; finalhandover/partition acceptance incomplete |
| F06 | Vùng cấm/hạn chế theo vị trí–cao độ–thời gian | 2 | Runnable4D syntheticairspace validity/conflict components; officialdata operationalqualification absent |
| F07 | Kiểm tuyến đi, quay về và nơi đáp với vùng trời | 2 | Runnable route/return/landing conflict checks; actualroutevalidation absent |
| F08 | Geofence upload/readback/breach | 2 | IsolatedAP fence/prearm component; nativeeditor/fulluploadworkflow absent |
| F09 | Dữ liệu vùng trời offline có thời hạn | 2 | Offlinecapsule/coverage/expiry component; operationaldata package absent |
| F10 | Preflight, GNSS/EKF/link/pin/failsafe alerts | 2 | Typedpreflight/failsafe components; latestintegrated longsession remainsfailed |
| F11 | Dự phòng năng lượng/gió/tải và điểm đáp thay thế | 2 | Reserve/wind/load calculator; Hera performancecurves notvalidated |
| F12 | Polygon/grid, camera/GSD/overlap/tốc độ | 2 | Compiler/readiness/intake components; realimagery coverage notqualified |
| F13 | Home, AMSL/AGL/ellipsoid/geoid/terrain | 2 | Datum/Home/source components; mixedterrain/native product incomplete |
| F14 | Corridor, structure scan, orbit/POI, oblique | 2 | Corridor subset implemented; structure/orbit/oblique incomplete |
| F15 | RTK/NTRIP/PPK và chất lượng định vị | 1 | RTK/correction/PPK readiness gates; NTRIP/rawGNSS/PPK processing notimplemented |
| F16 | Map/terrain offline và kế hoạch trên địa hình 3D | 1 | DEM/geodata model/observer foundation; offline native terrainediting notintegrated |
| F17 | Nhiều sortie, đổi pin, refly phần thiếu | 0 | No multi-sortie/batteryswap/refly workflow |
| F18 | Discovery và routing nhiều camera/gimbal | 3 | P1 actualAndroidSITL syntheticcamera/gimbal routing; no hardwarePhaseOne/topologyproof |
| F19 | EO/IR live, decode/switch và cảnh báo frame cũ | 2 | IsolatedlocalVP8 decode/watchdog proof only; no livecamera/networkfanout qualification |
| F20 | Camera/gimbal theo capability; Phase One | 2 | Genericcamera/gimbal repeatedcontrol; actualPhaseOne integration absent |
| F21 | Ảnh/video thực có nguồn, thời gian và GNSS | 1 | Syntheticcapture/metadatadeclaration foundation; no actual exposure/file/EXIF/timeGNSS pipeline |
| F22 | Đồng bộ nhiều feed, EO/IR và FOV overlay | 0 | Selectors/metadata are not synchronizedmulti-feed/FOV registration |
| F23 | Thermal radiometry, LRF và định vị mục tiêu | 0 | No radiometric/LRF/targetgeolocation product pipeline |
| F24 | AI hỗ trợ lập plan và giải thích preflight | 0 | No operational plan/preflight LLMagent |
| F25 | Nhận diện đối tượng/khuyết tật EO/IR | 0 | No EOIR perception/defect pipeline established |
| F26 | Bám đối tượng/gimbal và mất target | 0 | No closed-loop objecttracking/targetloss pipeline |
| F27 | Tránh vật cản và replanning có giới hạn | 2 | SeparateAP obstacle/sensorloss experiments; integratedavoidance/replan unqualified |
| F28 | Kiểm blur/coverage/GSD và đề nghị refly | 2 | Mockblur/GSD/overlap/quality models; no acquired-image/reflyclosedloop |
| F29 | GNSS-denied/VIO và night autonomy | 0 | No VIO/GNSSdenied/nightautonomy implementation established |
| F30 | Giới hạn AI, confidence, tuổi dữ liệu và fallback | 1 | UNKNOWN/provenance andAIunavailable policy foundation; actualconfidence/fallback agent absent |
| F31 | Journal và review liên kết nhiệm vụ | 3 | P1 actualmission-bound nominalaccepted/lossUNKNOWN review |
| F32 | Dataset lớn, stream/resume và integrity receiver | 2 | Hoststream/checkpoint and separateAndroidSAF components; no unifiedlargedatasetfinalworkflow |
| F33 | Timeline/replay lệnh, event, telemetry và media | 2 | Raw/event/posecorrelation components; no realvideo/media synchronizedtimeline |
| F34 | QGC/KML/GIS nhập xuất giữ ngữ nghĩa | 2 | KML/QGCSimpleItems subset verified; complex/fence/rally/fullGIS absent |
| F35 | Quota/retention/archive có kiểm soát | 2 | Hostquota/archive andnativestore components; targetendtoend incomplete |
| F36 | Fleet, lịch nhiệm vụ, vai trò và bảo trì | 0 | No fleetinventory/schedule/maintenance product |
| F37 | Remote cockpit và bàn giao có xác nhận | 2 | IndependentB localmTLS cockpit components; remoteoperationalhandover incomplete |
| F38 | Chia sẻ video/annotations/GIS có quyền | 0 | No livevideo/annotation/GIScollaboration workflow |
| F39 | Nhiều máy bay và deconfliction | 0 | No multiUAV/deconfliction product |
| F40 | Native lifecycle, persistence và restart | 3 | P1 process/coldboot retained23files/noautoconnect/authority; currenttargetfinal notaccepted |
| F41 | Xác thực, signing, chống replay và key lifecycle | 2 | EngineeringmTLS/pins +keylifecycle mocks; no productioncustody/radioMAVLinksigning qualification |
| F42 | Signed update, schema migration/recovery và supply chain | 2 | Hostupdate/trust/migration anddevsigning; no productionAndroidrelease qualification |
| F43 | Configuration, calibration và diagnostics | 2 | Typedfirmware/logicalMCU diagnostics components; physicaltarget calibration absent |
| F44 | Latency/jitter, overload, heat/power và endurance | 2 | Trace/load/guard andofflinefixes; no currentintegratedlatency/heat/endurance24h acceptance |
| F45 | SITL vòng kín, tải/gió và lỗi vật lý | 2 | Isolatedphysics/SITL runnable experiments; no calibratedHera/persistent1x completeUI product |
| F46 | 3D/âm thanh/weather bám trạng thái | 2 | LicensedPBR/groundpose/stale/audio components; airborneperformance/weather/acoustics unqualified |
| F47 | Kịch bản huấn luyện, instructor và chấm điểm | 1 | Scenario/corpus/viewer foundation; no instructorcourse/scoring product |
| F48 | Cockpit cao cấp: cảm ứng + joystick + nút | 2 | HistoricalglassAndroidUI verifiedsubset; allstates/daynight/HID/gloves/humanUX currenttarget unqualified |
