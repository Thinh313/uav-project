# SIMTRAIN52 — isolated foundation

This implements the first resource-admitted slice of the approved simulator plan. It is **not a live flight simulator or council-ready demo**. The previous source, candidate, trust state, SOT, ENDURE evidence and plan remain frozen.

## Try it

From the project root, `node pilot/simtrain52/server.mjs` serves a read-only preview at http://127.0.0.1:8806. If that owned preview is already running, reuse it. SIGINT stops only this preview. No command/API starts ArduPilot or sends flight commands.

The initial view is a static synthetic training yard with a four-rotor reference model, not a Hera model. Drag to orbit, scroll to change distance, choose close/range/top views or lighting. Choose an offline case and press “Phát lại tham chiếu” to inspect two seconds of stored open-loop physics. The keyboard monitor is separate and **cannot move the aircraft**. W/S, A/D, arrows show normalized mock axes after an explicit neutral-first connection. Changing focus disconnects it; reconnect explicitly. Mode request, synthetic ACK and synthetic observation remain separate events.

Audio is muted by default. Enabling it during recorded playback synthesizes rotor sound from estimated RPM, then mutes on playback end, lost focus or stop. It is not a measured Hera acoustic model. Mist/lighting only affect the art preview. The gust case contains recorded forces from the reference physics model; changing the visual weather selector cannot change that recording.

## Evidence and limits

- `evidence/simtrain52/admission1.json`: actual host/power/GPU/runtime observation and separate resource budgets. This is a timestamped observation, not a continuing admission. Recheck before any live launch.
- `contracts3.json`: 50 mock contract checks, including malformed packets immediately clearing held axes, neutral-first, calibration bounds, session/boot/source/time/sequence, stale/suspension, focus/device loss and ACK versus observed mode.
- `model1/`: all 7,200 sensor/PWM/aux frames, 1,200 Hz, three profiles. Each is compared byte-for-byte with the immutable original on this platform. The viewer uses explicitly derived 60 Hz presentation samples; no raw physics frames are removed.
- `browser4/`: 35 functional browser checks and screenshots at 1440, 1920, 1280 and 360 CSS-pixel widths. ANGLE Metal reports Apple M1 Max. This does not measure actual projector performance or certify 60 FPS.
- `verification3.json`: full raw readback and original-model replay, source preservation, disk floor and artifact budget.

The first browser run failed at mock mode correlation; its incomplete diagnostic evidence is retained. The cause could not be established from that receipt. Diagnostic instrumentation was added; subsequent runs passed. This is not proof that all transient timing problems have been eliminated. Input expiry remains 200 ms and never restores authority from a later packet.

Source stack: existing local Three.js/WebGL2 and font/audio modules served through an explicit file allowlist; no CDN, dependency install or copied old project. Own procedural geometry/material textures, flat metric yard. No surveyed terrain, collision engine, calibrated Hera geometry, live joystick integration, remote training, synthetic camera images or end-to-end mapping acceptance. No rain/wet-prop physics claim.

## Next gate

G0 remains partial: no actual projector/gamepad check. G1 is blocked by storage admission and unresolved inherited default 1× pacing. Initial ~20.7 GiB free failed the inherited short-launch minimum of 21.5 GiB. Later resource observation2 admitted a bounded idle probe; its result is described below. A historical admission snapshot must never override live storage checks. The requested 28 GiB is a recovery target, not permission to run an unbudgeted full campaign. An 18-minute raw/WAL/media/export run needs its own measured peak budget; the illustrative worksheet is more demanding.

When storage is admitted, create a new isolated AP/backend driver/output directory, keep speedup 1 and compensation cap 500 ms, journal all frames, correlate host/guest clocks and run the G1 matrix before connecting input to SITL. Never use old launch helpers to overwrite prior evidence. Manual/assisted/AUTO, camera/mapping, instructor faults and council rehearsal follow the approved gates. Do not unlock the disabled live buttons as a substitute for that adapter.

## Verification commands

`python3 pilot/simtrain52/verify.py 2` appends a new numbered readback/preservation receipt; it never starts SITL. Existing test receipts are exclusive. To rerun browser tests choose a new attempt number, retain failures, recheck disk first. Generator/test output paths must be changed prospectively for a new run; never overwrite previous evidence.

## Protected-path incident

Final verification1 detected121absent protected paths (80unique SHA) after they were present at admission. Cause is unknown. Under the user’s standing exact-SHA restoration permission, all121were copied exclusively from existing peers verified against the baseline hash;62.60MiB restored without regeneration, resigning, trust selection, soak launch or historical edits. The failed receipt remains. Verification2 matches all20,249protected paths and the5,051ENDURE path set after restoration. This does not prove uninterrupted original-path presence. Restoration bytes are historical files restored outside the17.3MiB new foundation artifact footprint.

## Bounded ArduPilot idle probe

After space increased above the inherited minimum, a prospectively scoped new driver ran one owned idle instance: `evidence/simtrain52-probe/idle01/`. No flight commands or published MAVLink ports. 4,800 consecutive AP servo→physics→sensor frames at 1,200 Hz, speedup1, cap500ms, fsynced WAL intent before send, all bytes reread against the original reference and correlated to AP receive/parse stages. The measured receive RTF was1.00259 across3.989host seconds. Host receive gaps p95=6.276ms, p99=7.166ms, max22.515ms: **a mean near1× is not sufficient pacing acceptance**.11fresh host/guest clock brackets matched;2startup timeouts remain. AP frame4800 is an unadmitted tail after backend completed0–4799, retained in the observer; it is not counted as an answered frame. No active UI, manual/assisted/AUTO, takeoff or mapping workload. Owned processes closed; all raw/state retained. This is a short G1 preparation probe, not gate completion.

Probe evidence has a separate256MiB ceiling and1.5GiB peak launch reserve in TIP-SIMTRAIN52-IDLE-PROBE. The final machine had more free space than initial admission; future launches still need live budget checks. Full council illustrative worksheet requires39.32GiB free, not merely the28GiB recovery target. Fixed AP trace/WAL capacities also require a retention/rotation design before an18minute campaign. Do not extend the idle driver to controlled flight or long runs by changing limits alone.
