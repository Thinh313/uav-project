# G3 native/controller handover

Prepared only under TIP-RUNTIME03. No actual host, emulator, AP, Docker, Android input, install, clear, build or listener was started by this Builder. The 67 passing mock groups verify helper behavior, not actual beta acceptance. Read-only replay calculations are adapted from G2 and retain the shared canonical CRC/mission verifier; these adaptations are not a new independent implementation.

New modules are `qa-root-controller.py`, `qa-runtime.py`, `qa-deadline-guard.py`, `qa-android.py`, `qa-device-actions.py`, `qa-ui.py`, `qa-ground-soak.py`, `qa-airborne.py`, `qa-ap-admission.py`, `qa-restart-proof.py`, and the native/media/raw-flight/cut/reboot/overlap replay helpers in this directory. Existing G1/G2 and preexisting G3 offline files are untouched. Under Root L2 integration approval, new pilot/beta06g3/{bootstrap.js,ui.mjs,ui-observation.mjs} are byte-exact G2 reuse; the served bootstrap SHA256 is def14e57a081e5aa88274b8022488d39a399cddd6eb7921ee74458934c12f951. The lifecycle wire format intentionally remains aeris-beta06g2-lifecycle-diagnostic/1 and the observation format remains clockvideo05-ui-observation-v1. Actual emitted VM snapshot, G3 route validator/observer and Python ground consumer contract pass with the same emitted snapshot. These are mock contract checks, not actual browser or native acceptance.

Start only after cooperation QA, source/pins freeze and Root's actual preflight:

```sh
python3 planning/beta06g3/qa-root-controller.py --serve 04
```

Keep this Python process and stdin alive throughout. One JSON command per line, maximum8192 bytes including newline, unique `commandId`, `rootApproved:true` for every effectful command. `status` is read-only. Never start a replacement controller around a live run or import old anchors. Initial commands:

```json
{"op":"start-host","rootApproved":true,"commandId":"g3-host-start","sourceAndViewerStoppedAndInspected":true}
{"op":"launch-emulator","rootApproved":true,"commandId":"g3-boot04"}
{"op":"status"}
{"op":"setup","rootApproved":true,"commandId":"g3-setup04"}
{"op":"start","rootApproved":true,"commandId":"g3-native-start04","variant":"initial"}
{"op":"store-before","rootApproved":true,"commandId":"g3-store-before-n1","variant":"n1"}
```

Wait for actual owned android-launch04 proof before setup. `setup` verifies unchanged installed APK df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d and owned emulator5582. It never installs. `start` restarts only this package, preserving native data. The snapshot requires retained native minimum34records/19files/13PENDING and maximum16PENDING. Actual snapshot governs remaining picker operations.

Root stages source/viewer/config visibly, measures current native viewport using screenshot/window data, then collects a new75s ground interval before EACH Connect. The clockJournal is the CURRENT host-app03/media/clock-events.jsonl or host-app03-restart/media/clock-events.jsonl, under evidence/beta06/generation03, passed as an absolute path. Two successful30s periodic renewals per role and unchanged20ms/60000ms bounds remain required.

```json
{"op":"ground-soak","rootApproved":true,"commandId":"g3-ground-n1","clockJournal":"ABSOLUTE_CURRENT_MEDIA_CLOCK_JOURNAL"}
{"op":"prepare","rootApproved":true,"commandId":"g3-connect-prep-n1","name":"g3-connect-n1","nativeFrame":[0,24,1280,740]}
{"op":"action","rootApproved":true,"commandId":"g3-connect-n1","target":"field-connect","reference":"ABSOLUTE_G3_CONNECT_REFERENCE","groundStagedAndInspected":true,"timeout":100}
```

Frame values are EXAMPLES ONLY. Root must replace them with actual measured geometry and inspect the resulting screenshot. Connect requires100s receipt timeout to include31sample AP admission plus launch, consumes the ground admission once and samples the AP anchor before its sole tap. No retries. Four new request ordinals map to N1 nominal, F1 cut, N2 nominal, F2 reboot. First two are constrained to hostinstance1; the second pair requires managed hostinstance2. Failed/uncertain input or scenario blocks later AP requests. Root must inspect a fresh independent raw nominal PASS before proceeding from N1 to F1 or N2 to F2; a UI Close ACK or generic closed review is insufficient. Unknown or failed raw replay ends the campaign without another request.

Use current visible preflight/grant/upload/discover/select controls and inspect both flight/payload references at the same config/model/client/run/boot. Grant late payload lease then invoke `airborne` with scenario `nominal`, `cut`, or `reboot`; the controller enforces N1/F1/N2/F2. Reserve remains AP225s, host240s, emulator240s immediately before ARM; original Home>1800ms, freshness, heartbeat and lease policies are unchanged. Fault choreography has no second measure/pause/capture. Root keeps source/viewer active through nominal ground/disarm. `complete-nominal` waits read-only and can Close only after the frozen complete/ground/disarm policy passes.

Run the new read-only replayers with new exclusive `generation03/qa-*.json` output names. Examples (all paths repository-relative):

```sh
node planning/beta06g3/qa-raw-flight.mjs RUN evidence/beta06/generation03/qa-n1-raw01.json CURRENT_PAYLOAD_WAL
node planning/beta06g3/qa-cut-replay.mjs RUN CURRENT_PAYLOAD_WAL evidence/beta06/generation03/qa-f1-cut01.json
node planning/beta06g3/qa-reboot-replay.mjs RUN CURRENT_PAYLOAD_WAL evidence/beta06/generation03/qa-f2-reboot01.json
python3 planning/beta06g3/qa-media-replay.py CURRENT_REPORT evidence/beta06/generation03/qa-n1-media01.json
node planning/beta06g3/qa-overlap-replay.mjs evidence/beta06/generation03/host-app03 report-01.json evidence/beta06/generation03/qa-n1-overlap01.json
```

`RUN` must be the actual s+20hex run. Each nominal must receive canonical accepted raw execution, report/overlap and media replay. Faults must show live exact lease≥5s, durable invalidation before effect, incomplete UNKNOWN, zero rights restore, and Root's separately correlated old-context refusal. UI ACK is not execution or native/provider acceptance.

Only after accepted N1 and deliberate closed F1 replays, Root inspects both and authorizes the single managed restart:

```json
{"op":"authorize-managed-restart","rootApproved":true,"commandId":"g3-restart-proof","rootInspectedActualReplay":true,"nominalReplay":"ABSOLUTE_G3_N1_RAW_QA_REPORT","faultReplay":"ABSOLUTE_G3_F1_CUT_QA_REPORT"}
{"op":"stop-host","rootApproved":true,"commandId":"g3-host-stop-one","sourceAndViewerStoppedAndInspected":true}
{"op":"start-host","rootApproved":true,"commandId":"g3-host-start-two","sourceAndViewerStoppedAndInspected":true}
{"op":"start","rootApproved":true,"commandId":"g3-native-after-host","variant":"after-host"}
```

Proof binds exact current G3 N1/F1 report/raw/request/review/closure/WAL bytes, canonical model/plan and chronology. Stop requires idle, zero leases/authority and inactive viewer plus Root's stopped publisher inspection; cleanup without proof does not authorize restart. Same Python host deadline, quota/counters and workspace persist. Reload publisher visibly, renew configuration and references and repeat75s gate before N2/F2.

Collect `store-after` early with `beforeReceipt` matching each scenario's before snapshot and unique variant; helper rejects collection when min(host,emulator)<90s. Optional remaining SAF is at most3picker operations (N1 raw, one fault raw, one linked capture); wrong-SHA diagnostic consumes0. Prior G2 workspace/export/import/cancel/process/coldboot results remain historical scoped PASS and need no repeat. Native picker command records a handoff only: Root must visibly complete/cancel provider and verify callbacks, native journal and exact provider bytes independently. No clear/install/quota reset. `native-negative` requires the actual visible bad-SHA target and native callback plus independent unchanged PENDING/artifact count; no hidden input.

Optional `stop-emulator`, followed by actual android-closure04 and `launch-persistence-emulator`, permits one boot05 only while original host≥240s. Boot05 is persistence-only and rejects all flight/AP paths, including sequence and airborne. It never resets the original host window. EOF/parent close terminates owned host and requests/waits owned emulator closure; retained AP containers remain Flight's exact-CID responsibility.

Verification receipts: generation03/builder-native-tests02.json16groups, builder-host-window02.json10, builder-restart-proof01.json13, builder-airborne-tests01.json5, builder-ground02.json18, builder-emitter-contract01.json5. Syntax checks passed for all new Python helpers and four MJS replayers. All classification is MOCK/BUILDER. Actual flight, Android, AP, media and native acceptance remain NOT_CHECKED until Root runs them. No scratch project/venv/dependency install was created. Temporary tiny airborne fixture directories were automatically removed after tests. Two tiny explicitly classified synthetic ground-journal fixtures remain under generation03 as evidence referenced by the ground mock receipts.
