# RtR AERIS / Hera · Project source of truth

Đây là điểm vào SOT cho dự án phần mềm điều khiển/vận hành drone độc lập trên HeraHub phục vụ Hera. Owner nguồn nội bộ là chủ việc RtR trong cuộc trò chuyện; Codex là maintainer dẫn xuất. SOT đã tồn tại từ M0, được mở rộng cùng BOM ngày 12/10/2026, không tạo kho thứ hai cạnh tranh.

## Tra cứu trước khi quyết định

| Nhóm | Nơi có thẩm quyền / nơi tra |
|---|---|
| Intent, ưu tiên khảo sát, target controller, branding, độ sáng và authorization | `source_canonical/product_truth.json` → `registry/product_truth.yaml` |
| BOM chủ việc cung cấp | Byte mirror `source_canonical/0.BOM26.xlsx`; original `/Users/os/Downloads/0.BOM26.xlsx` được giữ nguyên |
| Hera integration facts theo biến thể | `source_canonical/hera_context.json` → `registry/hera_context.yaml`: 28 document claims, một tập lỗi nguồn flagged, năm unknowns |
| Toàn bộ cell/formula/cache và BOM row để drill-down | `../hardware/hera/bom/{workbook.json,items.json,summary.json}` — 41 sheet, không cộng các master/variant |
| Spec HeraHub v2 nội bộ và phần cứng còn thiếu | `../hardware/herahub2/profile.json`; source references và hashes; BOM V1.1 không tự thay thế profile v2 |
| Thông tin web | `../research/*/sources.json`, claims và registry; public claim không được copy thành verified device capability |
| Yêu cầu, kiến trúc và phạm vi phần mềm | `../docs/{PRODUCT-REQUIREMENTS.md,BLUEPRINT.md,SURVEY01-CONTRACT.md}`; TIP và Completion tương ứng |
| Bằng chứng thực hiện | `../evidence/survey01` và các milestone trước; tests/browser captures/source hashes |
| Cổng phát hành | `index/verify_log.jsonl`, `index/.publish_token`, `sot.yaml`, `sot.hygiene.yaml`; token hợp lệ không tự cấp quyền bay/publish |

## Luật đọc

`CONFIRMED_INTENT / verified_primary` chỉ xác nhận chủ việc đã chọn/ủy quyền. `BOM_LISTED / claim` nói ô trong tài liệu liệt kê một part, quantity, unit và biến thể; `verified_value=null` vẫn giữ nguyên. `FLAGGED` lưu lỗi hoặc mâu thuẫn để xử lý, không tự chọn bên thắng. `UNKNOWN` không có dữ liệu đủ; `PROPOSED` là lựa chọn làm việc. Mã RtR trong BOM không mặc định là manufacturer part-number; PN/Dwr, internal PN, tên/revision và vendor part không được gộp.

HeraLink V1.1-DDL/DTC, ebox DDL/DTC, payload và HeraHub v2 là các scope riêng. Master (2)/(3) là sheet ẩn và được đọc đủ; Master (2) có cột khác, adapter dò header thay vì đoán. Có block lặp và thay đổi tên/PN; không cộng 6.483 dòng thành số linh kiện trên một máy bay. Các đơn vị pcs/cm/mm/ml không cộng chung. Không có serial/as-built tree hoặc ngày revision tổng được xác nhận.

32 cached error cells trong original được lưu nguyên; 7.617 công thức có cache, có external workbook references. Không recalc/ghi đè workbook để xóa dấu lỗi. Giá trị lỗi không làm đáp án numeric cho phần mềm. BOM tên Cube/Jetson/radio hỗ trợ tìm adapter nhưng chưa chứng minh firmware, transport endpoints, latency hoặc limit bay.

## Thay nguồn và kiểm

1. Chủ việc cung cấp/xác nhận revision thay thế. So hash original và mirror; snapshot mới chỉ được nhận sau review, không tự ghi đè khi drift.
2. Chỉnh canonical facts theo đúng owner; chạy adapter tương ứng và `tools/check_bom.py`, review diff và null/provenance.
3. Dùng baseline `accept` cho nguồn đã review, sau đó chạy full check/bites/gate. Kernel gốc không sửa.
4. Artifact dự án vẫn phải review nội dung; token không chứng minh file xuất tùy ý đúng registry. Không lịch kiểm tự động được tạo khi chủ việc chưa yêu cầu.

Lệnh tại project root: `AERIS_EVIDENCE_DIR=evidence/survey01 .venv/bin/python -B tools/verify_evidence.py`. BOM đọc bằng bundled Python/openpyxl qua `tools/read_bom.py`; chưa phải importer cho BOM tùy ý. Đổi nguồn cần kiểm header/ràng buộc của adapter.

Quyết định owner 2026-10-12: không dùng source RAGAS; RAGAS là đối chứng A/B. `INTENT.INDEPENDENT_BUILD`, `INTENT.AI_NATIVE_DEV`, `INTENT.FLIGHT01` là nguồn intent hiện hành. Unknown source RAGAS lịch sử không chặn triển khai.

SURVEY02 owner authorization is INTENT.SURVEY02; current view has 55 facts. Geographic public sources stay in research/geodata-20261012 and geodata/sources.json, not measured hardware facts. Current contract: docs/SURVEY02-CONTRACT.md; native intake remains NOT_CHECKED.

HERA03 authorization and owner-reported missing SDK/device are INTENT.HERA03 and INTENT.HERA03_INPUTS. Current view has57facts. APK/report model/browser receipts do not verify hardware; imported reports are unattested and not automatically canonicalized.

Trong lần HERA03, external original `/Users/os/Downloads/0.BOM26.xlsx` không tồn tại tại locator cũ. Bản canonical vẫn đúng fingerprint đã khóa; cell lineage được kiểm riêng. Fresh external-original check NOT_CHECKED; không dùng file Downloads khác làm revision thay thế.

QGC01 authorization is INTENT.QGC01; current registry contains58facts. QGC public schema claims remain in Refinery, not verified hardware facts. Current local contract docs/QGC01-CONTRACT.md; QGC application and HeraHub/HIL gates remain NOT_CHECKED.

QGC02 authorization is INTENT.QGC02, including owner-approved QGC-only native UI automation. Current registry contains59facts; user intent is the only new canonical fact. Actual desktop corpus and airborne simulator measurements remain milestone evidence, not verified aircraft/HeraHub capability facts. QGC01's historical NOT_CHECKED app/failsafe gaps are addressed by QGC02 evidence with explicit semantic incompatibilities; physical/HIL and universal roundtrip stay open. Contract docs/QGC02-CONTRACT.md.

Current QGC03 registry:60facts. INTENT.QGC03 is the sole new canonical owner intent;19intent/3proposal/9unknown/28BOM/1flagged. QGC03 camera/Home findings, actual test receipts and primary sourced claims stay outside device facts. Current workflow docs/QGC03-CONTRACT.md; hardware scope remains unknown.

REVIEW04 adds only INTENT.REVIEW04:61facts,20intent/3proposal/9unknown/28BOM/1flagged. Local actual simulator/archive/review receipts remain evidence; no aircraft/HeraHub capability promotion. Current contract docs/REVIEW04-CONTRACT.md.

PROFILE05 adds only INTENT.PROFILE05:62facts,21intent/3proposal/9unknown/28BOM/1flagged. Simulator policy/readback/proxy/browser snapshots remain implementation evidence; no aircraft-default or installed-capability promotion. Current contract docs/PROFILE05-CONTRACT.md.

BENCH06 adds only INTENT.BENCH06, quoting the owner's roadmap continuation request:63facts,22intent/3proposal/9unknown/28BOM/1flagged, digest3d85611e0bf3fa83. Mission/SITL/A/B preparation receipts remain engineering evidence, not installed capability or comparative superiority facts. RAGAS/device SDK, original BOM locator and physical gates remain unchanged. Current local workflow contract docs/BENCH06-CONTRACT.md.

RECOVERY07 adds only INTENT.RECOVERY07 owner authorization. Runtime packet/campaign checks are local evidence, not verified installed Hera/HeraHub facts. Kernel tests retain unknown external original BOM availability.

JOURNAL08 adds only INTENT.JOURNAL08 user authorization. fsync/SIGKILL/replay/SITL receipts are bounded host engineering evidence; no HeraHub installed capability or physical power-loss certification is promoted.

STREAM10 adds only INTENT.STREAM10:67facts,26intent/3proposal/9unknown/28BOM/1flagged, digest3bddc79f8fca8e24. Large-data/stream/recipient receipts are host engineering evidence, not installed-device/capture facts.

RESUME11 adds only INTENT.RESUME11:68facts,27intent/3proposal/9unknown/28BOM/1flagged, digestfabadc82e098919d. User authorization is canonical; immutable wire/checkpoint, TCP/SIGKILL, memory and UI receipts stay in milestone evidence. No SDK/device, physical capture/quality, physical power-loss or remote signed identity promotion. Current contract docs/RESUME11-CONTRACT.md. Canonical BOM remains pinned; external original locator is still NOT_CHECKED.

LIFECYCLE12 adds only INTENT.LIFECYCLE12:69facts,28intent/3proposal/9unknown/28BOM/1flagged, digestdde3aa59756fca96. Policy defaults, fsync/cleanup/reserve/kill/UI results are scoped host engineering evidence in evidence/lifecycle12, not installed HeraHub capability or physical capture/power-loss facts. Source edit reviewed as one added owner intent; retained BOM/variant/unknown facts unchanged. Current contract docs/LIFECYCLE12-CONTRACT.md.


ACCEPT13 current workflow contract: `../docs/ACCEPT13-CONTRACT.md`. Canonical addition is solely `INTENT.ACCEPT13`, the current user authorization; test outcomes live in evidence and do not promote hardware/capture/client-acceptance facts.


GEO14 current contract is `../docs/GEO14-CONTRACT.md`. Canonical addition only INTENT.GEO14; primary external datum definitions remain sourced Refinery claims. Thresholds are engineering policy; geoid/camera/physical quality facts are not promoted.


PACK15 v1.10.0 implements internal host deployment profiles, explicit separate data roots, bounded deterministic software packages, independent expected-digest/Ed25519 engineering trust, immutable staging/slot verification and conservative storage scenario estimates. Contract docs/PACK15-CONTRACT.md. No bundled runtime/native APK, observed HeraHub install or official RtR signer identity. Next hardware-free work: secure bootstrap/key ownership/rotation and verified release workflow with independent review; actual platform integration, native/HIL, field quality and commercial A/B remain observed-configuration gates. No external release scheduled.


TRUST16 v1.11.0 implements an independent digest-pinned bootstrap closure, separate engineering root/release/approval roles, consecutive dual-quorum rotation and durable high-water release selection. Interrupted transactions preserve raw events and block start until explicit exact-digest forward reconciliation. The managed launcher verifies current trust/package/slot and records child identity before IPC permits data writers; it holds trust maintenance lock through child lifetime. Contract docs/TRUST16-CONTRACT.md; operator runbook docs/TRUST16-OPERATOR-RUNBOOK.md. Local role separation is not independent human approval or official RtR signing authority. Legacy PACK15 remains a caller-policy engineering tool; managed target service permissions, external anchor delivery, OS/runtime custody, HSM/device secure boot/counters, physical power loss and native/HIL/field gates remain unmeasured. Next hardware-free work: staged deployment/data-schema migration and resource/isolation acceptance with rollback-safe forward recovery; independent security review and observed SDK/HeraHub integration remain separate gates. No external release.


UPDATE17 v1.12.0 adds digest-confirmed staged updates, independent copied data generations and layout schema2 with a typed original-byte catalog. Sealed record and original spool/media/receipt/checkpoint/decision formats remain original. Read-only parent-gated canary precedes release selection; phase journal and confirmed forward reconciliation preserve antirollback and original source. Contract docs/UPDATE17-CONTRACT.md. Existing source/backup evidence is retained, no automatic deletion or migration fallback. Engineering host trust and keys only, not official ownership/native deployment or physical power-loss assurance. Next hardware-free increment: measured runtime/resource budgets and isolation/service lifecycle acceptance for deployment candidates, plus broader real-world data intake/operator A/B when configuration permits. Independent security review and observed SDK/HeraHub/native/HIL/field acceptance remain separate gates.


RESOURCE18 v1.13.1 / selected sequence6 adds managed macOS Seatbelt, fixed V8 heap and parent-sampled RSS/disk/heartbeat budgets, readonly fresh resource observation/mutation admission, immutable begin/end supervision and digest-confirmed dead-runtime recovery. Actual bounded V8/Docker OOM, Docker tmpfs ENOSPC, Seatbelt denials, child/parent SIGKILL, replay/re-export and preserved664-file original/generations are host engineering evidence. Contract docs/RESOURCE18-CONTRACT.md; runbook docs/RESOURCE18-OPERATOR-RUNBOOK.md. Missing-policy UI fallback was found and fixed in separately signed6; original signed5/data/raw failure receipts remain immutable. No auto restart, downgrade, cleanup or unconfined managed fallback. RAM reclaimability estimate and RSS watchdog are not hard process-tree resource allocation guarantees; Docker sh/dd probes are not AERIS Linux/device performance. Next hardware-free increment: measure service latency/concurrency and long-running workloads with explicit admission/backpressure/fairness while preserving evidence, plus bounded operator workflow A/B intake. Official signer/OS-runtime custody, independent security review, Linux/native/SDK/HeraHub/HIL/field/physical-power-loss and operational flight gates remain separate. No external release.


LOAD19 v1.14.0 implements server-owned bounded request admission (observe4/control1/read2/write1/static8), zero queued work and explicit429 retry, handler+response joint slot release, deadlines/socket/header limits, fixed128-sample metrics and offline cache intake in batches of4 assets. Contract docs/LOAD19-CONTRACT.md; operator procedure docs/LOAD19-OPERATOR-RUNBOOK.md. Managed staged acceptance requires a real30-minute read-only mixed corpus/overload soak with explicit client percentiles/denominators/RSS/integrity gates before selected sequence7; raw receipts and completion report determine measured status, this roadmap entry alone is not a PASS claim. Original records/receipts preserved and no auto POST retry/rollback/deletion. Thirty minutes are bounded host evidence, not24h/multi-day/device SLA or field/SDK/HeraHub acceptance. Next hardware-free increment: longer24h endurance and service scheduling/operator acceptance on observed host configurations, then native integration when SDK/device are supplied. No unattended schedule or external publication inferred.


ENDURE20 v1.15.1 / candidate sequence9: progress-bound bulkRead1/bulkWrite1,60s advancement window requiring64KiB,6h absolute cap, ordinary30s and5s headers/keepalive preserved. Actual slow/fault/checkpoint tests and immutable24h read-only protected canary are the current hardware-free gate. Status RUNNING_NOT_FINAL is not acceptance; selection7 remains until complete continuous24h plus original/copy664-file and27-package replay, controller/payload integrity and latency/resource gates. Current contract docs/ENDURE20-CONTRACT.md, runbook docs/ENDURE20-OPERATOR-RUNBOOK.md, functional report delivery/COMPLETION-ENDURE20.md and eventual delivery/COMPLETION-ENDURE20-FINAL.md. SDK/HeraHub/native/HIL/field/multi-day remain separate.

ENDURE20 revision2: signed8/generation01 and first interrupted interval preserved in evidence/endure20-attempt01. Early response to any request carrying body framing disables keepalive (Connection:close), including host/path/auth/canary/overload rejection. This prevents post-response body drips after handler lease is legitimately released. New signed9/generation02 starts a fresh continuous24h; prior interval is not stitched.
