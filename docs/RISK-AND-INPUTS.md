# Risks and next inputs

| ID | Severity | Condition / next evidence | Current disposition |
|---|---|---|---|
| R-001 | P1 for A/B | Installed RAGAS binary/config/version and black-box scenario evidence | Owner excludes RAGAS source reuse. Source access is not a dependency; installed comparator execution remains NOT_CHECKED. |
| R-002 | P0 | Drone/firmware/controller/camera/radio configuration and responsible integration engineer | Hera controller target supplied; 25 internal office documents indexed. HeraHub 2.0 model candidate/spec claims recorded. Exact revision/density/input map/RF/payload still unknown; brightness is adequate by owner decision and non-blocking; runtime resources will be discovered. See HERA-CONTROLLER-BASELINE. Legacy rehearsal remains synthetic; FLIGHT01 adds a real simulator-only MAVLink adapter. |
| R-003 | P0 | Altitude semantics, geoid/DEM quality, geofence, mission upload and camera actuation | FLIGHT01 validates a flat-world SITL mission/readback/control slice. Operational datums/DEM/geofence and hardware camera/HIL remain open. |
| R-004 | P1 | Camera calibration, min interval, actual GSD and image quality | Synthetic camera; optical model only. |
| R-005 | P1 | CPU/GPU/memory/end-to-end video and telemetry latency | No product/hardware benchmark. |
| R-006 | P1 | RAGAS versionCode, updater logic, signed binary/SBOM | Public Android manifest 4.0.14/build111/arm64-v8a captured; installed build, package certificate, min/target SDK and update compatibility unknown. The earlier reused-b111 observation remains a hypothesis, not an OTA bug. |
| R-007 | P1 | Operator study of survey workflow vs current RAGAS/DJI | Unrun. Software QA does not establish UX competitiveness. |
| R-008 | P2 tooling | Transfer Refinery bites CLI assumes a distribution for every domain | Original full suite fails denominator bite for rollup_field=null. Applicable checks run through project wrapper with explicit N/A; full receipt retained, kernel unchanged. |

Owner to obtain missing hardware/SDK details and A/B comparator records: user/AI Officer RtR, with RtR's engineering owners. The current agent can research public materials and continue non-hardware work; no inferred authorization to message colleagues.

Useful input bundle: HeraHub SDK/docs, exact controller OS/SoC/RAM, vehicle/autopilot firmware, payload/lens/calibration profiles, radio transport/topology, 5 representative mission files, logs from normal/interrupted/camera-failure surveys, operator task descriptions. Begin with one supported configuration before multiplying variants.

HERA02 refines the required input to SDK/input trace, installed build, link endpoints, live stream descriptors and power API. See `HERAHUB-INTEGRATION-BACKLOG.md`; contract/replay/survey fixture work can proceed without settling display nits or nominal storage.

SURVEY01: component BOM supplied (41 sheets, variants/hidden masters) and mirrored in project SOT. Exact as-built remains unknown. WGS84 polygon/ideal camera engine is implemented only on a flat reference; missing DEM/AGL blocks readiness. Native input/video/power, QGC parity and HIL remain pending; FLIGHT01 supplies the first actual SITL slice. 32 pre-existing cached BOM errors are flagged; no repairs or count rollups inferred.
