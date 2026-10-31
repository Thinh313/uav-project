# TIP-SITLDISCOVERY41 — actual disarmed AP full-stream discovery/loss/reboot

2026-10-14. User explicitly authorizes real ArduPilot/SITL discovery, disconnect and reboot, isolated from frozen source/candidate/ENDURE. No SDK/Hera/APK/signing. Sequential specification/build/verify by one agent; no independent review claim.

## Scope / decisions

Reuse exact existing official static x86_64 `runtime/sitl/arducopter`, captured metadata4.7.1/commit dbe792162d06cab66c3475fd5556bf7a120f119e and pinned existing Ubuntu image. No rebuild/install/image pull. Owned disarmed simulator only, loopback5794, fixed resource/log budgets; inspect identity/PID/image/mounts before lifecycle operations. Never touch other containers/old states. Startup defaults are new isolated configuration; no in-band parameter writes.

Use immutable APSTREAM40 full framer/serializer against actual raw TCP and observe version/capabilities/typed named parameters. Outbound only GCS HEARTBEAT, COMMAND_LONG512 requesting148, named PARAM_REQUEST_READ. No ARM/mode/mission/failsafe/reboot commands. Reboot via exact owned Docker process; reconnect is an explicit new instance, never old-witness restoration.

Source indicates AUTOPILOT_VERSION uid=0; old F38/AP40 mock guard forbids zero UID. Test the actual incompatibility honestly using an offline projection of real raw bytes; no old source/contract override. New live observer permits zero UID ONLY with locally verified owned SITL binary/process association, UID2 retained as observation, authentication:false and hardware identity unknown. Do not invent UID or promote mock projection to actual acceptance. Current source/advertised version/captured official metadata association is not a bit-reproducible source build or cryptographic attestation.

## Requirements

| ID | Acceptance |
|---|---|
| R41-01 | Before/after protectedSHA includingAP40/candidate/ENDURE; floor20GiB +runtime1GiB+margin512MiB, new evidence32MiB and runtime state128MiB bounds. |
| R41-02 | Owned resource-bounded simulator, pinned binary/image/config, disarmed heartbeat and matching numeric version/custom commit/banner/metadata; observed UID/UID2 and capabilities retained. |
| R41-03 | Actual full-stream request/ACK/version and readonly typed parameter roundtrip with raw TX/RX/host clock lineage; keep CRC/provenance/authentication/execution distinctions. |
| R41-04 | Actual GCS socket close revokes witness and prevents old send; explicit new session re-discovers/reads, no retry or implicit restore. |
| R41-05 | Actual owned AP process restart: PID/boot observation and old link death/revocation; fresh discovery with same exactbinary, wrongtarget/late old bytes quarantined in fault seam; no claimed actual foreign hardware responder. |
| R41-06 | AP40 actual-byte compatibility result preserved, UID0 constrained extension tests, source-bound cold raw replay, framing/typed adversarial regression and old36/37/38/39/40 exact corpora. |
| R41-07 | Actual process closure/port/resource/state cleanup +source/evidence fingerprints/report; no flight/hardware/long-endurance/new signatures or canonicalSOT edit. |

Actual network evidence and injected wrongtarget packets are labeled separately. Attempt failures retained; no automatic failed transaction retries. If a gate fails, diagnose and preserve the result, then only a newly scoped attempt may run. Free space alone never authorizes other runtime/build work.
