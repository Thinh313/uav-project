# M1-CONTROL01: native manual/assisted, link loss and AP reboot

27/10/2026. User authorizes mock first, then owned Android–SITL manual/assisted,
link-loss/AP-reboot checks, full admitted frames, frozen source/candidate/ENDURE,
20/10GiB and no production signing. Existing development certificate may sign
only the isolated emulator APK needed for this authorized test.

## Roles and immutable inputs

Apply Vibecode6.3. Explicitly delegate native input/authority implementation,
host fault/profile/oracle implementation and separate independent QA. Contractor
owns admission, source/runtime closure and actual launches; Builders/QA must not
launch AP/emulator/live host services. No nested delegation needed.

All previous M0/M1-MOCK/runtime01/runtime02 source, profiles, APKs, raw, receipts,
handoff seals and canonical SOT remain immutable. New source only:
`native/betaintegrated01/control01/`, `pilot/betaintegrated01/control01/` and small
new versioned configuration artifacts in `runtime/betaintegrated01/control01/`.
New tests/TIP/ADR under `planning/betaintegrated01/m1control01/`; new evidence under
`evidence/betaintegrated01-m1control01/`. Import/select small exact modules from
previous closure; no whole project/SDK/ArduPilot source copies or downloads.

## Outcome and scope

One Android-native writer controls the simulated AP. Implement real bounded
continuous stick input under explicit neutral/consent/freshness/lease, rather
than calling a single synthetic zero pulse a manual controller. Initial manual
profile may be pilot stick control in LOITER (AP position/attitude assistance),
clearly labelled; ACRO/unassisted STABILIZE are not silently claimed. Assisted
profile includes explicit GUIDED/ARM/3m takeoff, observed hover/Hold, small manual
motion and observed LAND/disarm. ACK or command-write alone cannot pass motion,
mode, landing, disarm, failsafe or input-authority acceptance.

Reuse actual external AP03 and exact model/pacer where possible. A new versioned
typed parameter profile must reflect firmware4.7.1 source names/types and the
selected GCS/RC failsafes. Current referenceProfile95 is AUTO/internal-regression
policy, not an authority to disable arming checks or silently accept mismatches.
Builders propose exact mappings/parameter defaults for Contractor acceptance.

Post-arm Home changes need an explicit versioned observation/confirmation state
before takeoff, with raw datum/coordinates/time and operator test action, not an
implicit tolerant reseal. Unknown/new values fail closed. Keep actual preflight
checks; never disable checks to obtain an arm success.

## Invariants

- One native sender thread; no root/host MAVLink command broker. Sole writer
  owns flight and RC release. A passive AP monitor may only receive bytes, with
  zeroTX explicitly tested/recorded, for observing airborne GCS failsafe during
  the intentional native link outage.
- Native raw RX before parsing; intent/filefsync before each send; SENT/UNKNOWN
  distinction, segmented exact records, terminal timing and no restored lease.
- Input includes session/run/epoch/boot/operator/generation/sequence/guest clock,
  axes and freshness. Retain input-to-wire binding and reject foreign/stale/
  duplicated/late/expired input at actual send boundary. No automatic grant on
  discovery/reconnect/restart/reboot. Explicit fresh neutral and consent required.
- Link loss while holding forward: revoke local lease, stop stale output,
  retain uncertainty for unsent release, observe actual AP timeout/failsafe and
  terminal ground/disarm or report UNKNOWN. Reconnection must not prevent the
  intended failsafe observation by unintentionally restoring GCS heartbeats.
- AP reboot actual first on ground/disarmed, with owned new AP process identity,
  boot/epoch and complete discovery/preflight before any new consent. In-flight
  reboot only mock/replay in this tranche; never label it actual-tested.
- UI pause, queue/reader/write/fsync failures and test-runner failures follow a
  predeclared simulator-only abort/managed closure. No uncertain action retry.
- Keep model equations, speedup1/cap500ms, all admitted frames and exact timing,
  true15s host guard policyv2, entry20GiB/floor10GiB+256MiB. No hidden guard change.
- Local root bindings are orchestration trust, not remote authentication. No real
  aircraft, HeraHub/Xiaomi, LAN pairing, production key/sign or external publish.

## Mock-first acceptance

Test continuous input cadence/expiry/neutral/release, consent and boot/session
fencing, duplicate/reorder/type/target/clock faults; preflight/Home transitions;
disconnect and reboot while input is held; no implicit authority restore;
send/fsync/stage fault truthful partial prefixes; foreground intent ordering.
Use independently decoded raw protocol and state observations. Preserve failures.
Keep legacy read-only source/qualification distinct from new control capability.

## Actual plan and budgets

Window<=4h; <=3 repair/check cycles per repro family. Unit evidence<=256MiB/2000
files; new runtime evidence<=6GiB/12000files. Actual source/config/exec allowlist,
requested-duration original/copy/export peak and live guard must pass each time.
Build only cached tools with current free>=20GiB, scratch peak<=128MiB, reusable
`native/betaintegrated01/.build`, clean own classes/unsigned intermediates.

Initial allocation<=6 host/emulator starts and<=6 AP starts, one emulator serial
5582 reused with existing own AVD. Aim three bounded scenarios: nominal native
manual/assisted (<=90s), airborne link outage/failsafe (<=90s), disarmed AP reboot
and fresh readonly recovery (two<=60s epochs). Allow a bounded smoke/repair only
within those start caps; no automatic campaign resume or lock deletion. Do not
keep AP alive indefinitely while debugging UI. Each run has unique raw/epochs.
No30min run in this tranche. No large new raw copies/export needed to prove
control; independent cold verification may read closed original files with live
external anchors retained separately. Capacity still reserves declared peaks.

Actual PASS requires motion/modes and recovery observations from raw, exact
frame/STAGE/AP coverage and model replay, native input/authority/command oracles,
observed closure and no hidden restore. Stop with PARTIAL/NOT_READY if capacity,
current firmware/profile or any critical gate refuses. Do not mark whole M1 or
Beta complete from these bounded cases; 30min and full-cockpit/media gates remain.
