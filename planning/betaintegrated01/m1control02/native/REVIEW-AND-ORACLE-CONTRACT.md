# Current APK02: UP, release, new consent and LAND

Scope: review and pure-JVM consumer checks of existing frozen APK02 sources.
No product edit, APK build, ADB, Android, AP, socket or physical control started.
Tests reuse the prior independent QA's AP fixture scaffold; this Builder review
does not become a second independent certification. Independent CONTROL02 QA
has its own nominal sequence checks.

## UI producer path

On an actual UP/CANCEL, TouchControls clears both axes/pointers, retains the real
event uptime/action, sets one pending release and calls the Activity listener.
The listener stops the20Hz producer and samples current state once. That sample
has zero axes, pointers0, release=true and the real UP event time.

When the operator later clicks CONSENT, Activity.sampleNow runs before enqueueing
the consent action. It captures a **new** sequence and uptime/elapsed sampling
clock from the current centered UI. The last MotionEvent time remains the old UP
time; release=false because its pending flag was consumed once. This is a fresh
observation of centered UI state, not a new physical MotionEvent or sender-side
retimestamping. Authority accepts the neutral observation without granting. Only
the explicit CONSENT action creates a new lease; then the UI producer restarts.

Current code does not automatically restore consent from neutral samples, a
completed RC cleanup, a readback or a reconnect. The old lease ID is cleared;
the second successful consent uses a new grants counter/action ID.

## Exact nominal predicates

After UP, await all of: `releaseState=RELEASED`,
`rcOverrideActiveLocally=false`, `input.consent=false`, actual `flight.mode=17`,
current Home confirmation and fresh typed preflight. Preserve that checkpoint
before the second consent, because consent resets the release state to NONE.

Record first lease/grants. A new centered sample alone must leave consent=false.
After the second explicit consent, require consent=true, a different nonnull
leaseId and increased grants/input sequence. LAND's UI/native gate then requires
observed armed state and rcOverrideActiveLocally=false; it uses another fresh UI
sample and a valid new lease at the actual wire boundary. LAND9 write revokes
pilot authority immediately; it does not establish observed mode9 or ground.

Actual pass still needs CRC-checked AP mode9, fresh landed1/disarmed heartbeat/
position|relativeAlt|<=.4 in two distinct groups, no error/GCS-failsafe confounder,
full native/input/host/AP/frame evidence and managed closure. The mutable native
ground counter alone does not prove independent groups.

## Native raw ordering to verify cold

1. TOUCH_MOTION_EVENT UP and CONTROL_INPUT with release=true.
2. CONTROL_REVOKED before any safety output. Duplicate revoke reasons are
   legitimate, not multiple consent grants.
3. SAFETY_RELEASE_REQUESTED, then one TX_INTENT/file-fsync/local write of
   MAV_CMD_DO_SET_MODE176/custom17.
4. CRC-checked AP heartbeat mode17 in RX before SAFETY_BRAKE17_OBSERVED.
5. Neutral RC70 (first4 channels1500), then RC70 relinquish (first8 channels0,
   last10 channels65534). Each has its own intent barrier/outcome; no retry.
6. RC_NEUTRAL_AND_RELEASE_WRITTEN with localWriteOnly=true and no authority
   restoration. It is not AP execution evidence.
7. New centered CONTROL_INPUT, new OPERATOR_TOUCH_ACTION CONSENT and
   CONTROL_CONSENT with a distinct lease/neutralInputSequence.
8. Fresh input/action/binding for LAND; TX_INTENT/WRITTEN mode9, followed by
   CONTROL_REVOKED EXPLICIT_LAND_SENT_NO_MORE_PILOT_INPUT.

Normal pilot RC must not occur between revocation and the new explicit consent.
Read-only GCS/parameter traffic is distinct from the finite safety packets.

## Post-arm Home confirmation extraction

Decode each native JSONL record's base64 payload. The event kind
POST_ARM_HOME_EXPLICITLY_CONFIRMED contains actionId, atMs, armObservedAtMs,
postArmHomeObservedAtMs, preArmHome, confirmedHome and displayedHomeHash.
Home has integer latE7/lonE7/altMSLmm and datum
AP_HOME_MSL_IN_SYNTHETIC_EXTERNAL_PROFILE. The hash is SHA256 of compact UTF8 JSON
in insertion order latE7,lonE7,altMSLmm,datum (not sorted keys).

Require matching earlier OPERATOR_TOUCH_ACTION CONFIRM_HOME/actionId/hash,
postArmHomeObservedAtMs>armObservedAtMs, stable run/epoch/boot/operator/generation/
profile binding from the initial lifecycle/provider records, and exact Home
values in CRC-checked AP HOME_POSITION. The UI click uses the candidate hash last
rendered in its Home view, not an unseen latest getter. Guest atMs are Android
elapsed time, not host/AP clock; do not invent a conversion between them.

Raw chain/hash integrity is not remote authentication. Successful native CLOSE,
ACK or an anchor extracted from the same untrusted package cannot supply an
independent authority/flight assertion.

## Verified mock scope and remaining limits

Builder review01:7 current-source JVM groups and6 actual-source UI coherence
checks pass. Cases include complete release/new-consent/LAND, stale UP sample,
fresh neutral without consent, ACK-only hold, unknown BRAKE write, closed journal
FD and an observed synthetic Hold arriving700ms after UP.

The700ms case proves only that the native1.5s Hold-observation window can process
such an observation. It cannot prove AP BRAKE response, real altitude behavior
or the nominal RC_OVERRIDE_TIME0.5s interaction. In actual testing BRAKE must be
accepted and observed, with no unintended descent/failsafe confounder. If it is
not observed, native cleanup times out and the outcome remains unknown/failure.

The current native Home0,0 restriction is an acknowledged separate limitation;
the new geography oracle's legitimate0,0 support does not imply native support.
There is no need to change that unrelated native policy for this nominal site.

Receipt: evidence/betaintegrated01-m1control02/native/review01/results.json.
No native product bug was found in the requested nominal release/LAND path.
