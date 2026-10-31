# Root operator correction after diagnosed prelaunch refusal

This supplements frozen code/RUNNER without changing source pins or runtime. Before the long controller, the existing setup helper must create its separate long geometry receipt. Merely navigating to preflight is insufficient.

After short closed raw and independent QA pass, inspect a fresh screenshot from `setup_ui observe`, then run:

```
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -B -m planning.betaintegrated01.cockpit05-clockflight02.setup_ui preflight --next-case long --reviewed-current-screen-sha <exact_fresh_reviewed_SHA256>
```

Verify `android-setup01/ui-geometry-long.json`, current207sourceclosure, current-case prior private files, guardian freshness, actual power and fresh complete long budget. Only then explicitly invoke `actual_controller long`. The short uses default `--next-case short` and its own receipt. Neither setup step grants flight authority.

The first long invocation in this task was a Root operator sequencing error before AP launch, resource prime, config or STAGE: only `control/android/entry.json` existed. Its exact file was retained by atomic directory rename to `actual-combined01-prelaunch-refused01`; SHA and original/new path mapping are in `prelaunch-refusal01.json`. No flight interval exists to add. After completing the actual missing prerequisite, one explicit new invocation generated fresh epoch/boot/generation and began the sole actual long recording. This is a diagnosed correction, not permission to blindly retry any failed flight, reset locks, reuse raw files or overwrite evidence. Failures after runtime launch must preserve their complete prefixes and use separately reviewed new identities/paths.

All runtime clock/pub/INTENT/freshness/refusal semantics, APK and physical settings remain exact. A running hold or elapsed30minutes is not acceptance; external anchors, full strict raw clocks/model/AP/native authority, failsafe landing and restart preservation still decide the result.
