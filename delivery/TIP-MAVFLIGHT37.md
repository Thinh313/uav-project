# MAVFLIGHT37 — AP-FLIGHTOPS MAVLink adapter, offline only

14/10/2026. User authorizes adapter geofence/preflight/failsafe mock/replay. Scope: new pilot/mavflight37 and evidence/mavflight37, this TIP, ADR-050 and new completion/roadmap supplement. All old source, candidates, trust, ENDURE and restoration receipts immutable. No APK/build/install/SITL/emulator/signing/network/real commands.

Reuse APFLIGHT36 pure functions by read-only imports. Generate an 18-message schema subset from pinned local official MAVLink XML; compare schema layout/CRC with the existing upstream mavparse and produce an upstream Python serializer oracle in this module without compilation/install. Keep source pins, references and license. Bound combined new artifacts to 8 MiB; check free >=20 GiB with 16 MiB headroom before writes/tests.

| ID | Acceptance criterion |
|---|---|
| R1 | Binary MAVLink1/2 codec agrees byte-for-byte with upstream oracle and independently decodes it; CRC, field ordering, truncation/extensions, arrays, integer/float bounds, partial stream and corruption covered. Reject signed/unsupported flags; CRC is not authentication. |
| R2 | Fence polygon/circle/exclusions compile to int coordinates/float32 radius; quantization is explicit and geometry revalidated. Items omit altitude/action, which are separate readonly configuration. |
| R3 | Mock upload/ACK/readback/config match requires exact sender/recipient/type and current context. ACK/partial/mismatch/wrong peer/loss/reboot/stale/writer uncertainty never complete proof. Bounded duplicate request retry only to mock buffer, no automatic reconnect. No transaction UUID invented on wire. |
| R4 | Telemetry caches preserve sender/session/boot/link, monotonic receipt time, per-packet sequence and clock/frame provenance. Sentinel/nonfinite/absent extension fields remain unknown. Mode/landed/EKF/Home/battery/GPS fields normalize with explicit unit/datum. |
| R5 | Read-only named parameter requests/matches are typed and bounded. No parameter writes, arm, takeoff, mode change, clears or generic outbound command. Firmware-specific action mapping is not guessed. |
| R6 | APFLIGHT36 preflight/failsafe assessments consume translated wire observations plus explicitly synthetic supplements; wire-only incomplete lanes stay UNKNOWN. No percent/mAh/consumed-energy to remaining Wh, HDOP to meters, GCS receive to AP receipt/RC availability, ACK to execution. |
| R7 | Fence breach and heartbeat mode are separate timestamped observations; no causal/physical execution or failsafe success claim from their correlation. Replay corpus and rehashed false-result bites detect semantic lies. |
| R8 | Re-run original 33-case APFLIGHT36 corpus into new namespace; preserve all 13,463 restoration guards and additionally new restoration receipts. Append failures/attempts, record scope/deferred checks and source/evidence fingerprints. |

One agent switches specification, implementation and separate verification phases; no independent review claimed. Existing user authorization covers this isolated implementation. This is preparation of a restricted wire adapter, not full MAVLink protocol conformance, real AP admission, flight control, hardware/calibration or release acceptance.
