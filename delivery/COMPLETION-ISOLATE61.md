# ISOLATE61 — host/AP/filesystem latency and complete UI chunks

15 October2026. **PARTIAL: diagnostic implementation verified, stable1× NOT_MET.** Two planned actual starts consumed, no hidden retry or additional campaign. Single agent specification/build/verify following Vibecode transfer, scoped TIP and ADR072; no independent review claim.

## Delivered

New isolated pilot/isolate61 and evidence/isolate61, UI8816/API8817, simulatorTCP5874/containeraeris-isolate61. Prior ALLOC60/source/candidate/ENDURE/SOT/trust unchanged. No APK, SDK, dependency install, build, signature, whole-project copy or external publication.

WAL remains on host physical filesystem with full ordered writes, CRC/SHA chain and fsync for EVERY INTENT before sensor send. Preallocation disabled in both runs. Original host physics bytes and AP binary unchanged;1200Hz, speedup1 and500ms cap preserved. All flight freshness/identity/authority guards unchanged; neutral input is synthetic benchmark data, not Hera/human input.

AP trace placement bind mount versus guest tmpfs; same supervisor/observer architecture. New guest observer samples per-thread /proc stat/schedstat every20ms, keeps birth identities, raw counters/states,1s pressure/cgroup/memory context. New host in-memory rusage tracks process CPU/faults/voluntary and involuntary context switches alongside wake probes; existing os.write/fsync/snapshot timings preserved. Host iostat/vm_stat/thermal/power context retained. No global priorities, filesystem policies or background applications changed.

[Linux kernel schedstat documentation](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html) defines per-task runtime/runqueue-wait/timeslice counters. Here positive counters were observed; the sysctl path was unavailable, so that missing setting is retained. Guest counts are sampled windows, not exclusive per-frame waits. Host rusage includes all backend process threads and cannot establish exact host runnable-wait duration. Zero block counters do not prove no filesystem blocking.

[Docker tmpfs documentation](https://docs.docker.com/engine/storage/tmpfs/) states tmpfs is volatile, counts against container memory and may swap. It is used for diagnostics only, not the durable WAL. Immutable AP/probe files are exported and independently SHA-compared before container stop. Docker cp failed in initial mock; current export uses docker exec cat in mount namespace, fsynced exclusive host file, then a separate guest SHA+size pass. No volatile source is torn down on export failure.

## Gates and retained failures

55 mock checks before R1:18 syscall/fault,6 fsync/snapshot,11 UDP/backend (4800frames exact original sensor+aux),8 UI chunk/coverage/precision faults,6 tmpfs and6 bind guest/supervisor/archive checks. Additional6 v2 mock checks before R2 cover a writer intentionally ignoring TERM and bounded KILL/seal/source-SHA. Native mocks are synthetic; they are not AP flight evidence.

Mock evidence retained: initial docker cp failure with original source/container preserved then SHA-recovered; forced observer SIGTERM raced natural exit (valid result but143), fixed by waiting natural exit; a terminal empty task sample caused overly strict harness assertion, replayed against unchanged saved raw data with terminal lifecycle criterion. All failure/recovery receipts remain. No failed receipt was replaced with PASS.

R1 actual fresh-physics guard rejects LAND, then cleanup LAND cannot be confirmed. Driver requests simulator circuit abort, not observed landing. AP remains blocked in sensor wait after TERM; controller retains container rather than deleting trace. During retention observer reaches its8MiB quota and records GUEST_OBSERVER_QUOTA. Explicit forensic recovery validates owned container/PID/AP command, kills only the simulated AP child, waits reaping, flushes trace and verifies all immutable source/copy SHA before container stop. Original driver/closure FAIL, ownedContainerStopped:false and error remain untouched. Forensic raw PASS is NOT flight/controller PASS.

R2 uses new versioned artifacts: runtime-v2.py/ap-server-v2.mjs/guest-entry-v2.sh/guest-observer-v2.py/stop-ap-v2.sh/archive_v2.py. V1 files and original pins remain byte exact. V2 waits1s after TERM then records forced AP-child KILL if needed, only after backend closed; observer budget24MiB within32MiB probe tmpfs. Fixed guest memory384MiB/cpus2 unchanged. Stop-policy-v2.json is retained; KILL is diagnostic writer closure, not LAND evidence. Mock verified TERM-ignoring path before R2. Quota/shutdown differences are disclosed; no clean causal A/B claim from these two versions.

## Actual results

| Run | AP trace | Driver | Admitted frames | Whole RTF | Min full5s RTF | Cap clips | UI mean Hz |
|---|---|---|---:|---:|---:|---:|---:|
| R1 | bind | FAIL | 90470 | 0.969085 | 0.802833 | 354 | 54.53 |
| R2 | tmpfs | PASS_BOUNDED_COUPLED_CAPTURE | 96590 | 0.997277 | 0.952500 | 67 | 54.46 |

R2 completes normal preflight/takeoff20s neutral hold/LAND/ground/disarm/end. Both means remain below1 and subwindows still jitter; cap clipping/pacing-debt loss disclosed under unchanged AP policy, not a dropped physics frame. No new tolerance invented.

**187060 admitted frames** exact original sensor+aux oracle, ordered RX/INTENT/SENT, per-frame pre-send fsync and actual AP receive/parse correlation verified. All source-copy/raw hashes reread. Normal AP/unadmitted shutdown tails remain distinct. R1 raw checked by a separate forensic verifier honoring preserved failed closure/recovery receipt, not by rewriting old acceptance.

**9179 UI draw rows,20 opaque JSON-string chunks** saved before next run/reset: R1 4543/10chunks, R2 4636/10. Each <=500rows with index/SHA/size/count, run identity, closed/no-overflow, gap/duplicate/tail gates and independent meanHz. Precision preserved by passing embedded JSON strings; no >200k transfer or numeric-array roundtrip. Both complete, no missing UI tail here. This does not recover ALLOC60's earlier111missing rows. UI ~54.5Hz, not60Hz acceptance.

Guest samples R1 4738 (quota error retained), R2 4131 (clean AP_EXIT_OBSERVED). Original AP main trace thread maps to guesttid8/birthTick identity in both. AP-thread CPU/runqueue deltas over their differing sample windows are9.366s/0.716s and8.760s/0.264s respectively; not directly phase-matched totals.

## What is localized

R1 frame90464: host receive→send519.046ms versus1.000ms threadCPU. RX→compute438.560ms includes25.286ms RX write and413.274ms outside measured syscall. INTENT write75.610ms and fsync4.158ms also occur in the frame. In the overlapping661.86ms guest sample window AP ran1.483ms and waited runqueue4.831ms, with most sampled states sleeping. Host process had42 involuntary switches in a603ms covering window; that count is not a scheduler-wait duration. This locates substantial delay on host processing/wait, not a519ms AP arithmetic cost.

R2 frame42768: host64.776ms versus0.527ms CPU, INTENT write49.582ms and fsync12.935ms. In overlapping118.97ms guest window AP ran1.402ms and runqueue counter did not advance; no claim other threads/host never waited. Fsync maximum over R2 remains38.237ms. Removing AP diagnostic trace from shared path does not remove host WAL stalls.

AP local RTT p99 observed4.787→1.350ms, whole RTF0.96909→0.99728. Shared-host load/cache is uncontrolled, one run/mode, different closure/quota versions and R1 failure phases; these changes are evidence of an avenue, not causal proof or production optimization acceptance. Need repeatable controlled observations before selection.

Host and guest origins never subtracted naively: existing nonce brackets plus nearest-calibration projections are retained with uncertainty (R2 worst frame bracket width41.17ms). AP RTT and host service are reported as separate local durations, not invented exact one-way network latency. Small signed CPU/wall residual noise retained. Exact host runnable/I/O/GIL/preemption split remains UNKNOWN.

## Coverage, resource and handoff

Implemented6/6 scoped requirements. REQ1 invariant PASS; REQ2 archive v1 FAIL then forensic recovery, v2 PASS; REQ3 guest data R1 PARTIAL/quota error and R2 PASS, exact host runnable wait NOT_CHECKED; REQ4 mocks/chunked UI PASS, R1 flight FAIL and R2 bounded journey PASS; REQ5 storage PASS; REQ6 all-frame raw/SHA/pacing analysis and preservation PASS, stable1× FAIL. Overall PARTIAL. Final verifier24 scoped checks with explicit deferreds, no fullG1/Hera/signature/ENDURE acceptance.

Initial attribution reader refused absent normal R1 archive; forensic-aware analysis added without modifying old source/runtime. Initial setting-based availability label was conservative because sysctl absent; revised analysis states positive observed per-task counters and preserves original output. No data synthesized.

New2-run envelope1GiB/run,2.25GiB total, fresh22.5GiB admission and live20GiB+768MiB stop replace the old4-run24GiB policy only in this isolated scope. WAL384/AP128/MAV64/syscall64/stages64/probes+UI+analysis<=192MiB; no install/build. Current evidence0.800GiB. Free23.88GiB, minimum2s host point sample23.90GiB; no observed floor breach. Guest observed memory maxima~66MiB bind/~149MiB tmpfs, within384MiB. No evidence auto-deletion.

22575 prior protected paths before/after:0missing/0SHA mismatch, including ALLOC60 and ENDURE. Point-in-time checks only, not continuous-presence or ENDURE acceptance. All planned starts consumed, no automatic additional run. Current API command `node pilot/isolate61/ap-server-v2.mjs`; preview `node pilot/isolate61/server.mjs`, idle/no automatic flight. Source pins v1/v2 preserved and artifact fingerprints sealed.

Next: controlled host per-thread offCPU/filesystem wait attribution and repeated equal-phase measurements, keeping durable per-frame publication and the now-verified chunked UI collector. tmpfs diagnostics remain experimental; no default selection or new signature.
