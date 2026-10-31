# NATIVE29 · Native operator journey, isolated preparation

Android Views/Java shell for six captured survey plans → synthetic preflight → mock Fly → immutable historical review. It imports compiled contracts from the existing frozen survey/compiler/profile core read-only. It neither sends MAVLink nor integrates into frozen Fly. There is no SDK, radio, live vehicle input, real camera stream or signing operation.

The catalogue selects small/field/oblique surveys at 60/80 m in the existing flat SITL world. This is not an arbitrary native AOI editor. Changing a draft invalidates all gates. Home, altitude datum, current mission digest, session/generation/revision and four synthetic profile values must match before explicit start. Unknown observations default to unknown and fail closed. ACK alone never advances or completes a mission. Each route point and explicit mock landing are separate transitions.

Focus loss is UI suspension; aircraft HOLD is a distinct explicit mock action. Link loss, reboot, clock regression and active preflight mismatch interrupt the mock run. Restart offers historical review and a fresh draft, without restoring input, run authority or playback.

Mock input uses the existing N24 single-axis neutral/deadman/calibration gate plus explicit manual/front-gimbal/centre-gimbal roles. Manual acquisition requires mock HOLD. It does not establish physical mappings or implement full RC control. Native mock neutral samples continue only while their explicit source remains held and foreground; acquisition never occurs automatically. The inherited inner gate's label remains `MOCK_GIMBAL_OWNER`; the wrapper supplies the role and target.

Native playback verifies the original synthetic VP8 asset and uses a single lifecycle/generation-bound MediaPlayer. Android execution is NOT_CHECKED. The browser reference consumes actual pure-Java snapshots and can decode the synthetic clip in Chromium; it is not an Android screenshot or a native decoder measurement.

Historical records retain exact canonical event bodies and exact compiled mission bytes alongside parsed JSON. SHA detects corruption; it is not authenticated aircraft evidence. Host storage refuses corruption, quota exhaustion and existing pending-file collisions without deleting evidence. Android filesystem/provider durability and SAF export execution remain NOT_CHECKED.

From the project root:

```sh
node native/shell29/catalog.mjs
python3 native/shell29/build.py
node native/shell29/contract-qa.mjs
node native/shell29/browser-qa.mjs
python3 native/shell29/verify.py
node --max-old-space-size=64 native/shell29/walkthrough/server.mjs
```

Build uses the existing JDK/Android tools, checks disk space before work, removes only its `.build` scratch, and produces `dist/aeris-native29-unsigned.apk`. No debug/release keys are read and no APK is signed. This artifact is not a normal installable signed Android app. No emulator/device is available in the checked local paths. The GET-only host reference listens at `http://127.0.0.1:8794/`, with no command/data-write endpoint. Do not launch an ENDURE campaign or run legacy build helpers as part of this module.

Evidence: `evidence/native29/verification.json`, `delivery/COMPLETION-NATIVE29.md`. All runtime/Hera/device/SDK/physical video/input/24h acceptance requires separate evidence; canonical SOT and frozen baselines remain untouched.
