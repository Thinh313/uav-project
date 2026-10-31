# ADR-050 — Restricted offline MAVLink adapter

Accepted within user-authorized mock/replay scope, 14/10/2026. APFLIGHT36 descriptors have no MAVLink bytes, while frozen source/candidate and ENDURE must stay intact.

Create MAVFLIGHT37 as a separate namespace using pinned XML for a bounded binary schema and an existing upstream Python generator as a distinct serialization oracle. No dependency install/compiler/network service. All outgoing bytes terminate in returned mock-buffer objects; no transport implementation exists. Allowed outbound messages are PARAM_REQUEST_READ and the fence-specific MISSION subset only. Clear/start/ARM/mode/PARAM_SET/COMMAND_LONG are absent from outbound API.

Geofence mapping uses integer lat/lon and float32 radius, retains original-plan digest and quantization metadata, and compares AP-shaped readback rather than pretend descriptor tokens. Current sender, strict GCS recipient, externally supplied connection context, packet sequencing and transaction phase are correlation evidence, not authentication or a new wire transaction ID. A single bounded transaction per instance avoids reusing a link for a delayed prior mission reply; indistinguishable on-wire replays remain a limitation requiring authenticated real transport later.

Observed raw readonly parameters are not universal normalized failsafe settings. Standard packets do not carry several APFLIGHT36 requirements (remaining Wh, AP-side GCS receipt history, reliable RC-loss event, throttle-minimum context, Home datum identity). Wire-only assessments must therefore be incomplete. Explicit synthetic supplements can exercise the full mock path, with provenance and operational flags false. FENCE_STATUS, COMMAND_ACK and heartbeat mode changes remain separate observations with execution/cause unproven.

Frozen modules are imported without writes; original regression corpus is replayed into new evidence only. Historical SHA gate restored by RESTORE41 is checked again before/after, never overwritten or promoted to endurance acceptance. Runtime/signing/hardware conformance is deferred by the user.
