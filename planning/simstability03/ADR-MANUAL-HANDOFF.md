# Explicit manual handoff in simulator adapter revision03

Observed in actual run rd3d0444987034612aa66: GUIDED takeoff reached 4.57m, then automatic LOITER selection with default simulator throttle caused descent before the operator acquired input authority. No RC override intents occurred. This is not a passing manual mission despite an observed LAND/ground/disarm session ending.

Keep GUIDED position hold after takeoff. An explicit neutral claim reserves the fresh caller challenge and performs a bounded mode handoff: fixed neutral safety channels, observed LOITER, generation/session/boot checks, then a NEUTRAL_REQUIRED lease. Input TTL remains200ms and first neutral acknowledgement is still mandatory. Pending claim has no active manual axes and can be cancelled. LAND/closing fences late callbacks and owns precedence.

Pointer release, input expiry or background removes authority immediately, requests observed GUIDED position hold, then releases RC override. A narrow canonical-neutral safety packet may be emitted on stale telemetry only on the already-owned same socket/session/boot/run, exact42/1 and matching LIVE backend epoch. It cannot emit arbitrary axes, change mode or assert a successful hold without the original freshness and observation gates. Unconfirmed cleanup is recorded as uncertainty.

No reference model, speedup1,500ms cap, source/candidate, ENDURE, firmware parameter policy or physical-aircraft integration changes. The proposal is tested with original Authority logic and mock wire cancellation/expiry/closed capture cases first. Actual APK–SITL mode, pose, input sequence and failure behavior must independently pass; this ADR and mock counts are not flight acceptance.
