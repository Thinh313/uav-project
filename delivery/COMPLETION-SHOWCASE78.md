# SHOWCASE78 — browser simulation presentation

16/10/2026. **READY for scoped engineering presentation / scripted live E2E verified. Full Hera product acceptance remains PARTIAL.** Single agent performed specification, implementation and verification; no independent reviewer claim.

Open **http://127.0.0.1:8828/** for Flight Studio and **http://127.0.0.1:8828/live** for the control workspace. The presentation tab is kept open. Default recorded mode sends zero flight commands. Explicit **Bắt đầu trình diễn** enables audio; **Lặp** keeps a recorded flight cycling. Pause/seek/end silence were observed. A document-hidden/suspension guard is implemented; actual OS/tab-hidden signal handling remains NOT_CHECKED because the in-app browser visibility toggle kept document.visibilityState visible. No fake visibility event was injected to manufacture a PASS. Local glTF/PBR UAV, HDR illumination, panorama and ground come from unchanged VISUAL56 assets; no download/install/build/signing.

## Demonstrated and checked

| Scope | Evidence/result |
|---|---|
| Host contracts |36 checks: admission boundaries, HTTP/origin/path/token rejection, source catalog, stick mapping,12s script, RPM audio math. `evidence/showcase78/host-qa-final.json`. |
| Recorded 3D | Three actual SITL recordings: the new E2E empty/calm plus retained central/calm and offset/gust. New derivative rechecked the complete WAL CRC/SHA chain,134632 original intents and source SHA.122 display samples have recorded nonneutral input. Controller HUD uses logged local TX with approximate Node/backend clock-bracket midpoint alignment; it is not AP RC echo or measured input-to-actuation latency. Derivative SHA checked. Playback/pause/seek, camera controls, audio context/gain and repeat checked in browser. Timeline retains the full recording; initial playback starts1s before first estimated motor activity to skip the cold preflight wait. No original/raw frames deleted. |
| Live route | Browser → AERIS57 guarded input → SIMTRAIN53 → actual ArduCopter4.7.1 → SIM32 reference physics → 3D/audio. Explicit preflight, normal ARM, GUIDED5m, observed LOITER,12s scripted forward/yaw/lateral/back with neutral holds, one LAND, observed ground/disarm, explicit END. |
| Raw verification | Run `rad3ab2ece4a54e38a4ba`:134632 sensor/aux frames match original model, CRC/SHA chain and AP receive/parse; no admitted-frame gap.83 nonneutral RC intentions, one normal ARM with force parameter0. Five raw files re-read SHA,417947581 bytes. No inference of real images from ACK. |
| Review | Browser displayed `CURRENT_BYTES_MATCH_RECORDED_READBACK` for the new flight. Writer/backend/container closed without error. |
| Virtual sticks | Actual scripted key path qualified on SITL. Pointer forward and simultaneous yaw/lift, release, authority-loss cancellation and no auto-resume checked in separate DOM-only mock with network disabled. Physical pointer-drag→AP coupled run remains NOT_CHECKED. |
| Mission/QGC | Saved offline KML corridor `819c340b5cee…`:8 legs/3556m,392 expected commands, nominal14.8min, GSD1.03cm/px under explicit flat-terrain/camera assumptions. QGC negative fixture detected command206→0 as one executable semantic difference. This corridor was not uploaded or flown AUTO. |
| Restart | Controlled showcase server restart retained the plan/journal; authority was not restored.23 capability groups link retained reports with SHA and scope, including Phase One/dual-operator, journal/archive/receiver/identity and known sensor-loss failure. |
| Visual | Browser inspected at1920×1080 and default viewport; fullscreen actually entered1728×1084. These are host browser checks, not physical projector/customer acceptance. |

## Performance and remaining gaps

Actual receive RTF **0.9973276403×**, minimum complete5s window **0.8631432675×**. Stable1× remains unaccepted. Requested physics1200Hz, speedup1, cap500000µs and fsync-before-sensor were unchanged. Browser live sample showed approximately58Hz,5844 triangles/four rotors; this is a short renderer observation, not an end-to-end latency/GPU-completion guarantee.

Live workspace uses the unchanged SIM32 RPM synthesis; Flight Studio uses new procedural partials/noise driven by estimated RPM. Audio context/gain were checked, but physical listening/speaker output, measured Hera acoustics/SPL and projector hardware are **NOT_CHECKED**. Aircraft mass/CG/inertia/wind are provisional reference profiles, not a measured Hera digital twin. Panorama is photographic projection, not surveyed terrain/collision geometry. Rain/collision/contact response, sling load/motor-failure fidelity and hardware HID/HeraHub are not demonstrated as complete.

AUTO survey, live Phase One capture, all-payload integration, two physical operators and AI autonomy are not silently promoted by their contract/mock reports. SIMDROP77 recorded an unresolved sensor-loss safety failure; this showcase does not claim a successful mitigation. Catalog links are evidence navigation, not operational integration of all23 groups.

The actual AP run used the final control helper and unchanged core route. Later catalog/replay-loop/report refinements received browser/host checks without a second actual flight. The automated UI reviewer initially rejected an END attempt while the last visible state was airborne. No alternative route was used: a fresh UI showed ground/disarmed, then the explicit END succeeded; records remain intact.

## Preservation, resources and handoff

Initial18.768GiB admission was blocked. Small isolated preparation began after capacity rose above20GiB. Actual launch recorded31176515584 free bytes and passed the28GiB showcase gate plus inherited quota/pins. Existing20GiB floor guards remained enabled. Current point-in-time final verification recorded30.136GiB; no claim of continuously sampled minimum free space.

44,100 existing protected paths matched expected SHA maps at before/after checks:0 missing/changed. This is not ENDURE24h acceptance or proof of continuous path presence. No frozen source/candidate/SOT/trust/ENDURE rewrite, new software signature, SDK, APK or emulator. New simulation run evidence was appended and retained. Verification is in `evidence/showcase78/verification.json` and `preservation-after.json`.

Preview+backend stay available, with no active AP/container/lease at handoff. All flight starts remain explicit and quota/resource/preflight guarded. No automatic HTTP retry or authority recovery. The temporary input-mock server and QA listeners were stopped. Owned Docker runtime stopped/removed normally, evidence retained; image prune reclaimed0B. No temporary project copies, dependency installs or scratch folders were created/deleted. New flight allocated approximately403.26MiB; showcase artifacts were approximately1.8MiB before final report/fingerprint.

## Presenter sequence

1. Flight Studio: choose the new E2E flight, central/calm or offset/gust, click **Bắt đầu trình diễn**, enable **Lặp**, enter fullscreen. Explain that the source is recorded SITL and sound is synthesized.
2. For live control, open **Điều khiển trực tiếp**. Verify fresh≥28GiB, inherited retained quota and no active run. Choose a reference profile; explicitly start one bounded session. Cold EKF/Home may take40–50s; refresh configuration once ready. Do not force arm, retry uncertain writes or bypass checks.
3. Explicit takeoff/LOITER, then virtual sticks/keyboard or **Chạy bài điều khiển ·12s**. Focus loss releases authority; reclaim explicitly. LAND well before the120sim/150host-second deadline, observe ground/disarm, then END and review raw. Do not close an airborne session to force a pass.
4. Show offline KML/QGC and23-group evidence catalog separately; distinguish mock/replay, actual SITL and unfinished hardware integration. Physical projector/audio rehearsal is still required before promising a customer-ready demonstration.
