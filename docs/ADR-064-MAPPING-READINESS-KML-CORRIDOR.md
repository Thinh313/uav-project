# ADR064 · Isolated acquisition readiness, not operational flight readiness

Accepted for mock/replay implementation15/10/2026. User authorizes Mapping Readiness and KML/corridor while frozen source/candidate/ENDURE remain untouched.

Keep KML document semantics, compiled acquisition geometry, observed readiness, human review and journal as separate versioned objects. Only a current identity/boot/clock-bound synthetic observation can permit an explicitly confirmed mock run. Raw or imported records never confer authority. No network/flight API or actual image exists in this module.

Strict Python XML parsing is a host adapter; Android XML integration is deferred. ClampToGround coordinates identify AOI, not vehicle altitude; retained Z does not become AGL. Absolute/relative altitude and inner rings are inspection-only in this increment. Corridor uses square-capped per-segment survey rectangles with deliberate overlap at bends. This avoids claiming that naive mitered offsets cover bends or stay within a road. It can create duplicates and outside-area capture/transits. Route safety, continuous achievable camera coverage, dynamics and terrain remain NOT_CHECKED.

Readiness gates include camera profile and observed setting equality, test fixture, nav/payload distinction, correction freshness and independently declared reference frame/base. PPK recording preparedness is not PPK processing/accuracy acceptance. Nominal GSD/blur/footprints are model predictions. Trigger, observed exposure event and file inventory remain distinct; an ACK is never image proof.

Persistence is bounded no-overwrite SHA-chained draft/event history in a new root, reread and recompiled after process restart. Never resume mock authority after restart. Keep torn/unknown files and block; no automatic pruning or repair. Old previews and protected data are read-only references.
