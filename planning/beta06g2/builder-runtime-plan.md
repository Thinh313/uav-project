# BETA06 generation02: Root runtime plan

Prepared helpers only. No real Android, AP, browser publisher, host listener or SAF operation was executed by this Builder. Mock success is not beta acceptance. Use only the unchanged development APK, simulator host and owned emulator-5582. The decision in planning/beta06/DECISION-GENERATION02-BOUNDED-LIFECYCLE.md controls budgets.

## One qualified native-ARM profile, no pooled evidence

All four new N1/F1/N2/F2 requests must use **beta06-native-arm64-4.7.1** only. Exact cached binary is `evidence/sim32-instrument01/direct-uncorrected-source/arducopter`, SHA256 `1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41`, Linux aarch64, archived source4.7.1 commit `dbe792162d06cab66c3475fd5556bf7a120f119e`. Exact cached ARM image is `rtr-aeris-sim32-trace-builder@sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84`, explicit `--platform linux/arm64`, direct binary entrypoint, read-only exact binary mount and **AERIS_DIRECT_TRACE=0**. Root/QA must verify actual live image architecture, binary digest, profile, environment/entrypoint, process, resources and incoming firmware before ARM, in addition to exact new source-pins bytes and31sample AP admission. Never accept a release name alone.

This selects the archived observer-disabled binary with stock100pacer. Do not use the distinct f2be1f... pacer-v2 binary, old entry.sh/clockprobe, enabled observer or128MiB trace. CPU1/memory256MiB, internalquad/home/defaultparams, speedup1,540s deadline, clocks, mission/camera commands and every freshness/authority threshold stay unchanged. No download/build or rewriting runtime/sitl/arducopter. The retained old x86/amd64 generation01 request remains a separate failed-preparation profile, never nominal evidence for this one. Source normalization and exact ABI/SHA rejection are independent pre-runtime QA gates. No improved pacing,1x performance or calibrated Hera physics is claimed until measured.

## One controller, original deadlines

Start `python3 planning/beta06g2/qa-root-controller.py --serve 02` in one persistent Root PTY. Keep stdin open. Send one JSON object per line. Every effectful object needs `rootApproved:true` and a unique lowercase `commandId`; a failed sequence stops before its next input. Do not resend an input on an uncertain result. `status` is read-only. All anchors are sampled in this Python process before the relevant launch/input. A controller restart cannot restore anchors. EOF closes its own Node process and requests owned emulator closure.

Initial explicit commands:

```json
{"op":"start-host","rootApproved":true,"commandId":"g2-host-start","sourceAndViewerStoppedAndInspected":true}
{"op":"launch-emulator","rootApproved":true,"commandId":"g2-boot02"}
{"op":"status"}
```

`start-host` performs31 fresh disk samples first, anchors before Popen, and launches exactly pilot/beta06g2/app.mjs with actual parent PID and remaining host milliseconds. Outputs are host-app02, then host-app02-restart if explicitly authorized later. There is one30minute host window across both instances and both allowed boots. No manual Node launch, imported timestamp or second host anchor. Wait for actual owned launch proof before `setup`, then `start`; those commands inspect installed APK SHA and never install or clear data. `start` explicitly force-stops/restarts only this package with CLEAR_TASK, retaining its native store.

```json
{"op":"setup","rootApproved":true,"commandId":"g2-device-setup"}
{"op":"start","rootApproved":true,"commandId":"g2-native-start","variant":"initial"}
{"op":"store-before","rootApproved":true,"commandId":"g2-native-before","variant":"initial"}
```

Root must independently establish current native WebView bounds using actual ground PNG/window data, without assuming old [0,24,1280,740]. `prepare` takes `nativeFrame:[x0,y0,x1,y1]`, a new `name`, and records a screenshot/reference. Root inspects that screenshot before any dispatch. Always use fresh references after document, client epoch, AP boot/run, canonical model/plan or video configuration changes. No hidden JS, control POST, OCR compile, UIAutomator or stale coordinates while armed.

## Ground source and admission before every Connect

Root stages the existing browser publisher and Android viewer using actual visible controls before AP. Verify configured source/profile and current viewer. Video must show active calibrated frames, no degraded clock, current raw visibility/native foreground and continuous client session. The ground gate samples75s, bounded80s, requires one fixed viewer-clock run and source/config/model/client context plus two real periodic publisher and viewer renewals. Publisher diagnostics are normalized only at the authenticated new server route under the L2 six-to-five key rule; clock numbers/thresholds do not change. A rejected gate does not permit AP.

```json
{"op":"ground-soak","rootApproved":true,"commandId":"g2-ground-n1","clockJournal":"ABSOLUTE_CURRENT_HOST_MEDIA_CLOCK_JOURNAL"}
{"op":"prepare","rootApproved":true,"commandId":"g2-connect-ref","name":"g2-connect-n1","nativeFrame":[0,24,1280,740]}
```

The frame numbers above are an example, not proof. Replace with Root's actually measured current frame. After inspection, one `action` with target `field-connect`, inspected `reference`, and `groundStagedAndInspected:true` samples the AP anchor BEFORE its single tap. Immediately before input it revalidates the admitted fixed context and fresh current media/lifecycle sample. Maximum4 new Connect intents in generation02; boot03 allows none. Fifth is refused before input/allocation. AP source pins must exactly match evidence/beta06/generation02/flight-pins.json. Before the airborne sequence, qa-ap-admission also hashes launch.json and checks its exact qualified native profile/binary/image/command/observer0 fields. This replays recorded launch identity; actual live Docker and incoming firmware validation remain separate production guards, not inferred from metadata.

## N1 and N2 nominal sequence

Root performs initial visible `field-preflight` (timeout at most100s) and `field-grant`, `field-upload` on the flight tab, plus `field-tab-payload`, `field-discover`, `field-select` for the intended station/device. Correct firmware, fresh parameters, exact readback and geodetic model remain hard gates. Prepare and inspect BOTH flight and payload screenshots with all required dock targets fully visible/unoccluded at the same current configuration. Explicitly return to the payload tab and grant a late60s payload lease. The immediate sequence may contain at most12 actions and stops first failure; no hidden retries.

The `airborne` command accepts inspected `flightReference`, `payloadReference`, and `scenario:"nominal"`. It requires current DISARMED actualSITL, exact selected payload lease at least40s, re-runs preflight, checks Python AP≥225s/emulator≥240s/host≥240s reserves immediately before ARM, then taps ARM and Home→AUTO without a human tool gap. Home must still have strictly more1800ms. It waits at most20s for fresh actual AUTO/armed/height>5. Only N1/N2 start one selected30s video measurement, take one real linked-capture path, inject the deliberate500ms viewer pause, navigate to payload and command gimbal. UI receipts alone are not raw acceptance.

Root then saves the actual measurement report through the visible viewer control when complete and waits for actual mission completion. `complete-nominal` performs only bounded read-only waits before one visible Close, and phase policy requires canonical navigation completed, near home, fresh position and ground disarm. Never close early to create nominal success. Source and viewer stay ACTIVE through flight and ground disarm; selected30s metrics do not certify the entire flight. Root stops both explicitly only during disarmed staging/between scenarios. Record continuity separately.

Collect `store-after` EARLY after each scenario, before min(host,emulator) falls below90s. Provide its matching `beforeReceipt`, inspect actual native journal prefix/artifact SHAs and actual guest boot ID. Native historical elapsedRealtime values are not globally ordered across coldboots.

## F1 cut and F2 reboot

Use fresh current run/config references and the same preflight/readback/late lease/ARM/Home gates. `scenario:"cut"` or `"reboot"` waits for fresh actual AUTO/armed/height>5, navigates to payload, commands one gimbal, returns to flight, records a fresh exact-context active calibrated source/viewer frame/config point, then dispatches the single explicit fault while at least5s of the exact selected station/device/client-instance lease remains. Backend durable invalidation must precede actual fault effect. There is NO second video measurement, pause or capture in fault scenarios: their30s metric status is NOT_APPLICABLE_FAULT_SCENARIO. Active source/viewer and actual frame/config observations plus raw continuity replay remain required; no synthetic media PASS.

After fault, no automatic authority restoration. Inspect fresh human-reviewed refs after run/boot changes. The explicit old-context control uses only retained in-memory old token/context and must show its exact correlated guard refusal, not network timeout as refusal. Preserve pre/post durable receipt identities, zero leases, actual socket cut/reboot and no old-context command effects. Replayer results distinguish incomplete deliberate fault from nominal completion.

## One managed host restart, after accepted N1 and closed F1 only

Actual QA raw nominal and TCP-cut replays must exist and bind current request/review/raw/closure/WAL hashes. Request model/plan lives in `request.binding`. Exactly the first two new AP requests must be N1 and F1 with one canonical model/plan; a preparation failure is not eligible. Root inspects them, then sends:

```json
{"op":"authorize-managed-restart","rootApproved":true,"commandId":"g2-restart-proof","rootInspectedActualReplay":true,"nominalReplay":"ABSOLUTE_ACTUAL_N1_QA_REPORT","faultReplay":"ABSOLUTE_ACTUAL_F1_CUT_QA_REPORT"}
{"op":"stop-host","rootApproved":true,"commandId":"g2-stop-host-one","sourceAndViewerStoppedAndInspected":true}
{"op":"start-host","rootApproved":true,"commandId":"g2-start-host-two","sourceAndViewerStoppedAndInspected":true}
{"op":"start","rootApproved":true,"commandId":"g2-native-fresh-doc","variant":"after-host"}
```

Stop requires actual no flight run, no flight authority/busy, zero payload leases, inactive viewer and Root stopped publisher inspection; verifies exact clean app-closure. Cleanup is still allowed if restart proof is missing, but cannot authorize another listening instance. Restart cannot follow unexpected exit or failed preparation. Second instance uses SAME Python host anchor, workspace and AP counters. Explicit native process restart is REQUIRED before N2 for a fresh WebView document/CSRF/client context; it does not clear native data or recover rights. Reload publisher to new host bootstrap/server boot, establish new current viewer, remeasure refs and repeat75s gate. Then N2 nominal and F2 reboot, within the remaining original deadline. No automatic host restart or extra scenario.

## SAF and persistence, actual existing native paths

Before operations, inspect actual native `PICKER_PENDING` count; lifetime limit16 is unchanged. Prior count10 would leave6, but actual before-snapshot governs. Plan at most6 actual picker operations: workspace export/import, raw N1/raw fault, linked capture and explicit cancel. Existing QA wrong-SHA fixture rejects before PENDING and does not count as picker success. Do not clear data, raise quota or delete evidence/provider files.

In idle/no authority/no lease, Root uses `native-picker` with current inspected ref and one target: `field-export-workspace`, `field-import-workspace`, exact `field-raw-s...`, exact `field-capture-export-...`, or actual observed delivery file ID. Result means only INPUT_NOT_COMPLETED. Root completes/cancels Android provider UI explicitly and records actual callback, native journal and provider file bytes/SHA; do not infer native success from web dispatch ACK. Export exact raw and linked capture packages and run independent receivers; import verifies workspace bytes/model and never restores authority. Cancel must leave explicit cancel/unknown outcome and no invented success.

`native-negative` is narrowly field-qa-bad-sha only: one visible input, then a new actual native callback with OPERATION_NOT_CONFIRMED/SHA256_MISMATCH plus unchanged independent PENDING/artifact count. Its input receipt is NOT a native result.

Use `store-before`/`store-after` variants per scenario. For native process persistence use explicit `start` with a unique variant while idle. Optional `launch-persistence-emulator` requires confirmed boot02 closure, host remaining≥240s, and unused boot03. It resets ONLY the new emulator anchor; original host deadline remains. Boot03 rejects Connect/preflight/grant/upload/ARM/AUTO/fault even through batch/airborne paths. Store-after requires ≥90s remaining on host and emulator; do not defer all native proof to the final minute.

## Budgets and honest outcome

Admission31samples/min29GiB/30s/decline≤256MiB. Runtime28GiB250ms/15s forecast protects20GiB. All evidence/beta06 aggregate256MiB with stop200MiB and56MiB closure reserve. New processed HTTP-body budget1GiB is not retained stream capacity; existing queues/reports/codec/128MiB retained-media cap stay exact. Inspect actual media bytes and source replacement/report counts before each scenario; never reset counters. No source/viewer midflight stop to evade quota. AP540s and slow guest/AP clock are not waived:225s is an engineering reserve, not a certified mission duration. Missing completion, interrupted lifecycle, expiry, bad current frames, uncertain input or closed runtime produces PARTIAL/NOT_READY with retained evidence, not an expanded budget or rerun.
