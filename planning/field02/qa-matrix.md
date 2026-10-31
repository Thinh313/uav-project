# FIELD02 independent Contractor QA matrix

21 October 2026. Author is a separate QA agent from the Android and host Builders. This is a test contract, not a PASS receipt. Scope is engineering Android emulator + localhost companion + ArduPilot SITL + synthetic payload/media. Physical Xiaomi/Hera/camera, radio, thermal radiometry, production and 24-hour endurance are not certified here. Existing FIELD01 and protected history are read-only.

## Acceptance and falsification

| ID | User outcome and minimum PASS evidence | New counterexample to exercise | Severity if violated |
|---|---|---|---|
| Q1 | One canonical saved KML document reaches Android preflight, exact model/plan-bound upload/readback, AUTO and persisted review. Preserve raw KML bytes and meaningful camera commands; reject unsupported datum/frame. | Two different corridors with the same visible filename; change draft after preflight; a valid upload from an older plan. No stale ticket may cross this boundary. | P1 |
| Q2 | Android Fly simultaneously shows current SITL position, independently fresh video and selected payload state. Each display identifies source and age; unknown values stay unknown. | TCP remains open but AP heartbeat or position stops. A fresh media feed must not make a stale flight position appear current. | P1 |
| Q3 | RGB/thermal-look selection and mock gimbal/capture stay scoped to station, device boot, flight run/boot, model/plan and explicit lease. Capture JPEG is unchanged and references a real observed row from the same run. | Replay a valid decoded frame/capture from a previous flight; reboot the payload during an awaited command; revoked lease cannot complete a new action as success. | P1 |
| Q4 | A video relay outage is shown, control and durable journaling remain responsive, and recovery starts from a fresh valid source/config/frame without replaying obsolete video. Report native codec support separately from measured rendering. | With continuous AUTO, stop source or relay while issuing one payload command. Source restart resets identities; old registered frame is rejected. | P1 |
| Q5 | C2 cut or observed AP reboot ends flight/payload authority, marks incomplete execution honestly and retains all raw. Explicit reconnection creates a new session; no command retry, auto-resume or automatic lease restore. | AP boot clock resets while TCP is alive; lost link with a pending camera command; stale authority presented after reconnect. No old position may acquire the new boot identity. | P1 |
| Q6 | Android Activity/process and host restart preserve selected mission, captures and review semantics while all effective permissions are NONE. An interrupted flight cannot become a completed flight merely from restore. | Restart between intent and commit; background while encoder is live; duplicate callback after Activity recreation. Pending records remain inspectable and do not publish a committed image. | P1 |
| Q7 | Android SAF writes the selected immutable package, reads it back and verifies exact bytes before claiming success. A separate receiver validates raw flight, capture context and full index SHA before durable receipt. | Cancel picker, change committed model while picker open, truncate output, duplicate TAR members, wrong receiver, wrong run/boot or replay of a valid package. Failed receive does not advance a success ledger. | P1 |
| Q8 | Selected touch layout supports the entire journey with no clipped modal, blocked primary action or overlap. Show simulator/source label. Controls have >=48 px intended touch box where measured; touch target and visible icon are distinct concerns. | Long Vietnamese corridor name, error/UNKNOWN labels, both themes, 900x500 compact. Android WebView results must be obtained from actual emulator, not borrowed desktop screenshots. | P2 |
| Q9 | Disk >=20 GiB throughout admitted tests; bounded raw/media/WAL; owned processes close and partial test evidence survives. | Fail admission just above runtime threshold, quota reached during capture, fault closure with pending action. No evidence auto-deletion or silent retry. | P1 |

## Baseline evidence and boundaries

FIELD01 already contains one accepted actual SITL flight, two 30-second foreground desktop media windows, a Python cross-context delivery receiver and process restart preservation. It contains mock fault cases but no accepted real SITL C2/reboot fault. Its canonical WAL sorts nested JSON keys: compare semantic document/model/plan SHA and original KML/JPEG bytes, not JSON text ordering. Receiver SHA proves integrity, not sender authenticity or physical exposure accuracy. A camera ACK is not a physical image. Thermal-look is not radiometry.

FIELD02 topology is explicitly an Android WebView companion over ADB reverse to host endpoints, unless the approved TIP changes it. This does not prove a self-contained offline native GCS, native MAVLink direct transport, Wi-Fi latency, RF link, Xiaomi performance or Hera dynamics. Browser WebCodecs availability must be detected before claiming Android video; if unavailable, a declared native or bounded image fallback may have a distinct acceptance target, never relabel desktop codec measurements as Android.

## Evidence needed before a verdict

- Source fingerprints at the tested revision; exact owned emulator, APK hash/signing scope, SDK/ABI/WebView version and host topology.
- Each actual UI scenario: fresh UI hierarchy/screenshot, action timestamps, app source flags and the corresponding raw/closed review. API-only tests do not substitute for Android touch journey.
- Actual SITL cut/reboot evidence: transport/raw observer before and after, firmware/binary identity, monotonic/boot continuity or discontinuity, closure and authority snapshot. Test harness intent alone is not a reboot proof.
- Media: actual foreground source/canvas, codec/fallback, current-window frame count/fps/age and fault windows, measured clock uncertainty. No wall-clock-only or hidden-canvas performance acceptance.
- SAF output pulled after picker/readback: filename, exact size/SHA, canonical shared model, raw receive result, images' run/boot/model/plan and exact reference row. Separate receipt store must be unchanged on any refusal.
- Restore: before/after model/plan/raw KML/JPEG SHAs, review outcomes and explicit effective authority NONE. Pending is retained, not silently healed into success.

Verdict is READY only for the declared environment and accepted AC. P1 failure prevents a READY claim even if most test counts pass. Unrun Android, video or SITL fault cases are NOT_CHECKED, never inferred from presence of code or mock success. No large benchmark is needed for deterministic functions; operator-effort/commercial superiority remains unmeasured.
