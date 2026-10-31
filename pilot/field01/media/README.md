# FIELD01 media integration

This directory implements independent synthetic publisher and decoded viewer documents over actual localhost HTTP/TCP. It imports `media/big02/relay-core.mjs` unchanged. No physical camera, radiometry, Android, GNSS, or photon latency claim follows from this module.

## Host contract

```js
import {createMediaServer} from './media/server.mjs';
const media = await createMediaServer({
  port: 8871,
  out: '/absolute/repo/evidence/field01/media-unique-run', // new directory
  allowedOrigin: 'http://127.0.0.1:8870'
});
await media.listen();
// Stop only the owned media service:
await media.close();
```

Publisher page: `http://127.0.0.1:8871/publisher`. Start is explicit. H264 1280×720 at 30fps / 4Mbps is default. Unsupported H264 requires the operator to explicitly select VP8 fallback. `?compact=1` supplies a small source preview suitable for an iframe inside the cockpit. Keep it visible so the source remains foreground. Source and viewer use separate documents, browser time origins, tokens, API roles, and queues; each chunk goes publisher→HTTP server→HTTP viewer.

The iframe accepts only messages from its parent with the configured exact host origin:

```js
iframe.contentWindow.postMessage({
  type: 'FIELD01_SOURCE_START', feed: 'rgb', profileId: 'H264-720P30-V1'
}, 'http://127.0.0.1:8871');
iframe.contentWindow.postMessage({type:'FIELD01_SOURCE_STOP'}, 'http://127.0.0.1:8871');
```

`feed:'thermal'` is explicitly a synthetic thermal-look image, with no temperature/radiometry. A running source must stop before a new source selection. Source emits `FIELD01_SOURCE_STATUS` with `active`, `text`, `session`, and bounded raw counters. The host should accept only the exact media origin and expected iframe source. Readiness status is emitted after bootstrap; do not send Start until ready.

Viewer ES module is CORS available to the exact host origin:

```js
import {createViewer} from 'http://127.0.0.1:8871/viewer.mjs';
const viewer = createViewer({container: document.querySelector('#camera-scene'),
  onState: state => { /* update the host's existing media status */ }
});
await viewer.start();             // waits for independent publisher configuration
viewer.measure({durationMs:30000}); // requires a decoded frame first
await viewer.pause(500);          // explicit controlled fault, separately reported
const report = viewer.getReport(); // null until measurement completes
await viewer.saveReport();       // async durable JSON evidence on media server
const capture = await viewer.snapshot(); // freezes same decoded canvas+metadata
// capture is {frame,jpegBase64}; server binds only registered fresh frame references:
const verifiedFrame = media.readFrame(capture.frame);
viewer.stop();
```

`getPreview()` returns null when stopped or last decoded frame is older than 1000ms; otherwise `{frame,canvas,ageMs}`. `state()` includes counters and source age. `getReport()` returns a copy. `setFeed(feed)` validates the publisher-selected feed; feed authority remains in the publisher. Only the supplied container is changed.

`readFrame(frameOrFrameRef)` validates the current run/boot/config and last 1000ms, then returns a frozen copy. It includes `frameRef`, `frameId`, `run`, `boot`, `feed`, `configId`, `profileId`, `timestampUs`, aliases `sourceRun`, `sourceBoot`, `sourceTimestampUs`, `sourceHostBounds`, `displayHostBounds`, `referenceHostMonoMs`, `sourceToHostLowerMs`, `sourceToHostUpperMs`, and provenance. Passing an object also fences provided identity fields. `referenceHostMonoMs` is the midpoint of calibrated source time bounds in **NODE_HRTIME_MS**, i.e. `Number(process.hrtime.bigint()) / 1e6`. A host flight position in `performance.now()` must be explicitly converted using a measured process offset. Do not mix these clocks directly. Capture registration is browser self-report of WebCodecs canvas decoding, not an independent physical sensor witness. JPEG uses that exact frozen canvas; it is synthetic and re-encoding to JPEG is explicit.

## Clock and engineering evidence

Five request/reply calibration samples derive bounds on host minus each browser's monotonic clock. The narrowest sample with ≤20ms RTT and interval width is used, valid for 60s and refreshed every 30s. Source timestamps are calibrated before accepting chunks. Viewer uses a distinct calibration to derive lower/upper source→canvas latency. The p95 upper bound, not an unqualified midpoint, is compared with 300ms. Missing/expired/wide bounds produce `UNKNOWN`. These are software timestamp→canvas-call metrics; camera exposure, physical presentation, encoder/decoder hardware backend, CPU heat, and Android are unmeasured.

Foreground measurement requires 30–60 seconds, retains ≤4096 raw samples, includes source/encoded/published/dropped counters from publisher plus relay and viewer counters, and preserves failures. Visibility loss invalidates foreground coverage. Config changes and stop terminate the measurement with a reason. Controlled 500ms pause and keyframe recovery are separately identified. No 30minute or 24hour qualification is implied.

## Bounds and authority

Per encoded chunk ≤1MiB, header ≤2048B; relay ≤4 chunks /2MiB; browser encode/decode queues ≤2, outgoing ≤2, pending source/decode maps ≤8, server source frames ≤180, registered captures ≤32, report count ≤8, body/read/evidence bytes ≤128MiB/run, request rate ≤150/s, body deadline 1500ms, request timeout 2500ms, 20minute lifetime, disk admission/runtime floor >20GiB. No automatic file deletion. Restart generates new token/nonce and invalidates old frame references; no authority restoration.

Mutation needs bearer, boot nonce, exact Origin, target role, and JSON/binary content type. Service binds 127.0.0.1. A bootstrap token is accessible only via admitted loopback origin; this is a local pilot service, not hardened multi-tenant authentication. Unknown control endpoints fail closed. All media persistence uses `fs.promises` and serialized writes. Shutdown closes only the owned server/connections.

## Verification

`node planning/field01/media-http-test.mjs` runs actual ephemeral localhost HTTP/TCP tests and writes `evidence/field01/media-http-test-result.json`. It covers target/boot/config/feed, wrong token/nonce/origin/role, replay, queue/keyframe pause, body and header limits, stale frames/clocks, immutable host binding, failed-config clock transaction, report quota, and restart invalidation. Browser codec support, ≥30s foreground throughput and latency, and recovery must be recorded by the operator/browser flow. Node protocol tests do not certify browser performance.

### Stale encoded item recovery

The publisher discards an encoded item older than 750ms before network transmission and suppresses dependent deltas until a newly encoded keyframe. A source-clock rejection does not advance the source chunk sequence; the item is discarded, clock calibration is refreshed, and only a subsequent fresh keyframe may proceed. Clock repairs are limited to two per source start. Other uncertain HTTP failures stop the source without retry. The server retains its 1000ms source freshness check and 60s clock validity; the periodic 30s calibration renewal remains unchanged.

`node planning/field01/media-clock-recovery-test.mjs` verifies these stale-item and clock-error cases with actual HTTP, then sends a 95-second bounded synthetic non-codec stream with three clock renewals. This tests transport lifetime and clocks; it does not certify browser codec fps or source→canvas latency. Root browser verification must separately observe the H264 source beyond 90 seconds and save a valid foreground report.

Clock-validity markers use an exact1/1024ms binary grid so the existing strict60000ms protocol lifetime remains representable across renewals. Clock offset bounds still use unrounded request/reply timestamps.

The host panel checks canvas and publisher iframe bounds, computed ancestor clipping, and page visibility before measuring. It retains coverage loss through IntersectionObserver plus200ms checks. Reports expose `visualForeground`, `visualCoverageChecks`, and `visualCoverageFailures`; `engineeringGate.coverage` requires visual and document foreground. This is geometric/software visibility evidence, not proof of physical pixels or an independent human review.

### Explicit fresh source after a page reload

A page reload creates a new source run and boot. Relay01 intentionally rejects a different run/boot within an existing relay. The updated publisher explicitly requests `/api/new-source` only after the operator presses Start and after reading the currently configured source. Admission requires the previous config as a compare-and-swap fence, fresh unseen run/boot/config, publisher credentials and clock bounds. The media service closes the prior Relay01, drops every prior source/decoded capture reference, creates a new Relay01 unchanged, and persists a `source-replacement-XX.json` record. Previous report identities remain available for failure evidence; prior capture rights do not return. Replacements are limited to8 per service, total configured identities to32. Running services loaded before this route was implemented need an orderly restart before it is available. Browser source identity is never silently copied from the previous boot.

Pause recovery is armed only after the authenticated server pause response. Server returns a conservative host resume bound=start+500ms. A decoded frame certifies recovery only if its config/recovery identity matches, its source-host lower bound is at/after resume, and request-to-canvas elapsed is≥500ms. API RTT is separate. Reports retain recovered frame/time evidence, measurement start/end, current overlapping faultWindows and separately labelled priorFaultWindows. A pending HTTP response or pre-resume in-flight frame cannot count as recovery. This changes the pause request schema to require viewerId/configId and needs a server restart when upgrading an already running service.
