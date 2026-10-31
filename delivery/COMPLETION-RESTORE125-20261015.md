# RESTORE125 · Exact-byte recovery completion

15/10/2026 · **DONE / PASS_EXACT_BYTE_RECOVERY**. One agent specified, restored and separately verified sequentially; no independent human review claimed.

Recovered all **125/125** authorized missing paths using existing SHA-matching copies already inside this project. Total logical bytes copied: **67,149,802** (about 64.04 MiB). The 125 paths represent 84 unique original SHA-256 values. No screenshot, archive, binary or signature was regenerated or downloaded. Existing destinations were not overwritten.

The restored set includes the font and slot replicas, seven original signed software package replicas, historical screenshots/logs, protocol XML, preflight definitions, the previously built instrumented ArduPilot binary, and retained workspace archives/data. Recovering a binary does not execute it; recovering an archive does not run an import or restore operational authority.

## Requirement and verification results

| Requirement | Result |
|---|---|
| R125-01 exact scope/source bytes | PASS: authorized 125-path set, 84 SHA identities; all sources checked before copying |
| R125-02 admission/preservation | PASS: only the known 125 paths missing, no unexpected changed/new missing paths; source/destination and symlink/no-overwrite guards checked |
| R125-03 durable recovery | PASS: bounded exclusive staging, SHA verified before atomic no-overwrite publication, file/directory fsync, permission bits copied; 125 intents and 125 matching completion records |
| R125-04 separate integrity check | PASS: 24,499/24,499 protected paths match expected SHA; zero missing/changed/not-checked; 5,051 current ENDURE files match their pre-recovery snapshot |
| R125-05 resources/cleanup | PASS at observed checks: remaining space above 20 GiB, exact recovery budget plus 32 MiB evidence reserve admitted; owned staging directory absent |

5/5 recovery requirements met. Verification checks byte integrity, source equality, length, permissions, link count, event destination sets and inventory preservation; it is not a runtime or flight test. No build, dependency install, Docker/SITL/emulator/soak launch, software signing or physical flight occurred. No prior evidence or user data was deleted. Only task-owned unpublished staging aliases and their empty directory were removed.

## Incident/history retained

Original CYBER64 missing-path incidents, planning verification and failed preservation receipts remain byte-identical. They correctly describe the earlier absence and were not rewritten to PASS. New recovery evidence records the later repair. No ENDURE history, failed run, continuous-24h verdict, trust/signature event or canonical SOT was edited. Newly restored files have new filesystem inode/timestamps; original historical content remains exact.

Cause of disappearance remains **UNKNOWN**. Successful endpoint recovery does not establish continuous original-path presence, current software-signature trust acceptance, functional readiness or 24-hour ENDURE acceptance. Existing AUTO63 and hardware gaps retain their previous status.

## Reproduction/evidence

Read [verification](../evidence/restore125-20261015/verification.json), [restoration receipt](../evidence/restore125-20261015/restoration.json), [copy provenance](../evidence/restore125-20261015/candidate-search01.json), admission/baseline, per-file `restore-events.jsonl` and final artifact fingerprints. The guarded restore script refuses an automatic rerun; do not rerun recovery to overwrite evidence. All validation receipts are new files under `evidence/restore125-20261015`.

The original incident remains at [CYBER64 incident](../evidence/cyber64/preservation-incident.json). This completion is the subsequent resolution record; no historical document needs rewriting.
