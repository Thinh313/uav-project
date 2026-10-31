# BIG-02 / HOST01: media and geotag preparation without Android

Authorized 2026-10-21 by request to do BIG-02 before Android is ready. Contractor applies Vibecode Kit v6.3. Full BIG-02 remains NOT READY until actual camera/link/device gates.

## Outcome and boundaries

In the existing staged PHONE06 cockpit, exercise synthetic RGB and thermal-look encoded video through a bounded localhost transport, then capture a synthetic JPEG bound to exposure-time aircraft GNSS and independently verify its handoff. No separate dashboard, native source edits, APK build/signature, SITL, real aircraft, camera, geolocation permission or remote service. Frozen PHONE06 source07/APK01, candidate, canonical SOT and ENDURE stay read-only. Existing historical missing-path incident is retained, never silently repaired.

Source scope: `media/big02/`, `planning/big02/`, evidence under `evidence/big02/` and `evidence/big02-qa/`, `delivery/COMPLETION-BIG02-HOST01.md`. No dependencies/install/download. Cached browser WebCodecs + Node/Python stdlib. Preserve originals and every failed verification; no automatic data deletion.

## Architecture decision

Reuse PHONE06 overlay staging read-only. A new host-only script may replace native-only startup scripts in its owned staged HTML and add media controls into existing Fly/review panes. Other unavailable cockpit actions must be disabled/labeled. The laptop is the only qualified runtime in this slice. Native/WebView/phone/tablet and camera glass-to-glass latency are NOT CHECKED.

Browser software encoder, HTTP binary relay, software decoder and canvas display form the measured pipeline. Candidate profile H264 1280×720 30 fps, 4 Mbit/s, realtime; use explicit separately labeled VP8 or lower-resolution profile only if capability/budget unsupported, never silently count fallback as H264 PASS. Synthetic frame IDs and timestamps, run/boot/feed/config identity, RGB and thermal-look sources; thermal has no radiometry or temperature. Encode and relay queues bounded. Overflow of interframes requires resynchronization at keyframe, not blind decoder delivery of broken reference chains. Source clock versus relay clock must remain distinct; measured source-to-display is a same-browser software/canvas proxy, not exposure-to-photon. Report no measurement if frame identity or clock correlation is unavailable.

Declare engineering targets BEFORE live measurement in a versioned profile: desktop synthetic latency p95≤300 ms, p99≤500 ms, displayed FPS≥24 over at least 30 seconds, no unexplained ≥1 s freeze, recovery≤2 s after controlled transport interruption. These are assistant-authored goals, not DJI specifications. A miss stays FAIL/PARTIAL. Do not broaden codec/resolution/targets after observing results. Report samples, gaps/drops, stage durations, startup separately, host hardware/load and unavailable CPU/heat/device measures. No C2/WAL/raw/physics retention policy changes or flight-performance claims.

Relay must bind loopback, validate Host/Origin, require same-origin nonce for mutation, strict body/timeout caps, finite long polls, viewer count/queue caps, no redirect/proxy/public interface. No evidence writer on every frame; bounded in-memory traces with explicit export. Local faults: pause transport, wrong feed/boot/config, slow consumer/keyframe recovery, invalid/oversize input; reproducible independent mock tests.

## Capture contract (separate core)

Core `media/big02/geotag.mjs`: deterministic pure metadata validation/binding and package verify, Node built-ins only. Export a documented API and fixtures. Contract: source kind SYNTHETIC; run, aircraft, camera, boot and capture/frame IDs; exposure monotonic timestamp and clock domain; capture event versus ACK; bounded uncertainty and GNSS timeline from same run/aircraft/boot/domain. Interpolate exposure position only between quality/fresh samples with declared bounds, handle dateline, explicit WGS84 latitude/longitude and altitude datum. No relative-Home altitude relabeled MSL, no missing values replaced by 0. Camera lever arm unknown is explicit; position is aircraft GNSS at exposure, not target location. Missing event/file/time/GNSS/identity => QUARANTINE, without claiming original integrity lost. Use original JPEG bytes and SHA; sidecar accepted, no EXIF mutation necessary. Capture is synthetic, actualImages remains 0.

Use a manifest + original JPEG + sidecar handoff with deterministic SHA/context binding. An independently implemented receiver must verify exact files, hashes, size, schema and context, reject corrupt/swapped/replayed/wrong receiver packages and truncated transport. Valid package means integrity, not real image or successful mission. Keep sender/receiver receipts in bounded evidence, no signing or production identity claims.

## Responsibility and gates

Builder A owns relay/pipeline/cockpit/staging/profile/runbook/mock tests, documents APIs for Builder B. Builder B owns geotag core/fixtures/package and its unit tests. QA is independent, read-only production source, owns unseen adversarial tests and receiver verification implementation under QA scope. Contractor verifies actual browser UI, measured pipeline/export, fingerprints, cleanup and final report. Shared API coordination by messages, never simultaneous editing of same file.

Budgets: keep 20 GiB free with 256 MiB additional admission headroom; owned stage≤180 MiB, new evidence≤128 MiB, avoid capturing encoded video recordings, use aggregate traces/small JPEGs. Stop live work if floor approached. At most 3 bounded live measurement windows, 30–60 seconds each after mock gates, plus targeted repair/retest of affected path; do not repeatedly relaunch a failing full workload. No arbitrary test-count quota; bounded scenarios/time/bytes instead. Whole-project copying forbidden. Remove owned stage and close owned servers/tabs; preserve source/APK/evidence. Stop escalation for unsupported browser codec and report limits, not simulated PASS.

Acceptance HOST01 requires implemented local core, independent negative cases, current cockpit synthetic preview, explicit timing/source labels, valid synthetic capture roundtrip and no changed frozen hashes. Full BIG-02 is NOT READY: real camera/RGB-IR, exposure clocks, actual phone/tablet, external link/fanout, CPU/RAM/thermal budget and radiometry are separate gates. LLM is not runtime baseline for deterministic transport/geospatial integrity; operational user-value improvement remains unmeasured until actual hardware journey.
