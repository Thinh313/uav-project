# CLOCKVIDEO05 independent QA

**NOT READY.** The selected Android UI, video, recovery and synthetic payload overlap improved and have evidence. The nominal flight did not reach confirmed ground disarm before its unchanged deadline, and the separate live-lease AP reboot was not run.

- Source/mock gate: PASS, final 226 pins and prior baselines unchanged.
- Ground UI: nine flight targets and six payload targets fully visible/unoccluded, timely benign correlated navigation receipt. Previous clipping failures retained.
- Selected media: 867 displayed frames / 30.0012s, 28.898844 FPS; P95 upper bound 54.652917ms; explicit-start to fresh ready conservatively 332.1ms; 500ms relay recovery 565.9ms. Startup binds exact config through retained startupPhases; app/codec coldness remains unproved.
- Exact overlap: 74 AUTO observation points and two successful mock payload events definitely inside the bounded video window. This is not whole-window airborne duration or real exposure.
- Synthetic capture: exact JPEG/manifest/sidecar SHA, frame5044 present in measured samples, current run/boot/model/plan and raw position reference match. Real images0; sensor exposure unknown, not survey-qualified.
- Raw: 20,018 chained records, 12 upload / 24 readback, four camera206 commands, zero PARAM writes. Direct frozen semantic readback and declared Takeoff01 alternative proof match. Last heartbeat armed, landedState4, relativeHome3.764m. Acceptedfalse/abortedtrue. The unchanged canonical receiver rejects deadline closure; integrity diagnosis is not flight acceptance.
- Separate live-lease AP reboot/old-context runtime: NOT CHECKED. Request12 unused. Native after-store/restart: NOT CHECKED because ADB collection failed after closure.
- Preservation: protected1486, native7, evidence1496, source93, prior431, both37-file source archives and226currentpins: zero differences. Ten prior plus one new request. Historical symlink SHA semantics and95preexisting deleted Git paths are explicitly outside whole-repository completeness.
- Resources: minimum recorded free space34.459GiB. Owned derived stage132files/4,716,328bytes removed; evidence preserved. A declared L2 allowed third host on same second emulator without extending original20min deadline.

Detailed machine-readable result: `evidence/field02/clockvideo05/qa-final-independent01.json`. No QA live runs or production edits. Any future deadline guard mock must be labelled source-only and cannot retroactively qualify this flight.
