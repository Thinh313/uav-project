# ADR092 — AP internal quad behavioral gate

Accepted for isolated user-authorized SITL scope,16/10/2026. Keep SIM32 external physics / source / candidate / ENDURE untouched. Reuse pinned ArduCopter4.7.1 binary and existing Ubuntu image. No new build or software signature.

This gate verifies RC→autopilot→internal model→telemetry and virtual wall→DISTANCE_SENSOR→AP proximity→Loiter response. It does not close the existing SIM32 AP/backend pacing or Hera-calibration gates. Built-in physics differs; report it explicitly rather than calling it a SIM32 optimization.

Use body-FRD ray directions transformed by AP attitude into NED. Virtual wall is infinite plane NED north12m;8yaw sectors, range0.2..20m, centimetre MAVLink distances. Distance is measured from sensor origin/aircraft centre; contact audit subtracts provisional0.3m sphere radius. Invalid/no-obstacle values max+1 are sensor fixture conventions. No renderer controls aircraft. AP proximity output contains transformed/aggregated measurements; it is not a byte echo requirement.

AP source has500ms MAV proximity timeout; actual dropout test observes emitted data under the pinned binary, without assuming stale sensors force a stop. DISTANCE_SENSOR has no target/session fields. Local adapter must bind context before wire emission, but does not provide AP authentication. Wrong-target rejection is an adapter mock gate, not proof firmware rejects foreign sensor senders.

Log raw RX before decode and fsync TX intent before send; chain metadata is local integrity, not signatures. No automatic resend of unknown outcomes. Closure LAND is an explicitly logged cleanup action with telemetry if link permits; container stop is never declared successful landing. Child supervisor stops only its recorded container. Negative virtual-wall crossing has no physical impact response.
