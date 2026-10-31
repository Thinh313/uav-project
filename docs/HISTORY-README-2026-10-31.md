# RtR AERIS · Independent drone GCS

**Current assessment · 26/10/2026:** engineering alpha with verified Android–SITL
workflows; the integrated beta and complete simulation milestone remain **NOT READY**.
Read [current product status](docs/PROJECT-STATUS-2026-10-26.md) and the
[repository guide](docs/REPOSITORY-GUIDE.md) before using the historical launch
instructions below. `npm start` opens the original web workbench, not the latest
qualified Android simulator. Simulator results do not qualify a physical Hera.

The exact SIM-STABILITY03 source corrections are retained as an isolated
[source overlay](snapshots/simstability03/README.md). It is not automatically
selected or merged into the frozen application. Engineering APKs, large archives,
runtime caches and raw evidence remain host-local under the repository policy.

## Historical workbench and milestone notes

12/10/2026 · v0.9 / QGC03. RtR phát triển GCS độc lập trên kiến trúc mới, đối chứng A/B với RAGAS, hướng tới cạnh tranh DJI theo workflow. **Không dùng mã nguồn ứng dụng RAGAS.** AI hỗ trợ phát triển qua contract, compiler xác định và bằng chứng kiểm thử. Khảo sát/lập nhiệm vụ là workflow đầu tiên trong sản phẩm điều khiển/vận hành bay đầy đủ. Hera là sản phẩm phục vụ, HeraHub là đích cài; trắng/đen chủ đạo, vàng nhấn ít, độ sáng non-blocking.

## Native diagnostic / HERA03

Đã build APK riêng `native/diagnostic/dist/aeris-diagnostic-dev.apk`; mở `/native.html` để tải/kiểm hash và tiếp nhận JSON. APK native chỉ đọc Android Build/Window/InputDevice/MediaCodecList, opt-in input/lifecycle, xuất SAF local; zero permissions, không mạng/radio/flight bindings. Xem [native contract](docs/HERA03-NATIVE-CONTRACT.md) và [device runbook](docs/HERA03-DEVICE-RUNBOOK.md).

`npm run build:native` dùng SDK/JDK sẵn có (không tải/install). Khóa development signing nằm riêng `.local`, không phục vụ hoặc đưa vào source manifest. Host model/compile/signature/browser đã kiểm; **chưa cài/chạy trên HeraHub** vì owner xác nhận chưa có SDK/thiết bị. Import report chỉ là dữ liệu tự báo cáo, không attestation/SOT promotion/flight authority.

## Chạy và sử dụng

Node22+, không cần npm install. `npm start` mở planner tại http://127.0.0.1:8788/ với API bay tắt mặc định. Để dùng simulator:

```sh
cd "/Users/os/Downloads/AI technique/aeris"
python3 tools/check_runtime.py
./tools/start_sitl.sh
npm run start:sitl
```

Nếu container `aeris-sitl` đã chạy, không gọi start script lần nữa. Trang mặc định hợp nhất **Plan → Fly → Review**. Plan có polygon WGS84, camera mẫu/overlap/hướng/độ cao/tốc độ, vector OSM thật, profile Copernicus DSM, thư viện và gói nguồn ngoại tuyến. Fly: kết nối → chờ9preflight đạt → quay Plan nạp/đọc lại đầy đủ → GUIDED → ARM SITL → AUTO. Nhiệm vụ tự RTL/hạ cánh; HOLD dùng LOITER. Review xuất nguồn, yêu cầu và MAVLink journal.

Nạp chỉ khi disarmed; ACK không chứng minh readback hay thực thi. Sau mất liên lạc/kết nối lại, phải đối chiếu mission trước AUTO. Nút đọc lại chỉ download; không tự gửi lệnh bay hoặc khôi phục lịch sử chạy từ local storage. Bản nháp và onboard tách riêng. Cài gói ngoại tuyến, chờ cache shell xong rồi thử mất mạng: vẫn lập kế hoạch được, không có telemetry mới để điều khiển bay.

`/sitl.html` là engineering lab; `/legacy.html` giữ workbench SURVEY01 synthetic để hồi quy. GCS này **chưa là APK HeraHub hoặc bản dùng trên máy bay thật**. Hai policy hiện tại là simulator cố định Home và ánh xạ chênh cao DSM vào Home ảo; simulator vẫn có mặt đất phẳng. DSM EGM2008 30m gồm cây/công trình, không chứng minh AGL hoặc tránh vật cản. Camera mẫu chưa hiệu chuẩn. Chưa có native SDK/input/video/RTK, geoid/launch reference vận hành, QGC tái sinh ComplexItem/open-save parity hoặc HIL.

Simulator: official ArduCopter4.7.1, Docker Linuxx86_64 trên MacARM, image Ubuntu digest cố định, speedup5. Cổng5760 và8788 chỉ loopback. Để dừng: `docker stop aeris-sitl`. Không endpoint tùy ý, force-arm, parameter-write hay RC override. `runtime/sitl` giữ binary/params; không triển khai params mô phỏng lên máy bay.

## SOT, dữ liệu và bằng chứng

[SOT](sot/README.md), [view58facts](sot/exports/project-sot.html), [Blueprint/ADR009](docs/BLUEPRINT.md), [SURVEY02contract](docs/SURVEY02-CONTRACT.md), [roadmap](docs/ROADMAP.md), [native intake](docs/HERAHUB-NATIVE-INTAKE.md), [A/Bprotocol](docs/AB-EVALUATION.md), [Completion](delivery/COMPLETION-QGC01.md).

BOM original `/Users/os/Downloads/0.BOM26.xlsx` giữ nguyên; mirror/hash trong SOT. Không cộng các variant/master hoặc suy cấu hình as-built từ BOM. Public research ở `research/*`; dữ liệu nguồn địa lý ở `geodata/sources.json`. Manifest/pins khóa asset offline theo SHA256; nguồn/datum/giấy phép đi cùng export. Không cào public raster tiles; UI tự vẽ vector extract.

```sh
npm test
npm run check
node tools/survey02_qa.mjs
node tools/survey02_fault_qa.mjs
AERIS_EVIDENCE_DIR=evidence/survey02 .venv/bin/python -B tools/verify_evidence.py
AERIS_EVIDENCE_DIR=evidence/survey02 .venv/bin/python -B tools/record_checks.py
```

Browser QA dùng bundled Playwright; cần simulator/adapter bật và không có phiên khác thao tác đồng thời. Fault QA dùng proxy loopback5761 và **restart container simulator riêng khi disarmed**, không dùng cho phương tiện thật. Hồi quy SURVEY01 chạy `tools/survey_qa.mjs` với `AERIS_QA_URL=http://127.0.0.1:8788/legacy.html`, bundled module và evidence dir riêng. Không ghi đè bằng chứng milestone trước.

`evidence/survey02/ab02-bundle.json` ghi fixture/build/runtime/result A và B NOT_CHECKED. Không có kết luận AERIS vượt RAGAS/DJI. Timings Mac/Docker không phải HeraHub benchmark. Camera DataFlash là trigger mô phỏng, không có ảnh vật lý. Raw logs nén rồi dọn; LOG_DISARMED=0. SOT/Refinery gates kiểm integrity/provenance, không cấp quyền bay hay phát hành thương mại. Kernel phương pháp00–03 không chỉnh.

HERA03: 85unit/API +15host-model assertions,17browser native-intake checks,27GCS layout regressions. `evidence/hera03` giữ build/source/signature/captures/checks. External original `/Users/os/Downloads/0.BOM26.xlsx` hiện không còn ở đường dẫn cũ: canonical mirror/hash/lineage PASS, đối chiếu lại original NOT_CHECKED. Không chọn workbook khác hoặc phục hồi original tự động.

## QGC interchange / QGC01 v0.7

Mở `/qgc.html`: nhập .plan → kiểm Home/tuyến/cao độ/camera và chuẩn hóa → kết nối SITL → explicit review → nạp/readback → GUIDED/ARM/AUTO. Plan chính có nút QGC .plan để xuất nhiệm vụ đã compile cùng lineage simulator. Survey phức hợp dùng cached Items như snapshot đã lưu; nguyên bản/polygon/camera được giữ nguyên. Profile không tự bỏ geofence/rally hoặc chuyển datum/Home. QGC5.1.5 schema pinned; application open/save/regeneration parity NOT_CHECKED. Contract [QGC01](docs/QGC01-CONTRACT.md), evidence `evidence/qgc01`. Chạy `npm run test:qgc`, `node tools/qgc_fault_qa.mjs` trên simulator riêng; browser/source/regression runners dùng evidence dir mới.

QGC02 v0.8: `/qgc.html?milestone=qgc02` now loads seven hash-verified actual QGC desktop exports, compares before/after mission semantics, exports a bound diff, and requires explicit source review after an interrupted armed session. See `docs/QGC02-CONTRACT.md` and `delivery/COMPLETION-QGC02.md`. Desktop open/save tests revealed changes to Home, camera stop flags and regenerated Survey paths; compatibility is bounded, not universal. Four actual in-flight SITL failure trials and DataFlash are retained in `evidence/qgc02/failsafe`. No SDK/controller is needed for these tests; hardware remains unverified.

QGC03 v0.9: `/qgc.html?milestone=qgc03` adds explicit Home/height policies, source-bound camera-stop derivatives and original-source recovery. Main Plan export includes disclosed stop-pair2001 additions. Four actual desktop Save As outputs, two actual flights and30 simulated CAM events retained under `evidence/qgc03`. Camera/route semantics are stable with nullable stop pairs; QGC Home changes remain visible and blocked until review. See `docs/QGC03-CONTRACT.md` and `delivery/COMPLETION-QGC03.md`.

REVIEW04 v1.0: `/review.html?milestone=review04` opens durable per-attempt execution records independent of draft/live session. Source/lineage/readback/identity and conservative outcomes survive disconnect/restart. Hash-validated offline export/import and append-only operator notes have no flight authority. See `docs/REVIEW04-CONTRACT.md`, `delivery/COMPLETION-REVIEW04.md`, `evidence/review04`. Store `runtime/executions` is private and retained; budget errors are visible. `npm run test:review` requires dedicated loopback SITL and writes real simulator attempts. Profile/HeraHub and RAGAS/DJI A/B remain unverified.

PROFILE05 v1.1: explicit read-only configuration in Plan/Fly/QGC/lab, pinned simulator profile v1.0.0, ten-check preflight and 30s freshness at upload/ARM/AUTO. Versioned v2 execution records preserve profile definition/observation/guard snapshots; legacy v1 remains readable. Start `npm run start:sitl`, connect, open Cấu hình and read before upload. `npm run test:profile` runs actual isolated loopback flights; `node tools/profile05_fault_qa.mjs` tests injected observations disarmed. See `docs/PROFILE05-CONTRACT.md`, `delivery/COMPLETION-PROFILE05.md`, `evidence/profile05`. This four-parameter policy is not Hera defaults or whole-configuration/hardware acceptance.

CONTROL06 v1.1.1: shared toolbar/action-row geometry across Plan/Fly, QGC, Review and native intake. `npm test` includes the mandatory seven-viewport control gate; `npm run test:controls` runs it alone on an isolated static server without SITL. Bundled Playwright is reused; another host can set `AERIS_PLAYWRIGHT_MODULE`. Receipts: `evidence/control06`; rules: `docs/UIUX-DESIGN-STANDARD.md`. Offline shell version/hash refreshed. HeraHub physical UX remains untested.

BENCH06 v1.2: `/benchmark.html?milestone=bench06` reviews the source/runtime-frozen mission matrix and actual simulator run bundle. Three completed patterns, one HOLD/RTL interruption and four rejection cases prepare a future black-box A/B trial; RAGAS/operator/native results are NOT_CHECKED. `npm run test:benchmark` runs dedicated loopback flights with disarmed resets; follow with mandatory `node tools/bench06_wire_qa.mjs` and `npm run test:benchmark:browser`. Keep old receipts before rerunning. `npm test` retains the mandatory shared-control geometry gate; use a fresh `AERIS_EVIDENCE_DIR`. Contract/delivery/evidence: BENCH06. No source RAGAS, SDK, physical device, parameter writer or signed/commercial acceptance added.

RECOVERY07: `npm run test:recovery` runs the dedicated loopback loss/reboot matrix (requires normal aeris-sitl and an inactive preview). `npm run test:recovery:browser` checks read-only history/import/export/offline. Existing receipt directories are immutable; use AERIS_EVIDENCE_DIR for a new attempt. Review at `/benchmark.html?milestone=recovery07`, contract [RECOVERY07](docs/RECOVERY07-CONTRACT.md). Reboot here includes -w and erases mission; no retaining-flash or device claim.

JOURNAL08 v1.3.1: npm run test:journal verifies synthetic host SIGKILL/prefix/pending stages; npm run test:journal:sitl measures at least 600 real seconds disarmed plus short nominal flight regression. Stop the inactive preview first so the measurement owns runtime/executions exclusively. No automatic evidence deletion. Restart uses verified original byte prefixes; import-v3 and segment/gap visibility live in review.html. See docs/JOURNAL08-CONTRACT.md and delivery/COMPLETION-JOURNAL08.md.

HANDOFF09 v1.4.0: open `review.html` to link imported/synthetic PNG/JPEG/MP4, WGS84 GeoJSON or UTF-8 reports to a closed execution record. Declare source explicitly. Files have byte checks, append-only association revisions and shared bounded archive storage; they never alter flight outcome or prove capture during a mission. Export/open `.aeris-handoff.json` for a self-contained offline record, original spool, source/derivation/profile, reviews and file bytes. Limits and unverified capture/quality scope: [HANDOFF09 contract](docs/HANDOFF09-CONTRACT.md). Dedicated diagnostics: `npm run test:handoff:browser`, `npm run test:handoff:fault`, `npm run test:handoff:sitl` (requires exclusive archive and dedicated normal loopback simulator).

STREAM10 v1.5.0: `handoff.html` links larger files to exact closed records and imports/exports `.aeris-stream` through native File/network streaming. Separate source (8 GiB) and recipient (12 GiB) stores retain partial/orphan bytes. Limits: 2 GiB/file, 8 GiB/dataset, 512 files; bounded reports/GeoJSON still 8 MiB. Opaque survey-data is preserved without decoding/extraction/quality claims. Receiver commits only after complete manifest/file/global digest and EOF validation, and rechecks bytes on read. Native/HeraHub memory/capture remains unmeasured.

Use `npm start` / `npm run start:sitl` for declared `--max-semi-space-size=1` host GC configuration. CLI: `node --max-semi-space-size=1 tools/stream_handoff.mjs export RECORD_ID output.aeris-stream`; `import FILE RECIPIENT_DIRECTORY`; `verify MANIFEST_SHA RECIPIENT_DIRECTORY`; `reexport MANIFEST_SHA RECIPIENT_DIRECTORY OUTPUT`. CLI receiver directory must not already have a live server/CLI writer. Output paths use no-overwrite writes. JSON HANDOFF09 still opens in the existing review page. Streaming integrity and limits: [STREAM10 contract](docs/STREAM10-CONTRACT.md).

RESUME11 v1.6.0 adds explicit continuation of `.aeris-stream` intake after connection loss or host process restart. In the recipient list, choose **Tiếp tục từ…**, then select the same source package; the UI checks the bounded header and every checkpoint chunk before sending `File.slice(offset)`. Receiver rechecks all retained chunks and the exact cursor before continuation. Checkpointed stages are incomplete evidence, never accepted receipts. Only full semantic/file/body/footer/EOF validation publishes a receipt; accepted wire chunks support identical re-export and individual file streaming without a second dataset copy. Byte corruption disables acceptance/export. Existing v1 JSON/v2 whole imports and receipts remain readable.

CLI: `node --max-semi-space-size=1 tools/stream_handoff.mjs resume FILE RECIPIENT_DIRECTORY [EXACT_STAGE]`. The directory must have no live server/CLI writer; a unique matching-size checkpoint can be selected, but source prefix SHA must match. Ambiguous checkpoints require the exact stage. Failed intake prints durable checkpoint metadata. No automatic resume, flight writes or dataset deletion. [RESUME11 contract](docs/RESUME11-CONTRACT.md), [completion](delivery/COMPLETION-RESUME11.md). Host synthetic evidence does not establish HeraHub/physical power-loss/remote security performance.

LIFECYCLE12 v1.7.0: `/storage.html` quản lý dataset/checkpoint và chính sách có phiên bản. Dataset ACTIVE/SEALED; checkpoint ACTIVE/ABANDONED; hold bảo vệ bản dư liên quan. Chỉ dọn byte có bản giữ lại đã kiểm. Chunk của checkpoint đã bỏ cần gói VERIFIED cùng manifest ở stage khác; checkpoint/nhật ký còn giữ, trạng thái RELEASED_METADATA không mở lại để truyền. File duy nhất, chưa chứng minh, corrupt hoặc giữ hold không được chọn. Không tự dọn khi đầy hoặc sau restart.

Quy trình: chọn kho → lý do đổi vòng đời/hold/policy → **Xem trước dọn dẹp** → kiểm danh sách/bản giữ lại và tải hồ sơ → nhập đúng mã SHA 12 ký tự → xác nhận. Plan cũ bị từ chối khi policy/hold/inventory/byte/keeper thay đổi. Dọn bị ngắt giữ plan/start/progress bền; đọc lại để xác nhận tiếp hoặc dừng. Byte vắng sau restart mà chưa có ACK ghi riêng `ABSENCE_OBSERVED`. Nhật ký JSONL tải trực tiếp, không xóa bằng chính sách này.

Mặc định: 64 MiB quota cho metadata/audit, tuổi bản dư 24 giờ, floor 20 GiB và room cho một gói xuất (kể cả media legacy/header). Các kho cùng filesystem trong tiến trình phối hợp phần nhập còn lại và export leases; min floor/metadata giữ theo chính sách nghiêm nhất. Leases giải phóng khi xong/hủy/lỗi. Đây là điều kiện cấp dung lượng, không preallocation hay đảm bảo trước ứng dụng ngoài/đích nhận khác. Proof scan nội bộ không tạo bản xuất; cleanup vẫn dùng audit reserve khi intake/export bị chặn vì thiếu room. [Contract](docs/LIFECYCLE12-CONTRACT.md), [completion](delivery/COMPLETION-LIFECYCLE12.md). Chạy `npm run test:lifecycle` sau freeze và `npm run test:lifecycle:browser` trên root synthetic riêng.


## ACCEPT13 · explicit recipient acceptance

Open `/acceptance.html` after handoff. Select a freshly verified package and load a recipient expectation JSON from the known source/order. Compare exact manifest, record, source and profile SHA plus duplicate-aware name/hash/byte inventory. Review the source, acknowledge simulation scope, declare reviewer/conditions and type the plan code. Decisions are append-only and optimistic: stale plans/history, missing/corrupt files and physical-survey acceptance are refused. This is unsigned local engineering acceptance, not field/client quality acceptance. Download its separate acceptance audit; the original wire/record remains unchanged.

The wider corpus and actual end-to-end campaign are in `app/fixtures/accept13/suite.json`, `evidence/accept13/campaign.json`; see `docs/ACCEPT13-CONTRACT.md` and `delivery/COMPLETION-ACCEPT13.md`. Six accepted shapes/protocol patterns, four negative compiler cases and an interrupted multi-strip trial are evaluated. Generated reports/GeoJSON show planned simulator areas only, not achieved capture/coverage. SDK/HeraHub are not required for this slice.


## GEO14 · geographic and quality review

Open `/geography.html` for pinned geographical source, conservative DSM envelope and versioned predicted GSD/overlap review. Connect dedicated SITL, read Home/profile, compare, explicitly review scope/source with the plan code, then upload. No automatic ARM/AUTO. Review expiry/source/session or invalid Home blocks command authority; HOLD/RTL remain available. New v2 snapshots bind original geo bundle and travel unchanged in execution/handoff records; legacy v1/QGC remains readable.

Recipient quality reads the exact verified report JSON, compares declared values to engineering targets and exports a separate sealed assessment. Plan adequacy and byte integrity never verify capture/calibration/achieved coverage/accuracy. Field quality and fieldAccepted remain NOT_CHECKED/false. See docs/GEO14-OPERATOR-RUNBOOK.md, docs/GEO14-CONTRACT.md and delivery/COMPLETION-GEO14.md. No SDK/controller is needed for this bounded slice.


PACK15 v1.10.0 implements internal host deployment profiles, explicit separate data roots, bounded deterministic software packages, independent expected-digest/Ed25519 engineering trust, immutable staging/slot verification and conservative storage scenario estimates. Contract docs/PACK15-CONTRACT.md. No bundled runtime/native APK, observed HeraHub install or official RtR signer identity. Next hardware-free work: secure bootstrap/key ownership/rotation and verified release workflow with independent review; actual platform integration, native/HIL, field quality and commercial A/B remain observed-configuration gates. No external release scheduled.


TRUST16 v1.11.0 implements an independent digest-pinned bootstrap closure, separate engineering root/release/approval roles, consecutive dual-quorum rotation and durable high-water release selection. Interrupted transactions preserve raw events and block start until explicit exact-digest forward reconciliation. The managed launcher verifies current trust/package/slot and records child identity before IPC permits data writers; it holds trust maintenance lock through child lifetime. Contract docs/TRUST16-CONTRACT.md; operator runbook docs/TRUST16-OPERATOR-RUNBOOK.md. Local role separation is not independent human approval or official RtR signing authority. Legacy PACK15 remains a caller-policy engineering tool; managed target service permissions, external anchor delivery, OS/runtime custody, HSM/device secure boot/counters, physical power loss and native/HIL/field gates remain unmeasured. Next hardware-free work: staged deployment/data-schema migration and resource/isolation acceptance with rollback-safe forward recovery; independent security review and observed SDK/HeraHub integration remain separate gates. No external release.


UPDATE17 v1.12.0 adds digest-confirmed staged updates, independent copied data generations and layout schema2 with a typed original-byte catalog. Sealed record and original spool/media/receipt/checkpoint/decision formats remain original. Read-only parent-gated canary precedes release selection; phase journal and confirmed forward reconciliation preserve antirollback and original source. Contract docs/UPDATE17-CONTRACT.md. Existing source/backup evidence is retained, no automatic deletion or migration fallback. Engineering host trust and keys only, not official ownership/native deployment or physical power-loss assurance. Next hardware-free increment: measured runtime/resource budgets and isolation/service lifecycle acceptance for deployment candidates, plus broader real-world data intake/operator A/B when configuration permits. Independent security review and observed SDK/HeraHub/native/HIL/field acceptance remain separate gates.


RESOURCE18 v1.13.1 / selected sequence6 adds managed macOS Seatbelt, fixed V8 heap and parent-sampled RSS/disk/heartbeat budgets, readonly fresh resource observation/mutation admission, immutable begin/end supervision and digest-confirmed dead-runtime recovery. Actual bounded V8/Docker OOM, Docker tmpfs ENOSPC, Seatbelt denials, child/parent SIGKILL, replay/re-export and preserved664-file original/generations are host engineering evidence. Contract docs/RESOURCE18-CONTRACT.md; runbook docs/RESOURCE18-OPERATOR-RUNBOOK.md. Missing-policy UI fallback was found and fixed in separately signed6; original signed5/data/raw failure receipts remain immutable. No auto restart, downgrade, cleanup or unconfined managed fallback. RAM reclaimability estimate and RSS watchdog are not hard process-tree resource allocation guarantees; Docker sh/dd probes are not AERIS Linux/device performance. Next hardware-free increment: measure service latency/concurrency and long-running workloads with explicit admission/backpressure/fairness while preserving evidence, plus bounded operator workflow A/B intake. Official signer/OS-runtime custody, independent security review, Linux/native/SDK/HeraHub/HIL/field/physical-power-loss and operational flight gates remain separate. No external release.


LOAD19 v1.14.0 implements server-owned bounded request admission (observe4/control1/read2/write1/static8), zero queued work and explicit429 retry, handler+response joint slot release, deadlines/socket/header limits, fixed128-sample metrics and offline cache intake in batches of4 assets. Contract docs/LOAD19-CONTRACT.md; operator procedure docs/LOAD19-OPERATOR-RUNBOOK.md. Managed staged acceptance requires a real30-minute read-only mixed corpus/overload soak with explicit client percentiles/denominators/RSS/integrity gates before selected sequence7; raw receipts and completion report determine measured status, this roadmap entry alone is not a PASS claim. Original records/receipts preserved and no auto POST retry/rollback/deletion. Thirty minutes are bounded host evidence, not24h/multi-day/device SLA or field/SDK/HeraHub acceptance. Next hardware-free increment: longer24h endurance and service scheduling/operator acceptance on observed host configurations, then native integration when SDK/device are supplied. No unattended schedule or external publication inferred.


ENDURE20 v1.15.1 / candidate sequence9: progress-bound bulkRead1/bulkWrite1,60s advancement window requiring64KiB,6h absolute cap, ordinary30s and5s headers/keepalive preserved. Actual slow/fault/checkpoint tests and immutable24h read-only protected canary are the current hardware-free gate. Status RUNNING_NOT_FINAL is not acceptance; selection7 remains until complete continuous24h plus original/copy664-file and27-package replay, controller/payload integrity and latency/resource gates. Current contract docs/ENDURE20-CONTRACT.md, runbook docs/ENDURE20-OPERATOR-RUNBOOK.md, functional report delivery/COMPLETION-ENDURE20.md and eventual delivery/COMPLETION-ENDURE20-FINAL.md. SDK/HeraHub/native/HIL/field/multi-day remain separate.

ENDURE20 revision2: signed8/generation01 and first interrupted interval preserved in evidence/endure20-attempt01. Early response to any request carrying body framing disables keepalive (Connection:close), including host/path/auth/canary/overload rejection. This prevents post-response body drips after handler lease is legitimately released. New signed9/generation02 starts a fresh continuous24h; prior interval is not stitched.
