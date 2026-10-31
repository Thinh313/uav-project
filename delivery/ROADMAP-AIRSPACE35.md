# Roadmap triển khai sản phẩm AERIS — bổ sung35

14/10/2026. Người dùng đã cho phép triển khai từng bước đề xuấtGCS34. Không sửa roadmap/SOT canonical đang đóng băng.47/47 yêu cầu được ánh xạ; số này là độ phủ kế hoạch, không phải47 tính năng hoàn tất.

1. **AIRSPACE35** — Host contracts/corpus and isolated native mock.
2. **AP-FLIGHTOPS** — Scoped AP fence/modes/failsafe SITL, same identities/datum.
3. **ANDROID-RUNTIME** — Actual ART/lifecycle/input/video; real28GiB admission.
4. **HERA-BENCH-HIL** — SDK/protocol, authenticated transport and target configuration.
5. **FIELD-SURVEY** — Usable captured media, geodesy/quality and delivery.
6. **AI-ASSIST-AUTONOMY** — Independent perception metrics, bounded proposals and fallback.
7. **PERFORMANCE-AB** — Endurance/pacing/resource gates and named Ragas/DJI comparison.
8. **FLEET** — Roles/handover/deconfliction with multi-aircraft tests.

Không đóng gate chưa chạy: nguồn vùng trời/giấy phép, AP fence SITL, Android/Hera thật, video/media thật, AI tự chủ, endurance24h và đối chứngRagas/DJI vẫn riêng biệt. Android28GiB chưa đạt; không tải image/emulator. Sàn20GiB áp mọi build. Cài development APK không đồng nghĩa đủ khả năng thay Ragas trong bay thật.

| ID | Yêu cầu | Ưu tiên | Bước tiếp | Scope hiện tại |
|---|---|---|---|---|
| F01 | Hiển thị mode thực, mode yêu cầu và bên giữ quyền | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F02 | Điều khiển bằng joystick, hiệu chỉnh và tiếp quản | P0 | ANDROID-RUNTIME | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F03 | Arm, takeoff, AUTO, Hold, RTL, landing theo capability | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F04 | Pause/continue/resume sau gián đoạn và đổi pin | P0 | AP-FLIGHTOPS | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F05 | Dual-operator: tách quyền flight và payload | P1 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F06 | Vùng cấm/hạn chế4D: polygon, thời gian, altitude datum | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F07 | Đối chiếu tuyến, đường về và nơi đáp với vùng trời | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F08 | Geofence: edit/upload/readback/breach trên autopilot | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F09 | Dữ liệu vùng trời offline: phủ vùng, thời hạn và UNKNOWN | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F10 | GNSS/EKF/link/battery/failsafe alerts theo mức ưu tiên | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F11 | Dự phòng năng lượng, gió/tải và điểm đáp thay thế | P0 | AP-FLIGHTOPS | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F12 | Polygon/grid, camera/GSD/overlap/speed có đơn vị | P0 | ANDROID-RUNTIME | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F13 | Home/AMSL/AGL/terrain/geoid: nhìn thấy và đối chiếu | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F14 | Corridor, structure, orbit/POI, slope/oblique patterns | P1 | ANDROID-RUNTIME | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F15 | RTK/NTRIP/PPK: correction age, fix và độ chính xác | P0 | ANDROID-RUNTIME | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F16 | Map/terrain offline có kiểm vùng phủ và dung lượng | P0 | ANDROID-RUNTIME | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F17 | Lập kế hoạch nhiều sortie, đổi pin và refly phần thiếu | P1 | ANDROID-RUNTIME | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F18 | Discovery/route/identity cho nhiều camera/gimbal | P0 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F19 | EO/thermal live: decode, frame age, switch, freeze alert | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F20 | Điều khiển camera/gimbal theo capability và mục tiêu | P0 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F21 | Capture ảnh/video thực: source/time/GNSS/index/hash | P0 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F22 | Đồng bộ nhiều stream, EO/IR và bản đồ/FOV overlay | P1 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F23 | Thermal radiometry/LRF/geolocation với sai số | P1 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F24 | AI hỗ trợ lập plan với proposal/diff/validation | P1 | AI-ASSIST-AUTONOMY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F25 | Nhận diện đối tượng/khuyết tật từ EO/IR | P1 | AI-ASSIST-AUTONOMY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F26 | Bám đối tượng/gimbal, reacquire và mất target | P1 | AI-ASSIST-AUTONOMY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F27 | Tránh vật cản và replanning có giới hạn | P1 | AI-ASSIST-AUTONOMY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F28 | AI kiểm blur/coverage/GSD và đề nghị refly | P1 | AI-ASSIST-AUTONOMY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F29 | GPS-denied/VIO và night autonomy | P2 | AI-ASSIST-AUTONOMY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F30 | Thông báo giới hạn AI, confidence, evidence age và fallback | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F31 | Flight journal/review: quan sát khác ACK và ảnh thật | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F32 | Dataset lớn, handoff/resume/checkpoint/integrity | P0 | FIELD-SURVEY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F33 | Replay/timeline liên kết lệnh, video, event, mission | P1 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F34 | Nhập/xuất QGC/GIS có scope và dữ liệu giữ nguyên | P0 | FIELD-SURVEY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F35 | Storage preview/quota/retention bảo vệ bằng chứng | P0 | FIELD-SURVEY | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F36 | Fleet/mission scheduling và quyền theo vai trò | P2 | FLEET | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F37 | Remote cockpit/handover có xác nhận ownership | P2 | FLEET | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F38 | Chia sẻ video/annotations/GIS có quyền truy cập | P1 | FLEET | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F39 | Nhiều máy bay: deconfliction không suy từ multi-payload | P2 | FLEET | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F40 | Native lifecycle/private persistence sau restart/reboot | P0 | AIRSPACE35 | CONTRACT_OR_MOCK_PARTIAL |
| F41 | Transport signing/auth/replay protection/failover | P0 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F42 | Signed update/schema migration/recovery | P0 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F43 | Aircraft/payload configuration, calibration và diagnostics | P1 | HERA-BENCH-HIL | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F44 | Latency/jitter/overload/heat/power/long-run budgets | P0 | PERFORMANCE-AB | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F45 | SITL đóng vòng physics, tải/gió và lỗi | P0 | PERFORMANCE-AB | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F46 | Đồ họa/âm thanh bám trạng thái và nguồn dữ liệu | P1 | PERFORMANCE-AB | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
| F47 | Operator training/scenario score/Ragas-DJI A/B | P1 | PERFORMANCE-AB | ROADMAP_ONLY_REUSE_PRIOR_EVIDENCE |
