# Workbench02 Java01

2026-10-24. User authorizes the two pending Java patches, store mock/fault tests and Android typecheck; Android–SITL only after full admission. Original TIP and 8 MiB task budget apply. One assistant switches Contractor/Builder/Verify, not independent review.

- Patch WorkspaceStore to expose a stricter test quota only (never above production 8 MiB), retain 16 generations/128 MiB Android reserve, and reject a symlink at the named store root.
- Patch ShellActivity to reject coercion of request version strings/fractional values; version must be a JSON number equal to 1.
- Keep bridge patch and every previous evidence file intact. Add host tests for root symlink and quota bounds, JVM execution tests for actual broker request predicate if feasible; distinguish host mocks from ART/SAF/device execution.
- Repair test runner floor checks before every write, retain failed commands, keep fixtures inside Workbench02 and remove only compiler scratch it creates. No new dependency/SDK download, APK/signature or production change.
- AC: both exact pending patches present; host store/CAS/restart/rollback/corruption/fault/quota tests pass; Java source compiles against installed Android stubs; unchanged bridge tests pass; old source/candidate/ENDURE identities match. Admission is necessary but not sufficient: no runtime until current Workbench02 UI/source/controller integration is qualified. Do not substitute G17 for the new shell or relax its guards.
- Report limits: host no-op directory-sync callbacks do not prove Android directory fsync, filesystem power-loss guarantees, ART compatibility or SAF behavior. No full-store rollback detection claim from pointer rollback tests alone. Tests contain data only, no authority persistence/restore.
