# ADR098 · isolated Android workspace and native SITL bridge

2026-10-17. Accepted within user scope. Frozen82 remains baseline. Native83 has a separate application data directory, development APK and host process. Archive authority=false is invariant, SHA is integrity rather than authenticity. Export includes revision bytes and HEAD; import into a new retained generation only after structure and semantic checks. Provider readback proves returned bytes, not arbitrary provider powerloss durability.

Host connection is loopback only and target is process-pinned ArduPilot internal quad SITL. JS cannot open sockets; Java exposes bounded allowlisted actions. Process-local secret, native foreground lease and explicit per-session controls gate state changes. Stale/loss/background revoke; no retry of failed transactions. Readonly firmware/preflight precedes mission operations. Control evidence and native mock evidence stay separate. No claim of radio authentication, real Hera performance, physical media, hardware readiness or ENDURE acceptance.

## Qualification refinement after actual run01

First Android AUTO flight se929a9cff6d542099b51 uploaded/read back16items, observed6NAVwaypoints, terminalRTL, ground/disarm. Original63 completion demanded MISSION_ITEM_REACHED seq1 for TAKEOFF; actual stream reports2,3,5,7,9,11,13,15 and never1. Retain the first run NOT_ACCEPTED/aborted, not retrospectively PASS.

Pinned upstream ModeAuto verifies TAKEOFF then queues reached notification. GCS_Common holds one mission_item_reached_index per channel when scheduling that message. Last-index coalescing is compatible with the observed1→2 case, but internal scheduling causality was not instrumented; do not claim a firmware bug proven. Primary code URLs and captured SHA are recorded in evidence/native83/upstream-sources.json.

New isolated NativeMission83 keeps every command and readback unchanged. Require all NAV16 reached, plus a distinct TAKEOFF witness: at least300ms of consecutive fresh, increasing boot/host-time positions within1m of planned takeoff height and3m reviewedHome, consistentMSL/relative datum, AUTO/armed/airborne and current mission between TAKEOFF and firstNAV. Gap>1500ms, foreign target, bad clock, datum, low/far/noAUTO/noARM reset/refuse. Require terminalRTL/nearHome/land/disarm as before. Separate cold raw verifier recomputes this geometry rather than trusting online verdict. Mock adversarial gates precede a separately scoped second actual flight. No guard bypass, frame removal, speedup or autopilot parameter changes.
