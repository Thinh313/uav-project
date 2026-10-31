# ADR049 — AP-FLIGHTOPS preparation without runtime/source promotion

14/10/2026, accepted within explicit mock/replay authorization. AIRSPACE35 geo-awareness is not autopilot geofence enforcement or permission. Add isolated APFLIGHT36; do not alter candidate/Fly/native/ENDURE/signing/SOT.

Fence semantics chosen for this mock: one inclusion AND outside every exclusion, optional datum-bound altitude band. Refuse multiple inclusions/holes until the actual AP firmware/config/frame and QGC mapping gates establish meanings. QGC file admission is not permission to send its fence. Lat/lon order preserved explicitly, plan body hash after validation, full readback plus matching configured state needed. Transaction tokens are synthetic correlation metadata, not on-wire MAVLink authentication.

Read-only telemetry/profile/config separates each source and its freshness from decision. Missing/stale/wrongidentity/clock/unit data are UNKNOWN. GCS link and independent RC path remain separate. Configured failsafe action, limited mock expectation and actual synthetic observation are distinct; no automatic retry/arming/flight or parameter emission. Alert episodes prevent an old acknowledgement muting a new fault.

Return estimator is a synthetic envelope, not a Hera digital twin/calibrated performance model. Use lower available Wh and upper mass/wind/power/time/climb/landing/reserve cost. Wind cross-track and headwind can make return infeasible independently of battery. A route/environment/landing proof is required for mock suitability; energy-only result cannot produce operational SAFE or command RTL. Alternatives retain separate provenance and unknown/blocked reasons.

Below20GiB work limited to ≤8MiB new source+small corpus/receipts with existing interpreter; no builds or runtime download/launch. Tests are pure mock/replay, not AP SITL/Android/HIL. Separate reports/fingerprints for later permitted canonical reconcile; no implicit promotion.
