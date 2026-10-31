# Generation02 runtime/Android QA helper handoff

22/10/2026. Implements only QA helper variants under the explicit `DECISION-GENERATION02-LONG-CORRIDOR.md`. Generation01 helpers, product/native source, APK, source pins, earlier receipts and all runtime data are unchanged by Builder. No ADB/UI/emulator/AP process was executed.

New source files are `qa-runtime-v2.py`, `qa-android-v2.py`, `qa-device-actions-v2.py`, `qa-device-v2.py`, `qa-arm-auto-v2.py`, `qa-preflight-upload-v2.py`, `qa-live-actions-v2.py`, and `qa-runtime-mock-v2.py`. Exact hashes and scope are in `builder-generation02-runtime-preparation.json`. All Python AST checks pass;9 pure guard-policy cases pass with0ADB/0runtime. Every device/action helper imports only qa-android-v2; its ownership gate admits **03/04 only** and uses a new `qa-adb-commands-v2.jsonl`, never appending the old command ledger.

## Unchanged limits and preserved evidence

Cached Android API33 arm64, emulator5582/aeris-field02,4CPU/2GiB, GPUhost/no-snapshot,20min per cold boot. Admission31 samples≥29GiB over≥30s with peak-to-later decline≤256MiB. Runtime28GiB guard/250ms and15s forecast protecting20GiB; original96MiB task evidence limit remains. Existing native15+ artifact hashes and exact journal prefix are collected before/after each lifecycle run; native records may append only through the unchanged authorized app. No install, build, signing, cleanup or data reset exists in these helpers.

The new isolated adapter and canonical3× horizontal corridor are prepared by the product Builder, not these QA helpers. Root must verify their independent model/units/Home/pin/cumulative-cap gates before any AP admission. Nine prior AP requests remain; only new requests10/11 are permitted,12refused. These QA helpers never Connect or allocate a flight request. The two extra emulators03/04 and two extra AP requests are final distinct attempts, not hidden retries or threshold/speedup changes.

## Root commands

```sh
python3 -B planning/cockpitvideo04/qa-runtime-v2.py --plan
python3 -B planning/cockpitvideo04/qa-runtime-mock-v2.py
python3 -B planning/cockpitvideo04/qa-runtime-v2.py --start 03
```

When owned03 is booted and host03 is ready:

```sh
python3 -B planning/cockpitvideo04/qa-device-actions-v2.py 03 setup
python3 -B planning/cockpitvideo04/qa-device-actions-v2.py 03 store-before
python3 -B planning/cockpitvideo04/qa-device-actions-v2.py 03 start
python3 -B planning/cockpitvideo04/qa-device-v2.py 03 android-device-inventory03
python3 -B planning/cockpitvideo04/qa-android-v2.py capture 03 android-long-corridor03
```

Root explicitly chooses SITL/Connect in actual UI, observes current reference screenshot and supplies the real button y coordinates. Preflight/grant/upload and preflight/arm use those observed coordinates, not OCR guesses:

```sh
python3 -B planning/cockpitvideo04/qa-preflight-upload-v2.py 03 CURRENT-REFERENCE.png PREFLIGHT_Y GRANT_Y UPLOAD_Y
python3 -B planning/cockpitvideo04/qa-arm-auto-v2.py 03 CURRENT-REFERENCE.png PREFLIGHT_Y ARM_Y
```

The AUTO selector alone uses existing `.local/cockpitvideo04/qa-ocr-fast`, timeout2s, exactly one visible numeric5 plus literal AUTO match in the complete right-console bounds. It retains actual Home site/AMSL review, ready/readback checks and **>1800ms** gate remaining. No I/l→1, S→3, rn→m or other fuzzy correction. Generic OCR text-click is disabled in qa-android-v2; manual Root coordinates come from fresh screenshots. Accurate OCR stays excluded.

Payload/measurement/reboot phases are the Root-authored observed-coordinate helpers with unchanged predicates, now importing the03/04 ownership module:

```sh
python3 -B planning/cockpitvideo04/qa-live-actions-v2.py 03 payload-grant CURRENT-REFERENCE.png DISCOVERY_Y SELECT_Y GRANT_Y
python3 -B planning/cockpitvideo04/qa-live-actions-v2.py 03 measure-payload CURRENT-REFERENCE.png GIMBAL_Y CAPTURE_Y
# Second distinct real AP request, after its own fresh setup and active unexpired lease:
python3 -B planning/cockpitvideo04/qa-live-actions-v2.py 04 reboot CURRENT-REFERENCE.png REBOOT_X REBOOT_Y
```

These names are placeholders requiring the current screenshot file in the new task evidence root and real observed coordinates; never run them literally or reuse a stale layout. Measurement/capture still require airborne armed AUTO, height>5m and a same-run/boot/model/plan unexpired lease. Reboot still requires active unexpired lease and durable pre≥1/post0 proof plus raw PID/order verification. Root starts laptop producer near actual measure and Android receives only; source profile/quotas/clock/report thresholds remain unchanged. Accepted prior29.9FPS alone does not fill missing overlap or fault proof.

At task end, Root records store-after and explicit stop request03 or04, then independently verifies host/AP/producer/emulator closure, old SHA baselines, all append-only runs and evidence quota. Repeat the same commands with04 only after independent admission for the final cold boot; never overwrite03 intent/receipt or relabel an old attempt. A resource stop, missed window or missing predicate remains partial/NOT READY, not permission for another automatic generation.
