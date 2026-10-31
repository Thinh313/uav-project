# CREW02 L2 refinement04: B-only prewrite suppression

20/10/2026. Contractor requested and approved narrowly typed clean prewrite rejection. If operatorB loses current session/scope/revision after TX_INTENT WAL/fsync but before socket write is attempted, and A authenticated presence/aircraft ownership, common AP policy, foreground and trust remain valid, this local rejection must not disconnect A's aircraft transport.

A dedicated CrewPreWriteDenied02 category may suppress only that proven zero-write B intent, durably record TX_SUPPRESSED with exact wire/intent binding and reason, consume the intent as UNKNOWN/no replay and revoke B scopes. The already reserved wire sequence is explicitly accounted for as unsent, not falsely counted TX_WRITTEN and not silently removed. All raw RX/telemetry remain preserved.

Any attempted/partial/unknown socket write, WAL/audit/durable failure, common AP/foreground/trust failure or global clock/A presence invalidity still closes common transport. Do not classify arbitrary IOException or error strings as safe suppression. Fault test must expireB inside TX_INTENT WAL then prove zeroBwire and A authority/transport retained. This is required to satisfy frozen C08 during a pending B intent; no user permission or safety floor is relaxed.
