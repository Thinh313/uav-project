# Beta Workbench03

User24Oct authorizes one isolated integrated beta: repair SAF busy, Workbench → preflight → Fly → video/payload → review. Workbench01/02, G17, all old source/candidates/ENDURE are read-only. New paths only pilot/native/planning/evidence/betaworkbench03 and dedicated completion. Vibecode6.3, one assistant switches Contractor/Builder/Verify, no independent QA claim.

## Architecture / ADR
Use pinned Workbench02 UI/native source as projection, original Workbench planner and native92 model/compiler, qualified G17 MAVLink MissionLink/MockSocket, FIELD02 payload/client/store and G17 host-source video modules read-only. Integrate through one new coordinator and UI; no whole app fork. Exact counted native/UI transforms and original/effective SHA must be recorded. Workspace remains native data, controls always volatile. MockSocket is not ArduPilot/physics, synthetic image is not sensor exposure. No new vendor SDK.

The model accepted by scoped flight is the unchanged narrow native92 profile, no clamping. Workbench wider plans stay planning-only until valid. Explicit Home AMSL10 consent, preflight, grant, upload/readback, arm, post-arm Home approval and AUTO remain separate actions. MAVLink raw is fsynced before wire by existing MissionLink. Do not turn replay positions/ACK into acquired imagery or a successful flight. Raw/payload/media/review share binding/run/boot; unknown outcomes remain incomplete.

SAF fix projects only owned I/O terminal failure to reply/release; denied/busy requests must not release another operation. Keep native origin/session/byte/hash/CAS guards. Allow navigation only main loopback8894 and media subresources only loopback8893; no arbitrary URLs.

## AC / gates
B1 projection repairs SAF error release; host fault/cancel/busy/session tests and Java typecheck. Actual ART/SAF still mandatory.
B2 single compiled model hash shared by planner/flight/payload/review, reject profile/Home/session mismatch and stale source. No authority restored by native/host restart.
B3 protocol mock upload/readback/preflight/arm/post-arm Home/AUTO/ground review, incomplete faults and restart, bounded durable journal; legacy guards not relaxed.
B4 receiver-only cockpit video, encoder on separate host browser, real loopback transport; epoch/frame/config and flight binding, capture only via payload lease and valid frame. No physical or radiometric claim.
B5 same cockpit plan/preflight/Fly/payload/video/review and native workspace. Test nominal, link loss, reboot, foreground, concurrency, restart and export/import faults. UI/layout and native checks distinct.
B6 frozen preservation, finite budgets, new runtime admission and proof report. READY requires ALL mandatory actual Android–SITL cases on the same final source/APK; source/mock PASS is PARTIAL, not beta.

## Budgets / stop
Source/mock retained max256MiB including projected native/compiler checks and media evidence. No dependencies/downloads, no whole project copy. Stop new effects before physical20GiB+256MiB, preserve valid intermediates. Native compile scratch removed, fault evidence retained. Android/AP/SITL/build require original29GiB stable31samples/30s/maxdecline256MiB, runtime28GiB/forecast15s, hard20GiB, firmware identity, source pins/controller, speedup1 and cap500ms unchanged. At current25GiB do not launch or wait indefinitely. No production signature; development APK only after actual build/resource gates and scoped runtime qualification. No old campaign retries or old receipts overwritten. Limit any future actual campaign to2700s/two hosts/four AP/two boots with retained originals, no automatic retry.

Value evidence is deterministic correctness/integration; no runtime AI or measured commercial/user-effort advantage. No DJI parity claim.
