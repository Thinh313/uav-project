# Entry10 Android-only setup

Test-only Root helper: `planning/betaintegrated01/cockpit05-entry10/android/setup_ui.py`. Import and Builder mock checks execute no ADB/process or device action. APK02 c76669…958c3 and all source/native/core/authority guards stay unchanged. No AP, STAGE, CONNECT, flight grant, install, seed, clear, AX/CDP or JavaScript evaluation.

Root commands are deliberately split:

```text
python3 .../setup_ui.py observe
python3 .../setup_ui.py baseline
python3 .../setup_ui.py prepare-r6 --reviewed-current-screen-sha <current-observe-PNG-SHA>
python3 .../setup_ui.py save-r6 --reviewed-current-screen-sha <prepared-PNG-SHA>
python3 .../setup_ui.py observe
python3 .../setup_ui.py preflight --reviewed-current-screen-sha <fresh-post-save-observe-PNG-SHA>
```

Root must inspect the exact current screenshot before supplying its SHA. Every mutation takes a fresh focused1280×800 screenshot and refuses changed bytes. No automatic action retry. The Root must observe that the prepared field reads `SITL30min_Manual_Assisted` before Save. Field(280,246)/Save(275,616)/heading(260,150) use the previously verified APK02 geometry, but only after fresh Root approval. Ctrl+A/delete/text/Back/heading-tap keeps Save separate from IME/caret/menu interaction. No new intent/probe is added.

Active entry10 guardian is required before initialization, observations, command/metadata writes and every input mutation. Gate checks exact scope/serial900s, guardian and emulator PID start identity/group, current guardian source SHA, no closure/failure, real guard tail age<=2s, integer free bytes plus finite unrounded forecast above10GiB+256MiB, power AC or>20%, and32MiB metadata cap minus1MiB per-command reserve. Require at least25s deadline headroom. It never starts or resumes a guardian. Host whole-task resource admission is Root-owned; this UI gate authorizes no30minute flight.

Baseline saves canonical flat `E/initial-workspace-SHA.json` plus `E/initial-workspace-state.json`; proof lives in `E/android-setup01/baseline-proof.json`. Before r6, both actual map and whole workspace must equal the accepted previous8 files/r5+three explicitMOCK review records. Workspace listing uses safe validated explicit paths, no shell-glob evaluation.

Prepare changes only unsaved UI text. Save is one tap and verifies actual immutable draft6 file SHA/content/name, exact old id/kind/datum/units/geometry/3m altitude/width/training flag, and all old8 bytes retained; exactlyone new r6 file is permitted. It does not promote MOCK records. Preflight only navigates and verifies no owner/staged binding, NO_SESSION and disabled CONNECT. Only after fresh Root review is `E/android-setup01/ui-geometry.json` written for later explicitly authorized work.

All new evidence is under `evidence/betaintegrated01-cockpit05-entry10/`; no prior sealed soak/UI/native evidence is changed. Guardian/metadata failures retain partial logs and stop; no clearing, hidden retries, alternate UI automation, or permission restoration.
