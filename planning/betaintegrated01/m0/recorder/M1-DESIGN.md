# M0 recorder investigation and concrete M1 design

26/10/2026. Cold analysis only. No AP/Android/Docker runtime, native build,
dependency installation, signing, original-file mutation or compaction occurred.
The source decision below is an engineering proposal, not an implemented recorder
or a product acceptance claim. Machine evidence: `cold-analysis02.json` in
`evidence/betaintegrated01-m0/recorder/`.

## 1. Confirmed failure mechanism

The selected instrumented AP uses `SIM_StageTrace.cpp`, not the older LD_PRELOAD
observer `pilot/sim32-instrument01/aptrace.c`. The actual format is AERISD02:

- File allocation128MiB, header area4096bytes, event size64bytes.
- Capacity exactly `(134217728-4096)/64 = 2,097,088` events.
- `emit()` writes current event and publishes `committed` with release semantics.
  On the next event past capacity it sets failed=1 and exits AP with code94.
- AP03/AP05 retained headers both have committed=capacity and failed=1. Retained
  `container-before-stop.json` reports ExitCode94 for both. AP04 has failed=0 and
  949,359 committed events and was running before managed stop.
- A normal frame has5 JSON stages (10–14) plus3 pacer stages (20,21,24), or10
  events if pacer sleep adds22/23. At1200Hz the fixed capacity lasts about218.45s
  at8events/frame or174.76s at10events/frame. Extra/retry paths are not bounded by
  that nominal estimate.
- Even a nominal300s request needs at least175.79MiB at8events/frame; with10,
  about219.73MiB. Current128MiB cannot qualify the declared300s workload.

The host backend can still close a complete durable WAL prefix after AP dies.
Consequently AP03/AP05 have host `CAPTURE_CLOSED`/one WAL CLOSE but overall
FAILED_INTERRUPTED and `TRACE_FLUSH_FAILED`. Neither a host CLOSE nor an exit0
means full runtime/flight success. Actual AP04 remains a separate accepted short
manual capture; failed runs are never combined or promoted.

## 2. Other blockers before a30minute run

| Blocker | Source evidence | Required change in a new beta revision |
|---|---|---|
| Clock pending history exhaustion | `clock_host.py` stores every request forever, `limit=1024`, sends every333333333ns | Separate bounded pending map and bounded replay/late tombstones; stream completed records. Current code reaches capacity around341s, even after AP trace is fixed |
| Full-session stage list | `simtrain53/backend.py` appends all per-frame rows, then serializes a whole JSON array atclose | Stream fixed-format stage chunks and incremental summary; do not load all rows in RAM or stall closure to format a giant array |
| Full-session metric arrays | `wal_journal.py` appends timing integers to `append_cost` and `flush_cost` each record/barrier | Preserve exact timing in streamed stage records; compute bounded aggregate/quantiles without hundreds of millions of in-memory Python objects |
| Fixed legacy quotas | Projection WAL limit768MiB, recipient total2GiB, AP300s and host90min | A separately versioned beta run policy with measured requested-duration/capacity admission. Never rewrite old manifests/budgets or silently raise them |
| Old stage observer also fixed | `stage_trace.py`:16MiB,88-byte rows,190,603rows (~158.84s at1200Hz) | Retain the field semantics but add verified segmentation; copying this helper unchanged does not solve long-run |
| Closure after AP process exit | Runtime tries `docker exec traceflush` after the recorder has already terminated AP/container | Parent-owned drainer/flush lifecycle independent of AP main process; record both AP and writer outcomes |
| Closed elapsed still advances | `life()` derives elapsed from current `now()-launchMono` after closure | Persist the first terminal timing boundary and reuse it on all later reads; keep closure-in-progress duration separate |
| Harness state mismatch | Media05 force-stops/opens `/phone`, lands, then expects a navigation pixel template from another page state | Observe actual page/focus/target before navigation; use stable native accessibility IDs when exposed; template fallback remains grounded in an actual current screenshot |

No clock limit, quota or current cap is to be patched in place. A new policy must
bind source/configuration/duration/bytes and have an executable admission test.

## 3. Recommended segmented recorder contract

Use a new versioned recording layer in the beta integration seam. Retain the
original equations, frame chronology, speedup1, cap500ms, and sensor publication
barrier. Do not switch off stage recording to make a run pass.

### Host WAL

Each segment is an exclusive regular file with run, epoch, segment ordinal,
starting record sequence, previous-segment SHA/head and encoding version. Records
retain global monotonic sequence and the existing CRC/SHA chain. Do not restart
the frame or clock epoch on rotation. Reserve a complete bounded frame group and
closure/error metadata before admitting the next model step.

Ordering remains: retain RX → compute → append complete INTENT → fsync active
segment → send sensor → retain SENT/unknown outcome. A successful return from
`sendto` is local transmission evidence, not AP parse/execution evidence. If a
crash leaves INTENT without SENT, recovery reports uncertainty and never invents
the missing outcome.

Rotate only at a defined group boundary, pre-create/preallocate the next segment
under an admitted budget, synchronize the old segment before publishing its
exclusive seal receipt, and synchronize the containing directory/manifest record.
The next segment binds the previous head and sequence. No append after segment
seal; no rewriting of old bytes. Session CLOSE is distinct from segment seal.

Keep a small explicit closure/error reserve. EIO, short write, fsync failure,
queue/capacity exhaustion or missing successor cannot produce a successful session
CLOSE. Preserve every valid admitted prefix, attempted-record diagnostic and exact
first failure. Fail closed before sending another unjournaled sensor packet.

### AP stage trace

The observer requires a separately built/pinned artifact. Do not overwrite the
existing f2be... AP binary, source pins or old traces. A proposed double-buffered
or segmented append scheme uses bounded preallocated active/next chunks and a
separate durable drainer. Every event has global sequence/frame/kind/tid/time.
There is no ring overwrite or sampling. If the next chunk cannot be committed
within its declared capacity/deadline, preserve a failed prefix and stop; do not
claim a successful capture or silently skip instrumentation events.

The current load/write/store counter assumes an effective single writer; it is
not a safe general multi-producer reservation algorithm. M1 must either enforce
and test that contract or implement reservation plus ordered committed publication
for multiple writers. An atomic fetch-add alone is not a complete commit protocol.

The drainer writes chunk length/range/hash/chain, synchronizes file and metadata,
then records a durable sealed receipt. It remains alive long enough to drain or
report an incomplete active chunk even if AP exits. The session final verifier
requires contiguous event ranges, matching required AP stages for admitted frames,
no lost records, and truthful AP/drainer/host closures.

### Clock and metrics

Pending correlation IDs are bounded by the maximum outstanding requests and
timeout policy, not session duration. Completed rows stream to chunked raw data;
a bounded tombstone window distinguishes matched duplicates, late/expired and
foreign responses. Expired raw input remains captured/qualified as such, never
accepted as a fresh offset. Keep run/epoch/nonce fencing and offset uncertainty.
Do not extend freshness or reset the flight clock simply to reuse a map.

Stream exact per-frame timing fields into binary records. Summary quantiles can
use bounded histograms/reservoirs if their method/error is disclosed; acceptance
metrics that need an exact maximum must compute the maximum online and/or cold
from complete raw. No dropping the slow tail, frame or cost record.

## 4. Storage and admission

The analyzer measures all three retained runs rather than treating AP04's byte
rate as a universal bound. AP03 has about2173.74 WALbytes/frame versus AP04's
1847.81. For planning at1200Hz, use per-frame bytes, not the slower AP03 wall rate.
Observed averages are not strict upper bounds; the record-format16KiB cap is far
more conservative. M1 must declare field/shape limits and test them before
using an operational per-frame reserve.

`cold-analysis02.json` gives30min/2h/8h/24h scenarios with separate components:
empirical-max-mean WAL, nominal10APevents/frame, stage JSON, and a video aggregate
bitrate assumption of16Mbit/s. It also shows original+backup+handoff,25% contingency
and256MiB reserve. Video rate/copies/contingency are assumptions, not observed
media or measured compression. Other metadata, guest state, encoder buffers and
uncompressed export peaks still need allowance.

With those assumptions the primary24h sum is around448GiB, and three complete
copies plus contingency exceed1.6TiB. Lossless compression has not been measured
here. Long-run admission on this Mac cannot be justified merely because20GiB is
free. Use adequate dedicated storage or a separately qualified lossless format,
with a budget for originals, export and independent verification. No automatic
deletion, compaction or thinning of old evidence.

## 5. Closed timing and harness repairs

Capture `closedMono` and `closedAtUTC` exactly once when owned resources reach a
terminal state. Separate requested end, closure started and resources closed; a
durability failure that leaves closure unconfirmed must not falsely freeze a
successful duration. `life()` clamps active elapsed to the correct stored boundary
after close. Repeated end/read calls are stable; an old callback cannot update a
new generation. Wall-clock steps must not alter monotonic elapsed or extend a
deadline. Store timing in durable review and reconstruct historical views from
the sealed observation, not current `now()`.

UI test failures do not waive owned-runtime cleanup. Before each mutation verify
owned emulator/focus, visible selected page/target, same run/boot and fresh control
state. One uncertain dispatched action is observed/reconciled, never blindly
repeated. A selector mismatch is a no-action condition. The runner records the
failure and follows its predeclared simulator-only abort/closure path promptly;
it must not leave a live simulation until recorder exhaustion. If LAND is part
of that abort protocol, it is one fenced explicit action with observed outcome,
not a hidden retry or assumed landing. Failure to prove ground remains UNKNOWN.

## 6. Required M1 acceptance cases

1. Segment boundary at every record position and frame group; sequence/CRC/head
   continuity exact; no duplicate/lost frame, INTENT barrier before sensor return.
2. Short writes, EIO, fsync file/directory failure, ENOSPC, missing next segment,
   delayed drainer, exhausted queue and failed seal all preserve failed prefixes.
3. Crash before/after INTENT sync, sensor send, SENT, segment seal and session
   CLOSE. Recovery never promotes a prefix or invents an outcome.
4. Wrong run/epoch/segment, duplicate/missing/reordered chunk, tamper and receipt
   mismatch rejected by an independent cold verifier.
5. Multi-producer reserve/commit or a tested enforced single-writer contract;
   no overwrite of unread/uncommitted memory.
6. Clock observer simulated beyond1024 requests, nonce replay/late/expired/foreign,
   monotonic/wall jumps, bounded pending/tombstone state and unchanged age gates.
7. Timing/metrics/stage buffers remain bounded independently of frame count; all
   required exact timing records retained in stream. Closure does not serialize a
   full-session Python list.
8. Freeze elapsed on terminal close, idempotent end/read, late old callbacks and
   partial closure/durability failure. Historical timing survives cold restart.
9. UI current-page/selected-nav/IME/background/failed-template cases: no wrong
   mutation, no blind retry, prompt predeclared simulator abort/managed closure.
10. Small reference capture first, then5/15/30min actual AP+UI after admission and
    source/capacity readiness. Model PWM replay remains exact for unchanged model;
    changed instrumentation gets separate firmware differential/overhead proof.

All actual runtime tests above are NOT_RUN in M0. A mock/metadata/cold sizing PASS
does not close M1, BETA-SIM, physical Hera, acoustic or training-fidelity gates.
