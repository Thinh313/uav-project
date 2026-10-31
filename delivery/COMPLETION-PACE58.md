# PACE58 — AERIS57 pacing and full-frame verification

15 October2026. **PARTIAL / NOT_READY_G1_STABLE_1X.** Isolated preview: http://127.0.0.1:8810/. The engineering changes and diagnostic pipeline are implemented, but stable1× acceptance has not been achieved. No candidate selection, software signing, Fly integration, SDK/HeraHub or real aircraft operation. One agent performed specification, implementation and verification; no independent reviewer claim.

## Changes

New code only in `pilot/pace58`, evidence in `evidence/pace58`. Read-only original assets/UI and exact AP/native physics binaries remain in use. Experiments include native blocking UDP receive, reused stdlib JSON encoder, one auxiliary snapshot per step, no downgrade of inherited QoS, and removal of an optimized input's redundant upstream state GET. Input still passes through the canonical adapter's current session/boot, transport, firmware, heartbeat, physics epoch/age, lease, sequence, challenge and focus checks. No input write retry; a late neutral benchmark input tick is not replayed as a burst. Physics admits/journals every1200Hz frame independently.

The final diagnostic replaces nested Python observer lists with bounded contiguous uint64 buffers and compact WAL timing arrays; original WAL append/CRC/SHA/fsync-before-send logic is inherited unchanged. It also records per-frame thread CPU timestamps and passive GC callbacks. Runtime GC is neither disabled nor forced. Requested heartbeat4Hz is observed at a median250.488ms interval; maximum1,688.865ms still shows host delay. Thresholds remain input200ms, physics500ms, control heartbeat1,500ms, nominal speedup1 and negative-debt cap500,000us.

The old scene's FPS buffer stops collecting after its first1,200 draws. PACE58 now measures actual draws over each entire run; no startup FPS is reused as live flight evidence. New observer retained4,232/6,740/2,803 draws for O1/O2/B2 without overflow; around53.7–53.95Hz at1920×1080, p95≈25ms. Sustained60fps is **not accepted**. This observer measures presentation draws, not input-to-photon or1200Hz physics display.

## All five starts, including failures

All request IDs have one reservation and one started-run receipt. There were exactly FIVE actual runtimes and no automatic POST retry. Source versions, changes and prospective budget amendments are retained; the original four-way counterbalanced A/B plan was **not completed**. These are diagnostics, not a causal performance comparison under a controlled external host workload.

|Request|Admitted frames|Whole RTF|Minimum full5s RTF|Receive-gap p99/max, ms|Cap clips|Driver outcome|
|---|---:|---:|---:|---:|---:|---|
|B1|37,535|1.0006811|0.9990|6.924 /21.198|0|Wrong30s preflight deadline; unarmed, no takeoff|
|B3|108,320|0.9305601|0.2632|6.876 /370.549|3,260|Heartbeat freshness rejection; owned circuit abort, no observed LAND|
|O1|91,421|0.9990074|0.9373|6.882 /114.177|20|Stale challenge; subsequent LAND/ground/disarm and close observed, driver gate still FAIL|
|O2|144,000|0.9834086|0.8658|6.881 /113.206|1,133|Heartbeat freshness rejection; bounded frame limit, controller error retained|
|B2 final diagnostic|52,685|0.9123956|0.8432|6.988 /546.550|1,673|Physics freshness rejection during takeoff preparation; owned circuit abort, no observed LAND|

B2 is explicitly baseline receive/serialization plus the new compact recorder/CPU/GC observer and4Hz heartbeat, not an unchanged matched baseline. Only B1 has whole-runRTF≥1, and it never took off. **0/5 passed the complete coupled driver/pacing gate.** No window tolerance was invented or relaxed; the unapproved window/jitter acceptance budget in SIMTRAIN52 remains open. All partial windows and sliding1s distributions remain available in the analysis receipts.

A failed composite takeoff request may already have issued mode/ARM/takeoff commands before its physical observation fails. Its HTTP error or workspace `BACKEND_REJECTED` outcome describes failure of the composite operation; it must not be read as proof that no vehicle command executed. Per-command raw observations and the explicit owner-abort receipt are retained for B2.

## What the trace establishes

The slowest final captured host frame52655 took537.845ms from receive to local sensor send return, while its main thread consumed0.690ms CPU. Compute itself took0.138ms wall /0.132ms CPU; the durable-intent segment18.422ms wall /0.307ms CPU. Most remaining delay falls in the receive-journal/check segment. GC observer recorded **zero runtime collections** in this capture. There is substantial non-CPU waiting; the current evidence does **not** distinguish filesystem blocking, OS scheduling and GIL/other waits per syscall. It does not justify blaming the physics algorithm, disk hardware, GPU or any single host process. The compact observer did not resolve the pacing gate.

The correct next investigation is per-call wall/CPU attribution for `os.write`, `os.fsync`, atomic snapshot publication and receive waits, aligned with host/guest pressure samples. Test bounded preallocation or a lossless binary journal only after that attribution; preserve receive retention, pre-send durability, exact numeric oracle and full frame accounting. AP/backend co-location or a platform change would require a new numeric/platform oracle and ADR. Broad repeatability, loaded/gust profiles, long operation and sustained60fps remain NOT_CHECKED for this increment. No sixth runtime was started.

## Verification and preservation

- **64 scoped mock/offline checks PASS**: latest39 workspace/offline-oracle checks,11 backend UDP/fault/oracle checks,5 UI timing checks,5 canonical fastpath checks and4 compact-recorder checks. Earlier sandbox/ABI/preflight failures are retained. Successful mock backend compares4,800 dynamic offset/gust frames against the original model; this is distinct from actual AP evidence.
- **433,961 actual admitted physics frames** across all five runs: contiguous RX→INTENT→SENT, CRC/SHA chain, exact original sensor and auxiliary bytes, actual AP receive/parse correlation.25 current raw-file SHA checks match the diagnostic readbacks. Raw integrity PASS does not promote a failed flight/driver/controller to acceptance. Unadmitted shutdown tails remain separate.
- **21,328 cumulative protected hashes before/after, zero changes or missing paths.** Frozen source/candidate, ENDURE, canonical SOT/trust and earlier AERIS57 evidence unchanged. Point-in-time equality is not continuous original-path presence or ENDURE acceptance.
- Minimum recorded free space26.207GiB, above20GiB; final evidence about1.6GiB, within4GiB new campaign quota. Measurements are point samples plus inherited runtime admission/stop guards, not proof of continuous disk/power/sleep history.
- All five owned AP containers/backend/controllers ended. Only the isolated preview/API remain added on8810/8811; original services were preserved. No project copies, dependency installation or temporary build directories. No user/evidence files deleted. Each owned runtime retained its Docker image-prune receipt; no volumes or unrelated containers were pruned.

## Acceptance coverage

|AC|Verdict|Evidence / limit|
|---|---|---|
|01 preservation/resource|PASS scoped|`preservation-before.json`, `preservation-after.json`, host/admission/closure samples|
|02 mocks and durable barrier|PASS scoped|Latest QA receipts; injected fsync failure prevents publication; late UI spike and explicit buffer overflow detected|
|03 actual full-frame capture and clean flight closure|PARTIAL|All raw/oracles PASS; four cases lack successful complete driver/flight closure, O2 has controller error|
|04 stable1× / jitter|FAIL|Five retained distributions; no successful full coupled pacing gate|
|05 controlled A/B / UI|PARTIAL|Same scene/viewport/rate, but source refinements and failures prevent matched matrix; actual UI timing measured,60fps not accepted|
|06 handoff|PASS scoped|Source pins, current raw hashes, no active owned aircraft process, retained completion/reporting artifacts|

Authoritative machine receipt: `evidence/pace58/verification-final.json`. Per-run `raw-diagnostic.json` is **raw-integrity-only**, even when its controller or driver failed. The prior `readback.json` receipts and all failures remain in place. No signature, readiness promotion or product/Hera claim is made.

After the five actual captures, presentation-only corrections were checked with5 additional tests and browser review: FPS label uses measured mean rather than inverse median, pending-start text clears after resolution, and review labels explicitly include the final partial bucket (<5s). Thus69 scoped checks are retained in total; the earlier immutable machine receipt counts64 before these label tests. Backend/control/physics source matches the v5 launch pins. These final presentation changes were **not rechecked with another SITL run**; their exact old/current hashes and reversible-only display diff are in `presentation-final.json`. No sixth start was used to hide or replace any failed capture.
