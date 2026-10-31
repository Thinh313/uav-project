# APFLIGHT36 — AP-FLIGHTOPS mock/replay preparation

Isolated source-only module for F08/F10/F11. No APK build, native/Fly integration, SDK, sockets, MAVLink emitter, SITL/emulator, flight/parameter writes, release signing or ENDURE changes. Existing Node and stdlib only. Below20GiB scope is small source/fixtures/receipts≤8MiB; no project copies/tmp/dependency install.

## Interfaces

- `fence.mjs`: validate/compile typed polygon/circle subset; `FenceSession` synthetic upload/request/ACK/readback/config/breach flow. Single inclusion AND outside every exclusion, datum band optional; unsupported holes/multiple inclusions rejected. Model classification uses uncertainty+projection margin and analytic segment caps/erosion. Touch/thin conflicts can remain UNKNOWN rather than claiming definite breach. Model violation≠AP-observed breach/action. `proof()` only after all readback items+config match. Constructor/explicit new connection never restores prior proof. ACK-only, timeout, disconnect, wrongtarget and writer unknown never become enforcement.
- `qgc.mjs`: version2 fence projection, version1 polygon/circle records; lat/lon→lon/lat explicit, original raw SHA and non-fence fields retained. Altitude/actions stay unencoded settings, not invented QGC fence fields. Real desktop fixtures are source; Home remains planned/unobserved.
- `preflight.mjs`: eight independently timestamped, typed sources—heartbeat/mode, GNSS, EKF, GCS+RC link, battery, Home, normalized readonly config and full fence proof. Profile pins Home/fence SHA/config/limits/ages. Wrong/missing/stale/unit/clock/identity inputs produce UNKNOWN; adverse known values block mock readiness. No universal firmware defaults. Failsafe expectations separate configuration and limited synthetic context (disarmed/landed/selected modes, AP-side heartbeat latch, independent RC, low/critical timers); no control outputs.
- `monitor.mjs`: per-source sequence/high-watermark and snapshot hash, stable alert episodes, consequence ordering/top3+count, ACK does not resolve; fresh clear/reappearance creates new unacknowledged episode. Old action/config/episode rejected; unexpected synthetic actions retained as mismatch, not rewritten to desired action. Default `snapshot()` is explicitly historical/as-of; call `snapshot({epoch,nowMs})` for freshness check. Stale/foreign clocks become UNKNOWN with inferred actions removed. No restored authority.
- `return.mjs`: synthetic model energy/time envelope with conservative available Wh, base/payload/mass uncertainty, wind/gust/crosswind/headwind, climb/descent/delay/landing/reserve, model domain and checked fence corridor. Current-fix start/Home endpoint/route hash/datum and candidate IDs bound. Unknown model/energy/calibration/geometry/environment/landing remains UNKNOWN. Crosswind/headwind, insufficient energy/reserve or duration can make model return infeasible. Home/alternatives scored separately; lowest-energy viable **mock** candidate is not an autonomous recommendation.
- `ledger.mjs`: bounded SHA chain and acknowledgement-before-model-output callback;256rows/256KiB. In this pass the writer is a mock/test callback, not a measured fsync service. Lost/unknown reply, suspension, clock or quota blocks publication; no automatic retry. Historical rows do not restore authority. Actual durability must use the separately accepted journal/runtime adapter later.

All result flags keep operational approval, physical execution/enforcement and Hera hardware calibration false. No measured battery/power/drag/terrain model of Hera exists here.

## Model and bounds

Local spherical projection from exact A35 geometry: |latitude|≤70°, radius≤10km; engineering model margin from extent/latitude. Not certified geodesy. Fence≤9regions/256items/64KiB; source snapshot≤256KiB. QGC polygon subset≤64vertices each, no repeated closure. Return≤8routes×64points; mass/airspeed/altitude domain checked including uncertainty.

Model assumes a uniform bounded synthetic wind over the route/horizon. Ground-speed lower envelope is sqrt(airspeed²−crosswindUpper²)+alongwindLower, rejecting unreachable/too slow conditions. Horizontal and vertical time add conservatively. Power is a declared synthetic hover mass scaling+speed penalty+aux envelope; climb adds m·g·h/efficiency. Energy integrates W·seconds/3600 plus climb Wh, delay/landing and reserve. Uncertainty parameters are assumed bounds, not measured confidence intervals; no actual Hera guarantee or meteorological forecast coverage. Temperature/voltage sag/pack condition/onboard consumption and calibration still require hardware data.

Default examples are a synthetic reference3kg quad/550W hover, not Hera BOM or performance. Unknown real data cannot pass by borrowing these values.

## Run only small mock checks

```sh
node pilot/apflight36/tests.mjs
node pilot/apflight36/replay.mjs
python3 pilot/apflight36/verify.py
```

Receipts append by attempt, including failures. Tests/replay use existing interpreter only; no network or simulator launch. Read `delivery/COMPLETION-APFLIGHT36.md` for actual results and gaps. Real wire/SITL/Android/Hera tests NOT_CHECKED. Before real transport, actual retry/frame/quantization/authentication/config semantics must be proved on the pinned AP target; this descriptor model is not protocol conformance.

An initial scan found41 previously missing protected paths. They are retained as an unresolved historical preservation incident; no restoration or silent baseline replacement. Current work compares to both historical expected hashes and observed-before state. Mock PASS cannot close that gap or authorize release/ENDURE restart.
