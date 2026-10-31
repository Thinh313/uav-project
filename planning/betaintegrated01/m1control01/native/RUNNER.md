# CONTROL01 native Android runner contract

Diagnostic training controller, not final cockpit/HID calibration or real UAV.
`vn.rtr.aeris.control01/.ControlActivity`, API33 owned emulator5582 only.
Root is the only ADB, emulator, AP and live-service launcher.

## Connection and output

Use `run-as vn.rtr.aeris.control01` to place exact UTF8
`files/launch-binding.json`. Binding includes version1/rootOwnedContainertrue/
targetSystem42/modeCANDIDATE_EXTERNAL/profileId/binarySHA256/modelSHA256/
configSHA256/endpoint/firmware/run/epoch/boot/operator/generation, plus
`inputProvenance=ROOT_INJECTED_ANDROID_TOUCH` for ADB/UIAutomator runs.
Root's binding is trusted local orchestration, not remote authentication.

```text
am start -n vn.rtr.aeris.control01/.ControlActivity
  --es m1Action CONNECT --es m1ActionId <new-unique-id>
  --es launchBindingSHA256 <exact-private-binding-SHA256>
```

Only CONNECT/CLOSE/STATUS are accepted as explicit intent actions. Fresh queued
intent policy consumes after onPostResume, TTL2s, recent16IDs, no history resume.
**All active flight actions must use observed UI buttons**, because an Activity
intent can pause the owner and must close the socket. Inspect state through
run-as, never a STATUS intent during flight.

Private files: `files/latest-state.json` (atomic mutable checkpoint),
`files/control-runs/<run>/` (exclusive raw/segment/seal/session data),
`files/probe-<UTCms>.json` (actual minimumAndroid/EGL/WebView probes, codecs listed
as available only; actual decoder NOT_STARTED_NOT_OBSERVED/no-media profile).

## Visible UI controls and input geometry

All native buttons expose content descriptions:

`control01-consent`, `control01-guided`, `control01-arm`,
`control01-confirm-home`, `control01-takeoff`, `control01-loiter`,
`control01-hold`, `control01-land`, `control01-close`, `control01-connect`.

`control01-left-stick`: left horizontal yaw clockwise+, vertical climb+.
`control01-right-stick`: horizontal roll right+, vertical pitch forward+.
Get each current bound from UIAutomator. Stick center is the bound center;
radius is `0.32*min(width,height)`. Moving up produces positive forward/climb.
Raw axes are[-1,1]; declared small-motion envelope maps PWM to
`1500+125*{roll,-pitch,throttle,yaw}` on channels1/2/3/4. This is pilot-stick
control in LOITER with AP attitude/position assistance, not ACRO.

Every actual MotionEvent and its bounded history is queued for durable recording.
Separate UI-thread state samples20Hz bind source-instance UUID, context, sequence,
sample uptime/elapsed clocks, last MotionEvent clock, pointer state and axes.
The IO thread cannot retimestamp or synthesize a fresh input. The producer starts
only after the explicit consent action, stops on UP/CANCEL/focus/pause/closure.
An UP/CANCEL sends a fresh release observation then stops sampling. Another
consent requires a fresh centered observation and does not restore old authority.

## State and sequence

`preflightReady/preflightReason`; `flight.mode`, `armed`, `landedState`,
`relativeAltitudeM`, `horizontalSpeedMps`, `batteryWireMillivolts`, GPS/EKF/health,
`home`, `preArmHome`, `homeHash`, `postArmHomePending`, `homeConfirmed`,
`homeObservedAtMs/armObservedAtMs`, `hoverObservedMs`; `input.source`,
`acceptedInputs`, `lastInputSequence`, `grants`, `consent`, `leaseExpiresNs`;
`releaseState`, `rcOverrideActiveLocally`, `firstFailure`, native IO gap maxima.

Expected nominal sequence: wait exact typed39/readiness → explicit consent →
GUIDED, wait actualmode4 → ARM, wait actualarmed → await a new postARMHome
observation → read the visible candidate and tap Home confirmation → TAKEOFF3m
→ wait observed hover3m±.75/horizontal≤.5m/s across≥1s actual samples → LOITER,
wait actualmode5 → actual right-stick forward gesture≥1s → UP/CANCEL release →
wait observedBRAKE17, native neutral/relinquish completion → new centered consent
→ LAND → wait actualground/disarm before closing. No ACK/write alone passes.

Home confirmation binds the SHA actually rendered in the Home UI. A click never
fetches an unseen latest candidate; changed/stale/foreign Home refuses Takeoff.

## De-escalation and faults

User lease200ms renews only from a fresh UI sample. Expired input cannot revive
consent when it arrives before tick. Pointer-release/expiry/Hold revokes pilot
authority before a separate finite safety sequence: one fsyncedBRAKE17 request,
observe actualmode17, then one neutral RC packet and one RC relinquish packet
(channels1..8=0;9..18=65534). No retry. If RC was never active, observed Hold may
need only the mode packet and is recorded distinctly.

Stale telemetry, boot/generation changes, unknown writes, fsync failures, focus
loss and link loss stop pilot output. If cleanup is unsent or unknown, close the
socket and stop GCS heartbeats; the passive host observer must establish the
selected AP5s LAND failsafe and actualground/disarm, or report UNKNOWN. No
automatic reconnection or authority restoration. Inflight AP reboot is mock only.

Nominal RC override timeout0.5s and the separately declared link-loss timeout6s
have different purposes. Loss6s lets GCS5s LAND clear overrides before fallback
RC3=1000 masks the intended GCS observation. Neither changes the user200ms lease.

RX chunks retain their original read receipt clock before fsync. Apply gaps>200ms
cannot refresh flight state; native loop gaps>500ms are checked again at send.
Kernel/network age remains unmeasured. Host20/10GiB+256MiB/true15s guards and
all model/AP frame verification remain independent of the native raw receiver.
