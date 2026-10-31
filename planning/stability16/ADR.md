# Isolate complete quota audits, preserve authority deadlines

Status: candidate implementation and mock qualification, not integrated runtime acceptance.

## Evidence

The G15 inventory scanner already uses asynchronous traversal and periodic yielding, but the pinned inventory read/parse/hash is synchronous before the scan duration timer; requested full file hashing also executes crypto on the host event loop. Measure these costs before choosing a worker. A worker must execute the same complete scanner; no metadata shortcut or reduced coverage is authorized.

The retained failure is not proof this code caused heartbeat 367. Browser-local queue wait was zero; headers arrived after the1000ms deadline. Server-local work was about106ms including106ms journal barrier. These are distinct clock domains and cannot be used to invent a network or scheduling remainder. The native sleep log independently shows Clamshell Sleep15:54:43 and DarkWake16:04:37 on23October, consistent with the later592.9s loop gap and quota stale closure. Earlier UI/heartbeat failure remains separate.

## Decision

Implement an isolated bounded scanner candidate only if controlled measurements show isolation benefit. Retain original10s cycle,15s sample freshness, physical admission/runtime floor, complete metadata/hash checks, no overlapping audit and sticky failure. Count dispatch/startup time, reject late completion, invalidate on close/crash/malformed results; never renew freshness from an old sample. Do not replace durable heartbeat fsync with worker ACK or timer success.

UI work adds bounded diagnostic correlation and tests of the existing bootstrap. It does not change request cadence, queue, deadline, client lease or retry policy without a demonstrated defect. Keep browser lifecycle document, UI document and server boot identities separate. Report only local monotonic durations; res.end does not prove client delivery.

## Integration boundary

All candidate code and tests reside in pilot/planning/stability16. Do not mutate beta06 generation15 or its final proof writer to evade its28GiB gate. Runtime requires a future isolated composition and fresh original admission >=29GiB; current approximately26GiB means NOT RUN. Never resume failed G15. Missing legacy paths outside the protected baseline are recorded, not silently repaired. No production readiness claim follows from these mocks.
