# ADR093 — separate evidence acceptance from safety outcome

Accepted within owner-authorized new SITL campaign,16/10/2026. Frozen source/candidate/SOT/ENDURE and closed SIMSITL76 source/evidence remain unchanged. New code lives only in pilot/simdrop77, evidence/simdrop77 and local owned state.

A sensor that stops reporting does not necessarily force a vehicle stop. Test while the same forward input remains active; do not inject an application neutral/failsafe before collecting the result. Distinguish valid-sensor braking, invalid/missing-sensor policy and experimenter intervention. Classifications are evidence-based and may be unsafe. No inference of real collision response from a virtual-plane intersection.

Reuse pinned ArduCopter internal quad and76 wire/geometry policy read-only. Small isolated client adaptation adds task77 context/port5897 and a drainable sensor gate so committed cutoff means no queued sensor input remains. Log source/frame/boot/clock and every TX intent before side effect. AP's targetless DISTANCE_SENSOR still does not authenticate peers; local context gate is not a firmware security claim.

Four independent flights counterbalance AB/BA/BA/AB. Record all failures and source versions; no automatic restart/reconnect, no relaxed firmware/arm/freshness checks. A negative fault finding can satisfy the diagnostic requirement while failing the safety behavior gate. Never state all tests passed as a substitute for reporting unsafe observations. Held-input drop ends at8guest seconds or centre-crossing bound; commanded speedup1 does not synchronize clocks or prove1×.

The3kg SIM32 reference model, calibrated Hera dynamics, encoded media/audio, native hardware/HID and aircraft flight are outside this gate. Preserve historical attempts, no software signature or external publication.
