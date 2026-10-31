# CONTROL01 profile and acceptance decisions

27/10/2026. Contractor decisions before actual tests. User authorizes simulator
manual/assisted/link loss/AP reboot; hardware and production remain separate.
Vibecode6.3 Builder/Contractor/independent QA roles remain separated.

## Source-backed profile

Use exact previous AP03 external instrumented artifact/model/pacer and versioned
small parameter/configuration inputs, never change their old paths or receipts.
Firmware4.7.1 source is the authority for names/types; unknown values refuse.

- FS_GCS_ENABLE5 (INT8/type2 LAND), FS_GCS_TIMEOUT5.0 (REAL32/type9),
  FS_OPTIONS0 (INT32/type6). Old mask16 continues pilot control in LOITER and
  cannot qualify the intended GCS failsafe. Source events.cpp clears RC overrides
  on GCS failsafe before selecting LAND; no separate simulated RC transmitter.
- Nominal RC_OVERRIDE_TIME0.5s; separate link-loss-only profile6.0s, finite and
  greater than GCS5s. This isolates GCS LAND while the pilot input remains held;
  it is not the nominal timeout or evidence that a remote drone stops immediately
  at native lease revocation. Finite remote command persistence must be reported.
- RC_OPTIONS32 preserves throttle arming check; ARMING_SKIPCHK0 skips no checks;
  RCMAP_ROLL/PITCH/THROTTLE/YAW1/2/3/4, typedINT8. No forced ARM/DISARM.
- BATT_ARM_VOLT21.0 with fresh actual AP battery voltage required. Battery analog
  scaling10.1V/V and17A/V is bound to cached SITL source mapping FDM battery
  voltage/current. The model is a declared provisional simulated profile, not
  battery calibration or real Hera energy validation. No runtime parameter fix
  to defeat an arming refusal.
- GPS_HDOP_GOOD200; retain enabled fence and source-bound typed safety checks.
  Passive channel stream names are MAV2_* for this firmware, not legacy SR1_*.
  Passive observer sends zero application bytes, including no GCS heartbeat.
  Source-supported static `message-intervals-chan1.txt` in this task's owned AP
  state requests EXTENDED_SYS_STATE245 every250ms and HOME_POSITION242 every1000ms.
  Hash/bind it before boot; this is not evidence that the AP applied the rate.
  Actual fresh passive observations remain mandatory before any ARM. Version new
  profile metadata if its previous SHA had already been published.

## Input and safety authority

Native remains the sole MAVLink flight writer. Pilot manual means actual Android
touch-stick control in AP-assisted LOITER, not ACRO/unassisted flight or real HID.
Touch-state sampling is an independent live producer, not the sender relabelling
a cached sample as fresh. Record MotionEvent uptime and receipt/sample elapsed
clock distinctly. UI pause/focus loss/cancel or producer failure revokes authority.

Approved finite de-escalation: revoke normal lease, send one BRAKE17 request only
with current identity/fresh telemetry, observe mode17, then neutral and RC release
with exact channel semantics. Each write has intent/fsync and fresh boot checks;
no retry after unknown send. This separate safety authority never renews the
operator lease. If stale/write/journal/link failure prevents cleanup, close native
path, stop GCS output, retain release outcomeUNKNOWN and observe AP failsafe via
passive monitor. Never equate close/ACK with a safe aircraft state.

Post-arm Home confirmation binds the candidate actually shown to the operator,
with its current boot/datum/coordinate/freshness. Stale displayed candidate or a
later Home change rejects takeoff. Tests act as a scripted operator, not a human
evaluation or authorization for real flight.

## Predeclared scenario evidence

Root accepts independent QA metrics before actual: takeoff3m±0.75m; hover>=1s
with horizontal speed<=0.5m/s; held nonzero manual input>=1s and displacement
>=0.3m; normal horizontal envelope10m and altitude<=5m; groundabs(relativealt)<=0.4m
and two fresh landed/disarmed observations. Do not widen these after seeing data.

Nominal actual requires native commands, observed flight/motion/BRAKE/LAND and
disarm. Airborne loss cuts only the transparent native path while the Android
gesture is still held; FDM, clock and passive telemetry remain. Root confirms
actual forwarded nonzero RC before the cut. Graceful native CLOSE or whole Docker
network shutdown is not the loss injection. Reconnect/reboot never restores lease.

Actual AP reboot is on ground/disarmed first, with new owned AP process/container
identity, boot context and raw epoch; require fresh discovery/preflight and no
automatic ARM/control. In-flight reboot remains mock-only in this tranche.

All admitted FDM frames, INTENT barriers, SENT/UNKNOWN, streamed STAGE/AP records,
exact original-model replay, speedup1/cap500ms and storage20/10+256MiB/15s policy
remain mandatory. Source/parameters/software identities and budgets gate every
actual start. All failed prefixes remain; full M1/30min/Beta is not implied.
