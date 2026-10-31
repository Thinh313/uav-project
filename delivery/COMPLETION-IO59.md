# IO59 — syscall and host wait diagnostic completion

15 October2026. **DONE for scoped measurements; NOT_READY for stable1×/fullG1.** Same agent specified, implemented and verified; original-model replay and separate trace readers provide algorithmic cross-checks, not an independent human review.

## What changed

New isolated `pilot/io59` and `evidence/io59`, derivative preview8812/API8813 and attested simulator control5872/containeraeris-io59. No source/candidate/ENDURE/SOT/trust edit or new signature. No dependencies installed, no whole-project/tmp copy. Earlier PACE58 remains pinned. Small textual derivatives retain exact current physics, firmware4.7.1/AP SHA,1200Hz, speedup1 and500000µs catchup cap. Input authority guards and200ms freshness remain unchanged; input was synthetic neutral, not Hera/human input. No replay byte becomes a real vehicle command.

Each actual WAL `os.write`/`os.fsync` boundary now records monotonic wall/threadCPU, op/kind/frame, byte offset, requested/returned length and errno. MAGIC, emergency binary and snapshot open/write/close/replace tagged separately. No global monkeypatch. WAL CRC/SHA format and fsync-before-every-sensor-send retained. MAGIC positive short writes now completed exactly. Contiguous preallocated650010-row trace fails before an unobserved call if full; no ring/drop/compression. Actual trace was below capacity in both runs. Trace-seal IO, failure JSON and clock/epoch observer IO are outside these measured syscall sites and must not be presented as all process I/O. Snapshot policy stays atomic replace without adding a durability claim.

Absolute10ms wake probes in backend thread and separate host process retain scheduled deadline, actual wake, CPU and missed-deadline count/range. A late wake does not fire a burst of old probes. Managed closure attempts every observer/WAL seal even when one seal fails, retaining FAILED rather than skipping subsequent evidence.

## Verification and limits

35 final-source mock/fault checks PASS (18 syscall cases,6 fsync/snapshot cases,11 UDP/backend cases). Normal/short/zero/EIO/EINTR/ENOSPC, blocking fsync, capacity overflow, UTF8 snapshot, frame gap and signal closure checked.4800 final-source dynamic offset/gust frames exactly match original sensor and auxiliary bytes. An earlier4800-frame q01 check is retained separately and not added to the final-source count. Two actual starts out of the declared maximum2; no POST retry or authority revival. Both observed normal preflight, takeoff,20-second neutral hold, LAND/ground/disarm/end and clean controller/backend/container/wake-process closure.

| Run | Admitted frames | Whole RTF | Min full5s RTF | Receive gap p99/max ms | Cap clips | UI mean Hz |
|---|---:|---:|---:|---:|---:|---:|
| D1 | 96456 | 1.00028115 | 0.946833 | 6.851/45.359 | 4 | 53.27 |
| D2 | 96558 | 1.00028128 | 0.998833 | 6.912/40.700 | 0 | 53.13 |

**193014 admitted frames** exact original sensor+aux replay, one RX/INTENT/SENT each, actual AP receive/parse correlation, **810674 syscall observations**, every WAL byte observed and every INTENT fsync before sensor-send. Both raw5-file hashes and new syscall/wake/stage hashes independently rechecked current. Normal AP shutdown tails remain separate in retained raw/unadmitted evidence; this is conservation of admitted processing frames, not an assertion every shutdown servo packet received a new physics step.

Per-run independent syscall verifier has6 assertions; final verification has18 checks. UI draw traces4433/4432 rows retained at1920×1080, no overflow/errors; mean Hz recalculated from actual draw timestamps. UI was ~53Hz, not a60Hz achievement. Browser review independently reread319.1MiB raw for D2 and displayed CURRENT_BYTES_MATCH_RECORDED_READBACK. That is raw equality, not signature or flight-product certification.

Whole RTF>1 in both bounded runs does not establish stable1×: D1 has4 cap clips discarding2962µs of debt; no physics frame was removed. D2 has0 clips, min full5s0.998833. One-second windows and jitter remain below1. No window tolerance has been invented. Existing500ms cap was observed, never changed; it can discard pacing debt and is disclosed rather than equated with lossless pacing.

## What the trace now establishes

D1 worst backend frame47817:12.517ms wall /0.725ms CPU. RX→compute8.739ms includes only0.047ms measured write;8.692ms is outside that syscall. Thread wake late8.514ms and process wake late11.531ms overlap this frame. Other frames include fsync up to11.746ms and snapshot replace8.966ms.

D2 worst frame93464:33.224ms wall /0.559ms CPU. RX write12.061ms (CPU0.091ms) plus INTENT fsync20.490ms (CPU0.094ms) account for most wall duration. Thread probe was late17.899ms; separate-process wake max10.675ms over the run. This locates actual blocking/preemption intervals at I/O boundaries, but does not prove physical storage hardware is the sole cause. CPU model cost alone cannot explain this tail. D1 also proves waits can occur outside measured syscall sites.

**Exclusive kernel runnable/scheduler wait: UNKNOWN / NOT_CHECKED.** Wall-minus-threadCPU includes blocked IO, GIL, OS preemption and clock-wrapper overhead. Wake lateness is a scheduling/contention proxy, not exclusive kernel runnable time. No privileged kernel scheduler trace or syscall-entry kernel tracing was collected. Small signed negative phase residuals are retained from non-atomic CPU/wall boundary sampling; never clipped or interpreted as negative real wait. Host/guest origins use existing nonce brackets, never naive subtraction.

No-op wrapper calibration20000 calls: 1043.9ns wall/call, 1042.1ns CPU/call on this host. Sequential same-volume1000-frame WAL microchecks: original49.11ms wall/31.56ms CPU, timed57.27ms/39.53ms. These are order-confounded diagnostic overhead samples, not a randomized performance comparison. No observer cost is subtracted from runtime measurements. Source tuning preserves observedQoS33; no host priority/global scheduling changes. Runtime probes add memory/CPU; this is not observer-free timing.

Compared with failed PACE58 runs, these bounded means improve, but **no causal optimization claim**: host load was uncontrolled, and a bounded read-only D1 phase-total analysis ran during D2. Fixed UI/AP/model/source does not make the two runs a matched load A/B. No hardware-calibrated Hera, loaded/gust actual profile, long soak or broad host-load sweep was run here. No byte/platform change, fsync batching/removal, hidden speedup or hidden frame discard was used to obtain the result.

## Requirement coverage / health

REQ1 explicit syscalls PASS; REQ2 wake/offCPU proxies and honest attribution PASS within proxy scope (exact kernel wait NOT_CHECKED); REQ3 mock PASS; REQ4 two bounded coupled SITL captures PASS; REQ5 all-frame oracle/raw/pacing analysis PASS; REQ6 preservation and fingerprints PASS. Coverage6/6 scoped requirements. Python syntax and3 Node syntax checks PASS; no APK/build/signature requested. Stable1× product acceptance **NOT_MET**. Single agent verification; no independent expert signoff.

21,795 earlier protected paths checked before and after:0 SHA mismatch/0missing. These are point-in-time checks, not continuous path-presence or ENDURE acceptance. Free at final verification26.21GiB; no observed20GiB floor breach. New runtime admission24GiB, stop20GiB+768MiB, cumulative new budget1.5GiB. All raw/test/failure receipts retained, including verification-attempt01: verifier incorrectly counted top-level draw object fields rather than `.rows`; corrected in final-verify.py and independently recalculated Hz. No UI/runtime source or run evidence altered for that correction.

## Next engineering gate

Prioritize isolated WAL extent preallocation experiment (logical EOF/CRC/SHA bytes unchanged), separate snapshot I/O tail, then tighter native scheduling observation if needed. Prove exact-byte replay and unchanged per-frame durable publication in mock before a new separately authorized SITL plan. Compare with randomized/matched host loads and fixed observer mode. Do not remove fsync or relax freshness to pass. Measure AP's own5ms minimum sleep/batched pacer separately from host backend; it contributes receive-gap distribution even when mean RTF reaches1. UI phase scheduling toward60Hz is a separate remaining limitation.

No SITL remains active at handoff; preview remains read-only until an explicit newly reserved experiment. Both existing nonce IDs are consumed; rerun helpers intentionally refuse overwrite/retry.
