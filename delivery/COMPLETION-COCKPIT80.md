# COCKPIT80 — design review mock

16/10/2026. User requested mock before native implementation. Delivered a separate interactive design concept at localhost8840; no new APK, native implementation, release signature, SDK/device/SITL or frozen app changes.

The scene-first interface uses a compact64px header,72px rail and84px fixed telemetry/actions at1280×800. The camera/map stage occupies76.9% of the viewport; task panes are contextual. Black/white are structural, RtR yellow is an accent. Existing Barlow fonts contain all104 tested Vietnamese characters. Four views cover Fly, mission planning, preflight and review; day/night chrome and a clean scene view are included.

Physical-input UX is proposed, not verified Hera firmware mapping: sticks keep flight semantics, dedicated navigation controls handle menus, C1/C2 previews and local pilot/payload roles are separate from actual grants. No virtual-stick overlays occupy the default flight viewport. The input sheet displays channels only; it does not drive physics. Hold-to-confirm return has touch/keyboard cancellation, modal focus containment and fresh local role/link checks.

73 browser checks passed, plus final visual captures at1280/1024/1920. Browser tests include role restriction, lost-video versus lost-link distinction, stale-looking telemetry removal, no command queue, modal focus and56px target bounds. Original failed receipts retained. The root app selector bug was fixed, not dismissed as a harness timing issue. A final navigation icon change and input-hint copy are visual/copy refinements after functional acceptance; final captures and browser preview show the current version.

Files: `planning/cockpit80/README.md`, `DESIGN.md`, `ASSET-PROMPT.md`, HTML/CSS/module and read-only preview server. Evidence: `evidence/cockpit80/browser-qa.json`, `font-glyph-qa.json`, `visual-qa.json`, `preservation.json`, `verification.json`, `fingerprints.json` and hero screenshots. Generated image source/prompt is disclosed; no raster UI is baked into it. Reference artwork is not copied into the UI.

Runtime: only the mock localhost server remains for user review (port8840); headless QA browsers are closed. No dependency install, project copy, emulator image, build folder or Docker task. Disk remains above20GiB. Preservation receipt binds the older frozen map and NATIVE79 artifact manifest; it is a point-in-time SHA verification, not a continuous-presence claim.

Next gate: user visual/interaction review of this concrete mock, then scoped native implementation. Actual Hera touch/joystick/buttons, glove/outdoor ergonomics, render/input/video latency, native layout and flight authority integration are NOT_CHECKED. Do not call this commercial/DJI parity or aircraft acceptance.

## Glass01 visual revision

The user then requested translucent blur glass and unified alignment. Current material/geometry is described in planning/cockpit80/GLASS-REVISION.md. Background now fills the viewport under glass chrome;77% described the original uncovered stage. Camera controls share one dock/axis; heading and reticle share a scene axis. Actual CUA checks at1280×800 and1024×600 are in evidence/cockpit80/glass01/browser-layout.json, alongside current screenshots. Mock event logic is byte-identical; previous73 checks remain prior-revision evidence. No native/candidate/ENDURE change.
