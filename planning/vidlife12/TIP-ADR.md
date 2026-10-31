# VIDLIFE12: native direct and video readiness

Authorized by user 2026-10-31. Contractor specification. Objective: valid video-measure readiness in a guarded Android–ArduPilot SITL journey, with precise first-failure evidence. A faster failure alone is not functional success.

## Cold findings and unknowns

HOSTDIAG11 S01 failed PUBLIC_UI_TARGET_NOT_READY:video-measure without a guardian fault. Retained source records prove codec support/registration existed. UI.video is the measurement collection, so null before measurement is normal. MEDIA_NATIVE_BACKGROUND is a generic JS invalidation label, not proof of Android onPause. The native TCP path in this test belongs to the Node RootWire client, not an APK raw TCP socket.

Independent raw transport checks show the adapter requests message intervals200000us for [1,24,30,33,42,193,242,245] but omits heartbeat id0. Relay has34 heartbeat packets versus440 on the passive path; the last relay heartbeat precedes native EOF by3055.13475ms while other messages continue. Node records AP_CONTEXT_LOST:ROOT_HARD_HEARTBEAT_3000MS. This supports an explicit heartbeat cadence correction, retaining the guard. Real firmware support/accepted packet rate must still be checked, not inferred from a mock or ACK alone.

Source SCENE_CLAIM_ORIGINAL_AGE250 occurs earlier. Its exact validation substage is not recorded. The last lifecycle heartbeat intent precedes viewer invalidation by about970ms, consistent with a request deadline but not proof of its original reason. lifecycle() waits journal.flush() and unrelated payload.settled() after mutating operator state. Prove any decoupling in mock; do not retrospectively claim it caused S01.

## Allowed changes and isolation

Write only planning/vidlife12 and evidence/vidlife12. Reuse unchanged development APK8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1, Android app/domain and cached image/AVD. No new APK/signing, app clear, new identity, native quota or SAF-counter reset in this scope. Preserve all old source/candidates/evidence/ENDURE/trust/SOT. Selectively copy only117 runtime files from frozen2bd9ba916c3db0c9907163ff7f533da857c4abb0e5a43d0d8cc0be3baaf47b87 and the necessary small JS transitive overlay; independent writable inodes, no whole project copy. Old module inputs remain immutable and hash verified. No hidden runtime monkeypatch or unrecorded URL override.

Routing clarification before implementation: the required isolated behavior also needs an explicit server, companion and loader. Eight behavioral/routing JS modules plus a loader are approved, rather than forcing an arbitrary six-file count or hidden runtime rewriting. All actual bytes and paths must fit the unchanged quotas and finite input-role table.

Implement the explicit id0 request in the existing200000us cohort, with exact target42/1 and validMAVLink command511 bytes. Cover zero-id truthiness mistakes, rejection/unsupported firmware and missing actual heartbeat. Do not synthesize heartbeats or substitute the passive stream as the control stream.

Measured cadence refinement: raw id30/id33 each have135/162 host arrival gaps above250ms while their AP time_boot cadence is200ms. Request these two visualization streams at50000us; all other existing stream intervals stay200000us and the new id0 uses200000us. This is an upstream rate correction, not a relaxed freshness threshold or proof of the separate RootFDM scene-claim failure. Serialize correlated acknowledgments and require actual post-ACK heartbeat observations within the original freshness1500ms before readiness. An ACK alone never proves observed cadence. Verify additional bandwidth/records remain inside all original source limits.

Instrument bounded first failure, lifecycle request/dispatch/durability/settlement/reply, actual client invalidation reason, and source proof age at validation substages. Preserve original clock domains and correlate by exact context/request/nonce or qualified clock brackets. Never directly order Node hrtime, Python monotonic and browser performance timestamps without a supported mapping. Trace first failure before destructive cleanup, with bounded memory and existing journal/output owners; recording failure is secondary and cannot delay ingress revocation or restore authority.

Propagate lifecycle event origin and reason, retaining background/revoke behavior. Separate collection state from viewer/session/readiness state. Expose terminal startup failure promptly instead of waiting60s for a disabled target. Never enable measurement without a fresh qualified decoded frame, source/receiver identity and valid warm-key proof; do not fabricate collection/readiness or silently restart after a fault.

A heartbeat-only isolation correction is authorized if mock proves it: persist the heartbeat's own causal journal intent before acknowledgment, without waiting for an unrelated pending payload queue. Keep known payload fatal errors observable. All non-heartbeat operations, especially revoke/background/close/reboot, retain necessary settlement and cleanup obligations. Verify every operator role; do not trust caller-supplied role or drop a safety side effect. Retain the original1000ms client deadline and all lease/authority rules.

## Immutable guards and resource gates

All original guards stay unchanged, including100ms HostHealth,250ms clock/input/scene freshness,200ms UI/lease,1500ms flight freshness,3000ms hard heartbeat, speedup1/catchup500ms, fsync before sensor and all accepted physics frames. No backdating, new expiry allowance, fake timer qualification, frame skipping, authority revival or hidden guard waiver.

Cumulative artifact union currently7680000/8388608bytes includes every older pool. Count the same union plus new objects, and all new active source/QA/evidence metadata honestly. Keep original64MiB metadata,14owners,60686336future reserve including closure/ledger, native lifetime quotas and storage floor10GiB plus reserves. New traces must fit existing positive writer/path contracts and finite global limits; no new owner or cap. Prefer first-fault/aggregate age diagnostics over per-frame trace inflation. Do not delete or reclassify old evidence to fit.

Root owns all gate commands, immutable freeze and actual actors. Builder/QA may write mock/verifier outputs only in their new scope. First run mocks and independent source review, then pure artifact/admission checks. At most two new slots s01/s02, each the existing180s short simulation profile, no automatic retry. A second slot is only for a measured targeted repair with its own gate and fresh admission. No ten-minute run. External project evidence remains static during actual actors; independent live observations are held in RAM and persisted only after closure.

## Acceptance and reporting

Mock adversarial cases: heartbeat0 exact wire/target/ACK rejection; relay simulation cadence with original guards; unrelated payload queue pending/fatal/revoke obligations; late/foreign lifecycle acknowledgments; background/pagehide versus local invalidation; decoder source capability and session rollover; each originalAGE250 substage; stale frame refusal; capture/EIO/first-fault cleanup; finite queue/trace/global budgets. Run meaningful integration mocks against actual selected code, not a parallel implementation.

Independent QA checks old-byte preservation and the selected source graph, namespace origins, unchanged guards and budget conservation. Old/new candidate verification uses fresh processes to avoid the prior validator namespace incident. Preserve complete raw stdout/stderr, native/direct transport bytes, original video lifecycle/age evidence, accepted frame groups and physical cleanup. Do not complete a missing journal footer or treat an incomplete prefix as full media acceptance.

Functional PASS requires genuine target-ready and video-measure dispatch/ack with qualified receiver data in the actual Android–SITL short run. A source guard refusal, session failure or unrelated new blocker is NOT READY and must be reported precisely. No root-cause claim for old gaps unsupported by new evidence. Completion separates instrumentation, functional success and Beta/real-device readiness.
