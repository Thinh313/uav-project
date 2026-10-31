# FIELD01 host flight engine

Architecture: `HOST_NODE_GCS_SIM_ONLY`. This is a Node ground control application using a single fixed localhost TCP endpoint, not Android native TCP, aircraft hardware, Hera fidelity or physical flight qualification.

`Flight01` reuses the existing pinned AUTO63 MissionLink, FlightGuard and Preflight43 with their existing allowlist and fsync-before-wire-write raw journal. KML and supported QGC use the same Native92/PHONE07 compiler semantics through integration03. A committed `document92` is validated and locally replayed; its actual compiled plan is used verbatim. No source/controller/evidence from an earlier campaign is written.

## API

```js
import {Flight01} from './flight01.mjs';
const flight = new Flight01();
await flight.setDocument(document92);
const request = extra => ({...flight.state().request, ...extra});
await flight.action('connect', request({mode:'sitl', confirmSimulation:true}));
await flight.action('preflight', request());
await flight.action('grant', request({authorityConfirmed:true}));
await flight.action('upload', request());
await flight.action('arm', request());
const home = flight.state().live.homeReview;
// Render the post-arm Home and readback to the operator before this confirmation.
await flight.action('auto', request({homeReviewSha256:home.sha256,postArmHomeConfirmed:true}));
// Poll state().live.completion; ACK alone never means mission execution.
await flight.action('close', request());
```

Every request carries the exact instance, model SHA/revision, document SHA, plan SHA, mission SHA and, when connected, run/session/boot. Upload, arm and AUTO also require the current explicit authority ID. `setDocument` refuses edits while a session exists. Fresh preflight is readonly and does not grant arm permission. The explicit host grant permits only the owned simulator mission. The post-arm Home review expires after the inherited 10-second window; a stale or missing digest refuses AUTO.

`preflight` waits at most 90 seconds for readonly fresh GPS, EKF, AP prearm, Home and firmware observations, then performs one typed inspection. It does not repeat a timed-out command. The first terminal SITL test intentionally remains failed because its old 22-second wait encountered real AP prearm/EKF initialization. The error, raw capture and clean closure are retained. No new SITL attempt was spent on the readiness-wait repair.

`action('revoke', request())` removes authority. `abort`, `cut` and `reboot` require `confirmSimulation:true` and close only the owned session. `cut` injects transport/session interruption; `reboot` is an explicit teardown fault and **does not claim an observed physical or AP reboot**. A separate mock test regresses the actual AP boot-time field and checks that the inherited reboot guard invalidates authority. Fault reviews always have `accepted:false` and `execution.complete:false`. New process instances never restore rights.

`state()` includes `source`, `binding`, `request`, `live`, `authority`, latest position, pending transaction count, raw byte count, last review and storage thresholds. Root UI may poll this at 250 ms and invalidate payload rights if the flight session or authority becomes stale.

`positions({limit})` returns at most 6000 bounded records. `lookupPosition({hostMonoMs,maxDeltaMs:1500})` finds a reference record within a maximum permitted delta of 3000 ms. Callers must also check its run/session/boot/model/plan binding. Records contain:

- `hostMonoMs` and `telemetryReceiptHostMonoMs`: `Number(process.hrtime.bigint())/1e6`, the host monotonic domain shared with media source timing.
- `apTimeBootMs` / `timeBootMs`, boot, run, session and model/plan SHAs.
- `latitudeDeg`, `longitudeDeg` (also `lat`, `lon`), `altitudeMslM` and `relativeHomeM` in metres; ellipsoid altitude is null.
- GPS fix, satellite count, eph/epv and GPS host receipt age; simulated GNSS reference quality only.
- Raw record number/SHA pointer, `sensorTimeUncertaintyMs:null`, `physicalExposurePosition:false`.

The lookup method is `NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC`. It does not interpolate, convert MSL into ellipsoid, or claim the position of a physical exposure. Host reference delta is not sensor clock precision.

## Resource and ownership policy

The fixed container is `aeris-field01`, with `127.0.0.1:5970 -> 5760`. Docker CLI is `/usr/local/bin/docker`. No download occurs. The runtime checks cached binary SHA `011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482` and cached Ubuntu image `sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`.

SITL requires 31 actual one-second admission samples at or above 29 GiB free. At most three new FIELD01 SITL requests are allowed across all engine instances. The runtime is bounded at 540 seconds after launch, with admission/startup budget reserved within the 600-second attempt limit. Runtime stops below 21 GiB to protect the 20 GiB floor. AP state is bounded at 64 MiB, raw journal at 16 MiB and aggregate FIELD01 evidence at 512 MiB. It stops only the container whose ID and run label match the owned launch, retains its state/raw errors and runs `docker image prune -f`; volumes and other containers are untouched.

Each new run saves a source-pin snapshot before admission and verifies those sources. Generate current source pins with `node pilot/field01/flight/pin.mjs` only after reviewed edits, while no SITL attempt is active. The exact missing dependency loader aliases are recorded in that manifest: the missing tracked APSTREAM40 generated definition is read from Git into this task's vendor file, and missing integration03 generated compile/fixture paths resolve to existing crew02 source files. The protected missing paths are not restored. The original first SITL attempt preceded per-run pin snapshots, which is recorded as a provenance limitation in its completion report.

## Verification

`node planning/field01/flight-test.mjs` exercises mock polygon/corridor nominal missions, exact binding/authority/Home gates, link loss, explicit revoke, mock boot regression and teardown faults. `node pilot/field01/flight/verify.mjs RUN` independently decodes duplex raw bytes with FullFramer and checks CRC, identity, target allowlists, exact mission items, pre/post-arm readback, explicit Home digest, AUTO/navigation/terminal/ground/disarm evidence, position metadata and file hashes. It writes a new raw-verification result and refuses to overwrite an existing result.

The final integrated UI and real SITL attempts 2 and 3 belong to the root task. Mock and raw structural QA are not independent human flight approval or production certification.
