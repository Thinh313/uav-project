# PAYLOAD21 · independent Fly/Payload module

Static local simulation, separate from the ENDURE20 candidate. Node22+; no install/build required. Run from the aeris directory:

```sh
node pilot/payload21/server.mjs
# http://127.0.0.1:8789
node --test pilot/payload21/core.test.mjs
node pilot/payload21/browser-qa.mjs
.venv/bin/python -B pilot/payload21/verify-sources.py
```

The console has front EO/thermal, center fixed survey and rear EO synthetic fixtures. These are not Hera as-built addresses, counts, camera limits or timing. Select a payload → acquire simulated control → choose stream/action → inspect separate ACK and observed state. Capture produces a synthetic receipt with no physical image or file SHA. Angles are degrees; zoom is a factor. The flight bar is a synthetic HOLD/42m relative-Home observation; there are no flight/radio/SDK APIs. Use the fault panel to lose a video feed, camera control, gimbal or aircraft link; reconnect explicitly rediscovers with a new session/discovery identity and requires fresh authority. No automatic command retries.

Manager/control heartbeats and synthetic frames refresh once per second in the tab simulator, independently of command feedback. This timer is not an actual camera decoder or flight heartbeat. Tab background throttling can make pending outcomes uncertain; no device timing claim. The three fixtures are heterogeneous; discovery tests cover1/3/8 synthetic targets up to a simulation policy limit8, not supported Hera capacity. ACK correlation IDs/discovery generations are local normalization fields, not MAVLink wire IDs.

Review export is JSON with original target/session/discovery and synthetic origin, explicit incomplete flag after bounded256-event/command history eviction, and no physical media. It is in-memory, unsigned engineering evidence; refresh/closing starts a new session and is not durable journal recovery or survey acceptance. Export before leaving. Host QA receipts/snapshots are retained under `evidence/payload21`; browser and Node tests exercise this module only. SDK/native/video decoding, real media, actual new SITL payload runs, HIL/field and measured RAGAS A/B are NOT_CHECKED.

The separate static server binds only127.0.0.1:8789, GET-only whitelist assets, no data store or API proxy. Stop with Ctrl+C or SIGTERM to its recorded exact process. Do not stop the independent8788 canary. The existing licensed IBM Plex Sans asset is served read-only; no copied dependencies or font downloads. No service worker registration. Future integration/new signed release waits for ENDURE20 acceptance and new regression/signature gates.
