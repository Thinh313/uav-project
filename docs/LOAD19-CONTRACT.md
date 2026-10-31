# LOAD19 · Latency, concurrency and bounded soak

Owner-authorized hardware-free host engineering increment; v1.14.0 candidate sequence7. One agent switches Contractor/Builder/Verify phases; not independent audit. No flight commands, SDK/device, external release or full-project scratch copy.

| REQ | Acceptance |
|---|---|
|L19-01|Server-owned route classes: observe4, control1, heavy-read2, write1, static8. Zero queued work;429/Retry-After explicit retry, no auto repeat of commands/writes. Caller cannot assign class or loosen limits.|
|L19-02|Slots remain charged until BOTH async handler settled and response finished/closed. Client abort cannot free active storage/validation work prematurely. Stream pipeline/finally releases existing export reserves.|
|L19-03|30s request deadline cancels transport (not pretend committed data undone). Max32 sockets/32 requests per socket,5s headers/keepalive,30s body timeout,16KiB header cap. Deadline is cooperative; watchdog remains CPU-stall authority.|
|L19-04|Reserved observation/control pools remain available while read/write exhausted. Partition fairness only; no FIFO/client fairness claim. Fresh GET-only metrics with128 latency samples/class; unknown/offline/invalid UI clears prior results.|
|L19-05|Deterministic limiter/abort/deadline tests; actual slow/draining/aborted streams, concurrent read overload and synthetic writer rejection preserve existing record/receipts and no unauthorized flight call.|
|L19-06|Actual managed copied-corpus canary and30-minute mixed-read soak: duration/attempt/accepted/rejected/error denominators, client percentiles, event loop/RSS/reserve and stream terminal digest logged. Observe client p95≤1000ms and accepted read p95≤10000ms host engineering thresholds; no device SLA.|
|L19-07|Pre/post all664 source/copied files and27 acknowledged receiver packages unchanged, original156 record replay; explicit managed restart remains healthy. Candidate sequence7 selected only after accepted soak/canary.|
|L19-08|Versioned workload/policy, immutable release/phase/supervision, raw attempt receipts, scoped evidence/coverage/fingerprint and75→76-fact SOT intent-only update.|

Thirty real minutes are a bounded soak, NOT 24h/multi-day/HeraHub/flight certification. Server metrics are last128 completed requests/class including errors/aborts; client complete-campaign metrics separate. No automatic deletion/caching of validity/repair or downgrade. Frame/height/camera/acceptance semantics stay existing. Memory/resource policy18 and macOS Seatbelt retained; software signatures are not flight-record signatures. Quotas/fsync/byte replay decide store integrity. Disconnect/deadline after commit may leave a valid receipt without client ACK; reconcile by explicit digest, do not replay POST automatically. SDK/HeraHub/native/HIL/field, independent security review, hard process-tree/CPU limits and physical power loss remain NOT_CHECKED.

Known host engineering limit: fixed30s whole-request transport deadline applies to bulk streams/uploads too. Slower or very large transfers can remain incomplete and require explicit checkpoint/source review; successful completion on slower native/device storage is NOT_CHECKED. Progress-aware bulk deadlines and a separately reserved bulk pool are a next acceptance gate before slow-link/native deployment, not a claim made by this bounded host milestone.
