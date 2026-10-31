# CLOCKVIDEO05 UI / Android QA handoff

Builder source preparation only. No ADB, emulator, AP, browser runtime, install, build, signature or OCR compilation executed by this Builder.

## Geometry and evidence contract

Flight controls are in a non-scrolling 2×3 dock. The mission/profile/checklist/diagnostic area scrolls independently. Home reserves32px before arm; entering Home review cannot shift controls. Payload has its own fixed six-button discovery/select/grant/gimbal/capture/old-context dock, with settings/status in a separate scroller. Reboot and cut remain visible in the flight dock. At 1280×752 the console and receiver occupy separate rectangles; actual Android screenshots must verify computed CSS, font rendering and fully visible canvas. Pure source checks do not prove pixels. At viewport heights below600px, inherited deliberate console-open video hiding remains: no simultaneous video coverage claim there. Close the console or use the declared evaluation viewport.

Each target has semantic label, enabled phase, viewport rectangle, ancestor clipping checks and five hit-test points. A challenge issued on the Node clock precedes DOM sampling. The host consumes it once and exposes conservative challenge-issued-to-now age; Python never subtracts clocks. This diagnostic is not authority. Root must inspect an actual screenshot reference before using the helper. Fresh observation and screenshot are obtained for every tap, and geometry, client identity/epoch/instance, run, boot, model, plan and video config must still match. Current phase remains exact throughout screenshot-to-tap. The only pre-arm reference phase progressions are the explicit target-specific L2 rules in qa-ui.py: DISARMED to ARMED_HOME_REVIEW for AUTO with current Home gate greater than1800ms; DISARMED to AUTO for qualified video/payload/reboot and declared navigation/save/close. Airborne actions require current fresh modeAUTO, armed and height greater than5m; payload/capture/reboot additionally require a current unexpired lease bound to selected station/device and exact client instance. A changed run after fault always needs a new human-inspected reference. Checklist changes cannot move the dock. Expanded fault details intentionally overlay controls; hit tests reject occluded targets.

`uiActionId` is a random diagnostic identifier from one visible UI dispatch, echoed by host success/error responses and recorded alongside ACTION_END. Only an exact terminal receipt lets the harness advance. Rejection, absent acknowledgement or uncertainty stops, with no second tap/retry. Connect/close have explicit permitted run transitions; other actions cannot ACK after a different current run. A media receipt acknowledges the viewer operation, not AP/payload execution. Capture only ACKs after the synthetic committed-capture receipt. A correlated negative guard is required for the old-context refusal diagnostic; network/parse/timeout/wrong-action responses remain uncertainty, and unexpected command acceptance fails the diagnostic.

One explicit `Kiểm quyền cũ · mock` button retains at most one original payload context/token in memory only at an explicit fault/revoke boundary. It sends one synthetic gimbal command on click using original client identity. It reports the exact refusal and never calls that lease-specific proof unless the underlying error warrants it. Reboot pre/post durable revocation remains independent evidence. No restoration or automatic replay.

## Root-only commands

Run pure policies before runtime:

```
node planning/clockvideo05/qa-ui-mock.mjs
PYTHONDONTWRITEBYTECODE=1 python3 planning/clockvideo05/qa-runtime-mock.py
python3 planning/clockvideo05/qa-runtime.py --plan
```

Root starts only after independent source freeze/pins/admission gate:

```
python3 planning/clockvideo05/qa-runtime.py --start 01
python3 planning/clockvideo05/qa-device-actions.py 01 setup
python3 planning/clockvideo05/qa-device.py 01 android-device-inventory01
python3 planning/clockvideo05/qa-device-actions.py 01 store-before
python3 planning/clockvideo05/qa-device-actions.py 01 start
python3 planning/clockvideo05/qa-ui.py prepare 01 nominal-flight-reference01 --native-frame <x0> <y0> <x1> <y1>
```

Inspect that PNG. Use its `-reference.json` path for `sequence 01 <reference> <unique-prefix> field-preflight field-grant field-upload`. After a separately reviewed reference of the same stable dock, `field-arm field-auto` can be chained without a tool roundtrip; AUTO still requires the actual current Home gate greater than1800ms. No Home/freshness/speedup threshold changes. Controls must already be visible; the helper never opens hidden tabs or scrolls without observation.

For payload and media, Root first makes the relevant actual tab visible, captures and inspects a new reference, then dispatches allowed target IDs. Source is independently visible Chrome on the host. Stage scripts/source/viewer before arming, grant payload late, then measure/gimbal/capture/pause only within the recorded fresh airborne overlap. Reboot requires a separate flight and an actual unexpired exact lease; its always-visible simulation-only control is bound by the inspected flight reference. The old-context probe is one explicit UI action after fault. A later foreground restart/SAF must be performed by Root with no implicit authority restoration.

## Bounded budget

Only attempts01/02 and2cold boots,20min each, unchanged development02 APK SHA df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d. Cached API33 arm64,4CPU2GiB,gpu-host,no-snapshot.31samples over≥30s, all≥29GiB, decline≤256MiB. Refusals retain exact samples before launch intent; runtime250ms guard28GiB and15s forecast20GiB. Task evidence96MiB plus independently bounded AP append. AP slots10→12 are owned by the host Builder/root, not consumed by these preparation scripts. No downloads or new caches. No process was started and no scratch data was created by this Builder.


## Staged airborne choreography (Root only)

Prepare and inspect both flight and payload references after viewer/config is ready, while DISARMED in the same exact run. Ground initial `field-preflight` may use `qa-ui.py sequence 01 <flight-ref> <unique-prefix> field-preflight --timeout 100` to wait for sensor readiness before starting publisher. Root then explicitly grants flight, uploads/readbacks, discovers/selects payload. Grant the payload late, with at least40s of its original60s lease left before the controller. The controller explicitly refreshes preflight once immediately before arm, then performs ARM/Home/AUTO without intertool gaps, waits for actual fresh AUTO/armed/height>5 and performs visible media/capture/pause/tab/gimbal operations.

```
python3 planning/clockvideo05/qa-airborne.py --plan
python3 planning/clockvideo05/qa-airborne.py --airborne --root-reviewed --attempt 01 --flight-reference <inspected-flight-reference.json> --payload-reference <inspected-payload-reference.json> --prefix nominal-airborne01
```

For the separate fault run use attempt02, new inspected references and unique prefix plus `--fault`. It adds visible tab-flight and reboot after gimbal, still requiring an exact unexpired selected-payload lease. Every step uses `qa-ui.dispatch`, fresh screenshot/challenge/context/hit-tested target and terminal receipt, with no retry. The controller's positive status means UI sequence acknowledged only; raw mission, media overlap, capture metadata and revocation/reboot replay remain mandatory. Root saves the30s report later via visible UI. There is no automatic source restart, old-token replay or authority restoration.


## Ground native coordinate calibration

DOM rectangles are CSS/WebView coordinates, not physical screen coordinates. Before any control tap, Root derives current WebView content frame on the owned emulator while on the ground, using actual PNG and owned native window/UI hierarchy if necessary. Do not assume previous inset values. `qa-ui.py prepare` requires the explicit native frame; the reference binds actual PNG size, CSS viewport/dpr, uniform scale and current owned ShellActivity window frame lines. Each tap rechecks fresh screen dimensions, CSS viewport, owned currentfocus and exact frame/inset fingerprint, then converts the DOM center into physical ADB coordinates. Changed rotation, viewport, window, focus or insets refuse before dispatch. Only bounded `dumpsys window windows` is used during dispatch, never UIAutomator.
