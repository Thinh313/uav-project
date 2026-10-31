# APROUTE28 · Payload routing through actual ArduPilot SITL

Owner13/10/2026 authorizes real ArduPilot routing with mock payloads, separate from frozen source/candidate/ENDURE evidence; no Fly/SDK/HeraHub/new signature. Single agent changes roles sequentially, not independent audit. This scoped instruction supplies blueprint authorization. No product UI change.

Architecture: dedicated unchanged ArduCopter4.7.1 binary/container,1CPU/256MiB; GCS127.0.0.1:5774 → SERIAL0; synthetic busA5775 → SERIAL1 (camera100/shared manager154devices1/2); busB5776 → SERIAL2 (camera102/101). Only ArduPilot forwards between these sockets. No GCS direct peer delivery; IPC instructs fixtures to emit responses but cannot inject frames into GCS. Three cameras/two gimbals are test configuration, not Hera capacity. Unchanged T25 broker remains explicitly mock-origin; outer receipts prove actual AP network routing, never physical execution.

|REQ|Acceptance|
|---|---|
|A28-01|Dedicated fixed loopback ports/resource bounds/actual disarmed AP heartbeat, binary/config/container identity retained; new state only, no app/candidate edits.|
|A28-02|Learned discovery before dispatch; exact immutable targeted camera/gimbal command reaches correct AP serial bus, not other bus; response emitted on peer bus reaches GCS through AP. Four-point raw SHA/ordered receipts.|
|A28-03|Concurrent distinct cameras, shared-manager serialization/device feedback isolation, capture metadata remains synthetic; wrong system/component/recipient/command/device never completes target. No broadcast/AP-target/flight/mission/param commands admitted.|
|A28-04|Real peer/GCS close, heartbeat silence, payload reboot, explicit reconnect and actual AP stop/fresh boot invalidate authority/pending work; new generation/discovery mandatory; no retry/failover/historical resume. Late/duplicate/badCRC cannot resurrect completed/lost work.|
|A28-05|Bounded raw streams/log/socket buffers/deadlines fail closed, raw corpus replay target/route/cross-bus/response evidence, failures retained. Unsupported framing/signing not promoted.|
|A28-06|New unit/actual routing checks plus T25/P22/T26 regressions; before/after frozen2009/140/candidates/old attempts/module/trust-event hashes; stop only owned container/peers, image prune only, disk cleanup.|

Scope excludes mission upload/flight, AP component1 camera proxy (requires separate real AP camera backend), physical video/images, SDK/native installation, authenticated remote freshness, full hardware replacement, ENDURE acceptance and release signing. Plan camera target drafts remain drafts, not operational mission proof. ACK=acceptance only; matching feedback=consistent but causally unattributed. A link can carry several components: routing selects bus, fixture component dispatcher selects endpoint. Same-manager ACK ambiguity is serialized by existing tombstones until explicit new generation. Unknown peer liveness invalidates whole test session conservatively. No automatic restart of campaign or aircraft. Tests control only owned simulator, not other Docker workloads.

Primary official routing/serial documentation plus pinned firmware routing source captured with URLs/SHA/license; external claims remain claims. Observed raw routes determine test verdict. New ENDURE27 live observations/trust append may advance separately; old events/attempts never rewritten.
