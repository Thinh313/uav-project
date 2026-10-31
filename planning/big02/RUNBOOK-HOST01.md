# HOST01 encoded media and synthetic geotag slice

Run from `/Users/os/Downloads/AI technique/aeris`. This reuses the existing PHONE06 cockpit as an owned staged preview, with unavailable native/flight actions disabled. No Android, APK, SITL, hardware camera or external link is exercised. One laptop browser, one producer and one consumer. This is not a production transport/fanout choice.

## Source/mock gates

`node media/big02/relay-test.mjs`

`node media/big02/http-test.mjs`

The HTTP test invokes the actual handler factory with fake request/response objects, no listen or network, and leaves its small synthetic package/receipts in evidence. It uses a fresh evidence namespace, so rerunning requires an explicit new case root; never delete/overwrite the old result. Core/HTTP mock results are not WebCodecs or live latency measurements.

WebCodecs behavior references: https://www.w3.org/TR/2026/WD-webcodecs-20261019/ . Codec support is implementation-dependent. `prefer-software` is requested, but the actual backend is UNKNOWN. This slice proves actual encoded chunks and browser decoder output, not a backend attestation or camera glass-to-glass latency.

## Explicit stage/start, Root only

`python3 -B planning/big02/serve.py --evidence-root evidence/big02/live01`

Open `http://127.0.0.1:8864`. The command checks disk≥20GiB+256MiB, stages only the curated pinned overlay into `.local/big02/stage` (≤180MiB), removes native-dependent startup scripts only in the staged HTML and runs the fixed loopback relay. SIGINT/termination closes the owned Node process, writes closure and removes this stage in finally. Evidence and frozen originals are never removed. Do not copy the project or start a second listener.

The camera settings button opens the media panel. H2641280×720/30fps/4Mbps is the declared primary profile. The page checks browser encoder+decoder support. If H264 is unavailable, select the separately declared VP8 profile explicitly; do not label VP8 as H264 success. Unsupported profiles stop with no simulated PASS. Targets were declared before live measurement in `media/big02/profile01.json`: source-to-canvas proxy p95≤300ms,p99≤500ms, displayedfps≥24,≥30s foreground, no unexplained≥1s freeze, controlled recovery≤2s. These are assistant-authored engineering targets, not DJI specifications.

Choose **Bắt đầu nguồn**. Synthetic utility-corridor RGB passes through VideoFrame→WebCodecs encoder→HTTP binary relay→WebCodecs decoder→display canvas. Frame timestamp/ID, run/browser boot/feed/config and reference-chain recovery stay bound. Encode/relay/decode queues are capped; overflow suppresses interframes until a new keyframe, rather than delivering broken references. Use the existing RGB/IR payload button to switch to thermal-look; it has no temperature/radiometry. Both views remain synthetic. Telemetry/flight/native/payload execution are not present.

## Bounded measurement

Use **Đo foreground30giây**, remain on the foreground page for the full window, then **Lưu báo cáo**. Save actual results even if FAIL/PARTIAL. Do not change the declared profile/targets after inspecting results. At most3 live windows30–60s plus a targeted failure repair. A hidden page invalidates the window and stops the source. Reports retain frame/source/canvas samples, p50/p95/p99, displayedfps, display-interarrival distribution, maxgap, startup and stage duration distributions with missing counts. Browser time and Node hrtime are never subtracted from each other. Canvas-draw completion is not physical screen scanout; sensor/exposure-to-photon and actual CPU/heat/load remain NOT CHECKED.

For controlled recovery use **Ngắt relay500ms** during a measurement. Queued/dropped reference chains must recover with a new keyframe. Recovery is measured in the source browser clock after the explicit fault request; live results must establish the≤2s target. Switching feed/config, stop/start or an old timer must not complete a new measurement. Save report receipts through the UI; report files are bounded8×512KiB with complete sample/overflow disclosure. No video recordings or per-frame evidence fsync.

## Capture and handoff

Use the existing shutter while a fresh decoded frame is visible. The browser synchronously copies that displayed canvas and freezes its frame/context before asynchronous JPEG encoding. The original JPEG bytes are preserved, SHA-bound by Node, with a separate sidecar and manifest. Capture event and GNSS bracketing are explicitly synthetic in the same browser clock/run/boot/aircraft/feed. WGS84 ellipsoid altitude is not relative-Home/MSL; camera lever arm remains unknown; aircraft position is not target geolocation. `actualImages=0` throughout.

Open **Hồ sơ** from the existing nav. Download `original.jpg`, `sidecar.json`, `manifest.json` from the capture entry. Downloads are byte-identical to persisted originals, including JSON bodies; no Buffer JSON wrapper or EXIF mutation. The sender self-check is not the independent receiver. Root/QA independently verify exact package files/context/receiver/replay/corruption. Missing event/file/time/GNSS/identity is QUARANTINE with original retained, never manufactured0 coordinates.

## Limits and close

Host/Origin and nonce are required for mutation; one consumer/finite polling/header/body/time/request/queue/capture/report caps; loopback only. No command API, media permissions, geolocation permission, phone root, signing or remote services. The server keeps replay sets for its own lifetime; restart is a new receiver session and is not durable anti-replay or authority restoration. Use explicit Ctrl-C and close only this owned browser tab; confirm `.local/big02/stage` was removed. Keep all failed receipts/source history.

Full BIG-02 remains NOT READY until actual camera RGB/IR, exposure-clock calibration, phone/tablet/WebView, external transport/fanout, hardware resources/heat, radiometry and operator journey are qualified. No claim that one-host preview completes those gates.
