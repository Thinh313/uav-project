# Strict fast-OCR flight helper handoff

QA-only `qa-ui-fast.py`,22/10/2026. No ADB/UI, live control, app source or runtime was executed by Builder. The source provides two Root-only chains:

```sh
python3 -B planning/cockpitvideo04/qa-ui-fast.py 01 preflight-grant-upload
python3 -B planning/cockpitvideo04/qa-ui-fast.py 01 arm-home-auto
```

Optional explicit `--mock` accepts only an existing m-prefixed/MOCK run; default accepts only an existing s-prefixed/SITL run. No Connect action exists. Receipts bind attempt/mode/exact run/phase and refuse overwrite. A fresh full screenshot plus existing `qa-ocr-fast` (timeout2s) precedes each tap. Entire OCR glyph rectangle must lie inside right console `(740,250)-(1190,650)`, confidence≥0.45, and match exactly one strict numeric/text prefix:1+preflight,2,3+Upload,4+Arm,5+AUTO. No `I/l→1`, `S→3`, `rn→m` or fuzzy fallback is accepted. Missing/ambiguous matches log NO_ACTION_STRICT_OCR_REFUSAL and send no tap.

Each actual tap is preceded by fresh readonly state checks of exact instance/run/session/boot/model/plan/client epoch. Preflight readiness, explicit grant, readback, disarmed state and observed post-arm Home remain mandatory. AUTO retains eligible gate and **>1800ms** remaining. Chains have30s/10s total budgets respectively; they do not loosen a predicate, retry a command or extend Home/parameter freshness. Failed chains are not acceptance and may leave a previously executed operation pending; Root must inspect, not run the same chain again.

Stored actual image `android-mock-actions-bottom01.png` was read with fast OCR only under2s:138ms successful decode. `qa-fast-ocr-flight-bindings01.json` retains all raw rows. Actual image strict matches were **grant2 and AUTO5 only**. Preflight appeared `l- Doc pr•fllght`, upload `S. Uploadl r•adback`, arm `4.Arrntrén dat`; all three correctly refuse. `qa-ui-fast-selector-check01.json` records10 synthetic strictness cases, including those confusions and duplicate-row refusal. Those synthetic successes do not establish usable full-chain OCR on the real screen.

**Disposition: helper source ready, full real-chain usability NOT VALIDATED.** Root needs manual gestures for missing/garbled labels unless its new screenshot meets the same strict rules. Do not claim the chains meet live30s/10s targets from the138ms offline OCR sample. The accurate English OCR helper remains unusable under3s as reported separately. No source/layout change, confidence lowering or fuzzy correction is authorized here.
