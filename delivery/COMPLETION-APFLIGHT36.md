# APFLIGHT36 — geofence, preflight/failsafe và dự phòng quay về bằng mock/replay

14/10/2026. **Chuẩn bị chức năng: DONE trong scope mock/replay. Gate bảo toàn lịch sử: PARTIAL, còn41file thiếu từ trước lượt này.** Không có nghiệm thu AP wire/SITL/Android/Hera hoặc quyền vận hành bay.

User đã ủy quyền source-only, không APK/SITL/emulator mới, không đổi frozen source/candidate/ENDURE. Một agent thực hiện và kiểm lại; không audit độc lập. Existing Node/stdlib; không dependency install/socket/flight/parameter output, ký release hay candidate selection. Source mới ở `pilot/apflight36`, bằng chứng ở `evidence/apflight36`; không tích hợp Fly/native. Canonical SOT không sửa.

## Kết quả ba phần

**Geofence F08:** polygon/circle, một inclusion và tối đa8exclusions, altitude band theo datum. Từ chối holes/multi-inclusion/unsupported data thay vì chuyển nghĩa. Tối đa256items/64KiB. Typed mock upload intent→item requests→ACK-only→readback đủ mọi item và config đúng SHA. Sai đích/type/token/index/count/config, partial/duplicate/late/timeout/loss/clock/writer/suspension bị chặn; mất phiên cần instance kết nối mới, không retry hoặc restore proof. Input/response/output được clone để mutation trong lúc ghi không đổi intent/item đã ghi.

Point/corridor có uncertainty và projection margin; polygon interval/capsule/erosion analytic. Boundary hoặc thin conflict không đủ để chứng minh breach giữ UNKNOWN, không CLEAR. Tính toán vị trí bên ngoài khác mock AP breach/action observation; không chứng minh enforcement.

Hai file QGC desktop thật được giữ đúng byte/SHA, kiểm trích–xuất fence và bảo toàn các field ngoài fence. PlannedHome không thành observed Home. Altitude/action giữ trong cấu hình chưa mã hóa; không invent field QGC. Đây không là lượt mở/lưu QGC desktop mới hoặc actual MAVLink upload.

**Preflight/failsafe F10:**8nguồn riêng: heartbeat/mode, GNSS, EKF, GCS/RC, battery, Home, readonly config và đầy đủ fence proof. Version/unit/age/identity/clock/profile, expectedHome và expectedFenceSHA được kiểm. Nguồn thiếu/cũ/sai/uncalibrated→UNKNOWN; giá trị nguy cơ đã biết→BLOCKED. Config mismatch chỉ báo, không viết tham số.

GCS receive path không suy AP heartbeat receipt hay RC loss. Model expectations xét config và context giới hạn: disarmed/landed/selected modes, AUTO continuation, independent RC và low/critical battery timers. Configured/predicted/observed synthetic action tách riêng; ACK không execution. Chưa phải behavioral replica của pinned ArduPilot. Default thresholds là synthetic, không áp manufacturer/firmware defaults lên Hera.

Monitor giữ high watermark và source binding, không hạ mốc qua replay hoặc resetsourceID. Alert episode theo lỗi, sorted/top3+count; acknowledgement không xóa fault, clear/reappear tạo episode mới. Observation sai episode/config/time/target hoặc ACK bị từ chối; action khác expectation vẫn ghi đúng action/mismatch. Snapshot mặc định là historical/as-of; query clock cũ/stale/khác epoch trả UNKNOWN và bỏ expected action. Không restore authority.

**Dự phòng quay về F11:** availableWh lower bound, upper mass gồm payload/uncertainty, wind head/cross/gust và ground-speed envelope, horizontal+climb/descent+decision-delay+landing time, hover/speed/aux power và mgh/efficiency, reserve/duration/model domain. Không đổi SOC%/mAh sang usableWh ngầm. Thiếu model/calibration/data/fence/route/environment/landing giữ UNKNOWN. Gió không đủ khả năng, thiếu reserve hoặc duration quá giới hạn→INFEASIBLE_MODEL.

Route start đúng observed position, HOME endpoint/datum/hash và candidate IDs duy nhất; geometry/datum/fence assessed. Home/alternatives có kết quả riêng. Lowest-energy feasible **mock** candidate vẫn cần operator review, không phát RTL/LAND hoặc operational SAFE. Model reference3kg/550W và giả định gió uniform là synthetic; không là Hera BOM/calibrated power/forecast/terrain guarantee.

## Kiểm và artifact

| Nhóm | Kết quả | Evidence |
|---|---:|---|
| Schema/geometry/QGC/transactions/safety/return/fault/mutation/clock |161/161 PASS | `logic8.json` |
| Source-bound replay, gồm2QGC fixture |33/33 PASS | `replay6.json`, `corpus6.json` |
| Rehashed fake READY/readback/energy, hash tamper, forbidden ARM op |5/5 cắn đúng | `replay6.json` bites |
| Invocation khác tính lại toàn replay từ input | Khớp receipt | `verification1.json` |
| Syntax14modules +19metadata/source/budget gates | PASS theo scope | `verification.json` |
| Observed protected state before→after |9.365paths,0delta | `preservation-after.json` |
| Historical expected preservation | FAIL:41missing,0SHA changed | incident + preservation receipts |

**199ca mock/logic/replay/bite** tính mỗi nhóm một lần, không cộng các lần chạy lại. Independent analytical checks: vector-triangle wind envelope100cases, SI W·seconds/3600+mgh/efficiency equality, mass/wind/reserve/delay/uncertainty monotonicity. Full mock chain fence→preflight→failsafe→observed synthetic action→return được kiểm. Ledger writer là mock callback, chưa đo fsync/durability or actual transport.

Host benchmark30runs:8source preflight/failsafe +1candidate4point return, median0,65ms/p950,84ms/max0,87ms. Chỉ thời gian Node synthetic workload; không actual Hera latency/jitter/FPS/power/endurance. Không claim vượt DJI từ số này.

## REQ/AC coverage

| REQ | Scope | Kết quả |
|---|---|---|
| R36-01 | strict version/unit/identity/provenance/UNKNOWN | MOCK_PASS |
| R36-02 | real QGC subset semantic roundtrip/non-fence retention | HOST_FILE_PASS; desktop NOT_CHECKED |
| R36-03 | intent/ACK/readback/correlation/timeout/loss/writer/mutation | MOCK_PASS; actual wire NOT_CHECKED |
| R36-04 | uncertainty fence model vs observed mock breach/action | MOCK_PASS; enforcement NOT_CHECKED |
| R36-05 |8sources/readonly profile/config/Home/fence bindings | MOCK_PASS; real params/sensors NOT_CHECKED |
| R36-06 | alert episodes/sequence/freshness and action separation | MOCK_PASS |
| R36-07 | return energy/time/domain/wind/load/reserve | MOCK_PASS_SYNTHETIC_MODEL |
| R36-08 | separate Home/alternatives with route/environment gate | MOCK_PASS; real terrain/landing NOT_CHECKED |
| R36-09 | deterministic corpus/semantic replay/bites | MOCK_PASS |
| R36-10 | preserve observed state/no new runtime/budget | PARTIAL:historical41missing |

9/10requirements accepted at their **preparation/mock tier**; R10partial due preexisting preservation gap, even though task-time0delta. Not90%product maturity. All3requested feature areas have working preparation code; actual aircraft support remains unaccepted.

## Sự cố / giới hạn giữ nguyên

Initial scan found41missing protected paths before new code: original app/slot fonts,7old signed software packages, some old images/log/trace and an instrumented AP binary. Cause UNKNOWN. `preexisting-preservation-incident.json` giữ exact expected/observed SHA, initial failed gate receipt retained. Không xóa/rebuild/resign/restore hoặc cập nhật baseline để lấp gap.

`restoration-candidate-map.json` đã chỉ ra known same-SHA alternative paths cho41/41 theo inventory đã hash, chỉ đọc; không copy. Đây là cơ sở review cho bước khôi phục riêng. Original path presence liên tục **không được khẳng định**. Gate historical source/release không PASS vì chỉ0delta mới.

ENDURE27 vẫn FAILED vì `HOST_EXTERNAL_POWER_LOST`; không24h acceptance/resume/new interval. Endure/controller/candidate/canonical SOT và các byte đang hiện diện giữ nguyên. SIM32 speedup/cap500ms/frame policies không sửa. Source/candidate/Fly/native chưa tích hợp module này.

Failures retained: first thin-region assertion below supported polygon minimum area, then fixture corrected; interval confidence refined to distinguish uncertain intersection from proven breach. Initial corpus duplicateID was correctly refused; original corpus1/replay1FAIL preserved. No reinterpretation of failed receipts as PASS.

Admission free space khoảng17,78GiB; cuối kiểm khoảng22,77GiB theo receipt, có dao động ngoài namespace. Không vì dung lượng tăng mà mở APK/SITL/emulator trái scope. Module+evidence khoảng4,7MiB tại verification, dưới8MiB. Không whole-project copy/tmp/install/large dataset; không tạo build/runtime scratch, cleanup removed:0.

## Bước kế tiếp

1. Giải quyết41missing bằng đúng originalSHA theo inventory, giữ incident/history; không synthesize/rebuild/resign old evidence. Nghiệm thu integrity gate trước source/release promotion.
2. Scoped AP wire adapter/SITL khi được yêu cầu: actual firmware+config+schema/frame/quantization, mission_type=FENCE separate from flight/rally, complete upload/readback/breach/action; loss/reboot/stale/ambiguity/no side effects. Mock tokens không tồn tại trên wire, unsigned ACK không có remote freshness guarantee. Real retry policy phải được thiết kế/kiểm, không lấy one-shot mock là conformance.
3. Actual telemetry/parameter mapping, battery/mass/payload/power/wind/terrain/landing calibration on target; mock thresholds không thành actual defaults. Current native APK and Android gates theo kế hoạch riêng; user hiện đã chỉ định chưa build/run.
4. Hera bench/HIL và field survey/media/operator/A-B; ENDURE acceptance vẫn riêng. No SDK/HeraHub evidence fabricated.

Primary references and XML/QGC provenance in `pilot/apflight36/REFERENCES.md`, `wire-boundary.json`. Reports/fingerprints là source material cho lần reconcile được phép, không canonical fact promotion.
