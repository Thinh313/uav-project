# TIP-REVIEW04 · durable execution record and post-flight review

Owner2026-10-12 authorizes roadmap execution-record/post-mission review and SITL, without SDK/device. Continue Contractor→Builder→Verify in one agent; no independent-review or external-release claim. Preserve QGC01–03 evidence.

AC01 durable local records bound to one upload/recovery attempt, source/compiled/readback, aircraft/session/build/world/time identity; capture before disconnect/reset and survive server restart. Append/hash-chain integrity, bounded disk use, storage failures surfaced. Recovered open records remain unknown.
AC02 conservative evidence-derived outcomes: completed requires within-record successful readback + observed AUTO + final reached + fresh disarm/landed, no interruption; stopped/incomplete/unknown remain distinct. ACK, current index, recovered/history-less observation or operator review never promotes completion.
AC03 preserve validated QGC derivation ancestry when supplied; source/hash mismatch rejected before upload. Review/import/list never sends a flight command. Freeze relevant parameter/profile observations when available, explicitly missing otherwise.
AC04 operator review screen lists sealed historical attempts with outcome/source/vehicle/height/camera scope, timeline/reached gaps, integrity and evidence limits; original sources/export retained, append-only operator decisions bound to record digest. Review is independent of live/current draft/session and remains available after disconnect/restart.
AC05 offline exported-record import validates version/hash chain/source/readback/outcome; rejects mutation/corruption/unsupported versions atomically. Offline review cannot start/resume a vehicle or silently overwrite evidence.
AC06 actual SITL completed and deliberately interrupted flights, archive across disconnect/server restart, readback/parameter and landing evidence; restored observation never self-certifies completed history. No hardware camera/SDK claim.
AC07 unit/API/storage-failure/restart/tamper tests and browser/responsive/offline/operator review checks. Failure cannot be hidden by an overall count; required unrun checks NOT_CHECKED.
AC08 Completion/REQ coverage, manifests and SOT owner-intent addition through applicable gates; cleanup test scratch and retain fixed normal disarmed simulator. No project copy, dependency/native build or production release.
