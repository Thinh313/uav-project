# ADR-053 — full dialect framing with restricted semantic dispatch

Accepted within user-authorized offline scope,2026-10-14.

F39 intentionally rejects unknown-to-subset messages; wrapping it and filtering packets would leave transport sequence gaps. New APSTREAM40 validates the full pinned ArduPilot dialect before dispatch. The runtime-tree dialect and older captured M37 XML are distinct snapshots: require base layout/CRC compatibility for18 overlaps, record extension/metadata differences, and require exact22/148 wire bounds. Do not merge snapshots or edit old pins. A decoded-frame bridge populates the legacy telemetry cache from validated full frames; auxiliary frames advance legacy link sequence explicitly without rewriting raw bytes. Per-message boot clocks remain centralized. Foreign or CRC-unverified frames cannot advance the AP sequence/firmware witness.

Framing includes signed known frames, but no key/authentication implementation is introduced. Same-target signed/opaque unknown frames make an active discovery/inspection uncertain and invalidate it. Foreign/unsolicited frames remain quarantined with raw bytes. Known CRC corruption/unknown incompatible flags close the session. Full framing is not universal command or semantic support.

Discovery requires a fresh explicitly selected target heartbeat and one explicit mock REQUEST_MESSAGE. The only COMMAND_LONG output is512 requesting148, all other command parameters zero; other output is named readonly PARAM_REQUEST_READ. A request/ACK/version correlation cannot establish command execution/authentication or identify the actual binary behind source pins. No automatic discovery retries/reconnect/renewal, no mode/ARM/fence/parameter writes.

A new bounded mock audit handles broader traffic without changing old256-row ledgers. Production journal durability and full live rate/vehicle/firmware acceptance are future gates. All components are isolated; frozen source/candidate/SOT/trust/ENDURE unchanged.
