# ADR-011 · QGC Plan interchange without application coupling

Accepted locally within owner-authorized M2 on 2026-10-12. The production GCS stays independent. Inspect official QGC v5.1.5 schema serializers and selected upstream fixture; implement our own bounded parser/exporter, without compiling/linking QGC or reusing RAGAS code.

Keep two contracts: lossless source intake and a strict simulator execution profile. Plan v1/mission v2 data are retained even when execution is unsupported. Survey v4/v5 cached Items may be flattened only as an explicitly reviewed stored-command snapshot. Polygon/camera regeneration is not claimed. Geofence/rally are preserved in intake and block this mission-only adapter when nonempty.

Only pinned ArduCopter 4.7.1 quad, relative-home navigation, takeoff-first/RTL-last, bounded area/altitude and current supported speed/distance-camera commands enter loopback SITL. Import never relocates home, changes datum, promotes hardware facts or sends commands. Source original bytes remain in the envelope; server recompiles them. A separate companion receipt carries simulation provenance because standard .plan alone cannot enforce simulator-only use in another GCS.

Copter AP_Mission accepts unspecified NAV yaw but does not store it in these command records. Normalize null yaw to zero for this pinned adapter, display this normalization and retain null in original Plan. Other unsupported values fail closed. Current-item is live mission progress and cannot be content-compared; autocontinue is compared, and false is rejected because this autopilot stores true.

Costs: no universal QGC compatibility claim, unsupported payload/mission patterns remain review-only, application-level QGC open/save is a separate unrun gate. Benefits: no proprietary controller dependency, traceable exchange and actual autopilot evidence now.
