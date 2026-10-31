# ADR048 — isolated Airspace/FlightOps and durable native mock cockpit

Accepted for isolated engineering scope, 14/10/2026. Extends GCS34 proposal and NATIVE33 without changing frozen packages.

Three distinct domains: geo-awareness from source-bound4D zones; operational geofence upload/readback/breach; permission/operator policy. No domain authorizes another by implication. No real airspace provider has been verified; all synthetic clearance explicitly permits mock only. Empty maps, source-declared official flags, missing coverage/time/datum and stale inputs fail to UNKNOWN.

FlightOps keeps observed mode, requested mode, ACK and owner separately. Authority is volatile and tied to current target, boot, link generation and fresh monotonic observations. No stored owner, network radio endpoint, AI output or mock camera ACK becomes vehicle execution.

Native35 reuses exact N33 survey compiler/editor/journey and journal algorithm. A versioned outer capsule stores the inner validated journey and append-only scope-bound FlightOps/airspace audit entries. Historical observations remain evidence, never restored authority. Every accepted mock delivery needs a committed intent. Unknown persistence blocks further output until explicit reload. Development APK is a separate package using the existing private engineering identity; no candidate selection or release signature.

Bounded local metric projection, analytic clipping and segment capsules avoid dense sampling. Reject unsupported geometry rather than silently accepting.Extent/latitude-dependent horizontal model margin is a conservative engineering policy for synthetic testing, not geodetic certification. Real datasets, terrain, AP fence behavior, Android lifecycle and Hera input/video require separate gates.

Refinement after host testing: cross-runtime route metadata is quantized (≤0.1mm coordinate granularity, integer-mm timing before ceil), with outward-conservative interval/margin normalization. This does not change pinned compiled mission, physics speedup,500ms pacing cap or frames. Rehashed routes must replay the same compiler-derived route. Bounded work/result exhaustion emits incomplete UNKNOWN. Explicit datum/Home reference IDs prevent equal-label mismatches. Small build budget128MiB (separate from Android28GiB admission) with sampled allocated scratch; no runtime downloads.
