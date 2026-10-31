# FIELD02 repair01 UI/authority Builder handoff

22/10/2026. Implemented isolated FIELD02 source only. Native/AP/runtime/media protocol modules, old FIELD01/candidate/ENDURE evidence and APK were not edited. Contractor owns live Android/AP proof.

## Behavior implemented

- FIELD02 Payload01 extends frozen FIELD01 policy through a new local authority-observation wrapper. Each station binds exact client id/epoch/instance; lease observations bind gateway/station/client/run/boot/model/plan plus monotonic times. Status never includes bearer tokens.
- Invalidation clears permissions synchronously, snapshots pre/post lease state and queues one bounded durable `PAYLOAD_AUTHORITY_INVALIDATED` record. Repeated empty freshness polls do not append WAL rows. Status includes the persisted record seq/hash and prior observation after restart; leases themselves are never restored.
- Lifecycle, link/position freshness, payload boot/link, lease expiry and model/run identity changes invalidate. Explicit selection/revoke is station-scoped; selection preserves validated discovery so normal discover→select→grant still works and does not steal another station's lease.
- Any payload WAL append failure latches failed-closed and clears leases. Real store readOnly/poison is also observed. No grant or command can proceed after failed evidence; no automatic healing/retry. The existing FIELD02 store keeps its individually bounded record-copy fix, avoiding the inherited whole-array canonicalization failure.
- Before a flight fault/closure can invalidate rights, the new `fault-invalidation.mjs` validates the known action, active client, busy state, exact owned flight request, required explicit confirmation and close/ground preconditions. Only then does it invalidate, await the durable receipt and reassert the client before AP action. Payload reboot/disconnect similarly persist before adapter effect. Unknown flight actions reject before reaching the inherited action/error path.
- Cockpit displays latest invalidation reason, pre/post count and receipt seq. The payload fault UI now submits exact model/plan/run/boot/discovery/device context.
- DAY and NIGHT share semantic glass tokens for ink, muted, fresh, warning and error. Fresh video age/error no longer use light-only colors on bright glass. Video-plane empty text retains a separate dark translucent plate. Disabled controls have opacity plus dashed border; no opaque bar redesign or native build.

## Checks and honest scope

- `authority-builder-tests04.json`:11/11 actual-class tests with mock store/flight/clock, including nominal discovery/select/grant, wrong identity zero effects, durable order, expiry deduplication, reboot/loss, scoped revoke, restart observation/no authority, grant-await and delayed-response revocation races, and command-intent write failure with zero adapter calls. Reports01–03 retained as development iterations.
- Independent QA authored9 authority groups and app fault groups separately; their exact final source bindings remain Contractor/QA responsibility. Builder tests are not independent certification or live AP evidence.
- `contrast-raster-mock02.png` renders Barlow glyphs and alpha glass against black/white scene extremes. `contrast-png-analysis01.json` samples retained actual PNG glyph/background pixels:20/20 approximate contrast cases≥4.96:1. This is AppKit mock raster, not Android/browser pixels or ICC display certification.
- Initial contrast harness compile/extraction failure is retained as report01. Report02's exact-declared-RGB glyph-match flags were invalid because AppKit ColorSync transforms calibrated colors. The later readonly analysis samples stored glyph/background pixels instead, without deleting/replacing either report. Actual Android DAY fresh/error pixels still require Contractor live verification.
- Syntax checks passed for app/gateway/fault helper/UI. Native source freeze02 hashes remain exact. No emulator/ADB/SITL/build/sign action by this Builder during repair01.

## Remaining gates

Actual active-lease AP reboot revocation, cold-start/FPS/recovery and Android DAY warning visibility remain live gates. New metadata receipts cannot substitute for observed lease ownership immediately before the fault, zero rights after it, raw AP reboot evidence and rejected post-fault command. Root must preserve original NOT_READY and all failed observations.

Own Swift module cache/binary used for mock raster were removed. Evidence/fixtures remain in repair01. No AP cap or flight pin was changed by this work.
