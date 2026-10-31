# COCKPITVIDEO04 runtime/Android QA preparation

22/10/2026. Builder prepared helper source only. No ADB, emulator, browser control, SITL, install, download, build or signing was executed by Builder. Root is the sole live operator. Existing Android development02 APK and all prior native/flight evidence remain unchanged.

## Declared setup and resource budget

Cached AVD is **Android API33 arm64**, not API31. Use only `aeris-field02`, serial `emulator-5582`,1280×800 configured display,4CPU,2GiB RAM, GPU host and no snapshots. Package `vn.rtr.aeris.field02` must remain APK SHA256 `df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d`. `qa-device.py` checks the actual running SDK/provider/installed-byte hash; cached configuration alone is not device evidence.

Two new emulator attempts01/02 maximum, each20min. Runtime admission31 one-second samples≥29GiB, minimum30s, any peak-to-later decline≤256MiB. Poll250ms; stop below28GiB or projected15s free below20GiB; console≤4MiB, guard log≤512KiB, task evidence≤96MiB. Existing frozen AP cap9 retains7 prior requests, leaving **2 AP requests total**. These helpers never create a flight connection: Root's explicit UI Connect consumes those requests. Failed or aborted admissions still count as recorded by the frozen flight controller. Root must separately guard/close its host producer/app/AP; an emulator closure is not proof those processes closed or the disk floor held.

`qa-runtime.py --plan` is read-only. `--start 01` and`--start 02` are explicit actual launches. Exclusive attempt intent is persisted before Popen; existing intent/launch/log names refuse a repeat. Stop-request files are observed, not deleted. No automatic retries, evidence cleanup, AVD wipe, clear-data or reinstall.

Pure helper policy checks: `python3 -B planning/cockpitvideo04/qa-runtime-mock.py` passes9 cases (31s admission, short/fast/low/unstable admission, normal runtime,28GiB stop,15s trend stop, declared profile), with0ADB calls and0runtimes. All new helper Python AST checks pass. These are not Android/SITL acceptance.

## Exact root commands

From `/Users/os/Downloads/AI technique/aeris`:

```sh
python3 -B planning/cockpitvideo04/qa-runtime.py --plan
python3 -B planning/cockpitvideo04/qa-runtime-mock.py
python3 -B planning/cockpitvideo04/qa-runtime.py --start 01
```

The last command is long-running, writes new `evidence/field02/cockpitvideo04/android-*01.*` receipts and prints the owned PID. Root must run it in its managed execution session and inspect resource/ownership receipts before interacting. A second launch is allowed only as explicit attempt02 within TIP; never re-run01 or erase its intent.

Once Root observes boot completed on the owned emulator, map only the fixed cockpit ports:

```sh
/opt/homebrew/share/android-commandlinetools/platform-tools/adb -s emulator-5582 reverse tcp:8872 tcp:8872
/opt/homebrew/share/android-commandlinetools/platform-tools/adb -s emulator-5582 reverse tcp:8873 tcp:8873
python3 -B planning/cockpitvideo04/qa-device.py 01 android-device-before01
/opt/homebrew/share/android-commandlinetools/platform-tools/adb -s emulator-5582 shell am start --user 0 -n vn.rtr.aeris.field02/.ShellActivity
python3 -B planning/cockpitvideo04/qa-android.py capture 01 android-cockpit-start01
```

No install/sign command is included. If an external DocumentsUI task remains, Root may use its already approved explicit owned-task NEW_TASK|CLEAR_TASK recovery, recording the launcher artifact separately. Do not clear package data.

Root builds its read-only Vision OCR helper at `.local/cockpitvideo04/qa-ocr` from existing `planning/field02/qa-ocr.swift`; the UI helper checks that path and records its SHA. Remove Root's new OCR binary and module cache at task end; preserve all screenshot/OCR evidence. No UIAutomator exists in these helpers: the wrapper explicitly refuses any argument containing that command.

Individual actual gestures, each based on fresh screenshot/OCR or explicit observed coordinates:

```sh
python3 -B planning/cockpitvideo04/qa-android.py ocr 01 android-visible-controls01
python3 -B planning/cockpitvideo04/qa-android.py tap 01 'Payload' android-payload-tab01
python3 -B planning/cockpitvideo04/qa-android.py xy 01 1100 300 android-after-observed-tap01
python3 -B planning/cockpitvideo04/qa-android.py swipe 01 1140 560 1140 340 android-console-scroll01
```

OCR normalizes Vietnamese accents/Đ, requires confidence≥0.45 and exactly one matching visible label, then uses its screenshot bounding box. It never guesses among multiple labels or injects DOM/JS controls. Logs and screenshots are exclusive, bounded and timestamped. No retries after an uncertain command. Root must choose labels/coordinates from the current observation, not treat these illustrative coordinates as a predetermined control target.

## Modular nominal scenario

Root first imports/selects/saves the corridor model, compiles and explicitly chooses **ArduPilot SITL** in the actual cockpit, then taps Connect once. Confirm GET state has `mode:sitl`, expected model/plan/run/boot and no mock fallback. The sequence helper refuses a MOCK or absent run.

```sh
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 preflight-upload
```

This uses actual taps for readonly preflight, explicit grant and upload/readback. It returns disarmed. **Now** start the producer in the laptop browser and explicitly start the receiver on Android, observing host-only VideoEncoder and fresh received frames. Source controls stay on laptop; never load/drive a publisher in Android. Starting source near this step avoids consuming its frozen128MiB byte quota during EKF/preflight setup.

When video is ready, expose the right flight console and run:

```sh
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 arm-home
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 auto
```

Arm-home refreshes preflight before arm, records post-arm Home, requires the declared simulator site within1m and AMSL10±0.5m. AUTO uses a fresh screenshot and rechecks exact live gate immediately before its one tap, requiring>1800ms remaining. It does not extend/retry expired Home/parameter gates. Prepare video before arm; do not spend the short gate window opening a host browser or copying paths. If the gate expires, stop and preserve the partial attempt.

Select the visible Payload tab using real UI, then:

```sh
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 payload-setup
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 payload-capture
```

Setup performs discovery/select/explicit60s lease grant; it records the current redacted lease view. Capture phase performs a real gimbal/readback request and a fresh-frame capture request; Root must scroll the right console with observed gestures if a button is out of view. Requests alone are not accepted readback, exposure or correct-image proof. Root retains WAL/result and validates capture feed, source/session/config/clock/model/run/boot and exact raw position reference. Sensor/exposure accuracy remains unknown and images are synthetic/non-radiometric.

Measure30s of fully visible receiver canvas concurrently with active mission/payload. Root must retain the unmodified raw report and separate identity/report-SHA-bound overlap sidecar; this helper does not create/alter a performance PASS. Record exactly which interval was in flight/airborne and which payload events occurred; do not call all30s airborne merely because AUTO appeared. The source credit/profile/report thresholds remain frozen.

Expose flight console after observed RTL/ground-disarm:

```sh
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 nominal-close
```

This waits for observed complete navigation/RTL/ground-disarm, taps Close once and requires accepted review. Independent raw replay remains mandatory.

## Separate actual AP reboot scenario

Use the second remaining SITL request; it is distinct from emulator cold boot02 (either admitted emulator session may serve it within20min). Root performs real Connect and preflight/upload/Home/AUTO as above with fresh exclusive phase receipt names under attempt02. If reusing emulator session01, use attempt01 for the new connected run; phase receipts/screenshots bind their exact run ID, so they remain exclusive without pretending a second emulator launch. Do not rerun a phase for the same run or fake attempt02 ownership.

Prepare payload late enough to leave an unexpired lease at the actual fault. Root exposes Payload UI and uses `payload-setup`; then quickly returns to flight UI, opens the fault disclosure and exposes **Restart tiến trình AP**. Do not spend its60s lease window on video source setup.

```sh
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 02 reboot
```

Immediately after fresh OCR and before tap, the helper GETs readonly state and requires armed/fresh altitude>5m plus current `payloadLeaseObservation`: leaseCount≥1, matching run/boot/model/plan/clientId/epoch and remaining≥5000ms. It records exact observation, then one UI fault gesture. After close it requires zero current leases, no flight authority and durable `FLIGHT_REBOOT` pre≥1/post0 with the pre lease unexpired. Root/independent QA still verify receipt seq/hash ordering **before** actual AP effect, changed owned guest AP PID/StartedAt, raw incomplete outcome and no automatic regrant. A direct rejection using a fabricated token is not replay of the actual previous bearer token; distinguish tests explicitly.

Video may continue independently; continued pixels must not show fresh flight/control claims. Do not reconnect or regrant automatically. A later authorized process restart/SAF check must retain prior workspace/journal/media bytes and no restored rights.

## Closure

Root creates a new exclusive stop request for the actual admitted attempt, or signals only its controller PID. Example:

```sh
python3 - <<'PY'
from pathlib import Path
import json
p=Path('evidence/field02/cockpitvideo04/android-stop-request01.json')
with p.open('x') as f:json.dump({'reason':'EXPLICIT_ROOT_COMPLETED_OR_STOPPED'},f)
PY
```

Verify owned emulator/host producer/app/AP closure, remove only mappings introduced here, compare old/native/baseline SHAs and inventory any new append-only flight runs. Preserve every guard/partial/failure artifact. A guard trip, mode MOCK, missing overlap or not-run mandatory gate remains NOT_CHECKED/NOT READY; no helper's `exit0` is product acceptance.

## Explicit Android MOCK rehearsal before SITL

Root's scoped DECISION-MOCK-APPEND permits its one MOCK rehearsal request separately from AP budget; these helpers do not Connect or allocate a request. Root selects MOCK in the actual cockpit and explicitly connects once, then can call the same phases with `--mock`:

```sh
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 preflight-upload --mock
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 arm-home --mock
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 auto --mock
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 payload-setup --mock
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 payload-capture --mock
python3 -B planning/cockpitvideo04/qa-ui-sequence.py 01 nominal-close --mock
```

Every observation is labelled `mode:mock`, `notSITLProof:true` and exact m-prefixed run. The default refuses MOCK; explicit `--mock` refuses an s-prefixed/SITL run. The reboot acceptance phase refuses mock mode entirely. Receipt/screenshot names bind attempt+mode+exactrun+phase, allowing separate nominal/fault runs on the same admitted emulator without overwriting or silently rerunning a phase. Source/video/performance still require their own observations. No MOCK outcome substitutes for real AP nominal/reboot acceptance.

AUTO admission preserves the prior>1800ms window; source/viewer setup must finish before arm. Root may chain arm-home and auto in one managed shell invocation to avoid human/tool roundtrip expiry, while preserving two explicit actual UI gestures and all observations. No gate duration is changed.

## Root setup/start/native preservation wrapper

`qa-device-actions.py` provides the explicit operations omitted from readonly `qa-device.py`. It checks owned emulator receipt, qemu/AVD identity, calls ADB root only on5582, waits bounded90s for boot, reverses8872/8873, verifies installed APK SHA/API33/4onlineCPUs and records boot/provider. Setup/start intent receipts are exclusive before effects: an uncertain operation cannot silently repeat.

Recommended ordered commands after emulator launch and host companion ready:

```sh
python3 -B planning/cockpitvideo04/qa-device-actions.py 01 setup
python3 -B planning/cockpitvideo04/qa-device-actions.py 01 store-before
python3 -B planning/cockpitvideo04/qa-device-actions.py 01 start
# Root performs its actual rehearsal/mission/UI checks.
python3 -B planning/cockpitvideo04/qa-device-actions.py 01 store-after
```

The start action uses one explicit `am start -S -W --user 0 -f 0x10008000 -n vn.rtr.aeris.field02/.ShellActivity`, records previous/current PID and AM response, and refuses any active flight or payload lease. It clears the associated activity task only, never native app/provider data. It is intentional process cold start, not a viewer retry. A later approved restart test can use a new named variant with a matched preservation pair:

```sh
python3 -B planning/cockpitvideo04/qa-device-actions.py 01 store-before --variant restart-a
python3 -B planning/cockpitvideo04/qa-device-actions.py 01 start --variant restart-a
python3 -B planning/cockpitvideo04/qa-device-actions.py 01 store-after --variant restart-a
```

Store snapshots hash all native files (retained baseline15, bounded≤64), capture the exact journal≤1MiB read-only, and require the hash listing and captured journal to agree. After must retain every prior artifact SHA and the full journal prefix; valid new mirrors/append bytes are reported separately. A valid explicit workspace save may append journal/mirror evidence; it must not be confused with restoring authority. No `rm`, `pm clear`, reinstall, source change or provider-file write exists in this wrapper. Builder ran only AST checks, no ADB operation.
