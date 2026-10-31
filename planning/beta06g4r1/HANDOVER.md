# G4 recheck01 harness

Only12 necessary Python helpers were adapted from frozen G4. Production G4 app/runtime/readiness/profile/UI/bootstrap, all653pins and G4 flight replayers remain unchanged. Evidence still uses generation04, workspace02 and global G4 maximum4 AP requests. This is a test-harness recheck after the prior browser-blocked0AP session closed, not a new application generation or permission to retry a failed flight.

After the independent recheck gate, Root starts ONE fresh persistent process:

```sh
python3 -B planning/beta06g4r1/qa-root-controller.py --serve 08
```

Original2700s Python window spans both allowed hosts, boots08/09 and N1/F1/N2/F2. No clock import or restart around a live run. Boot09 is persistence-only. AP540s/225s reserve, host+emulator240s reserve and native90s collection reserve remain unchanged. Unique outputs are host-app04-recheck01 and host-app04-recheck01-restart, g4r1-host-console1/2, g4r1-qa-adb-commands.jsonl, and attempt08/09 receipts. Use g4r1 prefixes in every Root commandId, prepare name and replay output to avoid old evidence collisions. All effectful commands require rootApproved:true and unique commandId; max8192bytes per JSON line; no uncertain input retry.

Initial commands, after actual IAB permission has already been probed:

```json
{"op":"start-host","rootApproved":true,"commandId":"g4r1-host-one","sourceAndViewerStoppedAndInspected":true}
{"op":"launch-emulator","rootApproved":true,"commandId":"g4r1-boot08"}
{"op":"status"}
{"op":"setup","rootApproved":true,"commandId":"g4r1-setup08"}
{"op":"start","rootApproved":true,"commandId":"g4r1-native-start","variant":"initial"}
{"op":"store-before","rootApproved":true,"commandId":"g4r1-before-n1","variant":"n1"}
```

Wait for actual owned android-launch08 plus device online/bootcomplete before setup. The first host writer rehashes the exact17files/798359bytes closed workspace02 against workspace-baseline01.json, rejects any drift/symlink, and emits the proof before Popen. Every native snapshot compares old artifact hashes/journal prefix against the closed G4 android-store-after-browser-pending-06.json; actual baseline remains34records/19files/13PENDING,3picker operations left. No install/clear/quota reset. Collect matching store-after early while remaining≥90s. Prior G4 elapsedRealtime is not globally ordered across boots.

Stage IAB publisher from outset with VP8-720P30-V1 RGB synthetic, keep viewer current/foreground, inspect current native frame geometry. Before EACH Connect, actual75s interval using the current host-app04-recheck01/media/clock-events.jsonl or restart equivalent, with original two renewals per role and20ms/60000ms limits. No automatic restaging/retry. The unchanged helper retains bounded/redacted stale HTTP failure evidence and permits at most ONE explicitly diagnosed read-only recovery before any AP. Use originalG4 command authorize-ground-recovery only after inspecting the first failure. Second failure or failure after AP ends progression.

```json
{"op":"ground-soak","rootApproved":true,"commandId":"g4r1-ground-n1","clockJournal":"ABSOLUTE_CURRENT_RECHECK_HOST_MEDIA_CLOCK_EVENTS_JSONL"}
{"op":"prepare","rootApproved":true,"commandId":"g4r1-connect-prep","name":"g4r1-connect-n1","nativeFrame":[0,24,1280,740]}
{"op":"action","rootApproved":true,"commandId":"g4r1-connect-n1","target":"field-connect","reference":"ABSOLUTE_INSPECTED_CURRENT_REFERENCE","groundStagedAndInspected":true,"timeout":100}
```

Frame numbers are examples only; measure actual geometry and inspect screenshot. Connect consumes the interval once and samples AP anchor before its single tap. Product freshness and config/model/client/document/run/boot fences remain unchanged. Root uses actual visible CUA/authorized ADB controls only, no hiddenJS/eval/controlPOST/UIAutomator.

Efficient postConnect choreography, all screenshots inspected before dependent taps:

1. Prepare new flight reference after the actual run/boot appears. Explicit sequence: field-preflight(timeout100), field-grant, field-upload, field-tab-payload using that flight reference.
2. Prepare payload discovery reference, tap field-discover. Discovery updates selected device/options, so prepare a fresh payload reference, inspect it, then field-select. Keep intended mock RGB selected.
3. Prepare FINAL payload reference after select. Tap field-tab-flight using it; prepare/inspect FINAL flight reference with dock/video controls. Tap field-tab-payload using final flight reference. Both final references now share current run/boot/config/model/client and measured geometry.
4. While on payload, submit late payload grant and airborne as ONE explicit bounded sequence, with airborne last:

```json
{"op":"sequence","rootApproved":true,"commandId":"g4r1-n1-latelease-airborne","steps":[{"target":"field-pgrant","reference":"FINAL_PAYLOAD_REFERENCE"},{"kind":"airborne","scenario":"nominal","flightReference":"FINAL_FLIGHT_REFERENCE","payloadReference":"FINAL_PAYLOAD_REFERENCE"}]}
```

Airborne reads current state after late grant and performs read-only replay of existing AP admission, not another31second wait. Lease must have≥40s at entry; each real gimbal/fault tap separately checks exact live lease≥5s. It refreshes preflight, checks reserves, ARM and Home→AUTO without a Root tool gap, then fresh actualAUTO/armed/height>5 and nominal measure/capture/pause/gimbal. Fault scenarios cut/reboot omit extra media/capture/report quotas. Complete-nominal allows Close only after actual canonical navigation/RTL/ground/disarm. Source/viewer remain active through nominal ground/disarm. Reach preARM with≥225s AP remaining, meaning elapsed≤315s since Connect tap; UI preparation cannot reset this clock.

Use unchanged G4 replayers directly with exclusive generation04/g4r1-qa-*.json names, for example:

```sh
node planning/beta06g4/qa-raw-flight.mjs RUN evidence/beta06/generation04/g4r1-qa-n1-raw01.json CURRENT_PAYLOAD_WAL
node planning/beta06g4/qa-cut-replay.mjs RUN CURRENT_PAYLOAD_WAL evidence/beta06/generation04/g4r1-qa-f1-cut01.json
node planning/beta06g4/qa-reboot-replay.mjs RUN CURRENT_PAYLOAD_WAL evidence/beta06/generation04/g4r1-qa-f2-reboot01.json
python3 -B planning/beta06g4/qa-media-replay.py CURRENT_REPORT evidence/beta06/generation04/g4r1-qa-n1-media01.json
```

Native/media helper copies in the harness are explicitly frozen but production flight replayers stay direct G4 reuse. Canonical CRC/mission algorithms are shared, not independently reimplemented. Root requires independent raw nominal PASS before F1/F2. Only exact actual acceptedN1+deliberateclosedF1 replays permit authorize-managed-restart, followed by stopped source/viewer, idle/zeroauthority/zero leases, clean stop-host/start-host and explicit native start variant after-host. Same window/counters/workspace persist; reload publisher visibly for the new server boot and refresh references/75s interval. Any failed/uncertain input/scenario stops later AP requests. EOF closes owned host and requests/waits owned emulator closure; exact-CID retained AP closure remains Root/Flight responsibility.

Builder verification: generation04/g4r1-builder-harness-tests02.json PASS8checks, with frozen recipes run in-memory against this harness (17controller/profile/native,10host-window,5airborne,18ground groups). The normalized source check enumerates all12 helper differences; the only added behavior is the explicitly required before-first-writer workspace hash fence. Failed test-receipt01 is retained as point-in-time test infrastructure output, not actual runtime. All classification SOURCE/MOCK; no Builder AP/ADB/browser/listener occurred. Tiny airborne test fixtures are removed automatically; labeled bounded ground mock journals remain evidence. No dependency install, external venv or project copy was created.
