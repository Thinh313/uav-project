# Independent build dependencies / inventory

No RAGAS application source was downloaded or reused for FLIGHT01. Existing public RAGAS documentation/releases remain black-box comparison evidence only.

App/bridge: Node.js ≥22 platform APIs and browser ES modules; no new npm package. IBM Plex Sans asset inherited from UX01 under existing license. QA uses the host's bundled Playwright, not a new install. SOT uses project .venv dependencies already present.

ArduPilot SITL: official Linuxx86_64 static ArduCopter4.7.1 binary and default params from upstream; GPLv3, internal simulator use. Copyright/license upstream files retained in runtime/sitl; binary/metadata/params URLs and SHA256 in public-inputs.json. Docker Ubuntu24.04 image digest pinned in start_sitl.sh; no bespoke image built. Runtime is not bundled into an Android APK or published by this task.

Protocol: MAVLink minimal/standard/common/ardupilotmega XML snapshots with source hashes. MAVLink upstream COPYING distinguishes (L)GPLv3 generator licensing and an MIT generated-output exception; the exact upstream notice is retained in reference/mavlink. services/mavlink-definitions.mjs is a bounded generated derivative of those exact bytes. Generic framing/session/mission compiler are newly implemented. This is a development dialect, not a full firmware or transport SDK. Generated message fields are selected from open protocol definitions, not RAGAS.

Final commercial distribution/dependency SBOM must cover actual native services, libraries, licenses and build artifacts once selected. Current inventory is this increment's reproducibility record.
