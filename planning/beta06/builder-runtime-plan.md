# BETA06 Root controller and Android QA plan

Builder preparation only. No emulator, ADB, SITL, APK build or actual user input was executed by the Builder. Existing development02 APK, API33 four-core/2GiB receiver-only topology, ports8872/8873/5972 are unchanged. Nominal/fault claims require Root's actual runs and independent raw replays.

## Persistent Root process

Run one explicit controller per approved coldboot, in a PTY that remains open:

```sh
python3 -B planning/beta06/qa-root-controller.py --serve 01
```

Commands are one JSON object per stdin line. All action commands require `rootApproved:true` and unique lowercase `commandId`. An uncertain/rejected action terminates that command and any nested sequence immediately. Do not send queued command lines that assume previous success. No automatic reconnect, grant, retry, publisher start or anchor restoration. A new controller process starts without anchors and cannot ARM an existing AP run.

Examples (paths must be actual Root-inspected reference paths):

```json
{"op":"launch-emulator","rootApproved":true,"commandId":"boot01"}
{"op":"status"}
{"op":"setup","rootApproved":true,"commandId":"setup01"}
{"op":"start","rootApproved":true,"commandId":"start01"}
{"op":"store-before","rootApproved":true,"commandId":"n1-before","variant":"n1"}
{"op":"prepare","rootApproved":true,"commandId":"ground-ref01","name":"ground-ref01","nativeFrame":[0,24,1280,740]}
{"op":"action","rootApproved":true,"commandId":"n1-connect","target":"field-connect","reference":"ACTUAL_REFERENCE_PATH","groundStagedAndInspected":true}
```

The example native frame is historical, not a current assertion. Root must reprove the WebView frame on the ground from current PNG/native window/UIA if necessary; UIAutomator is forbidden during flight. The UI helper rejects changed viewport, scale, insets, window generation, document, client/epoch/instance, run/boot, model/plan or config. Fresh challenge-based observations stay≤1200ms. Root inspects actual screenshots before referencing targets.

Launch uses a child resource controller for31 stable samples≥30s,≥29GiB, peak decline≤256MiB. Only after that child reports ready does the persistent parent sample its own Python monotonic emulator anchor, fsync the proof, and issue a one-time launch permit. Child validates actual parent PID and watches parent liveness; EOF/parent death requests/stops only its owned emulator. One30min budget, guard28GiB/250ms/15s forecast, floor20GiB, evidence stop200MiB+56MiB closure. A refused admission creates no emulator anchor or launch. No old UTC/Node timestamp is converted into a Python anchor.

Stage and inspect host source/browser publisher/Android viewer/config and both tab references before Connect. Media body quota remains128MiB per host and never resets: Root may explicitly stop producer/viewer during long AP sensor warmup, retaining config only if actual readonly state does so, then explicitly start source/viewer again and inspect new-config references before ARM. A config in Connect staging does not assert live/fresh video; do not use inactive video as a measurement. Read actual media bytesRead budget before the second scenario. The persistent parent's Connect callback anchors immediately before the one physical tap, not before a later API poll. It records one returned input and binds the actual new SITL run only after exact ACK. Every ARM runs the225s AP/240s emulator reserve guard immediately before its one tap, using the same parent process and actual host boot. AP540s is conservatively measured from before Connect/admission. Reserves are engineering allowances, not certified mission durations.

## Tight explicit chains

`sequence` accepts1..12 explicitly supplied steps, stops at first failure, and derives unique per-step IDs. `kind:airborne` may occur only as the last step. Each action still requires Root-inspected corresponding tab reference and current exact context; bounded readiness wait≤2s is read-only, never a second input.

```json
{"op":"sequence","rootApproved":true,"commandId":"n1-late","steps":[{"target":"field-preflight","reference":"FLIGHT_REF","timeout":100},{"target":"field-grant","reference":"FLIGHT_REF"},{"target":"field-upload","reference":"FLIGHT_REF"},{"target":"field-tab-payload","reference":"FLIGHT_REF"},{"target":"field-discover","reference":"PAYLOAD_REF"},{"target":"field-select","reference":"PAYLOAD_REF"},{"target":"field-pgrant","reference":"PAYLOAD_REF"},{"kind":"airborne","flightReference":"FLIGHT_REF","payloadReference":"PAYLOAD_REF","scenario":"nominal"}]}
```

This is an example workflow, not proof that those references or selection are current. Root verifies expected selected station/device and the actual source config. Ground sensor discovery/preflight may take up to90s; prefer that slow check before publisher/late lease, then quick preflight refresh in tight chain. Already ACKed grant/upload must not be repeated silently. `airborne` performs fresh preflight, ARM, Home gate>1800ms, AUTO, fresh actual AUTO/armed/height>5, video measure/capture/pause500 and synthetic gimbal. It requires exact selected payload lease≥40s initially and≥5s at capture/gimbal/fault. `scenario:cut` or `reboot` explicitly adds the respective one visible fault after gimbal. Actual fault acceptance additionally needs raw PID/socket/revocation receipts and independent replay.

Nominal closure is separate explicit `complete-nominal` with exact run and flight reference, bounded≤180s read-only wait. Only fresh completed navigation/RTL/near-Home/ground/disarm can cause the one Close tap; no emergency/disarm/land command is generated. A failed/timed-out wait remains incomplete. Save video measurement through the visible Save control when its actual30s window completes; receiver raw replay remains independent.

After every N1/F1/N2/F2, collect store-after immediately while≥90s emulator reserve remains, not near shutdown. Explicit app restart uses `start` variant only after no active run/leases. Boot02 has its own new controller, new anchor, and new store-before. Old before receipts may be supplied as `beforeReceipt` for crossboot prefix proof, with no imported timing anchors. At most2 Connect intents per coldboot,4 new AP attempts total, no retries.

## Native store and SAF

Every before/after snapshot records actual guest `/proc/sys/kernel/random/boot_id`, owned emulator PID/attempt, exact native journal and artifacts SHA. Journal body hashes, sequence and previous-head are checked across all history. Historical elapsedRealtime may reset across coldboots; ordering is checked only within same known-boot appended segment. Crossboot append retains prefix proof and explicitly makes no global elapsed ordering claim. Native source/APK unchanged, no data clearing, no authority/viewer auto-restore.

Before pickers, `quota_decision(actualSnapshot,6)` must pass. Native lifetime quota is16 PICKER_PENDING entries, including cancellation and past restarts; last historical baseline had10, leaving6, but fresh snapshot is authoritative. Proposed six actual operations: workspace export, import exact exported workspace, nominal raw, fault raw, linked capture, cancelled export. Each export success requires actual picker, provider readback SHA, native EXPORTED_READBACK_VERIFIED and independent receiver exact bytes. Import requires actual picker, schema/SHA/CAS/model/readback verification and fresh mirror; no authority restoration.

One visible Review `field-qa-bad-sha` diagnostic reuses the most recent actual export URL/name and flips one expected digest hex. `native-negative` dispatches it once on ground, then requires a new real native callback `ok:false`, code OPERATION_NOT_CONFIRMED, message SHA256_MISMATCH. This rejection occurs before native PICKER_PENDING, consuming zero operation slots. Generic UI ACK is not native rejection. Root must compare native counts/artifacts/workspace before and after; callback alone is not provider proof. No invented HTTP response or hidden custom URI dispatch. Cancel uses one remaining actual picker and must retain original files/stage, report CANCELLED, never EXPORTED_READBACK_VERIFIED.

For SAF use explicit `native-picker` with `target`, actual inspected `reference` and unique commandId. This returns ONE_NATIVE_HANDOFF_INPUT_NOT_COMPLETED after one visible input, not flight ACK or provider success. It is ground/no run/no authority only, validated again immediately before input. The external picker legitimately backgrounds WebView and changes client epoch on return; flight receipt correlation remains strict and is not used to certify SAF success. Only Root interacts with the actual Android Documents picker. Choose unique destination names, retain all provider files, no deletion or overwrites. Export success dialogs are not independent integrity evidence: obtain exact exported bytes/readback and receiver verification. If quota, storage, picker or lifecycle gates fail, record NOT_CHECKED/NOT_READY rather than resetting native data or signing a new APK.

## Budget and limitations

Two coldboots and two listening hosts maximum,30min each; four actual AP requests total; no fifth. Evidence256MiB, early stop200MiB. Existing APK unchanged; no downloads/install/build/OCR. Per-scenario before/after and final closure required. Builder mock PASS is preparation only; Root's actual Android/AP/SAF/provider checks remain unrun until recorded. Explicit old-context probe needs new human-inspected reference after fault; never reuse the old-run geometry reference or restore a bearer token.

## Exact reference and restart choreography

1. Open the flight panel on the ground, actual publisher/viewer config present; prepare and inspect a flight reference. Click `field-tab-payload` using that flight reference, prepare/inspect payload reference, then `field-tab-flight` using payload reference. Both references must share current document/client/config/viewport/model/plan and actual phase/run/boot. Nothing in the controller can repair an old-config reference silently.
2. Connect exactly once through the persistent controller and that pre-connect flight reference. It binds the actual new run only after exact ACK. All pre-connect references have run=null and are now unusable for flight actions. If video is explicitly stopped for sensor warmup, no claim of active/fresh video is made.
3. After AP sensor readiness and explicit source/viewer restart, obtain fresh run-specific, current-config flight and payload references in the same visible tab-switch order. Root inspects all critical targets in both screenshots before late grants. If config/client/document/boot changes again, stop and prepare new references, never relabel an old one.
4. If current tab is payload, first step in the tight sequence must be `field-tab-flight` with the inspected payload reference. Then flight preflight/grant/upload use the flight reference; `field-tab-payload` uses flight reference; discover/select/payload grant use payload reference. Optional final airborne step first navigates back to flight using payload reference, then refreshes preflight/ARM/Home/AUTO. Root verifies the actual selected station/device, not a default name.
5. After nominal close and source/viewer stop, collect `store-after` variant matching that scenario's earlier `store-before`. `start` with a unique variant is an explicit native process restart only when no run, flight authority or payload lease exists. Inspect restored mission/model/plan/captures/reviews and zero authority; obtain new-document references. Do not reconnect automatically.
6. Boot02 uses `--serve 02`, its own launch intent/permit/anchors, and snapshots whose guestBootId is read again. To prove crossboot preservation, supply the actual prior snapshot path as `beforeReceipt` on an after snapshot; every old artifact and journal prefix must remain exact, while elapsedRealtime ordering across old/new guest boots is explicitly not asserted.

SAF buttons: Review `field-export-workspace`, `field-import-workspace`, `field-raw-<actualRun>`, `field-capture-export-<actualCaptureId>-<12hexOriginalSHA>`. `field-delivery-<run>` creates a delivery set through a normal UI receipt; any resulting `field-delivery-file-<run>-<sanitizedName>` link uses native-picker handoff only if actual fully visible/unoccluded and at least44px. Smaller/hidden links are refused, never clipped-tapped. Root may use the capture package to meet the linked-capture requirement without inventing a delivery-file result. Choose actual provider destinations and cancel in Documents UI manually; no automatic picker path selection, overwrite or deletion is implemented.
