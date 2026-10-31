# Product contract35 / UX state map

These are executable mock/synthetic contracts and capability boundaries, not declared Hera support. All47 proposed requirements are staged in `delivery/ROADMAP-AIRSPACE35.json`; no requirement is claimed fully operational from contract coverage alone.

| Domain | Binding / state | Gate / unavailable behavior |
|---|---|---|
| Aircraft/input | aircraft+mission session+boot+link generation; volatile owner NONE/LOCAL_MOCK | New observation after stale/reconnect/boot never restores owner; physical joystick/calibration/RC handover unavailable |
| Modes | observed HOLD/AUTO/RTL/MANUAL separately from requested/ACK/expired/rejected | ACK alone does not move route; fresh matched observation required, AUTO needs validated snapshot/mission, no auto retry |
| Mission | immutable compiler hash, arbitrary bounded editable WGS84 polygon, explicit saved draft | Edit/recompile/background/restart revokes gates; active editor locked, unsaved text not claimed persisted |
| Airspace | source/revision/hash/origin/captured/validity/coverage, altitude datum and Home ref,4D corridor | Legal provider unverified; empty/stale/incomplete maps never operational SAFE; acknowledgement not authorization |
| Fence | explicit synthetic rule SINGLE_INCLUSION and target upload/readback/breach | ACK not readback/enforcement; no implicit hole/union conversion; actual AP fence SITL unavailable |
| Alerts | sorted consequence/urgency, stable IDs, top3+extra count; underlying condition retained | ACK is audit only. Mock healthy bool cannot accept real GNSS/EKF/battery thresholds or energy reserve |
| Payload/video | exact target/payload/frameID/origin/receive-time, freshness independent of telemetry | Physical decode/camera capture/thermal/radiometry/LRF unavailable. Prior routing/protocol evidence remains scoped, not connected to native35 |
| AI | unavailable/proposal boundary | No runtime perception/tracking/VIO/avoidance or direct AI flight output; future sensor/compute/holdout/fallback gates |
| Review | outer v35 capsule binds inner33 mission/events + full assessment inputs + mock ops chain | Semantic replay rejects rehashed fake completion/route/clearance; immutable journal; restart evidence not restored authority |
| Performance | max source/route/work/findings and host-only timed corpus | Incomplete processing→UNKNOWN. Host timings not Hera latency/FPS/endurance. No change to physics pacing/frame policy |

## Four-stage state map

- Survey: DRAFT/dirty/saved/invalid/compiled. Edit revokes all gates. Explicit save; compiler lineage retained.
- Preflight: compiled → compare full source/route/time/datum → Home + datum confirmation. BLOCKED/UNKNOWN disables mock AUTO; advisory remains visible. Source/scenario/session/expiry/focus mutation invalidates certificate.
- Fly: no source → fresh synthetic observation → explicit grant → committed mode intent → ACK-only → matched mode observation. Points/landing are separate committed mock observations. Stale/loss/boot/focus or unknown persistence removes control availability; no inferred physical RC loss.
- Review: incomplete/interrupted/completed mock explicitly separate. No captured coverage or real media from planned photo count/ACK. Export replays complete capsule; restart keeps audit and appends interruption.

Hold/RTL/manual mock requests require current verified mock transport/owner/capability; AUTO adds current preflight/mission. Geo-awareness unknown alone does not create a universal block of emergency recovery. Real return viability/Home/energy/obstacle policy must be accepted on actual aircraft before operational actions. Fixed critical bar and aligned controls survive alerts/stage changes; details scroll separately. CSS52px tests do not prove Android48dp or operator usability.
