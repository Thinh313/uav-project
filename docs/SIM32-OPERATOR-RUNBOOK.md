# SIM32 / isolated engineering range

Preview: `http://127.0.0.1:8796/`. Reference quad-X only; not Hera calibration, native Android or physical payload/video acceptance. No software signing or ENDURE launch.20GiB host floor; admission reserves640MiB above it and tests stop when headroom approaches256MiB above it. Do not remove other projects/data to make a run pass.

From the project root, `node --max-old-space-size=192 pilot/sim32/server.mjs` starts the local preview without an autopilot or flight authority. Reuse this preview if already running. Never start a second server on the same port, alter an occupied port or stop another project's processes.

## Operator workflow

1. **Plan:** choose reference empty/central/offset load and calm/crosswind/seeded gust. Edit relative altitude5–20m, speed0.5–3m/s and square side11–30m. Validate through the existing AERIS compiler. Home is virtual10.854/106.807/AMSL10m; flat-reference altitude maps to relative Home only in this synthetic flat world.
2. **Start:** explicitly start the dedicated owned simulator. Bootstrapping has no flight authority; wait for actual AP heartbeat and physics. No automatic restart or resume. Simulator system42/component1, pinned4.7.1 binary; camera peers are synthetic, not aircraft links.
3. **Check:** confirm virtual Home/datum. Read-only preflight compares firmware/core profile and nine current simulator parameters. No PARAM_SET. Keep EKF/sensor/prearm checks. Grant expires60s. Upload/read back the complete mission before arm.
4. **Fly:** explicit ARM then AUTO, each requiring observed state. Repeated ARM/AUTO controls are disabled/gated; do not send a second AUTO to resolve uncertainty. RTL is an explicit simulator operation. A pause/loss of physics revokes freshness. The dedicated physical model, not the scene/animation, determines motion.
5. **Payload:** front100 and center102 expose synthetic zoom/focus; rear101 is fixed and refuses zoom/focus. Manager154/devices1/2 correspond to front/center. Camera selection cannot control a rear gimbal. One ACK key per generation; duplicate/shared-manager reuse is refused, so this engineering inspector has limited repeat operation. ACK and matching settings/pose remain unattributed synthetic observations, not proof of physical execution. Payload scene POV uses observed earth-frame quaternion and estimated FOV/zoom; no encoded/native video stream or photo file exists.
6. **End/review:** observed terminal/disarm/ground closes the owned backend/AP immediately and seals review. Explicit Stop also seals the current uncertain/interrupted state. Replay is read-only, with original backend/QA/scope acceptance status visible; it does not restore command authority. A failed/stopped backend alone never proves mission success. Download simulation review JSON, retain raw gzip/MAVLink and pinned profile/source hashes for audit.

Audio is initially muted, follows estimated RPM/model clock and engineering distance attenuation, and mutes on focus loss/stale data. It is not measured Hera sound/SPL. Synthetic landmarks have no collision; flat ground support has no bounce/contact fidelity. No arbitrary aircraft, CFD, ground effect, propwash or slung-load behavior is accepted.

## Explicit host QA

Use exclusive new IDs, one campaign at a time. `node pilot/sim32/campaign.mjs flight NEWID central crosswind` or `... offset gust` starts and hands directly to QA; `payload NEWID empty calm` and `fault NEWID empty calm` exercise routing or GCS-loss/backend-death. The controller never retries a failed campaign. CLI start/test handoff separately can hit the30s startup deadline; do not stretch/reset an old run to hide it. QA closes in finally; if closure fails, inspect labels/CID/PID before any owned stop.

`node pilot/sim32/live_browser_qa.mjs NN` uses an explicit new receipt number; source must be stable throughout the run. It starts a new UI simulator and stops/seals it. `node pilot/sim32/browser_qa.mjs NN` tests read-only replay, toolbar/responsive layout and audio at actual1280×800 canvas in the declared Metal workload. `python3 -B pilot/sim32/replay.py RUNID` streams exact model/hash verification into a new receipt; do not overwrite an existing result. Model replay is not aerodynamic calibration.

All failed attempts remain. Resource flight06, unused-verifier drift fault01, premature-bootstrap UI01, software-renderer/preflight-timeout UI02 and delayed-start payload04 are not accepted by elapsed time or later successes. ENDURE20/27 retain their own failures/intervals and bytes; no SIM32 result replaces24h evidence. Read the completion report and contract version2 for open performance/calibration/native/video/competitive gates.
