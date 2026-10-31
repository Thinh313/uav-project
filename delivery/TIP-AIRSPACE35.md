# AIRSPACE35 — Airspace & FlightOps, then native integration

Authorization: user 14/10/2026 requests stepwise implementation of GCS34 proposal. Existing development APK authorization retained. One agent switches specification/build/verify; no independent audit claim. Reviewable isolated implementation is authorized, without touching frozen source/candidate/SOT/trust/ENDURE or creating a software-release signature.

## Task graph

1. Contract + capability/authority/alert UX map; map all47 catalog requirements to implementation/evidence gates.
2. Bounded offline geo-awareness: polygon/holes/concavity, exact segment/corridor intersection, UTC exposure, altitude datum conversion and uncertainty, freshness/coverage/permission. Synthetic corpus only; no legal-provider verification or operational approval. Geofence mock upload/readback/breach is separate from airspace warning.
3. FlightOps mock: target/session/boot/link identity, observed vs requested vs ACK, ownership revocation, command timeout without retry, stable alerts, unavailable AI/video capabilities.
4. Reuse pinned NATIVE33 editor/compiler/journey and opaque Java journal in a separate native35 package. Atomic outer workspace binds inner journey and airspace/FlightOps evidence. Persist intent before mock peer; restart clears all control/preflight gates. Build with existing private development identity. Check algorithms, journal faults, host UI and APK assets/signature.
5. Actual AP fence SITL and Android/Hera gates follow only after scoped host gates and resource admission. No new SITL campaign in this pass; Android28GiB admission is unmet. SDK, provider data, live video and AI remain open.

## Requirements / AC

- R35-01: all47 feature IDs appear exactly once in staged roadmap; distinguish contract implementation, host proof, SITL and hardware acceptance.
- R35-02: finite bounded WGS84 local geometry; no hidden sampling; concavity/holes/touch/corridor cases analytic; invalid/global geometry UNKNOWN.
- R35-03: whole mission layers departure/survey/return/landing, altitude/time uncertainty, dataset SHA/revision/freshness/coverage, Home provenance; missing or unverified data UNKNOWN. Acknowledge is not permission.
- R35-04: assessment/certificate binds mission/route/context/source hashes; mutation/expiry invalidates; operationalAllowed always false.
- R35-05: mock geofence state needs exact target upload/readback and independent observed breach; no AP enforcement claim.
- R35-06: FlightOps observed mode follows fresh matched observation after ACK; wrongtarget/late/reconnect/boot/focus/stale revoke; no automatic retry or restored owner.
- R35-07: stable sorted alerts; ACK does not resolve; video age/target separate from telemetry; runtime AI unavailable.
- R35-08: integrated editable survey→preflight→Fly mock→review; durable outer capsule; write-unknown blocks output, restart retains evidence and interrupts unfinished inner journey.
- R35-09: scoped development APK zero permissions, exact assets/DEX/signature; host fault/browser tests and source/preservation hashes. Actual Android/native touch/input/video NOT_CHECKED.
- R35-10: actual AP fence upload/readback/breach SITL; NOT_CHECKED pending its scoped run (no inference from mock).
- R35-11: actual Android force-stop/reboot/ART; NOT_CHECKED while28GiB admission unavailable.
- R35-12: protect existing SHA baseline and20GiB floor; no installs/project copies; clean owned build/test scratch and preserve every failed receipt.

Policy choices: restricted synthetic permission must bind source+zone+route+time+altitude; prohibited stays blocked in mock. Real legal policy not inferred. Small local projection covers ≤10km at |lat|≤70° with a conservative extent/latitude-dependent model margin; no ellipsoid/global/terrain capability. Max128zones, rings256vertices total each, route2048segments; reject rather than truncate. Projection margin=1+0.007*extent+2*extent²*(1+abs(tan(latitude)))/6371008.8 meters; synthetic engineering bound, not geodetic certification. Dataset maxage1day; preflight30s. Resource/geometry performance metrics are host measurements, not Hera flight accuracy.

Verification refinement: hard cap1024findings/1,000,000candidate edges; bounding-box prefilter and explicit incomplete UNKNOWN, never silently truncate clearance. WGS84 metadata rounds9decimal places and leg duration uses integer millimeters before milliseconds; compiler mission bytes remain exact. Assessment intervals inflate outward1e-8 in t and margin rounds conservatively to mm to stabilize Chromium/Node replay. Datum IDs and Home reference IDs must match; AGL remains UNKNOWN without terrain. Small APK build admission128MiB is independent of unchanged Android28GiB gate; own scratch allocation sampled in receipt, no dependency install or new image.
