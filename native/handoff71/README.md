# HANDOFF71 — closed ROTATE70 generation → unchanged ARCHIVE69

16/10/2026 · [Local UI](http://127.0.0.1:8826/), host/mock only. Source default .local/rotate70/preview01 is read-only. Dedicated receiver .local/archive69/handoff71-preview01 uses original ArchiveManager69 unchanged. Existing preview69/68 and source/candidate/ENDURE are untouched.

From aeris, first creation only: `node native/handoff71/server.mjs --initialize`. Delivered preview already exists; later use `node native/handoff71/server.mjs`. SIGTERM/SIGINT close only the bridge/receiver locks. Never initialize over an existing workspace, delete locks, overwrite receipts or start source RotationManager through this bridge.

Operator flow: select a frozen/nonselected generation with CLEAN_CLOSED closure → export to69 → download data, custody receipt and control proof → explicitly import/check receiver → inspect VERIFIED receipt. Refresh/restart only reads stored records. A verified recheck does not create another import. No cleanup, authority restoration, rotation or operational command endpoint exists here.

Source capture validates identity/source pins/control chain/no pending, FREEZE and full byte/catalog/semantic history. It requires stable control+data before/after capture and refuses active/unknown/uncertain/corrupt/missing/aliased source. It does not open source Store/RotationManager or write a source lock. Current writer data are not copied; only immutable selected closed-generation bytes and bounded control proof are captured. Root/control bytes are internally consistent host observations, not authenticated identity or signed origin.

Bridge phases are exclusive canonical SHA-chained/fsynced START → CAPTURED → ADOPTED → EXPORTED → IMPORTED → VERIFIED. Custody binds source root/generation/FREEZE/control to packageSHA, dedicated69 workspace/generation/export/import and receiver receiptSHA. Package format69 is unchanged; carry proof and custody sidecars with it to retain source lineage. Recipient validation reads saved proof and package, not live source; no grant/token/command is replayed into a live engine. Historical images remain synthetic, actualImages0.

Restart never advances a phase or retries an operation. Explicit resume recognizes committed69 origin/receipts after a lost bridge checkpoint, so it avoids duplicate adopt/export/import. If69 only has BEGIN/partial files, it stays HOLD: unchanged69 has no generic partial-import repair API. Do not bypass with reinitialization, an alternate recipient or deleting evidence. START without complete capture also stays HOLD rather than automatically recapturing a possibly changed source. Finished old proof remains inspectable offline, labeled as saved historical observation.

Quota is32MiB across bridge and dedicated receiver, including hot/export/import/audit/proof, with reserve for the complete planned handoff. Package24MiB/store16MiB/control512KiB/proof1MiB bounds apply; oversized input refuses before new job. Disk floor20GiB+32MiB+reservation is checked before mutations. Full quota blocks; no pruning. No claim that copying within one disk frees storage. No receiver cleanup API is exposed.

Tests with a new run name:

```sh
H71_TEST_RUN=next01 node --test native/handoff71/tests.mjs
H71_CRASH_RUN=next01 node native/handoff71/crash-qa.mjs
H71_CORPUS_RUN=next01 node native/handoff71/corpus-qa.mjs
H71_HTTP_RUN=next01 node native/handoff71/http-qa.mjs
```

HTTP needs8826 free: stop only your managed HANDOFF71 preview first, leave originals and ENDURE running. Fixture roots use evidence/handoff71 plus new evidence/archive69/handoff71 and evidence/rotate70/handoff71 prefixes to respect the unchanged library root allowlists. Small dataset/proof/receiver copies are intentional evidence; no project clone, dependency install or disposable build copy. Task artifact budget48MiB.

`verify-custody.py <job-dir...> --output <new-receipt.json>` is a second Python implementation for canonical/control/custody/package/receiver byte bindings. Borrowed archive69/verify-packages.py also checks package/frame/chain bytes. Neither replaces semantic JS replay, a signature, hardware qualification or an independent auditor.

Limitations: same-host namespace receiver, not independent machine/device. No signed custody/external rollback anchor, production authentication, powercut/F_FULLFSYNC/Android/HeraHub or long-term retention/latency qualification. No SDK/APK/build/SITL/emulator/signature, source migration, Fly integration or ENDURE acceptance is implied.
