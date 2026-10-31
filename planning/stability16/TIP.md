# STABILITY16: heartbeat, UI freshness and scoped quota

User outcome: keep operator telemetry and durable heartbeats responsive during complete quota audits, without weakening authority, durability, quotas or deadlines. This is an isolated repair and mock qualification, not a resumed G15 campaign.

## Scope and roles

Contractor: root; server/quota Builder: beta_g3_flight; UI/clock Builder: beta_g3_native; independent QA: beta_g3_qa. Builders own separate files under pilot/stability16 and planning/stability16. All outputs are additive under evidence/stability16. Do not modify app, services, native APK, beta06 generations, source/candidate, ENDURE, existing pins, locks or canonical SOT. Never delete or restore protected files in this task. No new signing, dependencies, emulator or SITL during diagnosis/mock.

## Evidence and hypotheses

G15 ground admission refused at UI age 1564.706 ms against unchanged 1200 ms, then heartbeat 367 failed at 1070.8 ms against 1000 ms. Server processing for the correlated request was 106.143 ms; this does not explain client delivery. Later loop gap 592900.689 ms and quota stale refusal have unknown initiators. Do not subtract absolute timestamps between clock domains. Reuse retained traces; no retrospective root-cause certainty.

Measure full inventory cost, history parse/hash, traversal/lstat/read costs and event-loop/queue delay separately. Test a small bounded repair against the existing implementation with identical input and integrity checks. No hash skipping, mtime-only cache, increased deadline, hidden retry or authority restoration. A host suspension must still invalidate freshness; asynchronous completion after close/failure must never restore a valid quota sample.

## Acceptance

1. Diagnosis identifies measured bottlenecks and unknowns with source fingerprints. Distinguish modeled faults from observed G15 evidence.
2. Repair performs complete bounded inventory and retains exact metadata/hash validation and fail-closed stale/error semantics. No overlapping scans or unbounded queue.
3. Mock contrasts old/new under quota filesystem/CPU delay, heartbeat own fsync delay, UI/host scheduling delay, close, crash, malformed result and stale completion. Own barrier/deadline failure stays failure.
4. Diagnostics separate UI snapshot age, timer lag, queue wait, request header/body and server ingress/barrier/egress using local monotonic durations and matching identities. No cross-clock invented latency.
5. Independent QA tests adversarial cases and verifies all touched inputs unchanged. Existing missing paths recorded as pre-existing, never reported intact.
6. New scope <=32 MiB; no project copies, dependency installs or persistent background processes. Check free disk before each experiment; stop writes below 20 GiB.
7. Android-SITL is NOT RUN unless mocks and independent gate pass, protected inputs are verified, and original >=29 GiB admission/stability guard is satisfied. Current approximately26 GiB blocks runtime, not bounded mock. G15 final receipts remain unwritten if their unchanged28 GiB writer gate refuses.

## Deliverables and stop

One completion/verify report binds diagnosis, source, mock receipts and independent QA. Keep failures. Maximum three hypothesis experiments per issue, refine only on new evidence. READY means mock repair scope only; integrated beta readiness remains separate. No autonomous campaign retry. No LLM baseline needed: deterministic runtime correctness repair, not an AI product architecture claim.
