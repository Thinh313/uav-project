# Roadmap supplement36 — F08/F10/F11

14/10/2026. Giữ nguyên roadmap/SOT/source/candidate canonical đang đóng băng. GCS34/AIRSPACE35 là full-product reference; supplement này chỉ cập nhật gate chuẩn bị cho3feature.

| Feature | Mốc35 | Mốc36 | Gate tiếp |
|---|---|---|---|
| F08 geofence | abstract single inclusion peer | polygon/circle+exclusions, uncertainty/erosion, QGC subset, bounded transaction/readback/correlation | protected bytes restoration→actual pinned AP wire/SITL/enforcement |
| F10 preflight/failsafe | healthy bool/alert contract |8independent sources, versioned expectedHome/fence/config/limits, alert episodes, modeled vs observed actions | real readonly parameter/telemetry mappings+SITL→Hera bench/HIL/operator |
| F11 return reserve | energy UNKNOWN | synthetic mass/wind/power/time/Wh/reserve/domain + Home/alternative routes | calibrated Hera power/battery/payload/wind + terrain/airspace/landing proof |

Các phần này không đã tích hợp Fly/native và không bằng actual device/flight acceptance. Mock operationalAllowed=false. Production gate vẫn cần actual Android, control/input/video/payload, integrity/endurance/pacing, field media và named Ragas/DJI comparison. Không đưa AI autonomy/fleet lên trước core control/safety.

Resource increase không tự cấp quyền build/run: user đã chỉ định không APK/SITL/emulator trong lượt36.41preexisting missing paths có same-SHA candidates; historical integrity gate chưa đóng, không thay missing evidence bằng lần test mới. ENDURE27failed unchanged.
