# ALLOC60 — WAL extent preallocation

15 October2026. **PARTIAL: functional preallocation verified; performance NOT_ACCEPTED. Stable1× NOT_MET.** No default selection. Single agent specification/build/verify using scoped TIP/Vibecode transfer and ADR071; no independent reviewer claim.

## Implementation

New isolated pilot/alloc60,evidence/alloc60, preview8814/API8815 and attested simulator TCP5873/containeraeris-alloc60. No frozen source/candidate/ENDURE/SOT/trust edit, signature, APK, SDK, install or whole-project copy. All4 reserved ABBA starts consumed; no retries.

Darwin F_PREALLOCATE42/F_ALLOCATEALL4/F_PEOFPOSMODE3 reserves384MiB once on an empty new WAL before MAGIC/header. Local Apple SDK fstore_t32-byte ABI pinned, two fixed ctypes fcntl argtypes and variadic pointer on ARM64. Both preallocated runs return402653184bytes, physical allocation matches, logical EOF/file offset remain0 before first byte. No zero padding/ftruncate/PERSIST flag/fallback. Partial/unsupported/ENOSPC/changed EOF fails closed with receipt/descriptor closure before sensor readiness. Darwin-only; no Android/Hera preallocation claim.

CRC/SHA WAL format, exact original physics, ordered complete writes, per-INTENT fsync before sensor send,1200Hz/speedup1/cap500ms and all freshness/authority guards preserved. Both variants use identical optimized tuning/observer/control;5 control textual equivalence checks PASS after only namespace/port changes. Snapshot I/O unchanged. Runtime trace remains bounded, contiguous and fail-loud, not a ring. APFS retained reservation after close; quota includes full physical extents, not just logical file size. No trim/delete. Startup allocation timing is shown separately in io-analysis and never subtracted from pacing.

## Verification

61 scoped final mock checks PASS:20 allocation/EOF/byte/fault;18 syscall/short/error/blocking;6 fsync/snapshot;6 UDP/crash/reopen;11 UDP physics.4800 dynamic offset/gust frames match original sensor+aux bytes. Whole deterministic WAL bytes identical between variants under injected record clock. SIGKILL before/after fsync and normal UDP publication tested; process-crash readability is not power-loss durability. Each actual frame separately checked for fsync return before send.

325394 admitted frames exact original sensor+aux replay, one RX/INTENT/SENT each and actual AP sensor receive/parse correlation.1366690 syscall observations. All4 syscall verifiers and4 extent verifiers PASS; raw readback5-file and syscall/wake/stage hashes reread current. AP shutdown/unadmitted tails retained separately, not silently counted as model steps.

## All four attempts

| Run | Allocation | Frames | Driver | Whole RTF | Min full5s RTF | Cap clips | UI mean Hz |
|---|---|---:|---|---:|---:|---:|---:|
| R1 | none | 96619 | PASS_BOUNDED_COUPLED_CAPTURE | 0.999131 | 0.982833 | 19 | 53.48 |
| R2 | preallocate | 96884 | PASS_BOUNDED_COUPLED_CAPTURE | 0.923760 | 0.536500 | 8981 | 54.18 |
| R3 | preallocate | 35373 | FAIL | 0.502776 | 0.260333 | 20806 | 54.09 |
| R4 | none | 96518 | PASS_BOUNDED_COUPLED_CAPTURE | 0.884052 | 0.465667 | 8602 | 39.19 |

R1/R2/R4 complete preflight→takeoff→20s synthetic neutral hold→LAND/ground/disarm/end. R3 fails55s preflight readiness, stays unarmed and closes via managed END; raw PASS is not flight PASS. All owned processes/containers close cleanly. No guard/deadline/source changes or retry. Cap clips are disclosed pacing-debt loss under the unchanged AP500ms policy, not dropped physics frames. No new window tolerance invented; no campaign mean reaches1×.

ABBA uses same source/observer/profile/UI1920×1080. No deliberate host-load change or heavy analysis during active runs. Shared-host load/cache/thermal conditions remain uncontrolled; two samples/variant cannot establish statistical causality. R4 also degrades without preallocation (UI39.19Hz). Cgroup clock observations record0 additional CPU-quota throttles in all runs, not proof host scheduling/I/O is absent.

Because R3 ends after35373frames/29.4775model seconds, whole-run quantiles have unequal phases. Common10–25s model interval includes18000 independently checked ground frames/run, including the failure:

| Run | Interval RTF | RX write p99 ms | INTENT fsync p99 ms |
|---|---:|---:|---:|
| R1 | 1.000150 | 0.078459 | 0.156125 |
| R2 | 1.000065 | 0.058583 | 0.149584 |
| R3 | 0.573162 | 0.626250 | 1.181834 |
| R4 | 0.900044 | 0.134334 | 0.283666 |

R1→R2 interval shows smaller RX/fsync p99 but R3 does not reproduce it. Whole-run per-run p99 median ratios preallocated/none: RX2.76×, INTENT write3.16×, fsync3.28×. These descriptive/phase-imbalanced ratios are NOT proof preallocation causes regression. Reliable improvement is unproven; keep experimental. R3/R4 have large AP-side and host-wake tails as well. Wall-minus-threadCPU and wake lateness remain proxies; exclusive kernel runnable wait UNKNOWN.

## UI evidence limitation

R1/R3/R4 full raw draw traces4470/3245/3640 rows retained, no render errors/overflow, meanHz independently recalculated. **R2 DOM string export was cut at200000characters:**4821/4932 rows preserved,111tail rows unavailable. DOM full summary54.18Hz retained, but cannot independently recalculate from a full raw trace. Physics/WAL/AP evidence remains complete. Original truncated export, prefix and incident retained; missing rows not reconstructed or rerun.

Correct future collection:500-row embedded JSON-string chunks. R4 current3640rows reread exactly match its complete original (2 checks). Initial numeric-array chunk transfer rounded tiny ~1ulp values in34rows; retained and corrected with strings. It does not recover R2. No original receipt overwritten. Browser review rereads320.3MiB R2 raw and displays CURRENT_BYTES_MATCH_RECORDED_READBACK; this is equality, not signature/performance/Hera acceptance.

## Coverage / preservation / handoff

Implemented5/5 scoped requirements. REQ1 native extent,REQ2 mock,REQ3 bounded experiment,REQ5 preservation PASS. REQ4 physics/IO analysis PASS, UI raw export PARTIAL, performance acceptance FAIL. Fully verified4/5. Final verifier has39 successful scoped assertions plus explicit deferred111UI rows. Syntax checks PASS. No fullG1/production/ENDURE or power-loss acceptance.

Retained failures: native-smoke01 EFAULT from initial variadic ABI declaration (fixed before gates, native-smoke02 PASS); earlier structural crash harness excluded from61 in favor of real UDP qa-crash02; phase10–30s coverage assertion refused short R3, then disclosed common10–25s; final verifier caught truncated UI instead of reporting PASS; numeric chunk exact-equality assertion caught rounding before string fix. Runtime/raw bytes were not changed for analysis corrections.

22101 prior protected paths checked before/after:0missing/0SHA mismatch; point-in-time only, no continuous-path-presence or ENDURE acceptance claim. Free24.03GiB; minimum2s host point sample24.09GiB; controllers also enforce20GiB+768MiB live stop. Evidence allocated1.952GiB within2.5GiB budget. No auto cleanup or evidence deletion. All4 IDs consumed, preview idle.

Next gate: keep preallocation experimental, establish controlled repeatable host/guest and filesystem attribution, equal model phases and string-chunked UI capture before a fresh bounded test. Separate snapshot/AP-trace I/O tails from WAL. Fresh24GiB admission still required; no automatic extra SITL, no relaxation of fsync/speedup/cap to claim1×.
