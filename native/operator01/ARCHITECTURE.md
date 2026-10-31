# OPERATOR01: explicit repeated payload controls on native Fly

P1 isolated engineering module, package `vn.rtr.aeris.operator01`, reused curated source/assets from immutable N98verify. `planning/product-milestones/P1-TIP.md` is the accepted outcome and acceptance contract. No Hera/Phase One execution, remote authentication, production release or DJI superiority claim.

## Control contract

- Sole DirectTransport95 socket/RX/WAL and shared generation/sequence remain. Every actual write retains prepared/wire SHA binding, durable TX_INTENT, current native policy/foreground check, one socket attempt, TX_WRITTEN. Partial/unknown/fsync failure closes/revokes without retry.
- Native actuator intents globally spaced at least100ms, per camera capture>=1000ms, zoom/focus>=250ms, gimbal>=100ms. Rejections are explicit; no accepted intent is silently dropped/retried. Discovery is a separate explicit read of four endpoints, once/component/generation and quota-bound; neither discovery nor flight heartbeat consumes actuator pacing.
- Absolute gimbal angles use message287 with target42/154/device1 or2, vehicle-relative yaw flags32, UIdegrees→wire radians, both unused angular ratesNaN. No broadcast, joystick streaming, autonomous timer replay or rate-control/deadman claim. Fresh camera capability/manager ownership and current role grant are rechecked at write boundary. Authority1001 retains generation-wide component/command key fencing; ACK cannot establish device2 authority. Device ownership observations remain explicit synthetic fixture data.
- Camera capture2000 requests one image (param3=1), increments camera-local param4 sequence1..16777215. Zoom531/focus532 use absolute percent mode2. Each user action gets a native immutable transaction with owner/revision/session sequence; each prepared transaction has maximum one attempt and1000ms preparation lifetime. Explicit new commands are not retries.
- Repeated actuator transactions remain SENT_UNATTRIBUTED after one approved attempt. ACK77 for these commands is an independent ACK_UNATTRIBUTED observation, never promotion/completion/causality or permission. CAMERA_IMAGE_CAPTURED image_index does not carry the request's param4, so it cannot attribute a photo to an intent. Settings/pose/image observations are independent and tied to component/device/current session/boot. UI renders0actualImages and never counts an intent as an image.
- Revoke/transfer/loss closes or freezes unconfirmed records UNKNOWN. No authority restoration, reconnect or resend. Selecting a camera changes the viewed target only. Two local actors remain local roles, not authenticated independent controllers.

## Bounds and freshness

128 prepared intents/session,32 station history entries,15min native session,64 native RX in-flight events,32MiB raw WAL,131072byte payload-record size are hard bounds; no evidence deletion. Max128-intent snapshot is tested below100000bytes. A recent16-entry ACK view is a projection of raw bytes retained in WAL, with a cumulative count; it is not the evidence store. Wall/elapsed snapshots are not evidence of24h endurance.

Duplicate boot-time settings/pose do not renew freshness. Contradictory equal-boot settings/pose become UNKNOWN; component boot regression closes the common session. AP/link closed, unattached, stale or uninitialized yields unknown armed/freshness. Manager status/device ownership freshness gates every287.

`snapshotAtMs` exists in polled state for a visible native lease countdown. The durable semantic PAYLOAD_STATE comparison omits this derived clock-only field to avoid writing an unchanged large snapshot for every RX. All RX bytes remain fsynced, and state records retain their raw elapsedMs; no telemetry block/frame is dropped.

## Fly integration

`operator01.mjs` replaces fake shutter/payload/zoom/settings/authority handlers on the main Fly camera island. Native target/owner/armed/settings/pose/counts overwrite mock presentation after each cockpit paint. New controls are48px or larger, native source labels and request/observation/UNKNOWN/lease/quota are explicit. Native ResourcePolicy explicitly permits only the new same-origin assets. `operator-model01.mjs` is projection/range code only, never the authority arbiter.

## Primary references and provenance

Accessed2026-10-19. Official docs describe protocol semantics; local implementation/mock/SITL acceptance are separate evidence:

- https://mavlink.io/en/messages/common.html#GIMBAL_MANAGER_SET_PITCHYAW : message287 high-rate setpoints, pitch/yaw in radians, rates in radians/s. Existing generated/pinned Dialect95 has23-byte payload,CRCextra1.
- https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE : single-capture param4 sequence increments for duplicate prevention. CAMERA_IMAGE_CAPTURED263 image_index is a separate observation index.
- https://mavlink.io/en/services/gimbal_v2.html : manager/device identities, configure/status ownership, explicit target devices and high-level setpoints.
- https://mavlink.io/en/services/command.html : reliable-command transport normally retransmits without ACK. This P1 manual profile deliberately uses single-attempt best-effort and uncertainty; it does not claim full reliable-command retransmission conformance.

Existing P22/T25 codecs produce mocks. Generated upstream parser is the independent decoding oracle for wireCRC/field/routing checks. Host Java/JS checks are not Android touch tests or physical execution evidence. Original Payload97Test remains unchanged apart from package relocation; its attributed-ACK and one-shot assertions intentionally differ and the actual failed execution is retained.

## Targeted acceptance repairs retained

APK01/02/03 and exact changed prior source bytes remain in their evidence source-history directories. APK02 removes competing legacy payload painters: a static ownership map excludes native payload controls/captions from mock and flight painters; one Fly paint flow calls a semantically memoized native projection. APK03 replaces O(history) preflight snapshot checks with narrow frozen status/cohort accessors calling the identical private time/invalidation guard. Full diagnostics/raw/events and all bounds remain. Fixed-clock failed raw still fails the same3000ms cohort check; host cost measurements are not Android root-cause proof.

The04 draft replaces live numericIME editors with touch ranges, ±1 controls and three requested-angle presets. Range/step/preset changes do not send commands; applying is explicit. Main Fly zoom arrows remain explicit single-command actions and update requested controls/readouts before send. Real images remain0, with intent count shown in the larger panel. A bounded first domain-failure self-report records timing/phase before samples are cleared; it does not alter the failure decision or closure. LatestDATA metadata is one in-memory summary, not a per-frame log stream. Diagnostic construction or storage failure cannot prevent closure. Exact root cause of the prior generic freshness interruption remains unknown until fresh runtime evidence.
