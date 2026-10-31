# RESTORE41 — completion and verification

14/10/2026. Status: **DONE — EXACT_BYTE_RESTORATION_VERIFIED**, limited to exact-byte repair and current integrity. One agent restored files, then a separate read-only Python process verified the results; this is not independent review.

## Result

Restored all 41 missing destinations from already present copies whose SHA-256 was freshly checked against the original historical fingerprints. Total restored: 47,293,009 bytes (45.1 MiB). Every destination has the exact original SHA and expected byte count. No existing destination was overwritten. No APK build, SITL/emulator launch, new signature, trust selection, campaign restart or canonical SOT edit occurred.

| Requirement | Result | Evidence |
|---|---|---|
| AC-01: 41 exact original SHA files; sources unchanged | PASS — 41/41 | preflight.json, operations.jsonl, restoration.json, verification.json |
| AC-02: all historical protected files and previously present guards intact | PASS — 9,365/9,365 historical SHA; 13,463/13,463 total guards | verification.json |
| AC-03: preserve incident/history and record distinct restoration event | PASS — original APFLIGHT36 receipts unchanged; 41 intent/completion pairs and terminal journal event | operations.jsonl and input fingerprints |
| AC-04: disk floor, restricted operations, temporary-file cleanup | PASS — zero builds/runtime launches/signatures; all 41 staging names removed | restoration.json, verification.json |

Verification has 8/8 checks passing, zero missing files or SHA mismatches in the inventoried scope. The only before/after state changes are the 41 authorized paths going from missing to their exact original SHA. The current ENDURE inventory contains 5,051 files; its paths and byte fingerprints were unchanged across this repair. Historical protected files and final APFLIGHT36 source/evidence manifests also match. This is byte-integrity verification, not a new software signature or a runtime/flight test.

Available disk space at verification: 24,453,120,000 bytes, approximately 22.77 GiB. Admission checked the full 45.1 MiB copy budget plus receipt headroom against the 20 GiB floor; all recorded write checkpoints stayed above the floor. No dependencies or project copies were created. The only temporary files were 41 destination-local names ending `.restore41-20261014.partial`; all were removed. Their exact names are listed in restoration.json. No other data was deleted.

## Provenance and preserved history

The original incident at `evidence/apflight36/preexisting-preservation-incident.json`, candidate map and prior before/after/verification receipts remain byte-identical. Their historical MISSING/FAIL conclusions remain valid for their observation times; they were not rewritten to PASS. This report and `evidence/restore41-20261014` are a later repair event.

The reason for the original loss remains UNKNOWN. Current file presence does not establish continuous presence of the original paths. Screenshots, logs, packages and the ArduPilot binary were copied from SHA-identical existing artifacts; this does not represent a new screenshot capture, build, execution, flight or measurement. Source POSIX modes were copied, including the recovered binary's mode. Original file timestamps/permissions were not available and are not asserted to be restored.

The first read-only admission invocation stopped on an intentional protected-inventory symlink (`pilot/sim32-pacing02/clock_host.py`); no protected writes or restoration occurred then. The guard was narrowed to allow existing within-project symlink reads while retaining strict no-symlink checks on every restoration source/destination. `admission-attempt01.json` preserves that event. Subsequent admission required exactly the known 41 missing files and no additional protected drift before any copy.

## Artifact locations

- Scope/authorization: `delivery/TIP-RESTORE41-20261014.md`.
- Fresh original SHA comparison, observed pre-state, exact source/destination plan and disk admission: `evidence/restore41-20261014/preflight.json`.
- Append-only fsynced intent/completion log: `evidence/restore41-20261014/operations.jsonl`.
- Restoration details and cleanup names: `evidence/restore41-20261014/restoration.json`.
- Separate verification process, results and input fingerprints: `evidence/restore41-20261014/verification.json`.
- Task artifact SHA inventory: `evidence/restore41-20261014/artifact-fingerprints.json`.

The current inventoried byte-integrity gap is closed. ENDURE history and its previous acceptance/failure verdict are unchanged; no elapsed intervals are combined and no 24-hour acceptance is claimed. Actual Android, ArduPilot/SITL, Hera device, flight and new release acceptance are NOT_CHECKED in this task, as requested.
