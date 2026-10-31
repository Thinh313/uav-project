# FIELD02 Android design proposal

Builder native scope, 2026-10-21. Pending Contractor TIP before implementation/build.

- New `vn.rtr.aeris.field02` development-only Android Activity, no frozen-source derivation or mutation.
- Cached API33 arm64 emulator + build-tools36/JDK/android37.jar, no install/download.
- Explicit host-companion topology: control `http://127.0.0.1:8872`, media `http://127.0.0.1:8873` via ADB reverse. This is not native-direct MAVLink or hardware acceptance.
- Main-frame navigation allowlist only, subframes restricted to control/media; JavaScript bridge omitted to avoid granting callable Java methods to every frame.
- Native invokes lifecycle JS callback plus host heartbeat expiry. Background/focus loss fences authority; never resumes authority.
- Main-frame custom scheme `aeris-field02://export-workspace`, `import-workspace`, or `export-artifact?url=...&sha256=...&name=...` invokes native SAF. Source URL must still be trusted control origin; artifact path allowlist only, SHA mandatory. No redirects or arbitrary URL access.
- Workspace export fetches exact committed host bytes, stages immutable hash wrapper, fsyncs before picker; provider readback must match. Import bounds/schema/hash checked before host semantic validation + idle CAS save; authority never imported. Mirror remains readable offline but does not authorize flight.
- Capture/raw delivery downloads stage immutable verified bytes before SAF. Cancel/unknown/exported states append-only; no auto retry/deletion.
- KML/QGC chooser is Android ACTION_OPEN_DOCUMENT limited read. User gestures are real UI, not API shortcut evidence.
- Video capability measured on actual WebView. If WebCodecs missing, fallback must be explicitly labelled and separately qualified; desktop FIELD01 codec metrics never applied to Android.

Budget: max2developmentbuilds, stage32MiB, APK16MiB, app-local artifact quota128MiB and ≤16immutableoperations; no automatic cleanup. Host floor20GiB + forecast/headroom before build/emulator. No production signature, Xiaomi, SDK, Hera or physical media claims.
