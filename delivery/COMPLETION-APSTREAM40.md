# APSTREAM40 — completion and verification

14/10/2026. **DONE in offline mock/replay scope — MOCK_FULL_STREAM_DISCOVERY_VERIFIED.** New full-stream ArduPilot framing and explicit firmware discovery compose readonly safety inspection outside frozen application/candidate/ENDURE. One agent performed specification/build/verify sequentially; separate cold process/upstream oracle is not independent human/agent review.

## Delivered behavior

FullFramer covers the pinned transitive ArduPilot dialect:299 message definitions from9 XML files,188 v1 IDs and all dialect v2 IDs. Every message layout/CRC matches the pinned upstream parser. It preserves raw bytes and first/last byte receipt through fragmentation/coalescence; handles signed trailers and opaque unknown IDs without claiming authentication/CRC for unsupported frames. Known CRC errors and unknown incompatible flags fail closed. It is full pinned-dialect framing, not universal command/semantic support.

Discovery requires a fresh selected ArduPilot/Copter heartbeat and explicit start. A journaled COMMAND_LONG512 requests message148 at the exact target; all other command parameters are zero. ACK is recipient-checked diagnostic only; it never proves firmware or extends the1500ms window. Current matching version/capability/source/UID then starts28 typed readonly named reads. Wrongtarget/unsolicited/late/pre-request/signed/mismatching responses cannot bind. No automatic reconnect/retry/renewal or cached authority restore.

The outer gate observes auxiliary traffic and maintains the AP sequence across more than128 auxiliary packets without altering wire bytes. A validated decoded-frame bridge supplies legacy telemetry, with stable base mapping checked against the older XML snapshot; F38 reads unchanged parameter frames. Rich policy/failsafe/altitude results remain separate from incomplete A36 preflight. Generic bytewise cannot inherit Copter interpretation; missing AP-side/reference/Wh/fence evidence stays UNKNOWN.

Loss, owner change, stale/partial expiry, boot/context changes, incompatible heartbeat, firmware/parameter conflict, writer error and concurrent/revoked async work invalidate witnesses. New explicit boot instances require discovery and full readback again. Snapshots/serialized proofs cannot restore a witness; flight/operational/authentication/execution flags remain false. RX bytes/context are cloned before writer await so audit and decoder receive the same immutable bytes.

## Requirements / tests

| Scope | Current result | Receipt |
|---|---:|---|
| R40-01 full schema/source/codec |299/299 fresh upstream layout/CRC checks;9 XML pins |`schema1.json`, `overlap1.json`, `verification1.json` |
| R40-02..05 framing/session/discovery/readback |1015/1015 logic checks |`logic2.json` |
| Upstream vector coverage(included above) |974 vectors, all299 IDs;37166 split positions |`oracle-vectors1.json`, `js-vectors2.json` |
| Python upstream decodes actual JS bytes |974/974 |`oracle-check1.json`; overlaps vectors above |
| R40-06 corpus / falsification |44/44 scenarios,9/9 bites rejected |`corpus2.json`, `replay2.json` |
| Separate-process replay |44 outcomes exactly match receipt;88 journal chains valid |`verification1.json` |
| Original36/37/38/39 regression |33/33,41/41,54/54,40/40 exact original receipts |No old output write |
| Technical syntax |9JS;6Python files valid |No cache/build/typecheck/lint/full CI claim |
| Verification |20/20 gates PASS |`verification1.json` |
| R40-07 preservation |13,624 protected paths,0missing/changed SHA;5,051 ENDURE files unchanged |Before/verification/final preservation |

R40-01..07:7/7 implemented and verified in explicit offline scope. This is scope coverage, not percentage readiness to replace Ragas or exceed DJI. Build/APK/SITL/emulator/device/actual binary association/live throughput are NOT_CHECKED and were not required or run. No new software/crypto signature or candidate selection.

## Source discrepancy / development history

Initial schema preparation refused strict equality with old subset XML before writing definitions/oracles: runtime-tree XML and older captured reference files are different snapshots. `overlap1.json` records actual old/current differences; all18 stable base layouts/CRCs match. Version148 and parameter22 bounds are compatible. New full-dialect pins remain separate, no snapshot merge or historical rewrite, no assumption that these schemas identify the existing SITL/Hera binary.

The first guard invocation had a Python string typo and exited before hashing/baseline writes; corrected before the successful before gate. Parser emitted two enum bitmask warnings(MAV_BOOL_FALSE and CAMERA_TRACKING_STATUS_FLAGS_IDLE); message layout/CRC checks passed and source was not edited. These preparation incidents are not autopilot/runtime failures.

Logic1/replay1 passed their earlier source revision. Subsequent review added clearing old heartbeat selection on conflicting/unsigned-unsupported target frames, copying RX bytes/context before await, exact discovery timeout and wrong-system parameter tests. Current acceptance uses logic2/replay2 only; prior receipts remain unchanged. No failed flight/SITL run or retry occurred.

## Limits and preservation

Full stream is limited to pinned299-message dialect; opaque unknown IDs have no CRC/semantic authority. Signed frames are framed but unverified; test trailers are fabricated13-byte data, not actual signatures. Matching sender/UID/CRC/mock metadata is correlation, not remote identity or request causality. Same-key old replies have no protocol nonce. Sequence alone cannot detect all reboot/loss/reorder ambiguity; unsupported target traffic during active discovery/readback fails closed.

Discovery/readback window is still1500ms; named32-parameter and journal quotas remain engineering limits. Core receipt clocks/AP-side state are declared mock domains, not measured host–guest clock association. MockJournal8192rows/4MiB records every admitted/quarantined complete frame and raw chunk intent within admitted bounds; quota rejects rather than prunes. Injected/default persistence is mock, not production disk/power-loss durability. No live performance or long-duration result is inferred.

No mode/ARM/takeoff/landing, parameter write, fence upload/readback/enforcement, physical media/payload or native/Fly integration is produced. ENDURE retains its prior failure and unchanged history; no campaign launch/interval aggregation/24h acceptance. Firmware/source interpretation remains synthetic and unassociated with actual installed binaries or Hera devices.

Namespace measured10.19MiB at cold verification, under32MiB; host free24.68GiB at that observation, above20GiB. Final fingerprints/preservation receipt accompany handoff. New files are only `pilot/apstream40`, `evidence/apstream40`, TIP/ADR053/completion/roadmap supplement. Frozen app/source/candidate/trust/SOT/ENDURE/old modules unchanged. Integrity at endpoints does not establish uninterrupted original-path presence across past restoration incidents.

No whole-project copy, scratch install/build/cache/Next/Docker artifact or persistent service/process was created; nothing required cleanup. All mock Node/Python processes exited, source/evidence/oracle files are retained. No dependency download, SDK, APK build, SITL/emulator or signing.

Next gate is an actual named ArduPilot binary/firmware/source association and readonly discovery/type/clock/traffic acceptance in separately authorized SITL. Do not treat this mock result as permission to launch runtime, integrate frozen Fly or sign/select a package.
