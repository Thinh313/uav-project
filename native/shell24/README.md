# NATIVE24 · isolated native preparation

Ready in bounded host preparation scope. This is a separate Android Views/Java shell, not the production GCS, not installed HeraHub software and not a selected signed software release. No Hera SDK/device, network/flight endpoint or RAGAS application source. Candidate9/generation04 continues unchanged.

Run from the AERIS repository:

```
python3 -B native/shell24/build.py
node native/shell24/browser-qa.mjs
node native/shell24/walkthrough/server.mjs
```

Existing toolchain paths are pinned in build receipts. No Gradle/install/new venv is needed. Build refuses disk<20GiB, uses only `native/shell24/.build`, removes it in finally and never invokes `tools/build_native.py` (that historical helper mutates frozen app pins/cache). Rebuild changes the local development APK/source pins only. `make-fixture.mjs` regenerates a synthetic canvas/VP8 video and changes its bytes; retain current fixture/receipts unless intentionally preparing a new prototype revision. It uses existing Chromium, not a camera.

Artifact: `dist/aeris-native24-preparation-dev.apk`, package `vn.rtr.aeris.shell24`, version0.1.0-native24, min26/target33 compiled against existing37.0 platform. Signed using existing local diagnostic dev key read-only. Build/static checks and38 pure-Java fault tests passed; actual Android install/UI/input/SAF/checkpoint/native decoder/lifecycle remain NOT_CHECKED. The earlier development APK hash alias and build-attempt02/source receipt are retained; only `evidence/native24/native-build.json` identifies the latest build. No production/key-custody assurance.

Native UI: Plan/Fly/Review with illustrative region and a local-video area. Explicit synthetic clip or selected content document, one MediaPlayer, ≤64MiB copy, ≤1920x1080/120s after preparation. Raw gamepad observation requires focus/explicit capture and has128-row/16-axis/20Hz motion bounds. This never uses mock calibration to bind physical inputs. Pure mock replay shows neutral/deadman/session/device/calibration/focus/hotplug/stale handling. Only a simulated gimbal owner exists; complete aircraft manual-input/payload routing is future work, not hidden in this prototype.

Opening pickers, focus loss/pause/surface destruction stops player and raw capture; resume does not restart them. Old player callbacks are generation-guarded. First render event is kept separate from continuous frame-age/native camera latency; neither field is filled with guessed values. Historical bounded checkpoint cannot restore input/playback/authority. Review JSON includes self-reported build/session/clock and raw-index scope; it is not authenticated device evidence and never promotes SOT facts.

SAF requests local documents and accepts selected `content:` URI, with no persisted grant or network/camera/location/storage permission. Provider locality and native behavior still need Android tests. Copies are hashed and published under digest filenames, coalescing byte-identical copies; no published local copy is overwritten or automatically deleted. Conservative128MiB total admission and16MiB observed free-space reserve bound prototype storage; admission stops when prior copies consume the quota. This is not allocated disk reserve, production lifecycle management or tested power-loss durability. Copy30s deadline is checked between reads, not a hard interrupt of a blocking provider. Review export snapshots before opening its picker; recreation with no pending snapshot refuses export. Partial export errors remain explicit.

Browser walkthrough at127.0.0.1:8791 shows original host-Java replay bytes and actually decodes the pinned synthetic clip. This is a browser reference, not an Android screenshot.32 browser checks cover six scenarios, export, video decode, focus/workspaces, six viewport/action geometry, keyboard, corrupted clip/corpus and offline clearing. Corpus/clip hashes are checked before use. It has GET-only whitelist assets, no vehicle/data API, external endpoint or live video. Current browser decode metrics are `evidence/native24/host-video-decode.json`; no physical footage/radiometry or camera-to-display metric.

Contracts: `../../delivery/TIP-NATIVE24.md`, `../../docs/ADR-033-ISOLATED-NATIVE-SHELL.md`; evidence `../../evidence/native24`. Before/after fingerprints protect frozen source/slot/controller and older pilot modules. ENDURE20 intervals are not joined or restarted. PROTOCOL22 integrates offline into Fly only after actual ENDURE20 acceptance per its existing TIP; NATIVE24 does not extend that authorization to a live/native flight bridge.
