# APFLIGHT36 — chuẩn bị AP-FLIGHTOPS bằng mock/replay

User authorization14/10/2026: geofence, preflight/failsafe and return reserve; no APK/SITL/emulator, no frozen source/candidate/ENDURE modification. Existing Node/stdlib only. Disk below20GiB: authorized small source/fixture/receipt work only, aggregate new namespace ≤8MiB; no installs, builds, sockets, large datasets or runtime launch. One agent switches specification/build/verify; no independent audit claim. Canonical SOT remains frozen; reports are source material only.

## Task graph / decisions

1. Pin reference inputs and protected before/after SHA; exact reuse A35 geometry/common + two real QGC fence files. ADR049 and contracts.
2. Fence plan/schema/QGC subset and mock transaction: single inclusion plus exclusions, polygon/circle, no implicit holes/multiple-inclusion semantics. Intent→item requests→ACK-only→full readback; correlate target/session/boot/link/type/index and expire without retry. Point/uncertainty geometry and synthetic AP breach/action observations are separate.
3. Typed per-source GNSS/EKF/link/RC/battery/Home/readonly-config assessments; freshness/unit/identity and expected-profile comparison. Alerts separate configured/predicted/observed behavior; ack never resolves. No parameter writes or universally inferred RTL/GCS→RC loss.
4. Return energy envelope: available Wh lower bound, base+payload mass upper bound, wind/gust/crosswind, per-leg time/power/climb/landing and reserve; Home/alternative routes and unknown feasibility. Synthetic model only; no Hera calibration/real terrain or operational return guarantee.
5. Corpus replay binds all inputs/profile/model/expected results. Adversarial wrongtarget/stale/partial/readback/clock/writer faults and independent energy/wind analytical oracles; small performance measurements. Completion and evidence/source fingerprints, exact preservation.

## REQ / acceptance

- R36-01: strict version/unit/identity/provenance bounds; unsupported/missing inputs UNKNOWN, never operational approval.
- R36-02: preserve real QGC fence subset circle/polygon inclusion flag; version/order/radius unsupported or multiple inclusions refused; full `.plan` untouched, fence export/import semantic equivalence.
- R36-03: committed mock upload intent before any descriptor; ACK≠readback; all items and exact digest/config bound; missing/mixed/count/index/late/duplicate/wrongtarget fail closed, timeout/loss/reboot no retry/restored readback.
- R36-04: local point/corridor/altitude uncertainty fence classification INSIDE/OUTSIDE/UNKNOWN; mock breach/action observation distinct from calculation/ACK and physical proof.
- R36-05: GNSS/EKF/link/RC/battery/Home/config source-by-source freshness/sequence/clock/unit/profile; normalized expected configuration only read, no inferred real AP defaults.
- R36-06: stable alert episodes and consequence order; acknowledgement retains condition, clear only fresh evidence; configured and model-expected response distinct from observed synthetic action, physical RC not inferred from GCS loss.
- R36-07: bounded conservative return time/energy, base/payload/wind uncertainty/altitude/domain, reserve and full landing; missing model/calibration/route/environment gives UNKNOWN, impossible wind or insufficient energy refused.
- R36-08: Home vs alternatives evaluated on bound route/source context; single-candidate feasibility not permission or safe/autonomous landing. No blanket RTL recommendation or flight output.
- R36-09: executable deterministic corpus replay with source/profile/model hashes, semantic revalidation and negative-bite tests; benchmark scope explicit.
- R36-10: all protected SHA unchanged, no builds/download/socket/flight commands, owned output budget/cleanup, all failures retained.

Actual AP wire compatibility/enforcement/failsafe, Android/Hera/video, calibrated battery/mass/power/terrain and ENDURE24h remain NOT_CHECKED/failed as applicable. Mock transactionUUID/session evidence cannot authenticate a real MAVLink ACK; actual mission protocol supports retransmission, whereas this intentionally restricted mock profile stops on timeout. No hidden protocol conformance claim.

Pre-build scan detected41 protected baseline discrepancies already present. `preexisting-preservation-incident.json` retains expected vs observed SHA; no restoration/history edit. Continue isolated dependency-present mocks, compare after against both historical expectations and observed-before state. R36-10 full historical preservation remains FAILED/partial until separately resolved; no release/soak gate can pass from mock results.
