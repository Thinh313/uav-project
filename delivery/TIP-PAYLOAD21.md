# TIP-PAYLOAD21 · Flight and multiple payload foundations

Authorization: owner 2026-10-13 asked to implement the previously proposed RAGAS comparison → independent aircraft/payload architecture → multi-payload simulation/operator workflow. No SDK or connected HeraHub. Single agent, separate specification/build/verification; no independent review claim.

Scope: executable independent simulation slice in `pilot/payload21`, external published capability matrix and A/B protocol, adapter contracts, negative/fault fixtures, Fly/Payload console, exportable simulation review and reproducible tests. No RAGAS application code reuse. Hardware tests remain NOT_CHECKED.

Decision: ENDURE20 is currently running an immutable 24-hour candidate. No change to its app/services/package, controller helpers, signed slots, source/copy corpus or trust state. New module runs separately on loopback8789, with no runtime data writers, transport sockets, flight APIs or automatic command retries. This is a future integration module, not a selected production release. Documented integration follows ENDURE20 acceptance, new package inventory/signing and regression gates. No new approval required for this authorized reversible local work.

| REQ | Acceptance criterion |
|---|---|
| P21-01 | RAGAS published claims have original snapshots/hash/span and separately scoped AERIS evidence; absent human A/B produces no comparative winner. |
| P21-02 | Route identity binds aircraft/session/camera component or proxy camera ID and distinct gimbal manager/device IDs; duplicate/invalid/broadcast targets rejected. |
| P21-03 | Commands require discovered fresh capabilities and confirmed per-target authority; selection never retargets an in-flight request; bounded concurrency/journal. |
| P21-04 | ACK and observation are separate; rejected/mismatched/stale/late feedback cannot complete commands; timeout has uncertain outcome and no auto retry. |
| P21-05 | Video loss, camera link loss, gimbal faults, authority loss and aircraft link loss have scoped effects; reconnect needs explicit rediscovery/reacquisition. |
| P21-06 | Three heterogeneous synthetic payloads support selective feeds, zoom/focus/capture and gimbal workflow; all views/captures/events remain labeled simulation. |
| P21-07 | Evidence export binds targets/session/units/provenance and conservatively distinguishes synthetic capture receipt from physical media; event eviction makes completeness false. |
| P21-08 | Browser workflow, keyboard/focus, equal control geometry, responsive viewport and negative/fault scenarios pass; frozen ENDURE20140-file inventory and five controllers remain exact. |

Dependencies: P21-01/02 architecture → P21-03/04 core → P21-05/06 simulator/UI → P21-07/08 verification. Deferred physical gates: recorded as-built airframe/radio/protocol/payload configuration → SDK/native/video transport → bench/HIL → controlled flight/operator A/B. Actual new SITL payload execution is NOT_CHECKED; no cached flight becomes a new run.
