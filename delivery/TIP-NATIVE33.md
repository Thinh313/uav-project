# NATIVE33 — durable native survey journey

Authorization: user requests survey → preflight → Fly mock → review with persistence/restart on emulator, preserving frozen source/candidate/ENDURE and 20 GiB floor. Prior authorization for a private development APK persists. No software-release signature or device/flight connection.

## Scope / decisions

Reuse NATIVE30's exact pinned survey/compiler and editor codec in a separate `native/journey33`; never run old builders or overwrite old receipts. A single agent switches specification, implementation and verification phases; this is not independent review. Existing architecture is authorized; no additional blueprint approval. Following the user's storage question, continue all small implementation and host checks. Android runtime remains NOT_CHECKED unless the real 28 GiB admission gate passes; never lower the gate using sparse-file estimates.

One workspace journal atomically binds editable draft, current mission/events and bounded previous sessions. Commit each mock action before displaying its saved result. A failed/unknown write blocks further transitions until explicit reload; no automatic retry. Restart retains evidence, converts unfinished sessions to a new appended interruption event, clears compile/preflight and never resumes control. Draft save is explicit; unsaved typing is not falsely acknowledged as saved.

## Requirements and acceptance

- R33-01: four-stage offline native journey, arbitrary bounded polygon compilation exact to pinned core; invalid input revokes gates.
- R33-02: versioned atomic workspace and immutable revisions; every accepted mock transition checkpointed, history retained and no automatic deletion at limits.
- R33-03: force-stop/process restart/reboot restore committed draft/history only; unfinished run explicitly interrupted; fresh compile/preflight required. Host verification is not Android acceptance.
- R33-04: review verifies event semantics, mission/form lineage, monotonic events, chain and ordered landing; ACK never moves the route, synthetic media never becomes physical evidence.
- R33-05: pending/corrupt/stale/quota/write-unknown and background/stale preflight fail closed; no duplicated mock transitions or automatic retry.
- R33-06: development APK has no permissions/network, uses existing dedicated development identity; manifest/assets/DEX/signature checked, old APKs unchanged.
- R33-07: actual installed Android journey, private persistence after force-stop/reboot and ART fault boundaries; requires owned emulator and real disk budget. NOT_CHECKED if admission unavailable.
- R33-08: before/after protected SHA verification; floor20 GiB, guarded small-build budget, cleanup owned build/test scratch, preserve all failure receipts.

Evidence: `evidence/native33`. Completion report records implemented versus accepted REQs separately; NOT_CHECKED is not PASS.
