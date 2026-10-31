# Sensor-loss safety follow-up — proposal, not implemented

16/10/2026. Scope: next isolated requirement after the diagnostic campaign. Canonical SOT/roadmap/source/candidate and ENDURE remain frozen. Actual campaign outcomes and counts live in campaign-summary.json; no prediction here is an accepted result.

Loss of proximity capability must be explicit operator state, distinct from “path clear.” No fresh obstacle messages can mean sensor loss, telemetry loss or another unavailable path; it cannot authorize continued advance by itself. Bind health/source/aircraft/boot/frame/time to the active input owner. Freshness budgets must be versioned against actual firmware/transport and measured dynamics.

Proposed next increment: mock an assistance contract that marks avoidance unavailable, refuses continued forward command authority from the AERIS-owned route according to a declared policy, records the intervention, and requires explicit revalidation before authority returns. Then test its actual vehicle response on isolated SITL under held input, latency, restored sensors and competing input sources. A neutral/braking command or its ACK is not proof of a stop or sufficient clearance. Action selection must be qualified for mode, velocity, available positioning and operator ownership; this note does not prescribe automatic LAND or change real-radio behavior.

Do not claim AERIS can override a physical Hera radio path without SDK/interface/authority evidence. Sensor recovery does not silently resurrect stale commands, leases or ownership. Require observed response, no duplicate sends, clear operator indication and preserved before/after raw evidence. Keep exact failure outcomes from77; a later mitigation does not rewrite them.

Real Hera dynamics, multiple obstacles/sensors, mounting/FOV, blind spots, wind/payload and physical stopping tolerances still require the15data groups recorded in SIMFEEDBACK75. No flight-ready claim or signature until those separate gates are met.
