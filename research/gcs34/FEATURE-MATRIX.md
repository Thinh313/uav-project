#47 yêu cầu tính năng đề xuất ·14/10/2026

Các ưu tiên và khả năng là đề xuất; scope trạng thái AERIS chỉ từ nguồn dự án, không phải nghiệm thu Hera. Xem RESEARCH-BRIEF.md và aeris-source-status.json.

|ID|Nhóm|Tính năng|Ưu tiên đề xuất|Bằng chứng AERIS hiện tại|Điều kiện còn thiếu|
|---|---|---|---|---|---|
|F01|Điều khiển và quyền thao tác|Hiển thị mode thực, mode yêu cầu và bên giữ quyền|P0|SITL_PARTIAL|Flight firmware, RC path, transport authority|
|F02|Điều khiển và quyền thao tác|Điều khiển bằng joystick, hiệu chỉnh và tiếp quản|P0|MOCK_ONLY|Hera input mapping/SDK, bench and HIL|
|F03|Điều khiển và quyền thao tác|Arm, takeoff, AUTO, Hold, RTL, landing theo capability|P0|SITL_PARTIAL|Observed firmware/mode support and command gates|
|F04|Điều khiển và quyền thao tác|Pause/continue/resume sau gián đoạn và đổi pin|P0|SITL_PARTIAL|Mission progress/readback, explicit operator review|
|F05|Điều khiển và quyền thao tác|Dual-operator: tách quyền flight và payload|P1|MISSING|Identity/auth, ownership transfer and input routing|
|F06|Vùng trời và an toàn|Vùng cấm/hạn chế4D: polygon, thời gian, altitude datum|P0|MISSING|Authorized authoritative data and source/validity version|
|F07|Vùng trời và an toàn|Đối chiếu tuyến, đường về và nơi đáp với vùng trời|P0|MISSING|Geometry engine, uncertainty and actual return strategy|
|F08|Vùng trời và an toàn|Geofence: edit/upload/readback/breach trên autopilot|P0|MISSING|QGC nonempty fence currently rejected; firmware-specific protocol|
|F09|Vùng trời và an toàn|Dữ liệu vùng trời offline: phủ vùng, thời hạn và UNKNOWN|P0|MISSING|Licensed cache/update policy; no fabricated no-zone clearance|
|F10|Vùng trời và an toàn|GNSS/EKF/link/battery/failsafe alerts theo mức ưu tiên|P0|SITL_PARTIAL|Real health/fault telemetry and observed configured action|
|F11|Vùng trời và an toàn|Dự phòng năng lượng, gió/tải và điểm đáp thay thế|P0|MISSING|Calibrated aircraft/battery/payload model and terrain/landing data|
|F12|Nhiệm vụ và khảo sát|Polygon/grid, camera/GSD/overlap/speed có đơn vị|P0|HOST_AND_SITL_PARTIAL|Physical camera/calibration, target mission semantics|
|F13|Nhiệm vụ và khảo sát|Home/AMSL/AGL/terrain/geoid: nhìn thấy và đối chiếu|P0|HOST_AND_SITL_PARTIAL|Actual datum/terrain coverage; flat-world gate not production|
|F14|Nhiệm vụ và khảo sát|Corridor, structure, orbit/POI, slope/oblique patterns|P1|MISSING|Separate mission corpus/firmware/camera acceptance|
|F15|Nhiệm vụ và khảo sát|RTK/NTRIP/PPK: correction age, fix và độ chính xác|P0|MISSING|GNSS/caster transport, physical reference validation|
|F16|Nhiệm vụ và khảo sát|Map/terrain offline có kiểm vùng phủ và dung lượng|P0|HOST_PARTIAL|Target-device runtime and field coverage|
|F17|Nhiệm vụ và khảo sát|Lập kế hoạch nhiều sortie, đổi pin và refly phần thiếu|P1|MISSING|Real acquisition coverage and mission state continuity|
|F18|Payload và video|Discovery/route/identity cho nhiều camera/gimbal|P0|AP_ROUTING_SYNTHETIC_PEERS|Actual payload SDK/firmware/boot identities|
|F19|Payload và video|EO/thermal live: decode, frame age, switch, freeze alert|P0|HOST_SYNTHETIC_VIDEO_ONLY|Real stream descriptor/decoder/native thermal budget|
|F20|Payload và video|Điều khiển camera/gimbal theo capability và mục tiêu|P0|AP_ROUTING_SYNTHETIC_PEERS|Actual capture/settings/attitude responses and owner|
|F21|Payload và video|Capture ảnh/video thực: source/time/GNSS/index/hash|P0|MISSING_PHYSICAL_MEDIA|Actual file acquisition and capture correlation|
|F22|Payload và video|Đồng bộ nhiều stream, EO/IR và bản đồ/FOV overlay|P1|MOCK_PARTIAL|Sensor calibration/time sync/frame-geographic alignment|
|F23|Payload và video|Thermal radiometry/LRF/geolocation với sai số|P1|MISSING|Radiometric/laser API, calibration and uncertainty|
|F24|AI và tự chủ|AI hỗ trợ lập plan với proposal/diff/validation|P1|MISSING_RUNTIME_AI|Model/mission optimizer, deterministic admission and operator review|
|F25|AI và tự chủ|Nhận diện đối tượng/khuyết tật từ EO/IR|P1|MISSING_RUNTIME_AI|Versioned models and labeled application-specific evaluation|
|F26|AI và tự chủ|Bám đối tượng/gimbal, reacquire và mất target|P1|MISSING_RUNTIME_AI|Fresh perception, target identity, payload/control acceptance|
|F27|AI và tự chủ|Tránh vật cản và replanning có giới hạn|P1|MISSING|Proximity/vision sensing, onboard compute, AP interfaces and closed-loop tests|
|F28|AI và tự chủ|AI kiểm blur/coverage/GSD và đề nghị refly|P1|MISSING_RUNTIME_AI|Actual images/geography and independent image-quality oracle|
|F29|AI và tự chủ|GPS-denied/VIO và night autonomy|P2|MISSING|Appropriate navigation sensors/illumination, compute and field acceptance|
|F30|AI và tự chủ|Thông báo giới hạn AI, confidence, evidence age và fallback|P0|MISSING_RUNTIME_AI|Per-model reliability/authority contract; no direct LLM flight output|
|F31|Hồ sơ và vận hành offline|Flight journal/review: quan sát khác ACK và ảnh thật|P0|HOST_AND_SITL_PARTIAL|Native/device power-loss and long-run acceptance|
|F32|Hồ sơ và vận hành offline|Dataset lớn, handoff/resume/checkpoint/integrity|P0|HOST_DATA_TESTED|Native storage, physical media and recipient workflow|
|F33|Hồ sơ và vận hành offline|Replay/timeline liên kết lệnh, video, event, mission|P1|HOST_PARTIAL|Actual stream time synchronization and frame indexes|
|F34|Hồ sơ và vận hành offline|Nhập/xuất QGC/GIS có scope và dữ liệu giữ nguyên|P0|BOUNDED_CORPUS_PARTIAL|Broader pattern/fence/rally semantic corpus|
|F35|Hồ sơ và vận hành offline|Storage preview/quota/retention bảo vệ bằng chứng|P0|HOST_DATA_TESTED|Target filesystem/capacity/permissions/power behavior|
|F36|Đội bay và cộng tác|Fleet/mission scheduling và quyền theo vai trò|P2|MISSING|Fleet service, operator workflow and licensed hardware|
|F37|Đội bay và cộng tác|Remote cockpit/handover có xác nhận ownership|P2|MISSING|Network/auth/control channel and supervised handover|
|F38|Đội bay và cộng tác|Chia sẻ video/annotations/GIS có quyền truy cập|P1|MISSING|Actual media path, access policy and privacy|
|F39|Đội bay và cộng tác|Nhiều máy bay: deconfliction không suy từ multi-payload|P2|MISSING|Multi-aircraft safety architecture, identities and validation|
|F40|Nền tảng, bảo mật và bảo trì|Native lifecycle/private persistence sau restart/reboot|P0|HOST_VERIFIED_ANDROID_NOT_CHECKED|Android runtime gate28GiB and actual target HeraHub build|
|F41|Nền tảng, bảo mật và bảo trì|Transport signing/auth/replay protection/failover|P0|MISSING_PHYSICAL_TRANSPORT_AUTH|Observed radio/firmware/key provisioning; software package signature is separate|
|F42|Nền tảng, bảo mật và bảo trì|Signed update/schema migration/recovery|P0|HOST_ENGINEERING_TESTED|Official key custody, target native and production release|
|F43|Nền tảng, bảo mật và bảo trì|Aircraft/payload configuration, calibration và diagnostics|P1|PROFILE_READONLY_PARTIAL|Actual parameter corpus, hardware and maintenance authority|
|F44|Nền tảng, bảo mật và bảo trì|Latency/jitter/overload/heat/power/long-run budgets|P0|PARTIAL_OPEN_GATES|Default1x and24h not accepted; reference workload/device required|
|F45|Đào tạo và đối chứng|SITL đóng vòng physics, tải/gió và lỗi|P0|REFERENCE_SITL_OBSERVED|Hera physical calibration; existing model provisional|
|F46|Đào tạo và đối chứng|Đồ họa/âm thanh bám trạng thái và nguồn dữ liệu|P1|HOST_SYNTHETIC_PARTIAL|Native hardware performance and real acoustic references|
|F47|Đào tạo và đối chứng|Operator training/scenario score/Ragas-DJI A/B|P1|MISSING_ACCEPTANCE|Matched configurations, protocol/operator sample and no-regression gates|
