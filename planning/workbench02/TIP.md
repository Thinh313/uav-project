# NATIVE Workbench02

2026-10-24, authorized Workbench01 → isolated Android shell, mock first; Android/SITL only when actual admission passes. Vibecode6.3, one assistant switches Contractor/Builder/Verify, no independent-review claim. New scope only pilot/workbench02, native/workbench02, planning/workbench02, evidence/workbench02 and dedicated completion report. Workbench01, G17, all old candidates/ENDURE immutable. Retained task budget8MiB, physical floor20GiB. No whole project copy, no dependency installs. Native typecheck/host store tests may run small; APK/emulator/AP require29GiB stable original31-sample gate and existing28GiB runtime protections. No production signing.

## Design / decisions
- Project Workbench01's pinned UI in memory with exact counted replacements for native load/save/SAF and lifecycle only. Serve its original CSS/font/geometry by read-only reference. Pin the original SHA, test inverse equivalence and no authority restoration. No copied app/source tree.
- Android shell is host-companion, loopback8892 via a future ADB reverse. Java broker validates origin/session/foreground, serializes native data operations, uses app-private immutable generations + fsync/atomic same-directory renames, no java.nio ART move dependency. No automatically deleted evidence or restored authority. No SDK/hardware driver.
- Native save returns only after body+head fsync and directory sync, with exact raw-byte SHA and expected-head CAS. Pending files/orphans/corruption cause read-only refusal. Bundle semantic validation remains on the frozen WB01 receiver; native broker must validate receipt/raw SHA before committing. Cancellation/failed SAF/short write/readback mismatch do not report success.
- SAF export/readback and import are explicit data operations. A native pause revokes mock approval; no background simulation or auto-retry. Host/browser clocks are not flight time.
- WB01 wider planning limits must not bypass mission92 native/SITL profile. Adapter accepts only explicit synthetic Home AMSL10 consent, exact tested Home/camera, AGL10–30m, speed0.5–2m/s; replay mission92/native94 compile through frozen modules, hash-bind source/model/target. Out-of-profile rejected without clamping. This is preparation/attestation, not upload or actual execution.
- Never run old G17 campaign as proof of a new UI. Actual integration must retain original resource/lifecycle/control guards and pass source/pin/controller gates; no flight dispatch exposed by this preparatory shell. G17 combined AUTO/video/payload acceptance remains NOT READY.

## AC
N1 pinned projection actually replaces persistence/export/import/lifecycle, no localStorage fallback in native mode; mock only explicitly labeled.
N2 plan/pixel review uses frozen host semantics; native body/hash/format and model92/compile94 binding consistent, invalid datum/profile/camera/target rejected.
N3 durable data store tests: CAS, corruption, quota, pending, fsync/rename failures, restart, rollback indication, zero restored authority; no cleanup of data generations.
N4 Java shell security + SAF bounded data/cancel/readback; host tests/typecheck only distinct from ART/SAF actual acceptance.
N5 mock native bridge: correlation, wrong session/id, timeout, foreground loss, storage errors, no implicit success/retry; all valid intermediates retained.
N6 source/admission/preservation report, actual Android/SITL mandatory gates. If under29GiB, no build/boot/AP or waiting loop; report runtime NOT RUN and milestone PARTIAL.

Runtime AI absent; deterministic code baseline retained. User time/effort advantage vs CLI unmeasured. Do not claim DJI parity or full native usability from mock/typecheck.
