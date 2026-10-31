# AERIS57 · Unified simulator workspace

15/10/2026. **PARTIAL — integrated engineering workspace, not fullG1/council/Hera/product acceptance.** Preview http://127.0.0.1:8809/. New code under pilot/aeris57; new evidence under evidence/aeris57 plus append-only fresh SIMTRAIN53 run directories. Source/candidate/SOT/trust/ENDURE and earlier modules unchanged. Single agent separated specification/build/verify; no independent human reviewer.

## Delivered behavior

Five views in one Barlow/RtR white–graphite/yellow workspace: Nhiệm vụ, Preflight, Fly, Review, Năng lực. Large GLB/PBR/HDRI scene receives fresh real reference physics from ArduPilot through the existing owned backend. The camera frames the region beside workflow panels; visual placement/zoom never changes aircraft pose. Defaultmute RPM synthesis reused; acoustic listening/realism not accepted.

KML polygon/corridor parsing/planning reuses mapping51, explicit feature/flat assumption, preview route and metrics, plan SHA and restart-persistent hash-chain journal. QGC comparison reuses MISSION55; run5 camera206→placeholder0 example is DIFFERENT. KML plans are not wired to upload/AUTO. Capability table exposes17 groups and source reports with SHA/scope, including native MCU, payload routing, geofence/failsafe, storage/handoff, signing/update and durability. It is a sourced inventory, not operational integration of all17 groups.

The fixed8807 adapter adds own token/origin, typed route allowlist, created session/run/boot ownership, no automatic POST retry or restored authority. Original backend alone attests target42/1, firmware4.7.1, configuration/Home and manages runtime/WAL. Explicit takeoff gesture now includes observed GUIDED5m→LOITER and immediate neutral-first claim. It closes the default-throttle gap while waiting for a separate claim. Ground claim is refused; stale200ms/focus/workflow change releases and requires a new explicit claim. Short key taps send immediately plus50ms input cadence. LAND clears local lease/keys first, then requires ground/disarm before end.

## Actual run ledger — all starts retained

|Run|Outcome|Frames|Whole receive RTF|Scope|
|---|---|---:|---:|---|
|ra45934624373400c8399|Failed unarmed deadline|144000|1.0001148|No accepted closure; not a successful flight|
|re5a3da42e7054469a44e|Failed unarmed deadline|144000|0.9414412|No arm/takeoff request; pacing failed|
|re60bf5311cd247d4ad20|Managed LAND/close; raw/oracle PASS|91673|1.0002151|Separate delayed claim; grounded before native-key test,0 non-neutral RC frames|
|rac6f221623f243eeb292|Managed LAND/close; raw/oracle PASS|88143|0.9866904|Explicit neutral handoff held≈5m;4 non-neutral RC packets, workflow release/reclaim, LAND|

Original-model exact sensor/aux frames on successful closed runs: **179816**. Pha đọc lại riêng of all4 WALs verifies CRC/SHA-chain/RX→INTENT→SENT conservation for **467816** frames. The **288000** failed-run frames remain failed; they are not added to accepted flights. Current SHA of all5 canonical raw files checked for each successful closure. AP image/binary/rate/speedup/cap pinned in original launch receipts. No admitted frame was dropped to improve rendering.

Run3 successful raw integrity does **not** mean accepted1× pacing:5s RTF minimum0.8004332, receive-gap p99 6.805875ms/max54.533625ms. Run2 minimum0.9939955 includes a short final bucket; raw buckets are retained rather than normalized away. Presentation was explicitly capped60Hz after the early120Hz run; host conditions were not counterbalanced, so this is not an A/B proof of the cap's effect. No full G1, sustained60fps or input-to-photon acceptance.

The ledger contains4 starts while the earlier narration counted3. `start-accounting-incident.json` corrects that count and identifies the omitted early unarmed run. Four distinct intent/outcome pairs exist; source has no POST retry/start scheduler, but no client/actor request ID was captured, so the exact interaction origin of the extra recorded start is UNKNOWN. The self-imposed campaign count was exceeded relative to the earlier TIP narrative; no further starts were made after discovery. Bounds/quota/floor held; all evidence retained. `live-verification.json` was an incomplete3-run receipt and is superseded for totals by **live-verification-complete.json**, never overwritten.

## AC coverage

|AC|Result / evidence|
|---|---|
|01 preservation/resource|PARTIAL for campaign count; preservation/resource passed within observed host points;21,035 ordered protected hashes before/after; campaign-count deviation above recorded. No continuous-presence/ENDURE inference.|
|02 plan/KML/persistence|PASS scoped offline; actual browser compile264 planned commands, source/plan SHA, explicit assumptions, journal restart and quota/corruption/competing-writer guards.|
|03 QGC semantic|PASS scoped offline; actual run5 placeholder difference, malformed reject, equal case; no new QGC runtime/regeneration test.|
|04 adapter/authority|PASS scoped mock+SITL; target fixed via old backend, session/boot/route/origin/token and unknown-write no-retry guards.|
|05 live UI/render|PARTIAL; explicit handoff, actual RC/raw, nav-release/reclaim, LAND/close. Keyboard tap coverage only; no joystick, sustained maneuver/figure8, acoustic listening or hardware validation.|
|06 review/restart|PASS scoped host; raw SHA review, RTF shown; actual preview restart retains41 records, head and plan SHA, resets ownership, no automatic AP.|
|07 negatives/browser|PASS scoped final39 checks in qa7; earlier qa1 failure retained. Browser desktop/horizontal-bound checks at1920/1280/857/390/320. No final-page JS error observed; layout repair retained.|
|08 full coupled regression/pacing|PARTIAL; two actual closures/oracles passed but pacing matrix unaccepted; final display-only caching/frustum/labels/backdrop refinements checked browser/mock only, not another SITL run.|
|09 capability inventory|PASS sourced inventory17 groups; scope/limits and report allowlist, not a claim all modules execute live in this shell.|
|10 delivery|PASS scoped engineering handoff: startup/runbook, screenshots, reports/fingerprints; no active AP at end.|

Final mock/oracle suite **39 PASS/0 FAIL**, not a cumulative sum of qa2–qa7. It includes actual KML/semantic libraries plus synthetic adapter faults: stale/focus/neutral authority, wrong boot/route, unknown write across restart, quota, competing writer, corrupt/pending journal, LAND when separate audit is full, origin/token/path guards. qa1 used obsolete root fixtures with an invalid video-stop reserved field; fixed selection to the pinned run5 corpus, not a change to old fixtures/oracle.

Actual managed preview restart: same journal head, same plan9bbd9358cb30…,41 records, pending0/uncertain0, no restored owner or controller. `restart-before/after.json`, `exported-workspace.json`; page reload restores explicit feature/settings but resets the next flat-assumption acknowledgement. Browser fail-loud caught an accidentally nested framing helper during display refinement; moved to module scope, reloaded/reviewed successfully, retained display-framing-repair.json. No physics/flight guard bypass.

## Remaining critical path

Resolve AP/backend pacing with fixed workload and fuller clock/phase analysis before fullG1 acceptance. Then mission upload/readback/AUTO survey/corridor, guided setpoints/RTL/takeover/resume, virtual camera/gimbal images with provenance, instructor faults/scoring, tuned audio/weather/contact physics, controlled payload A/B, projector18minute rehearsal and HeraHub/native/hardware gates. Existing landscape is a photographic projection, not complete collision/terrain geometry; reference quad is not a calibrated Hera. No new software signature/APK/release/candidate selection or public publication.

All earlier previews/services kept; only new8809 preview added, source8807 backend reused. Docker runs are bounded and original owner stopped its own containers/backends; original runtime performs image-prune only, no volume/container pruning elsewhere. No project/tmp copy, dependency install or evidence deletion. Handoff disk remains above20GiB; final exact observation is in preservation-final.json. Tool/UI warnings and all failed attempts remain in receipts.

Coverage for this increment:7/10 AC scoped pass (70%),3 partial (01,05,08); this is not a software/product completion percentage. Final39-check suite is qa7. Display-camera framing now reserves the visible region beside workflow panels; reviewed at857px, no aircraft pose/physics/control change. Latest exact preservation/resource observation: preservation-handoff.json. See verification-final.json for the final NOT_READY_G1/council status.
