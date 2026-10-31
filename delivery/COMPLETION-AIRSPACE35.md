# AIRSPACE35 — triển khai Airspace & FlightOps vào hành trình native riêng

14/10/2026. **PARTIAL_CURRENT_HOST_VERIFIED_APK_ANDROID_SITL_PENDING**. Người dùng đã ủy quyền triển khai từng bước đề xuấtGCS34. Một agent tách đặc tả/build/verify; không gọi là audit độc lập. Source/candidate/SOT/trust/ENDURE đóng băng không đổi.

## Đã triển khai

1. **Kế hoạch toàn sản phẩm:**47/47 candidate requirements được gắn đúng ID, ưu tiên, bước triển khai và gate trong `ROADMAP-AIRSPACE35.{md,json}`. Đây là độ phủ kế hoạch;0/47 được tuyên bố nghiệm thu vận hành đầy đủ. Các mốc tương lai còn phụ thuộc actual Android, Hera/SDK, source vùng trời, video/media, perception và đối chứng.
2. **Engine geo-awareness:** source/revision/SHA/origin/captured/validity/coverage; polygon lỗ/lõm/biên; giao cắt segment và corridor analytic; kết hợp vị trí–độ cao–thời gian trên departure/survey/return/landing. Datum ID và Home reference phải đối chiếu; phép chuyển REL_HOME↔AMSL dùng Home synthetic fresh và uncertainty. AGL thiếu terrain, ellipsoid/global và nguồn real chưa xác minh→UNKNOWN. Hash chỉ kiểm toàn vẹn. Restricted mock permission phải đúng source/zone/route/time/altitude; acknowledge không tạo giấy phép. Operational approval luôn false.
3. **Giới hạn xử lý và hiệu suất:** AABB lọc ứng viên rồi clipping đúng; không dùng sampling trong production.1MiB dataset/128zones/2048segments/1millioncandidate edges/1024findings. Hết ngân sách ghi incomplete UNKNOWN và không tạo certificate. Oracle slab200ca và falsification50corridors×201sample chỉ nằm trong test. Host128zones/4segments/30runs: median3,65ms, p954,93ms, max5,75ms. Chưa đo Hera hay workload toàn hệ thống; không suy thắng DJI hay tốc độ bay từ số này.
4. **Geofence mock riêng:** typed SINGLE_INCLUSION upload→exact target readback→observed breach; ACK không chứng minh readback/enforcement. Từ chối holes/union thay vì chuyển nghĩa ngầm. Chưa có AP fence adapter/UI đầy đủ hoặc nghiệm thu SITL thực.
5. **FlightOps mock:** observed/requested/ACK/owner tách riêng; target/session/boot/link, tuổi telemetry, duplicate/late/wrongtarget và timeout. Intent phải commit trước peer; AUTO gắn certificate SHA và snapshot đúng session/mission. Fresh telemetry sau stale không tự khôi phục owner; focus/restart/loss hoặc write-unknown thu hồi gate, không retry. Alert sorted top3+count và acknowledgement audit không resolve lỗi. Video descriptor/age độc lập; AI/input/video vật lý unavailable. Chưa có dual flight/payload operator handover hay live transport trong native35.
6. **Native journey tích hợp:** editor/compiler/journey N33 byte-for-byte, Java journal algorithm giữ nguyên với package riêng. Capsule35 atomically lưu inner33 mission/events + toàn bộ assessment inputs + chained mock ops. Route snapshot phải replay đúng compiler, không chỉ cùng missionSHA; rehash để che xung đột vẫn bị từ chối. Restart giữ prefix/audit/snapshot, thêm interruption và không restore quyền. Review/export nhận lại JSON có semantic replay; không ảnh thực hay execution từ ACK/planned photo count.
7. **UI thực thi trên host:** cùng mission context qua4stage, map fit/zoom/region, tuyến và vùng mock, panel video synthetic, instrument mode/owner/datum/freshness/GNSS và energy UNKNOWN. Critical bar cố định; controls chung52CSSpx, không lệch hàng khi alert đổi.1280×800 và360px được kiểm; không suy CSSpx thành Android48dp hay glove acceptance. Đã xem screenshot thực, sửa map quá nhỏ và context panel giữ scroll sai khi chuyển stage.

## Bằng chứng kiểm

| Nhóm | Kết quả cuối | Artifact |
|---|---:|---|
| Engine/corpus/authority/fence/bounds |85/85 host PASS | `evidence/airspace35/logic9.json` |
| Pinned editor/journey + capsule/fault regression |115/115 PASS | `native-logic1.{json,txt}` |
| Java journal faults/quota/symlink/history |31/31 PASS | `java-tests03.txt`, `build03.json` |
| SIGKILL thực3JVM do test sở hữu |19/19 PASS | `crash1.json`, raw snapshots/receipts |
| Chromium + Java journal đầu-cuối/restart/export/lost reply/UI |29/29 PASS | `browser5.json` và `browser5/` |
| Receipt/source/signature/assets/cleanup gates |23/23 PASS theo scope partial | `verification2.json`, `verification.json` |
| Frozen before/after |8.883paths,0missing/changed | `preservation-before.json`, `preservation-after.json` |

279ca host/regression/fault/browser tính mỗi nhóm một lần, không cộng số lần chạy lại. Đây không là Android/ART, AP fence SITL, power loss hay Hera proof. Chữ ký development03 được kiểm lại trực tiếp apksigner v2/v3/certificate; metadata build không thay kiểm chữ ký.

## REQ/AC coverage của mốc35

| REQ | Scope | Kết quả |
|---|---|---|
| R35-01 |47IDs / staged gates | HOST_PASS |
| R35-02 | bounded analytic geometry / adversarial oracle | HOST_PASS |
| R35-03 |4D source/coverage/datum/Home/permission, conservative UNKNOWN | HOST_PASS_SYNTHETIC_ONLY |
| R35-04 | mission/route/context/source/policy certificate binding / mutation | HOST_PASS_MOCK_ONLY |
| R35-05 | fence mock upload/readback/breach, no implicit conversion | HOST_PASS_MOCK_ONLY |
| R35-06 | authority / mode / ACK / reconnect / wrongtarget / no retry | HOST_PASS_MOCK_ONLY |
| R35-07 | stable alerts / ack≠resolve / independent video age / AI unavailable | HOST_PASS_CONTRACT_ONLY |
| R35-08 | integrated journey and atomic capsule/prefix/restart/export | HOST_PASS_ANDROID_NOT_CHECKED |
| R35-09 | APK03 signature/assets accepted for old revision; current APK missing | PARTIAL_CURRENT_APK_NOT_CHECKED |
| R35-10 | actual AP fence upload/readback/breach SITL | NOT_CHECKED |
| R35-11 | actual Android ART/private persistence/force-stop/reboot | NOT_CHECKED |
| R35-12 | preservation/floor/noinstall/scratch cleanup | PASS_SCOPE_GUARDS |

9/12mốc REQ đã đạt đúng tier host/contract được chỉ định (75% của **mốc35**, không của sản phẩm). R09partial, R10/R11chưa chạy. Không có release acceptance hoặc tuyên bố thay Ragas/vượt DJI.

## APK và gate còn mở

APK development03: `native/flightops35/dist/aeris-native35-development-03.apk`,382.507bytes, SHA256 `b0ab7382dfe343350feb6a231426b25757806cfb6abb32f1012aa36b68faee6a`. Package `vn.rtr.aeris.flightops35`, minAPI26/target33, zeropermissions, dedicated existing native31 development cert. Không software-release signature/candidate selection.

**APK03 là revision trước source hiện tại.** Sau03, source thêm bounded-work/result và wording; build.py thêm đo scratch/budget. Những asset khác nhau: `shell.mjs`, `core/airspace.mjs`; xem drift trong verification. APK04 không khởi động build vì thiếu20GiB+128MiB headroom. Không ký/lách gate hoặc đưa03 như APK mới nhất. Current engine/native UI đã qua host tests; current APK **NOT_CHECKED**.

Disk tại bàn giao khoảng17,74GiB (có dao động; signature verification trước đó đo khoảng19,76GiB, xem timestamp/bytes trong receipts), dưới20GiB. Đã dừng build/runtime mới; chỉ đọc kiểm package/hash và ghi báo cáo nhỏ. Không cài dependency/emulator hay khởi động SITL/soak. Android28GiB admission vẫn giữ nguyên. Các module/bằng chứng mới khoảng48MiB; không suy nguyên nhân toàn bộ biến động dung lượng từ đó. Không xóa dữ liệu khác của người dùng.

ENDURE27 vẫn FAILED `HOST_EXTERNAL_POWER_LOST`; không24h acceptance, không cộng generation01..04 và không restart.8.883protected paths khớp SHA; không sửa app/services/candidate/corpus/trust/canonical SOT/ENDURE. Không khẳng định original paths tồn tại liên tục qua các incident trước.

## Lỗi giữ lại / refinement

- Driver ban đầu lỗi dấu ngoặc; chưa test. Hai assertion đầu cần chỉnh fixture đúng minimum polygon area và dùng explicit async latch; receipts FAIL giữ nguyên.
- Browser1/2 chặn preflight do route metadata Chromium/Node khác chữ số cuối, trong khi compiledRaw giống nhau. `cross-runtime-route-diagnosis.json` giữ raw diff. Chuẩn hóa tọa độ9decimal, timing integer-mm trước ceil và outward interval/mm; không nới compiler hash hoặc đổi physics/speedup/cap500/frame policy. Browser3/4/5 PASS với source hashes riêng.
- Work-budget test ban đầu bị source1MiB gate chặn trước; fixture được giảm32zones để cắn đúng work gate. logic8FAIL/logic9PASS giữ lại.
- Final verifier1 nhận sai tên trường minSdk và thấy thư mục diagnosis trống được async reader tạo lại. Đã sửa parser, rmdir đúng thư mục trống sở hữu và giữ verification1. verification2PASS; không sửa binary/evidence cũ.

## Cleanup / bước tiếp

Đã xóa riêng scratch: `native/flightops35/.build` của3build, `.qa-store-1`..`-5`, `.crash-qa-1`, `.diagnosis-store`. Giữ toàn bộ raw/failure journals trong evidence; không tạo project copy/tmp/distDir/dependency install/Docker artifact.

Thứ tự kế tiếp:

1. Khi đủ20GiB+small-build budget: build current APK, verify exact assets/signature và host regression cần thiết; khi≥28GiB thì actual Android theo runbook. Không hạ gate hoặc dùng APK03 như current.
2. Scoped AP-FLIGHTOPS: kiểm pinned firmware/schema/frame fence, upload→readback→inside/outside/breach/action→loss/reconnect; giữgeo-awareness/authorization riêng. Khi chưa đủ tài nguyên vẫn có thể rà soát contract/corpus bằng đọc; không tự mở SITL mới dưới sàn.
3. Actual Android rồi Hera bench/HIL với input/radio/video/payload source và operator authority thật; energy reserve, terrain/RTK/corridor/offline survey và camera-media quality có metric. Giải quyết open pacing/resource/endurance gates trước release.
4. Field survey/media→review/handoff, AI proposal/perception/quality/tracking với holdout/fallback, rồi A/B trên named Ragas/DJI configuration. Fleet/VIO/night theo phần cứng và scope riêng.

Canonical SOT vẫn đóng băng. Report/fingerprints này là source material cho lần reconcile được phép sau, không tự promote vào registry hoặc firmware/hardware claims.
