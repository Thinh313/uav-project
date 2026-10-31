# BETA06 generation01 lifecycle investigation (read-only)

The initiating heartbeat transport/renderer error is **UNKNOWN**. No pinned app/bootstrap/native/helper source was changed and no runtime/UI/ADB action was performed by this Builder. This is a bounded diagnosis of the ended/unarmed run, not acceptance.

## Observed facts

- Host overlap journal has402 successful lifecycle events:2 activate and400 heartbeat. It contains no successful background or stop event.
- Epoch1:207 lifecycle events; last successful heartbeat host335990121.365541ms. Largest preceding successful-event gap was1409.0695ms. Epoch2:195 lifecycle events; last heartbeat336344190.811875ms, largest preceding successful gap1015.6385ms.
- Actual AP raw `s220913d46e964ec6af94` record922 has FIELD02_CLIENT_AUTHORITY_REVOKED / CLIENT_HEARTBEAT_EXPIRED at hostNs336347331386166. It follows epoch2's last successful heartbeat by3140.574291ms. The3s guard worked; no ARM was observed in this investigation.
- Host OBSERVATION continued:738 inter-observation gaps, maximum1344.982333ms, P95 approximately1139.502292ms. This argues against a multi-second complete host-Node event-loop pause across those recorded points, but does not measure individual HTTP dispatch/response scheduling or browser execution.
- UI diagnostic sequence continues after both client expirations. Its `foreground` field is the conjunction of document visibility, native environment foreground and host client.active. Thus foreground=false in that diagnostic does NOT independently prove Android background/sleep.
- Root's ground snapshot reports Android mWakefulness=Awake, no device idle and current ShellActivity focus at that sampled instant. That snapshot does not attest continuous foreground for the whole preceding interval.
- Viewer periodic30s and retry45s calibration both produced zero accepted probes; reported viewer RTTs include75.1–1613.9ms, outside the existing strict clock limits. Clock remained valid only to its original expiry and stopped at host336024612ms. No threshold was loosened. Epoch2 heartbeat failed much later, with viewer already stopped, so active decoding alone does not explain both failures. No shared cause is proven.

## Source mechanism and observability gap

Frozen `pilot/clockvideo05/bootstrap.js` serializes lifecycle requests in one Promise queue. requestLife fetch and response.json have no application deadline. A pending heartbeat holds heartbeatPending and can block a later queued foreground/background call. The bare heartbeat catch clears local session and emits field02AuthorityLost, preserving fail-closed behavior but discarding the original error/rejection reason. Future interval ticks intentionally stop when session is null; only explicit foreground can activate a new epoch. This explains persistence AFTER an error, but the source alone cannot identify which error occurred in generation01.

Successful lifecycle journaling happens only after client.action, payload.settled and a durable journal fsync. Failed lifecycle requests are not logged with request-start/end/error. UI paint rebuilds SVG/other presentation on refresh and media preview renders on receiver callbacks; neither duration nor renderer long-task/timer lag is captured. Browser connection-pool queuing, delayed fetch/body, synchronous paint, host/filesystem contention and native visibility transitions therefore remain distinguishable hypotheses, not established causes. Unbounded fetch is a demonstrated failure path, not a proven actual event.

## Minimal isolated generation02 proposal (not deployed)

1. Own bootstrap copy in new authorized generation, with whole fetch+JSON deadline≤1000ms. Abort timeout, keep a generation/request ownership fence, do not allow a late response to commit local session. On failure clear local session and require explicit foreground; no retry, autoactivation, authority restoration or TTL extension.
2. Add bounded redacted lifecycle diagnostics: request/queue start/end/timeout/rejection, browser timer scheduling lag, raw document.hidden and nativeForeground separately, desiredForeground, pending action age and session epoch/active. No CSRF, token or bearer payload. Record actual error code instead of bare catch. Host record request receive/response finish/revoke reason and monotonic durations separately; never subtract unrelated clock domains.
3. Measure paint/refresh/decoder callback time using a bounded ring or count/max histogram and available browser long-task observation. These are diagnostics, not heartbeat authority. Do not keep a session alive from a worker/native surrogate if the actual UI is stalled.
4. Keep3s client TTL,750ms cadence,20ms calibration cap, clock expiry and noautoauthority semantics unchanged. First run only ground/read-only stress to show bounded requests and distinguish renderer vs transport; do not spend another AP request merely to observe a heartbeat failure.

`qa-lifecycle-diagnostic.mjs` executes the exact frozen bootstrap in a VM: injected server negative clears session/no autoactivate; held fetch blocks pending/queue; explicit foreground works only after prior settlement. `qa-lifecycle-deadline-proposal.mjs` is a planning-only seam, NOT loaded by the app. Its mock proves whole-response deadline, timeout abort, late ACK cannot commit and explicit negative preserved. Evidence: builder-lifecycle-counterexamples01.json (4PASS) and builder-lifecycle-deadline-mock01.json (4PASS). Neither proves the initiating real cause or fixes generation01 retrospectively.
