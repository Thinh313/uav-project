# STABILITY16 quota isolation, source/mock scope

The candidate is an isolated G15-scoped composition, **not wired into G15 and not an Android-SITL acceptance**. Frozen G15 files are imported read-only. Healthy measurements did not establish a G15 heartbeat cause or a healthy performance advantage. A controlled1250ms quota read/CPU stall distinguished the old host-thread path from worker isolation; an own heartbeat fsync or host-scheduling stall still failed the unchanged1000ms deadline.

## Effective modules and API

- `pilot/stability16/quota-worker.mjs`: calls the exact frozen G15 `scan({verifyHashes})`. Complete traversal, metadata/mtime checks, requested full SHA checks, bounded entries/depth and original policy remain unchanged. No result cache or test fault hook.
- `pilot/stability16/quota-scanner.mjs`: one worker, one pending scan, zero queued requests. `scan({verifyHashes:boolean})` rejects overlap; `fresh()` returns an immutable accepted sample or fails closed; `diagnostics()` reports state and observed numeric termination; `await close()` cancels pending work, invalidates the sample and terminates the owned worker. Worker startup, synchronous inventory load and delivery are inside the parent10s cycle. Serialized responses are bounded64KiB and checked for exact schema/context/totals. The explicit G15 policy/inventory tuple rejects another policy before worker creation. No future generation may silently reuse it.
- `pilot/stability16/quota-resource.mjs`: `await createResourceGuard({root,out,onStop,onObservation})` performs the first isolated scan before returning, then preserves the1s audit cadence, caller-driven tick, original G15 decision and15s resource trend, original durable trace writer and4MiB trace cap. Expected caller tick remains250ms. A failed decision closes the scanner before notifying the owner. `await guard.close()` always attempts both durable fd closure and worker termination; the first error propagates and repeated close returns the same promise. Callback failure is diagnostic and never restores a valid sample.

Freshness uses the parent dispatch anchor conservatively, not the time a delayed message reaches the parent. `acceptedAtMonoMs` is diagnostic only. Worker absolute timestamps never become parent freshness anchors. Parent deadline/stale checks use its own unchanged Node performance clock; no cross-process absolute subtraction occurs. An unexpected error/exit, malformed result, expired cycle, stale sample or close cannot be cleared by a subsequent message and does not spawn a replacement worker.

## Future composition boundary

No current entry or listener imports this candidate. A future explicitly authorized isolated entry must:

1. Create a scanner, await the requested complete scan (full hashes for original phases that require them), obtain actual `statfs` free bytes, and pass the sample to the unchanged G15 `decide` with the original counters/phase. Await scanner close in `finally`. Do not run admission and observer workers concurrently.
2. Await guard construction before exposing a listener or controls. This is an async API, so replacing an import in the frozen synchronous G15 listener is insufficient. Keep the guarded launcher, physical admission, original controller deadlines, request authentication, complete sealed-history worker/control fences and all frame/durable evidence rules.
3. Call `tick()` at the original250ms cadence. On refusal, close the owning host through its original cleanup path. Await `guard.close()` before declaring managed closure, including failure paths. Any close error is a failed closure, not success.

The current real approximately26GiB free space correctly refuses the unchanged28GiB runtime decision; actual admission still requires29GiB. The controlled handler fixture excludes only its physical constructor admission to permit source/mock experiments; a separate real guard test demonstrates the actual refusal. That fixture never calls the production guarded `app.listen`, creates no flight transport and claims no physical admission.

## Evidence and qualification

`builder-quota-diagnosis01.json` measures the real8527-entry inventory,1970226B pinned manifest and306022057B full historical content read. Healthy scans already yielded effectively. `builder-quota-02-comparison01.json` retains one corrected network-authorized execution of the same healthy/parity and six controlled cases. The first sandbox `EPERM` failure and pre-correction harness bytes are preserved. All six durable overlap journals remain, and all owned loopback listeners/workers/scratch trees were closed/removed.

The comparison used pre-tuple scanner SHA `be5ee30485e1d2eafbb29f32acd5fbbbd8695aed7c699665ba73aa39b36b1b56` with the identical final worker. QA found a self-consistent false historical-total result could pass. Its counterexample and the exact old scanner bytes remain. The final scanner adds only the approved pinned-basis check and exact historical-total equality; no scan, scheduling, deadline, barrier or worker path changed. Final independent QA checks that delta and current worker parity instead of duplicating the timing suite.

`builder-quota-guard-tests02.json` checks the final observer: real physical refusal invalidates its sample, unchanged quota/trend decision with a clearly labeled32GiB statfs fixture produces a durable trace, and simultaneous owned fsync/close failures still terminate the worker and propagate the first error. Earlier guard proof and pre-stop-close source remain.

The Native `ui-timing.mjs` consumer is separate diagnostic-only code. It reports UI observation age, local queue/timer/send/header/body spans and matched server ingress/barrier/egress spans without inventing a cross-clock/network residual or treating `res.end` as client delivery. No request cadence, retry, UI age,1000ms deadline,750ms heartbeat or3000ms host lease changed. Root power evidence attributes the later approximately594s gap to clamshell sleep; the earlier G15 UI/heartbeat initiator remains unknown.

## Limits

Worker isolation is controlled-stall hardening. It cannot make an own durable barrier timely, prevent host suspension, make an incomplete inventory authoritative or certify a new campaign. The worker is trusted frozen code; structural validation rejects malformed/context-inconsistent output, not a Byzantine worker that fabricates an entirely plausible inventory. Whole-task disk budget remains32MiB, with a20GiB floor. No protected file was deleted/restored, no dependency/build/signing occurred, and actual runtime is NOT RUN.
