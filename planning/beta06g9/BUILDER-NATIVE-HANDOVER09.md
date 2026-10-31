# G9 Native source/mock handover

Namespace-only Native siblings of frozen G8:14 Python helpers, four canonical read-only replayers and upfront qa-root-live18.py. Attempt18 is the flight boot;19 is persistence-only. Outputs are generation09/host-app09, host-app09-restart and workspace01. Expected manifest is generation09/flight-pins01.json. All old G7/G8 source/evidence/counters remain separate. G8 Connect refusal occurred before AP/anchor/input because its shared quota host regex retained host-app07; G8 host and emulator closed cleanly. G9 Flight central host binding is the sole behavioral repair, with old-fails/new-passes real-directory and Python→Node tests required before gate. G8 actual AP0. G7 actual SITL0; its three mock requests are historical mocks, not actual flight requests. Historical actual17 remain separately SHA-bound.

No guard/control/clock/freshness/replay algorithm changes. Explicit whole-source normalization against G8 and equality of every Python numeric constant cover all19 operational siblings. In particular forecast=free-rate*15 and forecastSeconds15 remain unchanged. Physical admission31 samples/30s/min29GiB/max256MiB peak decline; runtime28GiB/15s forecast20GiB floor. Original2700s Python host window,2hosts,4AP N1/F1/restart/N2/F2, AP540s/speedup1, reserves225/240/90s. No retry/restored anchors or authority. R2 completion policy remains directly imported from immutable planning/beta06g4r2/complete_nominal_policy.py.

Final G7 quota allocation carries forward unchanged:2228MiB category envelopes,256MiB global emergency,2228MiB category sum below2304MiB early and2484MiB with emergency below2560MiB hard as defined by the shared policy;8192entries including412closing. Native736entries/672normal,112MiB=96normal+16close;512normal file claims plus32directories+2ledger separately. SourceQA544entries/512normal. PNG240×5MiB with160dispatch/48prepare/32direct. All future-headroom tables, Native512-file and PNG-subtype prechecks, complete proof caps and cleanup reserves remain exact. Heavy checks precede latest UI observations. Optional exports remain allocation0. Existing APK df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d and ARM artifact .local/beta06g3/arducopter are reused; no build/install/signing.

QA owns the exact original closed G5 workspace fork20files/870221bytes. First-writer guard verifies it before store lock; no consumed G7/G8 workspace reuse. Native baseline remains generation04/android-store-after-n1-closed-08.json:19files/34records/13PENDING/3remaining. No reset/clear/quota reset. HOSTDIAG08 observations do not substitute for fresh live admission or prove flight.

Root alone runs actual effects after independent source gate, host diagnosis and fresh admission. Builder checks are source/mock only. Start from the repository:

```sh
python3 -B planning/beta06g9/qa-root-controller.py --plan
```

Launch the one live controller through exec_command with tty:true, retain its session ID, and send bounded newline-delimited JSON through write_stdin:

```sh
python3 -B planning/beta06g9/qa-root-live18.py
```

TTY is required before controller import, mkdir or journal; root-controller18-live.jsonl is exclusive. Keep this one process/stdin alive. Send ONE stdin command at a time and wait for its response; never queue later commands for a child to consume. Explicit Controller sequence remains allowed for reviewed action steps. Every effect has unique commandId and rootApproved:true. Initial explicit commands:

```json
{"op":"status"}
{"op":"start-host","rootApproved":true,"commandId":"g9-host1","sourceAndViewerStoppedAndInspected":true}
{"op":"launch-emulator","rootApproved":true,"commandId":"g9-boot18"}
```

WAIT for actual boot complete sys.boot_completed=1, then ONE setup and start/variant initial, store-before/variant n1. Root operational order: create/start the synthetic IAB publisher only AFTER emulator admission, actual boot and setup complete. This separates initialization without changing any guard. Stage source IAB VP8-720P30-V1 and Android viewer, inspect fresh nativeFrame, then prepare with exact observed rectangle. Source/viewer remain active during every75s ground admission and actual AUTO/media window. Never UIAutomator while AP active.

Before EACH Connect, use ground-soak with literal current clock path /Users/os/Downloads/AI technique/aeris/evidence/beta06/generation09/host-app09/media/clock-events.jsonl (host-app09-restart after restart). Inspect75s contiguous/two renewals and fresh geometry. Explicit field-connect uses timeout100 and groundStagedAndInspected:true. No extra runtime mock/AP trial. Failure/uncertainty latches progression; only the existing once-explicitly-diagnosed read-only ground recovery before anyAP is permitted.

PostConnect: fresh flight reference → preflight/grant/upload → payload tab/fresh reference/discover → refresh after option discovery/select → final payload reference AFTER selection → flight tab/final flight reference → payload tab. Inspect both screenshots. Explicit sequence late field-pgrant then airborne as LAST step with both references and exact scenario nominal/cut/reboot. Lease entry≥40s and existing reserves remain. R2 complete-nominal accepts fresh canonical completion/ground/disarmed/nearHome even if stage remainsAUTO, never the badge alone. Bounded concurrent diagnostics retain all polls, hashes and observation ages; sequential reads are not claimed atomic.

Require N1 independent raw/media/capture/overlap/index PASS before F1; deliberate F1 live-lease/raw/index PASS before authorize-managed-restart. Stop source/viewer on ground, authorize with rootInspectedActualReplay:true and exact nominalReplay/faultReplay, stop-host with inspected flag, then start-host with same flag. Original controller/window/emulator18/counters persist. Reload source for host2, new references and75s admissions for N2/F2. Pending/unknown close indexing stops all later progression; deliberate incomplete fault review remains valid only with its exact replay.

After four scenarios, keep host2 live. Stop source/viewer, inspect fresh ground/zeroauthority/lease/indexfailure, store-after18. stop-emulator with sourceAndViewerStoppedAndInspected:true captures the single-use in-memory fresh pre-stop18 proof. Wait clean explicit android-closure18.json and helper exit. launch-persistence-emulator consumes that proof, same host2/window; no stopped-native observation. Wait bootcomplete, ONE setup, start/variant cold, inspect history/native/WAL/artifacts/zero restored rights and store-after19 with explicit beforeReceipt.

Final order: stop-host2 WHILE19 native UI is alive/fresh, using sourceAndViewerStoppedAndInspected:true; verify clean app closure. Then stop-emulator19 WITHOUT source flag, wait clean android-closure19/helper exit, then EOF. No third host/window/counter reset.

Replayers use the same G7 argument order and exact finite proof names under generation09: qa-n1-raw01.json, qa-n1-media01.json, qa-n1-overlap01.json, corresponding n2 names, qa-f1-cut01.json, qa-f2-reboot01.json, qa-native-persistence01.json. Scenario proof≤2MiB/six perAP; campaign128KiB/16names; final aggregate4MiB/32closing entries. Full serialization only, no truncation or frame dropping. Media synthetic/payload mock; actual G9 AUTO/linkloss/reboot/persistence remain NOT_RUN by Builder and cannot be inferred from mock checks.
