# COCKPIT05 soak Android operator fork

Root alone runs device/ADB/emulator/AP/flight. These test helpers perform no device or subprocess action on import. Builder performed only in-memory syntax/import/decision mocks. No APK/source/signing change.

Import the uniquely named local modules to avoid an old04 generic-module cache:

```python
sys.path.insert(0, str(ROOT / 'planning/betaintegrated01/cockpit05-soak/android'))
from cockpit05_root_operator import RootOperator
from cockpit05_android_operator import AndroidOperator, OperatorError, PACKAGE, ACTIVITY
```

`PACKAGE='vn.rtr.aeris.cockpit05'`; `SERIAL='emulator-5582'`; Activity `.CockpitActivity`. Source methods remain exact04 except the package constant and local import name. All control descriptions stay `control01-*` and stick methods use real Android touch. No CDP, browser evaluation, synthetic authority, transport/MAVLink sender, scenarios, command retries or restored native lease.

Root constructs `RootOperator(case_evidence, current_run, current_generation)` explicitly. `.state()` reads `files/latest-state.json`, never workspace/MOCK review history. Context mismatch rejects. `_fresh_state()` compares actual device uptime with current native HB/position <=1500ms, rejects future/invalid ages. Native action/home/consent/lease readiness checks are unchanged; helper predicates cannot grant native authority.

Existing APIs: `.layout()`, `.state()`, `.wait_state(predicate)`, `.explicit_connect()`, `.explicit_tap(action)`, `.start_stick_hold(description,horizontal,up,duration_ms)`, `.navigate_fly()`, `.navigate_review()`, `.screenshot()`. Every action is an explicit Root call with fresh package focus/state/screen and current native measured button/pad bounds. Native input producer/authority stays in selected APK, not in this helper.

Navigation reference `evidence/betaintegrated01-cockpit05-soak/native/nav-reference01.json` comes from exactCSS plus reviewed actual05 screenshot27, NOT a new UIAutomator measurement. Root must independently approve a fresh actual screenshot/focus before assigning `op.nav_geometry`. References at1280×800: survey[17,254,79,318], preflight[17,318,79,382], Fly[17,382,79,446], review[17,446,79,510]. Visible labels remain Khảo sát / Trước bay / Bay / Hồ sơ. Active underline changes no button geometry.

Root must preserve existing05 private workspace/4seed generations/native r5/3MOCK review bytes and SHA before creating actual r6 through UI. Historical/MOCK records are not current telemetry, ground qualification or permission. New current context must be staged explicitly, then visible CONNECT, neutral consent and complete native guards. Restart restores history only. Runtime only after actual admission20/10GiB and power/source guards; current failed entry does not authorize a bypass.

Native exports remain Root-bounded per active case and selected capacity/oracle policy. The generic `.export_private()` exists unchanged but does not enforce campaign aggregate caps, so Root must NOT call it for whole history or unbounded data. Root's bounded selected-run tar implementation should enforce the approved one-copy limit; never delete old evidence to fit.
