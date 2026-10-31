# TIP-APSTREAM40 — full pinned ArduPilot stream and mock firmware discovery

2026-10-14. User authorizes mock/replay only; no SITL/emulator/APK/signing. Separate source/candidate/ENDURE preserved. P0; dependencies APFLIGHT36/MAVFLIGHT37/FIRMWARE38/FLIGHTADAPTER39 accepted immutable artifacts. Use existing Node/Python stdlib/upstream parser, no install/project copy. Sequential specification/build/verify by one agent, not independent review.

## Decisions

Generate the complete transitive ardUpilotMega XML dialect from the existing local upstream tree, hash every XML/parser input, compare every wire layout/CRC with upstream mavparse. Strict initial overlap equality exposed different XML snapshots before generation: compare stable base mapping/CRC for18 overlaps, retain extension/metadata differences, and require exact22/148 wire bounds. Generate test-only upstream Python serializers for v1/v2. Full-stream means framing/decoding that pinned dialect, not semantic/flight support for every message or future custom dialect. Unknown IDs retain raw opaque frames without claiming CRC/authentication. Signed known frames are framed with trailer/CRC but never authenticated or admitted as firmware evidence.

Do not wrap F39's private narrow session or rewrite raw sequence bytes. A new outer session validates all AP packets; an explicit bridge advances legacy submodule transport sequence across validated auxiliary packets, retaining original raw frames/byte times. Reuse readonly F38 typed reader and M37→A36 preflight; no fence uploader/parameter writer/flight broker.

## Requirements / acceptance

| ID | Requirement |
|---|---|
| R40-01 | Complete include-closure schema, all layouts/CRCs match upstream; v1 IDs<=255, v2 full24-bit IDs, extensions/arrays/wide integers/text/zero truncation; source pins/license retained. |
| R40-02 | Bounded full framer with first/last byte times, fragmented/coalesced streams, known CRC validation, signed trailer and opaque unknown quarantine; corrupt known frames fail closed without hiding discovery. |
| R40-03 | Explicit current target/session/boot/link/clock context, per-AP sequence/boot handling across auxiliary messages, duplicate/reordered/foreign quarantine; no raw re-encoding or clock scaling; stale/loss/reboot revokes all witnesses. |
| R40-04 | Fresh target ArduPilot/Copter HEARTBEAT before explicit REQUEST_MESSAGE512/param1=148 mock request; one1500ms bounded discovery, ACK diagnostic/recipient gating and version source/capability/identity checks. Late/unsolicited/wrongtarget responses never bind; no auto retry or renewal. |
| R40-05 | Typed readonly readback, separate policy/preflight/altitude scopes; all unsupported/missing state UNKNOWN; generic profile cannot inherit Copter interpretation; weak process-local witnesses, no serialized restore. |
| R40-06 | Mock journal intent-before-output, bounded audit/raw quarantine, writer/revoke/concurrency faults, wrongtarget/loss/reboot corpus, semantic tamper bites and cold replay; exact original36/37/38/39 regressions. |
| R40-07 | Protected before/after SHA including39/source/candidate/ENDURE,20GiB floor,32MiB namespace +64MiB reserve. No runtime/software build/signature/canonical SOT changes. |

## Outputs / verify

`pilot/apstream40`, `evidence/apstream40`, ADR053, completion and roadmap supplement. Replay source-bound exclusive append receipts, failures retained. Test every pinned dialect message with upstream vectors, all split positions and mixed-stream routing. Binary association/actual link/AP state/Android/Hera/enforcement/flight/ENDURE acceptance NOT_CHECKED. Same unsigned wire-key replies have no transaction nonce; correlation is not authenticated causality.
