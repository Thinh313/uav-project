# AIRSPACE35 / Native35 — isolated engineering handoff

Current scope: editable survey → source-bound4D preflight → FlightOps mock → durable review. No radio, SDK, vehicle/mission command endpoint, physical video or runtime AI. No Ragas application code. Native WebView hybrid engineering shell; actual Android/ART is not accepted yet.

`editor.mjs`, `journey.mjs`, `pins.mjs`, `vendor/*` are exact NATIVE33 bytes. Java journal algorithm retained with package relocation; header remains AERISWORKSPACE33 as opaque container provenance. Activity has a separate native35 origin/bridge/private directory and an explicit asset whitelist. The payload is a versioned native35 capsule: inner33 validated journey + append-only airspace snapshots + chained mock FlightOps audit. No authority restoration on load. Limits:262144B capsule,4 historical sessions,8 full airspace snapshots,256 FlightOps events,512 immutable Java revisions/64MiB journal. Refuse at limits; no deletion or automatic recovery/retry.

Preflight binds exact compiler-derived route (departure/survey/return/landing), mission hash, source hash/revision, UTC window, coverage/corridor, altitude datum ID/Home reference and uncertainty. Integrity hash does not establish source authority. Synthetic clearance is only for mock; unverified real sources and missing/stale references are UNKNOWN. AGL/ellipsoid/global geometry and real national airspace data are unavailable. Restricted synthetic permission must bind zone/source/route/time/altitude; acknowledge cannot substitute. Prohibited mock stays blocked. Assessment/certificate never approves real flight.

Geometry uses local spherical projection at |lat|≤70°, radius≤10km. Conservative extent/latitude margin includes an engineering sphere/WGS84 allowance; it is not a calibrated geodetic accuracy claim. Polygon≤256 vertices total/9rings,128zones,2048segments,1MiB dataset. Analytic segment/polygon and capsule clipping; no production point sampling. Candidate-edge budget1million and findings1024; budget exhaustion explicitly incomplete UNKNOWN. AABB prefilter does not approximate intersections. Coordinate metadata rounds9decimals, duration uses integer-mm distance before ceil; outward conservative interval/mm normalization makes browser/Node replay stable. Pinned compiled mission, SIM32 speedup/cap500ms and all frames unchanged.

FlightOps separates observed mode/request/ACK/owner. Synthetic capability profile supports HOLD/AUTO/RTL/MANUAL; it is not a discovered Hera firmware profile. AUTO requires fresh mock mission/preflight and committed source-bound intent before peer delivery. Owner tied to target/session/boot/link, never resurrected by telemetry after stale/reconnect/focus/restart. Wrongtarget/replay/late/duplicate ACK refused; no automatic retry. Sorted bounded alerts, ACK does not remove faults; video freshness independent, real media0. Operational geofence is a separate abstract SINGLE_INCLUSION mock upload/readback/breach contract. No MAVLink conversion/enforcement claim; holes/unions refused rather than silently converted.

## Run / gates

When host disk admission permits:

```sh
node pilot/airspace35/tests.mjs
node --test native/flightops35/editor.test.mjs native/flightops35/journey.test.mjs native/flightops35/capsule.test.mjs
python3 native/flightops35/build.py
node native/flightops35/crash-qa.mjs
node native/flightops35/browser-qa.mjs
```

Host preview: `node native/flightops35/server.mjs` on8798, offline mock API and Java journal in this module only. Do not start while below20GiB. Each host save rechecks20GiB floor plus write reserve; no flight endpoint. Native bridge never uses localhost/network.

Current APK development03 is a validated prior revision. Current source includes later bounded-work/result and wording refinements; APK04 admission was refused, so03 must not be labeled current. Receipts preserve all3 builds and failed browser/driver attempts. Current host115+engine85+browser29 passed; Android/Hera/real AP fence NOT_CHECKED. Existing host journal jar is unchanged Java algorithm from03 and tested with19 actual owned-JVM SIGKILL checks; that is not device reboot/power-loss proof.

Read `delivery/COMPLETION-AIRSPACE35.md`, `delivery/ROADMAP-AIRSPACE35.md`, `evidence/airspace35/verification.json` for exact accepted/deferred scope. Source/candidate/SOT/trust/ENDURE are unchanged. No new soak, software-release signing or Fly integration.
