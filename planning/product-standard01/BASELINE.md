# AERIS: mốc sản phẩm GCS cao cấp v1

20/10/2026. Đây là overlay kế hoạch mới theo quyết định của chủ dự án. RAGAS không còn là tiêu chí parity hay gate nghiệm thu. Lịch sử, source/candidate/canonical SOT và ENDURE không đổi. Không chạy APK/SITL/emulator hoặc ký trong công việc lập mốc này.

Mục tiêu: một cockpit dùng trên HeraHub cho khảo sát, kiểm tra hạ tầng, cứu hộ và giám sát chuyên dụng; có đường mở rộng theo cấu hình UAV/payload được xác nhận. Không mặc định hỗ trợ mọi UAV chỉ vì cùng MAVLink.

Không có một danh sách ISO được dùng ở đây để chứng nhận “GCS cao cấp”. Bộ yêu cầu dưới đây do dự án tổng hợp: ISO9241-210 tham chiếu quy trình thiết kế lấy người dùng làm trung tâm; ISO/IEC25010 tham chiếu chất lượng; MAVLink là hợp đồng giao thức; ArduPilot là hành vi firmware; QGC là tham khảo workflow; Android là tham khảo thao tác cảm ứng. Chỉ đọc public abstract của ISO, không có audit conformity hoặc chứng nhận. Tiêu chí kỹ thuật chi tiết là đề xuất engineering, không được gán thành ngưỡng ISO/nhà sản xuất.

## Những gì đã có và cách đọc

P1 OPERATOR01 đã có APK thực trên emulator: nhiệm vụ AUTO, camera/gimbal lặp, bàn giao hai vai trong cùng cockpit, mất link→UNKNOWN/RTL, SAF provider/readback và persistence/coldboot;12AC đạt trong scope đó. NATIVE98 cũng có Android–SITL mission/fault/restart chứng cứ riêng. Đây là kết quả được giữ và tái sử dụng đúng source/configuration.

P2 CREW02 có hai tiến trình/operator mTLS riêng và một số ca SITL đã kiểm. INTEGRATION03 hợp nhất thêm QGC, haioperator và observer3D nhưng NOT READY; chưa tái đạt nominal/fault/export/restart cuối trên binary mới. Không chuyển PASS của APK cũ sang APK mới; cũng không xóa khả năng đã chứng minh của APK cũ chỉ vì increment mới fail.

MOCK: dữ liệu/giao thức tổng hợp. HOST: kiểm file/service/thư viện thật trên máy tính. ANDROID: emulator thực. SITL: ArduPilot thật với drone/payload giả lập. BENCH/FIELD: phần cứng/bay thật; hiện chưa có nghiệm thu Hera. Những lớp này không thay thế nhau. “Chưa” trong bảng là chưa qualification phạm vi nêu, không khẳng định tuyệt đối code không tồn tại.

48 dòng là nhóm yêu cầu truy vết, không phải48feature đã xong hoặc tỷ lệ trưởng thành. P0 áp theo profile phát hành; P0_CUSTOMER giữ ưu tiên PhaseOne/dualoperator từ Research Partner; P0_SURVEY áp khi công bố workflow khảo sát; training và fleet có gate riêng. Một thao tác có nút trên UI chưa là capability thực.

## Bảng chức năng chuẩn và hiện trạng

| ID | Nhóm chức năng mục tiêu | Ưu tiên | Nền đã có bằng chứng | Gap trên sản phẩm tích hợp / thiết bị |
|---|---|---|---|---|
| F01 | Mode thực, mode yêu cầu, chủ quyền điều khiển | P0 | ANDROID+SITL: quan sát mode, pending/UNKNOWN và quyền trong P1 | INTEGRATION03 chưa tái nghiệm thu trọn hành trình |
| F02 | Joystick, nút/roller và tiếp quản | P0 | MOCK: contract calibration/mapping MCU; có thao tác cảm ứng Android | Chưa HID/USB/RC vật lý HeraHub; đường RC độc lập chưa xác nhận |
| F03 | Arm, takeoff, AUTO, Hold, RTL, land | P0 | ANDROID+SITL: P1/NATIVE98 có AUTO→ground/disarm | Từng mode/manual transition và toàn bộ final INTEGRATION03 chưa đạt |
| F04 | Pause/continue/resume nhiệm vụ | P0 | FOUNDATION: có snapshot/mission reconciliation và restart không phục hồi quyền | Chưa nghiệm thu final pause/resume/reboot/đổi pin liền mạch |
| F05 | Hai operator độc lập và bàn giao quyền | P0_CUSTOMER | ANDROID+SITL: P1 bàn giao hai vai cùng cockpit; CREW02 có mTLS B riêng/pilot-loss | P2 và INTEGRATION03 chưa đạt toàn bộ consent/partition/final review |
| F06 | Vùng cấm/hạn chế theo vị trí–cao độ–thời gian | P0 | MOCK: engine geo-awareness và đối chiếu nguồn/coverage/validity | Chưa nguồn vùng trời chính thức được xác nhận cho địa bàn vận hành |
| F07 | Kiểm tuyến đi, quay về và nơi đáp với vùng trời | P0 | MOCK: corridor/route/return/landing conflict checks | Chưa xác nhận địa hình/vùng trời và đường thực trên Hera |
| F08 | Geofence upload/readback/breach | P0 | SITL: FLIGHTSAFETY42 đã kiểm fence/prearm trong scope riêng | Chưa full fence editor→native→AP trong final và Hera |
| F09 | Dữ liệu vùng trời offline có thời hạn | P0 | MOCK: nguồn/coverage/validity/UNKNOWN | Chưa bộ dữ liệu offline thực được cấp phép và vận hành |
| F10 | Preflight, GNSS/EKF/link/pin/failsafe alerts | P0 | SITL+ANDROID: adapter4.7.1 đọc đúng kiểu; P1 kiểm preflight và loss | Phiên dài bản mới còn stale/cohort; chưa bộ fault kết hợp trên target |
| F11 | Dự phòng năng lượng/gió/tải và điểm đáp thay thế | P0 | MOCK: mô hình Wh/gió/khối lượng/reserve và alternate | Chưa power curve/battery/load/wind Hera hiệu chuẩn |
| F12 | Polygon/grid, camera/GSD/overlap/tốc độ | P0_SURVEY | HOST+ANDROID: compiler/camera readiness và mission intake có kiểm | Chưa độ phủ/GSD/chất lượng ảnh thật; positive polygon unseen còn thiếu ở slice mới |
| F13 | Home, AMSL/AGL/ellipsoid/geoid/terrain | P0 | HOST+SITL+ANDROID: review Home và một số datum/source gates | Chưa mọi mixed-frame/DEM/no-data trên target và mission cuối |
| F14 | Corridor, structure scan, orbit/POI, oblique | P1 | HOST+ANDROID: corridor có mô hình/nạp; các pattern còn lại chưa qualification | Corridor final chưa bay; structure/orbit/oblique không suy từ demo |
| F15 | RTK/NTRIP/PPK và chất lượng định vị | P0_SURVEY | MOCK: FIX/correction age/base/reference/PPK-readiness | Chưa correction link, raw GNSS/time sync và xử lý PPK thật |
| F16 | Map/terrain offline và kế hoạch trên địa hình 3D | P0 | HOST: mô hình geo/DEM và observer3D riêng | Chưa map/DEM offline-native đầy đủ và 3D terrain mission editor |
| F17 | Nhiều sortie, đổi pin, refly phần thiếu | P1 | PLANNED: có record/plan nền | Chưa planner/resume/refly end-to-end |
| F18 | Discovery và routing nhiều camera/gimbal | P0_CUSTOMER | SITL+ANDROID: ba peer camera/two gimbal tổng hợp, actual MAVLink routes | Chưa qualification toàn bộ final; chưa topology/as-built Hera |
| F19 | EO/IR live, decode/switch và cảnh báo frame cũ | P0 | MOCK/FOUNDATION: contract input/video; màn3D không phải video camera | Chưa live decode/latency/loss/reconnect/thermal video thật trên HeraHub |
| F20 | Camera/gimbal theo capability; Phase One | P0_CUSTOMER | ANDROID+SITL: P1 lệnh camera/gimbal lặp; contract Phase One | Chưa camera/gimbal thật, exact Phase One model/API và thao tác liên tục trên thiết bị |
| F21 | Ảnh/video thực có nguồn, thời gian và GNSS | P0 | SITL: trigger/capture tổng hợp; P1 actualFiles=0 | Chưa exposure/file/media thật và time/GNSS correlation |
| F22 | Đồng bộ nhiều feed, EO/IR và FOV overlay | P1 | PLANNED/FOUNDATION: selectors và route mô phỏng | Chưa synchronization/calibration và live overlay trên target |
| F23 | Thermal radiometry, LRF và định vị mục tiêu | P1 | PLANNED: target-specific integration còn mở | Chưa số đo radiometric/range/extrinsics/uncertainty thực |
| F24 | AI hỗ trợ lập plan và giải thích preflight | P1 | PLANNED: chưa nghiệm thu agent/model vận hành | Chưa baseline/usefulness/unsafe-proposal corpus |
| F25 | Nhận diện đối tượng/khuyết tật EO/IR | P1 | PLANNED: chưa runtime perception được nghiệm thu | Chưa dataset/model/hardware metrics và domain-shift |
| F26 | Bám đối tượng/gimbal và mất target | P1 | PLANNED: chưa closed-loop tracking qualification | Chưa mất/đổi target, reacquire và operator takeover thực |
| F27 | Tránh vật cản và replanning có giới hạn | P1_HARDWARE_CONDITIONAL | SITL_ISOLATED: đã có corpus/campaign cảm biến tránh vật cản | Chưa integrated safety envelope/cảm biến Hera; không phải DAA đầy đủ |
| F28 | Kiểm blur/coverage/GSD và đề nghị refly | P1 | MOCK: model blur/coverage/readiness và review | Chưa xử lý ảnh thật hoặc AI chất lượng đã kiểm |
| F29 | GNSS-denied/VIO và night autonomy | P2 | PLANNED | Chưa VIO/navigation model/sensors/field evidence |
| F30 | Giới hạn AI, confidence, tuổi dữ liệu và fallback | P0_IF_AI_ENABLED | MOCK/FOUNDATION: UNKNOWN/provenance và policy nền | Chưa AI runtime để đánh giá khả năng giải thích/fallback |
| F31 | Journal và review liên kết nhiệm vụ | P0 | ANDROID+SITL: P1 accepted nominal, loss giữ UNKNOWN | INTEGRATION03 chưa final accepted review |
| F32 | Dataset lớn, stream/resume và integrity receiver | P0 | HOST: stream/checkpoint/receiver; ANDROID: P1 SAF2.8MB | Chưa ghép large-data/native/latest-run final thành một flow |
| F33 | Timeline/replay lệnh, event, telemetry và media | P1 | HOST+ANDROID: raw/mission/review và observer có đối chiếu | Chưa synchronized camera-video/media timeline đầy đủ |
| F34 | QGC/KML/GIS nhập xuất giữ ngữ nghĩa | P0 | HOST+ANDROID: SimpleItems/QGC và KML scopes đã kiểm | Chưa mọi ComplexItem/terrain/fence/rally/native GIS workflow |
| F35 | Quota/retention/archive có kiểm soát | P0 | HOST: quota/lifecycle/archive có evidence; native persistence nền | Chưa hết dung lượng/Android SAF/cleanup toàn hành trình target |
| F36 | Fleet, lịch nhiệm vụ, vai trò và bảo trì | P2 | PLANNED: quyền flight/payload chưa tương đương fleetadmin | Chưa fleet inventory/maintenance/scheduler/backend |
| F37 | Remote cockpit và bàn giao có xác nhận | P1 | ANDROID+HOST+SITL_PARTIAL: companion B mTLS riêng | Chưa vận hành mạng xa/loss/latency/handover final |
| F38 | Chia sẻ video/annotations/GIS có quyền | P1 | PLANNED: có data handoff, chưa live collaboration | Chưa video fan-out/annotation sync/access audit |
| F39 | Nhiều máy bay và deconfliction | P2 | PLANNED | Chưa multi-aircraft command isolation/deconfliction |
| F40 | Native lifecycle, persistence và restart | P0 | ANDROID: P1 process/coldboot23files exact; newprofile35files exact | Final INTEGRATION03 journey/private-after chưa xong; chưa HeraHub |
| F41 | Xác thực, signing, chống replay và key lifecycle | P0 | HOST+ANDROID: engineering mTLS B thật; mock KEY74/key lifecycle | Chưa production trust/key custody/radio/MAVLink signing và bảo mật target |
| F42 | Signed update, schema migration/recovery và supply chain | P0_RELEASE | HOST: TRUST16/UPDATE17; ANDROID: development-signedAPK | Chưa production Android update/key ownership/SBOM/license/support qualification |
| F43 | Configuration, calibration và diagnostics | P0_TARGET | SITL: typed firmware profile; MOCK: MCU calibration/mapping | Chưa exactHeraHubMCU dialect/USB/SDK và calibrationbench |
| F44 | Latency/jitter, overload, heat/power và endurance | P0 | HOST+ANDROID+SITL_PARTIAL: stage traces/guards; offline repairs | Chưa long-run integrated/24h; source/profile khác không thànhmatched A/B |
| F45 | SITL vòng kín, tải/gió và lỗi vật lý | P1_TRAINING | ISOLATED_SIM: physics/SITL và fault traces | Chưa Hera calibrated model, sustained1×/đủframe/cap500ms trong fullUI |
| F46 | 3D/âm thanh/weather bám trạng thái | P1_TRAINING | HOST: licensed PBR3D + synthetic opt-in rotor audio; groundpose verified | Chưa airborne30s fullquality final, âm học/mưa/gió Hera hiệu chuẩn |
| F47 | Kịch bản huấn luyện, instructor và chấm điểm | P1_TRAINING | MOCK/FOUNDATION: scenario/corpus và simulator viewer | Chưa course/instructorstation/scoring validated/remote-training flow |
| F48 | Cockpit cao cấp: cảm ứng + joystick + nút | P0 | ANDROID+HOST: glasscockpit, theme/icons/islands và UI snapshots | Chưa operator/glove/day-night/popup/all-state acceptance trên HeraHub |

## Hành vi chất lượng bắt buộc

- Fly luôn thấy máy bay/phiên, nguồn dữ liệu, mode thực, quyền operator, pin/link/GNSS và cảnh báo ưu tiên. Camera/map/3D đổi layout không giấu thông tin critical. Local/manual/assisted/AUTO rõ ràng; RC trực tiếp, GCS input và payload control có ownership khác nhau.
- Geofence là cấu hình/enforcement trên autopilot khi được hỗ trợ. Geo-awareness là nguồn vùng trời và kiểm xung đột. Vẽ vùng đỏ không chứng minh firmware đang chặn bay; acknowledgement không tạo quyền bay. Return/failsafe thực thi bởi firmware và cấu hình đã kiểm.
- Manual có pilot control; assisted gồm Hold/ROI/orbit/gimbal assistance theo capability; AUTO thực thi mission đã duyệt; AI chỉ đề xuất hoặc thực hiện trong envelope đã kiểm. Không có “AI tự bay” chung chung từ chatbox hoặc object-detection.
- Camera ACK không là exposure, file hoặc ảnh thật. Giữ planned/reported/files riêng. Khoảng chụp, shutter/readout, focus/lens calibration và GNSS/time sync quyết định mapping readiness; gắn gimbal hoặc fixed đều cần kiểm cấu hình phù hợp nhiệm vụ.
- Mất link/nguồn/quyền, reboot, background hoặc stale không tạo automatic replay/restore authority. Retry giao thức nếu có phải hữu hạn, phân loại idempotent/unknown-dispatch và được thiết kế/kiểm; không áp blanket retries cho lệnh bay/payload.
- Mỗi release có supported configuration matrix, package/source/firmware/camera pins và bằng chứng riêng. Module mock, host storage/security và engineering APK không đóng production gate. ENDURE hiện chưa có nghiệm thu24h; không cộng các interval lỗi.

## Rubric UI/UX và hiệu suất: mục tiêu engineering

Trắng/đen RtR, vàng nhấn ít; typography tiếng Việt có weight rõ, tabular numerals, đơn vị/datum sát giá trị. Glass dùng backdrop/contrast thích nghi; tránh nhiều lớp blur chồng nhau hoặc icon-only không có accessible label. Không đặt vô số thẻ thông tin mặc định lên video. Một hệ token/grid/spacing/control-size dùng chung cho header/footer/islands/popup/keyboard/insets, theme state và control disabled/pending/error.

Ngưỡng thao tác đề xuất: hitbox ít nhất48dp cho Android; glove mode56–64dp cần người vận hành thử. Icon nhìn thấy có thể nhỏ hơn hitbox. Local touch-to-feedback p95≤100ms trên cấu hình chốt là mục tiêu đề xuất, chưa đo và không gồm ACK/radio/video. Test găng tay, tay trái/phải, sun/night, haptics/audio theo mức ưu tiên, đổi theme và OS scaling. Tên/chức năng icon nhất quán; không lấy đẹp từ screenshot làm nghiệm thu thao tác.

Giữ nguyên gate observer INTEGRATION03 đã chốt: foreground1280×800/fullquality/30s, RAFp95≤33.4ms/p99≤100ms, coverage/visibility/overflow kiểm đủ. RAF không là GPU-present hoặc latency của video. Không nới freshness1500ms, cohort3000ms, speedup1 hoặc physicscap500ms để chạy qua gate. Profile4CPU/2GiB khác profile2CPU/1.5GiB nên không coi là matched A/B.

Usability gate trước field: pilot đại diện thực hiện plan→preflight→Fly→fault→review trên controller; có hoàn thành tác vụ, thời gian, lỗi thao tác, recovery và workload. Ngưỡng/độ lớn mẫu phải chốt trước phép thử; hiện human semantic/usability signoff chưa có. Safety-critical unintended action và split authority là release blocker, không bù bằng điểm thẩm mỹ.

## Roadmap theo milestone sản phẩm

| Mốc | Kết quả người dùng và gate ra | Phụ thuộc |
|---|---|---|
| M1 Integrated Operational Alpha | Một Android cockpit chạy đúng KML/QGC subset→preflight→upload/readback→AUTO→ground/disarm/review; B độc lập điều khiển đúng nhiều payload; partition/pilot-loss; SAF đúng run; restart. Đủ10AC INTEGRATION03, không chỉ module xanh. | Chẩn đoán bootstrap/cohort, resource admission ổn định; giữ mọi bằng chứng cũ. Không tự chạy lại theo tài liệu này. |
| M2 HeraHub Bench Ready | Cài trên controller thật; joystick/nút/USB/MCU mapping, radio/auth, video decode/age/switch, đúng camera/gimbal/PhaseOne model; bench/HIL fault theo cấu hình. | SDK/dialect/model/firmware/thiết bị; protocol unknowns phải được chủ nguồn xác nhận. |
| M3 Field-Validated Survey & Inspection | Bay kiểm soát, mapping/inspection có ảnh thật, đủcoverage/blur/GSD/checkpoint/RTK-PPK như claim; manual/assisted/AUTO/return và loss được nghiệm thu theo cấu hình. | M2 và test plan/điều kiện/người vận hành được phép; không có quyền bay thật từ bản kế hoạch. |
| M4 Commercial Release | HumanUX, signedupdate/migration/recovery, threatmodel/security audit, SBOM/licenses, quota/longrun/thermal, bộ cài chính thức, support/training; không P0/P1 trong scope. | M1–M3; actual endurance không thay bằng elapsed time hoặc mock. |
| M5 Advanced Assistance & Training | AI có benefit baseline/heldout; tracking/obstacle/VIO nếu cần; simulator manual/assisted/AUTO có physics/acoustics hiệu chuẩn, instructor/scoring. Fleet/multi-UAV chỉ khi có nhu cầu và test riêng. | Data/model/sensors và boundedauthority; không lấy3D observer làm simulator hoàn chỉnh. |

Ưu tiên hiện tại: đóng M1 và chuẩn bị intake M2; không tiếp tục sinh module hạ tầng riêng nếu không giải quyết gap của hành trình. Không dùng RAGAS parity hoặc thiếu source RAGAS làm điều kiện dừng. Đối chiếu sản phẩm tham khảo có thể là phép đo phụ, còn gate là hành vi/quality/mission outcome đã công bố.

## Nguồn và provenance

Ma trận JSON chứa acceptance riêng từng dòng và các report bằng chứng. Các trạng thái hiện tại lấy từ báo cáo được giữ lại, không chạy lại kiểm trong tác vụ này. Fingerprint chứng minh byte đã tham chiếu, không tự biến báo cáo thành nghiệm thu thực. Browser-capture giữ tài liệu công khai từ tool; official documentation vẫn là publisher claim. Không promote vào canonical SOT hoặc verified_primary.

- STD-UX: [ISO 9241-210:2019 public abstract](https://www.iso.org/standard/77520.html). Human-centred design lifecycle reference; full normative text not audited.
- STD-QUALITY: [ISO/IEC 25010:2023 public abstract](https://committee.iso.org/standard/78176.html). Product quality model reference; not a universal GCS feature list or certificate.
- STD-SEC: [NIST SP800-218 SSDF1.1 final](https://csrc.nist.gov/pubs/sp/800/218/final). Secure development reference, not AERIS security certification.
- REF-INPUT: [Android accessibility guidance](https://developer.android.com/guide/topics/ui/accessibility/apps). Interaction reference; Android touch target guidance48dp, further glove targets proposed locally.
- PROTO-MISSION: [MAVLink mission protocol](https://mavlink.io/en/services/mission.html). Mission/fence/rally transfer semantics; implementation support must be checked per firmware.
- PROTO-CAMERA: [MAVLink camera v2](https://mavlink.io/en/services/camera.html). Discovery/capabilities/protocol reference; not evidence of PhaseOne support.
- PROTO-GIMBAL: [MAVLink gimbal v2](https://mavlink.io/en/services/gimbal_v2.html). Manager/device and control ownership reference; application role policy must be tested separately.
- REF-FAILSAFE: [ArduPilot GCS failsafe](https://ardupilot.org/copter/docs/gcs-failsafe.html). Firmware behavior reference; do not assume UI buttons execute safety control.
- REF-PLAN: [QGroundControl Plan View master](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/plan_view/plan_view.html). Feature/workflow reference, not conformance standard; freeze exactversion for futuretest.

Không cài dependency, không build, không chạy flight/emulator, không tạo chữ ký hoặc sửa source/candidate/ENDURE. Không có scratch ngoài repo cần dọn.
