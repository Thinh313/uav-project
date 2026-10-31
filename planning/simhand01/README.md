# AERIS SIM · Engineering handoff

This is an isolated simulation handoff for macOS on Apple Silicon and an explicitly selected Android USB device. The phone is the cockpit; the laptop renders the observer. It does not connect to real aircraft or restore control rights. Current aircraft/physics profiles are generic references, not a calibrated Hera model. Physical Xiaomi, actual AP closed-loop operation and final rendered visual acceptance remain NOT_CHECKED unless a separate retained receipt proves them.

## Verify and unpack

Use the supplied SHA256 for the archive through an independent trusted channel. A manifest proves byte integrity, not production source authentication.

From the source checkout: `python3 -B planning/simhand01/archive.py verify delivery/sim-handoff01/aeris-sim-handoff01-engineering.tar.gz NEW_EMPTY_DIRECTORY`.

The receiver rejects traversal, links, duplicate members, corrupt bytes and unexpected files. After extraction, run `python3 -B planning/simhand01/launcher.py doctor` from the extracted root. No SDK, image, dependency or asset download is performed automatically. Missing prerequisites produce FAIL.

## Prerequisites

Validated host family: macOS ARM64, cached Python3.14.6, Node24.14.1, Android platform-tools at `/opt/homebrew/share/android-commandlinetools/platform-tools/adb`, Docker Desktop with the exact cached `rtr-aeris-sim32-trace-builder:local` image `sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84`. The archive includes the explicit simulator code, native extensions, AP binary, scene assets, APK and licenses; it does not embed Docker images, SDKs, signing keys, other flight evidence or credentials. Unsupported Windows/Linux hosts are refused. No claim of clean-machine portability is made.

## Start and stop

Double-click `planning/simhand01/Start AERIS SIM.command`, or run `python3 -B planning/simhand01/launcher.py start --ack-simulation`.

The original engineering workspace has an immutable task stop at 2026-10-26T11:01:21UTC and refuses later runtime launches. An independently verified extracted bundle has no historical task budget. An explicit receiving operator Start creates one fresh bounded session budget under `evidence/simhand01/session-budgets`: maximum90min host, maximum300s per AP, at most6 AP/host starts and2GiB/12000 evidence files. No automatic renewal, reconnect, AP start or ARM occurs. Existing evidence is never automatically deleted.

Admission requires20GiB free with31 samples over30s; live floor10GiB plus256MiB reserve,256MiB decline guard and15s forecast. The launcher closes its owned host before the deadline with30s reserved for closure. Owned process identity and start stamp must match. A stale lock is reported, never silently deleted.

Stop with `python3 -B planning/simhand01/launcher.py stop` or the Stop command. This targets only the recorded launcher and its owned host. It does not kill unrelated processes or prune containers/volumes. Inspect `launcher-closure.json` and the gateway `host-closure.json`; exit0 alone does not establish a successful flight or complete evidence.

## Install on an explicitly selected USB device

Enable Android developer options and USB debugging, connect a data cable, and accept the computer prompt on the intended phone. List devices with `adb devices -l`. Never use an arbitrary first attached device.

`python3 -B planning/simhand01/install.py install --serial YOUR_USB_SERIAL --launch`

The installer verifies APK SHA, sets only `adb reverse tcp:8896 tcp:8896`, installs `vn.rtr.aeris.simhand01` and optionally opens `/phone`. It never requests physical root, modifies phone settings, or touches other apps. Without a matching attached serial, it waits at most60s then reports NOT_CHECKED. The sole allowed emulator identifier is owned `emulator-5582`. Do not infer real-phone acceptance from emulator results.

Explicit uninstall, including only this app's private data: `python3 -B planning/simhand01/install.py uninstall --serial YOUR_USB_SERIAL --confirm-own-app-data-removal`. No automatic uninstall or evidence cleanup is performed.

## Operate

Phone: `http://127.0.0.1:8896/phone` through USB reverse. Laptop observer: `http://127.0.0.1:8896/observer`. Select a reference scenario, explicitly start/connect, check firmware/Home/preflight, grant from neutral, then use the supported manual/AUTO controls. Source labels and actual telemetry determine status. Never infer execution from an ACK. Release, blur, app background, pointer cancellation, stale input and lease expiry revoke authority. Observer controls never issue flight commands.

LAND/abort remains accessible. Close/land the session before review/export. Unsupported payload, mission or sensor features must remain marked unsupported/NOT_CHECKED. Reference mass, wind and rotor geometry are not Hera calibration. Synthetic RPM audio is opt-in, limited, muted and stopped on stale/end; it is not a calibrated acoustic model.

## Records and SAF

The native `SimNative` bridge offers explicit SAF export/readback SHA and untrusted import. Import is then verified by the host and shown as history only. Control rights never come from stored bytes. Some high-rate raw WAL is retained externally and referenced by hash rather than embedded in the JSON package; `RAW_EXTERNAL_NOT_EMBEDDED` is not a full raw verification claim. Preserve the referenced files and use the cold receiver with the original root when required. Exported metadata alone cannot certify physics, image quality, real photos, or subjective flight realism.

See `NATIVE-BRIDGE.md` for the exact bridge contract, `dependencies.json` for file provenance, and `pilot/visual56/credits.html`, fontOFL and Three/kernel licenses for retained third-party terms. Licensed scene assets are reused offline; no new rights certification is claimed.
