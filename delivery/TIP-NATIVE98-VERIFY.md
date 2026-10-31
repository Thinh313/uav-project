# NATIVE98 verify continuation

19/10/2026. User resumes after freeing storage. SPEC → BUILD → VERIFY by one agent. Scope unchanged: close integrated Android flight/payload acceptance, no hardware or production.

Decision: prior APK02 reproduces opaque JS close before ARM. Build development03 under native/native98verify using same Java package and dev signing key, isolated src/assets, with bounded first-observed JS fault diagnostic from 26-check mock patch. Source/candidate/ENDURE/NATIVE98/previous acceptance bytes frozen. No outcome/root-cause inferred from diagnostic alone.

AC1: source delta and mock/regressions/signature exact, old hashes preserved. AC2: owned emulator-5582 responsive; install exact new APK and old private SHA; read-only Home/GNSS/EKF/prearm. AC3: KML preflight/upload/readback/post-arm Home/AUTO with airborne camera/gimbal then ground/disarm/review, independent raw parser. AC4: separate active-owner/pending capture + link cut; authority revoked/UNKNOWN/no retry, passive AP failsafe/RTL/ground. AC5: restart retains workspace/raw/reviews, restores no control; protected hashes and clean process shutdown.

Floor20GiB, admission26GiB, runtime guard21GiB emulator/20.5GiB AP, speedup1; existing fsync-before-send and freshness unchanged. Reuse AVD/no download/project copy. Existing dev APK/ADB/root authorization on owned emulator only. Preserve all failures.
