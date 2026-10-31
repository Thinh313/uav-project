# CLOCKVIDEO05: clock lifecycle and semantic cockpit UI

22 October 2026. User explicitly authorizes correction and mock first, then concurrent mission/payload/video and AP reboot on owned Android–SITL. Vibecode6.3: Builder production, Contractor live operator, independent QA. No new APK/signature/SDK/device, old source/candidate/ENDURE/current COCKPITVIDEO04 artifacts immutable.

## Outcome and boundary

New code only pilot/clockvideo05, planning/clockvideo05, evidence/field02/clockvideo05, new completion. Curated small fork of cockpitvideo04 and necessary media files; no whole-project copy. Preserve all previous431 artifact hashes and original protected baselines. Original source manifests/cap9/cap11 stay byte-identical. New isolated adapter may admit at most cumulative12 SITL requests from observed10, binding all10 prior request hashes; request13 refused before writes. Exactly2 new actual AP requests, at most2 host sessions and2 cold boots,20min/session, AP540s. Count failed admissions after request creation. No further implicit retry/extension. Runtime writes only new request directories, never old.

Cached unchanged development02 APK and fixed localhost8872/8873, owned emulator5582 only. Existing ADB/root permission retained. All flight/payload control through actual visible UI; no hidden evaluation or control POST. Readonly GET evidence allowed. Use existing80.6867m corridor fixture with exact Home/model/plan provenance unless compiler proves data-only change needed and Contractor records it. No speedup/parameter/authority/freshness relaxation. Generic AP4.7.1 internal quad, not Hera calibration; synthetic camera/gimbal/imagery, ACK not exposure.

## Clock repair

Reproduce deferred-await/old epoch/config/overlapping periodic-reactive calibration races in mocks before repair. Keep5 probes, same-boot and20ms accepted probe bounds, validity60000ms, server future20ms/stale1000ms, encoded age750ms, reactive cap2 and queue/credit caps. Add bounded per-probe/rejection/epoch/visibility diagnostics, no secrets. Old callbacks cannot update or stop a new session. Prefer captured immutable session and one calibration flight per config, cancellation/post-await epoch checks.

Explicit L2 lifecycle policy allowed if tests justify it: a failed periodic renewal at30s must not discard an otherwise valid existing clock mapping. Keep its original expiry unchanged; allow at most one additional calibration batch at45s, then stop no later than original60s expiry if renewal never succeeds. Every probe/failure/degraded interval is recorded. Initial calibration still requires a valid probe. Unknown/expired mapping frames never accepted or reported fresh. This is bounded renewal of valid clock evidence, not chunk/flight retry, not expiry extension or automatic source restart. Reactive freshness recovery cap2 remains. Mock exact expiry, cancellation, all-five rejection and exhausted renewal. If evidence suggests another cause, record it and repair only supported mechanism.

## UI/harness repair

Avoid stale coordinates: stable, fully visible action area independent of checklist/diagnostic height; clear semantic accessible labels; phase-aware enabled state, no preflight/AUTO chaining bypass. Protect video canvas and controls from overlap. Build a QA harness with current screenshot/semantic target identification and receipt acknowledgment before advancing; reject uncertain/duplicate dispatch. No UIAutomator stall during armed freshness windows; inspect its behavior on ground only or use verified fixed action geometry plus fresh screenshot and actual receipt. No OCR/model build during flight. Stage all scripts and payload before arm, late explicit60s lease. Foreground browser source must be visibly monitored, never inferred continuous from one screenshot.

## Acceptance

1. Mocks reject old epoch/config callbacks, invalid boot/timestamps/expiry/recovery overflow, and UI action selection after expanded checklist/profile. Frozen authority/mission/lease contracts pass. Independent source/pins/cap/baseline gate before runtime.
2. Android unchanged APK, survey/preflight/Fly/review/persistence; stable visible control geometry in relevant states. Host source only, receiver-only continuous decode. No lifecycle auto-rights/reconnect.
3. New actual nominal run: canonical upload/readback/Home/arm/AUTO/navigation/RTL/ground-disarm raw acceptance; 30s measured video≥24FPS, P95upper≤300ms, start→fresh≤1500ms. Qualified synthetic capture and gimbal mock readback inside window while actual AUTO/armed/height>5 with fresh telemetry. In-window500ms relay interruption recovery≤2000ms. Report exact sampled overlap; no whole-window airborne/real camera claim.
4. Separate actual fault run: live unexpired exact lease, airborne AP reboot via UI; durable revocation before effect, actual owned AP process PID/start-time change and raw causal receipts, zero automatic rights restore, rejection of old context/token checked distinctly. Frozen fault policy closes without reconnect, so a new MAVLink boot/session observation is NOT_CHECKED and must not be inferred from the process restart. Video continuing never proves C2. Preserve/restart records without restoring authority.
5. Independent raw/media/overlap/lease replay; protected hashes0diff; clean closure. Required unrun scenario NOT_CHECKED/NOT READY.

## Resource and stop

20GiB hard floor,31 admission samples≥29GiB/no>256MiBdecline;250ms runtime guard28GiB/15s forecast20GiB. New task evidence≤96MiB plus bounded AP append; preserve original aggregate quotas. No downloads/install/build/signing; source-stage and own QA cache cleanup only, no evidence deletion. Capture admission refusal samples in new evidence, no lost diagnostics. Host/helper admission before listener/emulator start where possible to avoid wasting sessions. No automatic HTTP control/campaign retry. Contractor may make bounded new admission observation after documented changed disk condition before launch intent, never erase a refusal. Stop repeated investigation without new evidence. Baseline LLM not applicable to deterministic transport repair; disclose no equal-condition topology benchmark.
