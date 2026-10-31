# ADR103 — passive flight-failure observation and portable raw evidence

Accepted within user-authorized simulation scope. Native87 closes the control socket on loss or lifecycle revocation; that protects authority but cannot by itself observe subsequent AP failsafe. Native88 inserts an owned loopback pass-through channel between that control socket and the pinned simulator. Every upstream/downstream byte and cut/close is journaled with bounded SHA/fsync capture. The channel sends no independent MAVLink messages. After downstream loss, AP continues receiving zero GCS heartbeats and its response remains observable. Main Fly remains stale/revoked; a separate incident panel labels passive observations.

Airborne failure qualification must bind exact process/boot/session/plan/AP configuration and show last forwarded GCS heartbeat → failsafe/mode → observed ground/disarm. Review for an interrupted run stays unaccepted even if failsafe lands. Explicit acknowledgement of fresh safe terminal state does not restore grants. Only closing the old interrupted session and an explicit new readonly session can continue the workflow.

Portable handoff contains raw/control+observer streams, mission and run identity/closure rather than only review hashes. Receiver verifies a bounded manifest and independent raw consistency before publishing a receipt; missing or modified bytes cannot become a completed package. Development integrity proof is not source authentication, customer acceptance or Hera calibration.

No physical SDK/device exists. Bench preparation defines machine-readable intake and honest UNKNOWN/NOT_CHECKED outcomes. Native88 does not change source/candidate/ENDURE/canonical SOT, does not sign production or infer pacing/24h acceptance.
