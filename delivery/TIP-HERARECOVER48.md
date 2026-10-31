# TIP HERARECOVER48 · pending journal / workspace quota

Authorization: user15/10 requests isolated mock/replay handling of pending journal and quota; no automatic evidence deletion. One agent performs separate specification/build/verify phases; no independent-review claim. No release approval is needed for this already authorized host-only module.

Input: frozen HERAPERSIST47 capsule/JVM journal; immutable actual JVM crash fixtures. Source/candidate/trust/SOT/ENDURE and prior modules remain frozen. The live47 store/preview is not a recovery target.

Design: import a bounded byte-preserving evidence bundle; validate raw journal records, lineage, HEAD/pending and semantic replay. Require an explicit candidate choice plus digest-bound confirmation. Archive every input byte in a new generation before creating a disconnected47 workspace, carrying only an explicitly selected saved draft. Pending intents are never executed. No in-place HEAD promotion, LOCK removal, deletion, retry or automatic active selection. Rotation uses the same explicit procedure and retains all generations. A ready receipt is required before a staged generation can be used; incomplete generations remain quarantined and consume quota.

AC01: strict raw/bundle parsing, SHA/length/name/chain and semantic replay; malformed/tampered inputs fail closed; exportable raw corrupt evidence is not usable as authority.
AC02: pending/orphan/committed cases classified without equating ACK/intent with execution; explicit choice, digest and acknowledgement required; source exact across processing.
AC03: staged generation archives all bytes and plan, creates fresh disconnected mock session and draft, verifies before ready receipt; interruptions at each boundary never publish incomplete generation. Restart validates ready receipt and archive again.
AC04: per-journal16MiB, aggregate64MiB, max4 generations, host20GiB plus reserve; account partial generations/allocated bytes and projected growth; reject quota without deleting evidence. Numeric edge/ENOSPC/EIO tested by injection, no full disk experiment.
AC05: local UI inspect → select → confirm → stage → revalidate after restart, export/import integrity, disabled ambiguous controls,52px actions, responsive1280/1024/360; actual browser/host tests.
AC06: preservation14354 files plus ENDURE inventory, bounded own artifacts, no APK/build/sign/new SITL/emulator; final report with quantitative coverage and limitations.

Boundaries: evidence hashes prove byte integrity against a pinned digest, not producer authentication. A root journal record may already contain history and is labelled an unattested root anchor. No claim of physical MCU flash, power-loss durability, Android support or automatic reclamation. Quota exhaustion requires export/verified off-host retention and a separately authorized cleanup process; this module has no delete endpoint.
