# HERA03 v0.6 / native diagnostic foundation

Owner asks for the most reasonable complete next step on2026-10-12 and confirms no SDK/device connected. Deliver a runnable, development-signed diagnostic APK and its evidence pipeline, using the public Android APIs already available in the host SDK. This is an independent pure-native Java module; it does not select the final production GCS framework or embed the browser flight UI in an unverified WebView. No RAGAS application source.

## Artifact and build

Package `vn.rtr.aeris.diagnostic`, version0.6.0, minAPI26, targetAPI33, compiled against existing Android37.0 platform stubs with build-tools36.0.0 and existing JDK26. Minimum and target are diagnostic build choices, not measured HeraHub compatibility. The supplied device spec/public docs still identify a candidate Android13 controller; installed OS/build/ABI remain unknown.

`npm run build:native` runs javac→d8→aapt2→zipalign→apksigner locally without Gradle/network/dependency installs. Compilation/DEX/package/signature and pure model tests have real receipts. APK is `native/diagnostic/dist/aeris-diagnostic-dev.apk`; exact SHA and source/tool fingerprints are in `evidence/hera03/native-build.json`. Local development key is `.local/native-signing/diagnostic.p12`, private, excluded from source manifest/server exports and Git. It must not become a production signing key. APK signature is not device-report attestation.

Manifest requests zero permissions; backup/debugging/cleartext traffic are disabled. No native network/radio/vehicle/video connection, parameter changes, arm commands, flight bindings, camera/location/Bluetooth/phone/storage permissions or remote report upload. The only exported component is the launcher Activity. Compilation does not confirm installation, launch, SAF or input behavior on Android.

## Observation and session contract

Four groups use public native APIs: Build/version/ABI; current window size/density/rotation/insets; input devices and motion ranges; AVC/HEVC decoder enumeration. Each observation has source, status, elapsed time and value; exceptions leave null unknowns. Input descriptor is hashed; alias/revision are operator declarations, not hardware authentication. Device type stays physical-or-unknown or emulator, never automatically “verified HeraHub”. Codec enumeration/hardware flags are not live codec/stream/concurrency/latency tests.

Explicit capture toggle observes gamepad/joystick raw key/axis events while Activity has focus; ordinary keyboard text/touch are excluded. Axis sampling is bounded to20Hz, ≤64axes; trace/lifecycle ring buffers retain300events per group with dropped count and monotonically increasing global sequence. Hotplug/focus/pause/stop stop capture and leave an event boundary; resume does not resume capture automatically. Background hotplug/inputs are not continuously observed. No calibration/deadzone/channel/flight semantics are guessed from raw values.

Each Activity instance has a new capture UUID. App-private checkpoint retains a historical snapshot; reopening only labels it previous-session data. Window/input state is probed anew, not restored from disk. Saved instance state retains alias/revision only. SAF ACTION_CREATE_DOCUMENT exports a snapshot prepared before the file picker; losing focus stops capture. Exported evidence names this boundary rather than claiming continuous capture through the picker. JSON bytes are bounded512KiB; oversized/failed writes report failure.

## Import and trust

`aeris-native-capture` v1 has platform/scope/operational flag, capture wall/elapsed clocks, declared identity, producer build ID, four observations, bounded trace and null integration fields. The browser independently validates exact schema, pinned build ID, time/numeric bounds, duplicate fields/groups/sequence, source/context and integration-unknown rules before atomic local archive write. Corrupt import preserves the valid archive; stored raw bytes have SHA256 checks and can be exported/removed locally.

`replay` is REPLAY_ONLY. Physical-or-unknown/emulator data is IMPORTED_UNATTESTED. A self-reported source/build ID and JSON hash cannot prove APK origin, actual device identity or source authenticity; reports never automatically update SOT or unlock flight controls. Local retention is a historical capture, not live telemetry. Older than7days is marked stale; future clocks beyond5minutes fail for device clock review. APK hash and report build ID are separate concepts.

`native-model-replay.json` comes from the actual Java report model with explicitly synthetic observations and context replay. Cross-language tests check model→JSON→browser validation; they do not run Android native APIs. Browser screenshots show the intake/review page, not the APK's untested native UI.

## Device execution gates

Host ADB inventory found zero devices; owner confirms no SDK/device connection. These gates remain NOT_CHECKED: install/launch on exact HeraHub build, native window/insets, actual input/hotplug/focus, codec enumeration/decode, SAF export/restore and Activity/process-death behavior. Physical radio/payload SDK, video endpoints, input calibration/channel map, RTK and controller power APIs remain unknown. APK is READY_FOR_DEVICE_DIAGNOSTIC_TRIAL, not a deployed/native GCS or operational flight release. Follow HERA03-DEVICE-RUNBOOK before any device operation.
