# FLIGHTADAPTER39 — completion / verification

14/10/2026. **DONE in authorized offline composition scope — MOCK_COMPOSITION_VERIFIED.** APFLIGHT36, MAVFLIGHT37 and FIRMWARE38 are composed in a separate readonly adapter. Specification, build and verification were performed sequentially by one agent; cold replay is a separate process, not independent human/agent review.

## Result and product behavior

- A bounded union framer recognizes all18 M37 messages and unsigned-v2 AUTOPILOT_VERSION148; version announcements no longer disappear in the older decoder. Exact bytes and first/last byte receipts survive fragmented/coalesced input. Signed/incompatible, corrupt or unsupported frames close the session. This is a deliberately strict19-message subset, not a full live AP stream implementation.
- One central mock identity/context/sequence/boot/clock gate dispatches whole frames to old telemetry and typed readback. Duplicate/reordered/foreign packets are quarantined; they cannot renew witnesses. Conflicting same-target firmware or previously read parameters revoke even under duplicate/reordered sequence. Per-message AP boot-ms wrap is distinct from accepted regression; local clocks are never scaled or merged with AP guest clocks.
- Fresh reviewed firmware starts one read pass of28 typed parameters through F38. C-cast/bytewise distinctions, type/count/index65535/precision/range checks and1500ms freshness remain. Outputs are named PARAM_REQUEST_READ20 buffers only, MOCK_BUFFER_ONLY and networkSent:false, after mock journal intent commit. Identical announcements do not refresh binding; no reconnect/retry/resume API exists.
- One inspection contains M37→A36 preflight and F38 rich policy/failsafe/altitude results. Generic bytewise profiles cannot inherit Copter telemetry/policy interpretation. Missing AP-side state/references, normalized configuration, verified fence and remainingWh remain UNKNOWN. mAh/V and action graphs are not substituted into the old normalized policy.
- WeakMap-issued readonly inspection witnesses are process-local and immutable by canonical comparison; serialized/tampered snapshots cannot restore them. Session/boot/link/epoch change, stale/suspension, owner/focus loss, firmware/config change, writer error, concurrency and revoke-during-commit invalidate the instance and prevent subsequent publication. Audit prefixes remain available; terminal reason is retained in snapshots/replays. FlightAuthority/authentication/execution/enforcement stay false.

## Evidence and exact counts

| Check | Final result | Evidence |
|---|---:|---|
| Logic / adversarial / cold old regressions |236/236 PASS |`evidence/flightadapter39/logic4.json` |
| Previously accepted upstream vectors through union framer |185 vectors,5671 split positions |144 M37 vectors +41 F38 version/parameter vectors; included in logic count |
| New source-bound routing/readback/loss replay |40/40 match |`corpus4.json`, `replay4.json` |
| Hash/semantic falsification |9/9 reject |`replay4.json`; rehash cannot turn loss into authority or mock into execution |
| Separate-process replay |40 outcomes byte-for-byte equal to accepted receipt |`verification1.json` |
| Journal chains / readonly output whitelist |80/80 chains valid |Two audit streams per replay case in cold verification |
| Original APFLIGHT36 / MAVFLIGHT37 / FIRMWARE38 |33/33,41/41,54/54 exact old receipts |No old receipt/output write |
| Verification gates |16/16 PASS |`verification1.json` |
| Technical syntax |7JS +2Python files valid |Node syntax and Python AST, no cache/build |
| Protected historical scope |13,594 paths,0missing/changed SHA |`preservation-before1.json`, `verification1.json`, final preservation receipt |
| ENDURE inventory |5,051 files unchanged |Exact inventory equality and all protected SHA |

Counts overlap where stated; neither tests nor vectors are flight trials or product readiness percentages. R39-01..07 all implemented and verified within this offline scope (7/7). Build/APK/typecheck/lint/actual binary/SITL/Android/Hera acceptance is NOT_CHECKED, outside this task. No full upstream CI claim.

## Failures and refinement retained

`logic1.json` failed one assertion: a snapshot could enter the constructor and only fail later at bind. Constructor now immediately requires the exact reviewed contract shape; no restored reader authority was actually issued by that failed path. `replay1.json` failed the late-reordered fixture because its old wire sequence reused an old host timestamp; host regression was correctly rejected. Fixture now retains old wire bytes with a new arrival timestamp. Original FAIL receipts are unchanged.

Logic2/replay2 precede conflict quarantine guards; logic3/replay3 precede the generic-profile telemetry restriction. They remain historical, not current acceptance. Accepted source hashes are bound to logic4/replay4/corpus4; verifier never automatically selects a changed source or newest attempt.

## Boundaries and remaining work

This composition is readonly observation/preflight inspection, not fence upload or live flight transport. M37's REAL32-only fence-completion contract is not borrowed for typed F38 readback. Therefore geofence upload/readback/enforcement and a complete READY preflight are not newly claimed. Wire-only preflight remains UNKNOWN. No app/Fly/native integration or software release is produced.

Reference firmware4.7.1/source bundle is still not associated with any existing SITL/Hera binary; MOCK0038/UID/board/context values remain synthetic. CRC/unsigned sender IDs/local metadata do not authenticate radio or establish remote replay protection. Sequence alone cannot distinguish all loss/reorder/reset cases. One1500ms read cycle and strict message subset are conservative engineering limits; full-stream discovery, signing/authentication and longer parameter workloads need separately reviewed policies.

Default/injected persistence is mock. Host power-loss/OS crash, production storage durability, actual transport, physical RC/video/camera/gimbal, firmware failsafe scheduling, active fence, Android/Hera and A/B Ragas/DJI remain NOT_CHECKED. A matching ACK is diagnostic, not execution/media. ENDURE retains its historical failure; no interval is combined, campaign restarted or24h acceptance inferred.

## Preservation/resources and handoff

New files only under `pilot/flightadapter39`, `evidence/flightadapter39`, TIP/ADR052/this report/roadmap supplement. Frozen app/source/candidate/trust/canonical SOT/ENDURE and old module/receipts unchanged. Namespace measured7.53MiB at cold verification, under16MiB budget; host free25.02GiB at that check, above20GiB. Final namespace/fingerprint receipt accompanies handoff.

No scratch copy, temporary install/build/cache/Next/Docker artifact or persistent test process was created, so none required deletion. All Node mock processes exited; raw/failure evidence remains. No SDK/dependency download, APK build, SITL/emulator, flight output or signing took place. Integrity at before/after observation does not prove uninterrupted original-path presence across previous restoration incidents.

Next authorized preparation can extend a reviewed full-stream adapter and associate actual firmware discovery with a named AP binary. Actual SITL/runtime/native/signing requires its own gate and authorization. Roadmap supplement is separate; canonical frozen roadmap/SOT is not reconciled in this task.
