# G4 native/controller handover

SOURCE/MOCK preparation only under TIP-INTEGRATED-RUNTIME04 and Root's final cadence decision. No actual host, AP, emulator, browser, Android input or listener was run. Existing G3 and G4 corrective runtime/readiness sources are immutable. The new UI fork changes only diagnostic observation interval500ms/nonforced throttle400ms; normalized comparison with G3 passes. Bootstrap SHA256 def14e57a081e5aa88274b8022488d39a399cddd6eb7921ee74458934c12f951 and UI observer remain byte-exact G3/G2 reuse, with unchanged G2 lifecycle and CLOCKVIDEO05 observation wire formats.

After final independent gate and pins, Root starts ONE persistent process:

```sh
python3 -B planning/beta06g4/qa-root-controller.py --serve 06
```

Keep stdin and this process alive. One JSON object per line, maximum8192bytes including newline. Every effectful command requires `rootApproved:true` and unique lowercase `commandId`. Never resend uncertain input or replace/restart this controller around a live run. `status` is read-only. Start commands:

```json
{"op":"start-host","rootApproved":true,"commandId":"g4-host-start","sourceAndViewerStoppedAndInspected":true}
{"op":"launch-emulator","rootApproved":true,"commandId":"g4-boot06"}
{"op":"status"}
{"op":"setup","rootApproved":true,"commandId":"g4-setup06"}
{"op":"start","rootApproved":true,"commandId":"g4-native-start06","variant":"initial"}
{"op":"store-before","rootApproved":true,"commandId":"g4-store-before-n1","variant":"n1"}
```

Wait for actual android-launch06 before setup. The original Python2700s window is sampled before host Popen and spans both allowed hosts, boots06/07 and all four AP requests. Child permit uses this same absolute host deadline, so permit delay cannot add time; emulator also has a2700s engineering cap beginning before permit. New host CLI uses `pilot/beta06g4/app.mjs`, `generation04/host-app04` then `host-app04-restart`, and `generation04/workspace02`. Ports8872/8873/5972 and owned emulator5582 are unchanged. New profile beta06g4-native-arm64-exec-4.7.1 still uses immutable .local/beta06g3/arducopter0755, same exact SHA/image, AP540s and all flight clocks/thresholds. No install/clear/quota reset.

Each native store snapshot compares current file hashes and journal prefix against the closed G3 final receipt `evidence/beta06/generation03/android-store-after-failed-launch-04.json`. G3 baseline is34records/19files/13PENDING; lifetime picker limit16 leaves3. The current snapshot governs any later appends. Collect each store-after with a matching beforeReceipt and unique variant while min(host,emulator)≥90s; old native artifacts must remain unchanged. Prior SAF/process/coldboot results remain historical, not new flight proof. Optional remaining3SAF operations may cover N1 raw, one fault raw and linked capture. Wrong-SHA diagnostic consumes0 and requires a visible current target, actual callback and independent unchanged PENDING/artifact count. Picker input alone is only a handoff; actual provider bytes/callback/native journal remain required.

Before EACH Connect Root stages publisher/viewer visibly, including explicit VP8-720P30-V1 RGB synthetic configuration, and measures current native frame from screenshot/window data. Collect a NEW75s ground interval using the CURRENT host media/clock-events.jsonl, with two successful30s renewals per role under original20ms/60000ms bounds:

```json
{"op":"ground-soak","rootApproved":true,"commandId":"g4-ground-n1","clockJournal":"ABSOLUTE_GENERATION04_CURRENT_HOST_MEDIA_CLOCK_EVENTS_JSONL"}
{"op":"prepare","rootApproved":true,"commandId":"g4-connect-prep-n1","name":"g4-connect-n1","nativeFrame":[0,24,1280,740]}
{"op":"action","rootApproved":true,"commandId":"g4-connect-n1","target":"field-connect","reference":"ABSOLUTE_CURRENT_G4_REFERENCE","groundStagedAndInspected":true,"timeout":100}
```

Frame numbers are examples only; replace with actual measured geometry and inspect the screenshot. Connect consumes its ground admission once, uses exactly100s receipt timeout and samples the AP anchor before its single tap. Current foreground/freshness/geometry/model/client/run/boot/config all remain mandatory. No UIAutomator, hidden browser execution or control POST by Root. Fresh refs are required after context changes.

Ground failure now preserves the actual bounded HTTP response prefix SHA/count, response status, request elapsed time, actual finite age and redacted parsed body in the failure receipt, without an extra HTTP request. Bound64KiB; malformed/truncated bodies keep SHA/count only to prevent credential leakage, explicitly labeled as such. Nonfinite/bool/nonnumeric age remains invalid and diagnostic age is null. The1200ms guard is unchanged. Normal source publication was1000/900ms, leaving about200ms scheduling/network margin. The new diagnostic500/400ms cadence increases that nominal margin to about700ms, keeps one publication in flight, and does not refresh telemetry/cache or prove the G3 initiating cause.

Root may explicitly authorize at most ONE additional read-only75s interval after inspecting a concrete first failure and performing an explicit recovery, before ANY AP request. No automatic reconfiguration/retry:

```json
{"op":"authorize-ground-recovery","rootApproved":true,"commandId":"g4-ground-explicit-recovery","rootInspectedRawGroundFailure":true,"diagnosis":"CONCRETE_DIAGNOSIS_FROM_RETAINED_FAILURE","explicitRecovery":"ROOT_OBSERVED_EXPLICIT_RECOVERY"}
```

Then use a new `ground-soak` commandId. Failed intervals never count as admission. A second failure, or ground failure after any AP request, ends later AP progression. No new campaign or controller restart is permitted.

Finite request order is N1 nominal, F1 cut, managed host/native process restart, N2 nominal, F2 reboot, maximum4. Fifth is refused before allocation. Failed/uncertain action/preparation/airborne sequence latches campaignFailed and prevents another Connect. Root independently inspects canonical accepted N1 raw replay before F1, and N2 raw replay before F2. UI ACK/Close and generic closed review are insufficient. `airborne` requires current inspected flight/payload references and enforces scenario ordinal, exact late lease, preflight/readback, AP225s/HOST240s/EMU240s reserves and original Home>1800ms. Nominal source/viewer stays active through actual completion/ground/disarm. `complete-nominal` performs read-only waits then Close only after frozen completion policy. Faults use no additional measure/pause/capture; require fresh AUTO/exact lease≥5s, durable invalidation, incomplete UNKNOWN, zero authority restoration and a separately correlated old-context negative.

Read-only replay commands use NEW exclusive generation04/qa-*.json names:

```sh
node planning/beta06g4/qa-raw-flight.mjs RUN evidence/beta06/generation04/qa-n1-raw01.json CURRENT_PAYLOAD_WAL
node planning/beta06g4/qa-cut-replay.mjs RUN CURRENT_PAYLOAD_WAL evidence/beta06/generation04/qa-f1-cut01.json
node planning/beta06g4/qa-reboot-replay.mjs RUN CURRENT_PAYLOAD_WAL evidence/beta06/generation04/qa-f2-reboot01.json
python3 -B planning/beta06g4/qa-media-replay.py CURRENT_REPORT evidence/beta06/generation04/qa-n1-media01.json
node planning/beta06g4/qa-overlap-replay.mjs evidence/beta06/generation04/host-app04 report-01.json evidence/beta06/generation04/qa-n1-overlap01.json
```

RUN is the actual s+20hex run; use actual report/WAL paths. Shared canonical CRC/mission verifier is unchanged; copied arithmetic replayers are reused calculations, not newly independent implementations. Do not pool historical generations.

Only after accepted actual N1 and deliberate closed F1 replays, Root explicitly authorizes the single managed restart, stops source/viewer on ground, verifies zero run/authority/leases, clean host closure, starts host2 and explicitly restarts native process for a fresh document:

```json
{"op":"authorize-managed-restart","rootApproved":true,"commandId":"g4-restart-proof","rootInspectedActualReplay":true,"nominalReplay":"ABSOLUTE_G4_N1_RAW_QA_REPORT","faultReplay":"ABSOLUTE_G4_F1_CUT_QA_REPORT"}
{"op":"stop-host","rootApproved":true,"commandId":"g4-host-stop-one","sourceAndViewerStoppedAndInspected":true}
{"op":"start-host","rootApproved":true,"commandId":"g4-host-start-two","sourceAndViewerStoppedAndInspected":true}
{"op":"start","rootApproved":true,"commandId":"g4-native-after-host","variant":"after-host"}
```

Same original2700s deadline/workspace/counters persists. Reload publisher visibly to the new server boot; renew references and75s admission before N2/F2. Replays bind exact current G4 raw/request/review/closure/WAL hashes and same canonical model/plan. Optional boot07 requires actual boot06 closure and host≥240s; it is persistence-only and rejects Connect/preflight/grant/upload/ARM/AUTO/fault even through batch paths. EOF closes the owned host and requests/waits owned emulator closure; retained AP containers remain exact-CID Flight closure responsibility.

Request-budget arithmetic is SOURCE inference, not measured performance:500ms publication uses2requests ×2Hz=4/s;1Hz state refresh plus750ms lifecycle heartbeat totals about6.333/s,11400 per30min host media lifetime. Existing20000 per-host application request cap leaves about8600 for Root reads, forced/event publications, assets and controls. Those extras are not automatically bounded by the periodic rate, so this is not a universal full30min success guarantee. No request cap, counter, clock, heartbeat, state-refresh cadence or media quota was changed. The one45min campaign still requires managed host restart; both host instances retain original media30min limits.

Builder receipts total89 distinct passing mock groups: native-tests03(17), host-window01(10), restart-proof01(13), airborne-tests01(5), ground01(18), emitter-contract02(5), ground-diagnostics02(13), cadence02(8). Earlier same-group receipts are preserved point-in-time and not added to this count. Actual emitted UI payload passed authenticated G4 POST/GET and same-output Python ground consumer in the cadence test. All checks are SOURCE/MOCK, not actual Android/AP/media/75s acceptance. Actual required gates remain NOT_CHECKED until Root runs them. No scratch project, dependency install or external venv was created; tiny temporary fixture directories are removed automatically. Explicitly classified ground journals and in-process handler receipts remain as bounded test evidence.
