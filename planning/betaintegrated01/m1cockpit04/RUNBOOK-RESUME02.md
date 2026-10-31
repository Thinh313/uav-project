# APK02 / combined 30-minute qualification

Engineering emulator scope only. No physical Hera, SDK, media or production
release. Previous COCKPIT04 partial receipts, APK01 and ENDURE stay unchanged.

## Selected inputs

- APK: `native/betaintegrated01/cockpit04/dist/aeris-cockpit04-development-02.apk`
  SHA256 `3273c9cb3fec67f2b1598761eaf4b02bde27097babeea162d3482fd925c3fd45`.
- Native receipt: `evidence/betaintegrated01-m1cockpit04/native/build-02.json`.
- Host receipt: `evidence/betaintegrated01-m1cockpit04/host/module-manifest02.json`.
- External resource policy: `pilot.betaintegrated01.cockpit04.revision02.capacity`.
- Native journal160 MiB; one export168 MiB; cumulative export ceiling192 MiB.
- Old runtime/profile02/typed39/AP/model/pacing/fsync source remains selected.
  Profile02's old three-case budget labels are superseded by the explicit
  revision02 external resource ledger, not by changing its parameter/config SHA.

## Admission and operation

Root alone owns runtime/ADB/actions. Check actual free space and observed power
again. Entry20 GiB, live floor10 GiB plus256 MiB reserve and real15-second
priming/forecast remain mandatory. Never reuse an earlier admission, fake AC,
delete evidence to fit, reset guard state or resume a partial flight interval.

The emulator02 attempt was refused before any process launched. Its refusal
receipt/source are retained. Next identity is emulator03. Cached API33 ARM64 AVD
and emulator-5582 only; do not install dependencies, download images or copy the
project. `bootstrap_android02.py 02` now reserves emulator03 and checks entry
before creating its directory. Observe PID/start identity and boot completion.

Only after admission: verify APK/source pins; install APK02 on the owned emulator,
verify installed SHA, inspect the fresh UI and stored training polygon. Retain
the previous package's private-data baseline and all prior records. No AP or
flight action is needed for this installation/setup phase.

`actual_combined02.py 01` is the new Root-only controller. Before invoking it,
require independent oracle mock readiness, coherent current APK02/host02/helper
pins, source boundary PASS, reserved ports and current entry admission. It uses
the existing host backend/profile02 and requires inert staged native preflight
before AP starts. Its resource guard and both runtime journals prime using real
time. At most ONE combined start is selected; a failed start needs diagnosis,
not automatic retry or new consent.

The actual scenario is survey/preflight, post-ARM Home confirmation, takeoff3 m,
LOITER/forward input, UP/revoke/BRAKE/neutral/relinquish, explicit new neutral
lease, at least1800 s continuous assisted airborne hold, then transparent link
cut and AP GCS failsafe LAND. There is no native user-LAND in this scenario.
This is distinct from losing link while holding the stick forward. Capture
foreground/native elapsed and uptime, host, AP boot/guest and model clocks.
Do not count separate intervals or synthetic clocks as wall-time qualification.

## Closure and independent receiver

Preserve native FAILED/uncertain review after the intentional fault. Passive AP
ground/disarm proof is separate from what disconnected native could observe.
Ordinary restart must restore exact draft/review files, a new view epoch and
NO_SESSION/ownerfalse/bindingnull, never authority or automatic reconnect.

After managed closure, use `capture_external02.py <case>` for outside-raw parent
anchors, then `make_confirmation02.py 01` for explicit Home binding. The receiver
is `qa/actual_combined_cold.py <case>` and uses revision02 native160/168 readers.
It verifies the original host raw in place, every admitted frame/model/AP stage,
native CRC/input/lease/cleanup, geodesy, clock duration, source, failsafe and
restart. No full host raw copy, extraction, compression, frame dropping or
duration/speedup/cap changes. Keep all failed prefixes and diagnostic output.

Stop the owned emulator after the run and verify protected source/candidate/
ENDURE boundaries. Mock PASS or a ready APK is not actual30-minute acceptance.
If fresh entry admission fails, report actual NOT_RUN without weakening gates.
