# Continuation contract for the team's m801 state (team code)

This contract fixes the exact app-data state that a new G1 may start from: the
team's replayed equivalent of the owner's m801 (83 files, 9 directories). It
follows the owner's step 2 in `docs/handoff/NEXT-MILESTONE.md`. **The team decided
(2026-11-06) to keep the owner's strictness but pin the team's own exact values**,
taken from the team's read-only forensic capture `evidence/betarc01/m801` (raw TAR
SHA-256 `85493859…`). This is a team decision, not the owner's.

Passing the contract proves only that a TAR is this state. It grants no archive,
resume, APPLY or authority, and it is not G1, SDK qualification or flight
acceptance. It does not use the post-g103 75-file decoder (`reconcile_h7.reconcile`).

## Files

| File | Purpose |
|---|---|
| `continuation_l10.py` | The contract: `verify(tar, tar_sha, pin, pin_sha)` returns a proof or raises `ContractError` |
| `m801-continuation-pin.json` | The pinned values (SHA-256 `b5318c62…`), written once by `make-continuation-pin.py` |
| `make-continuation-pin.py` | Prepare-only builder. Checks every property below from the team evidence before writing, and refuses to overwrite |
| `verify-continuation.py` | Command-line check of one TAR, prints the proof |
| `test-continuation-l10.py` | Mock tests: positives and the owner's negative cases |

## What `verify` checks

1. The TAR bytes match the given SHA and pass the owner's strict TAR reader (`tar_profile_h7.reader.scan`).
2. Exactly the 92 pinned entries, no more and no fewer. Each has the pinned type, mode, UID, GID, size, SHA-256 and mtime.
3. Content checks that do not rely on the pin:
   - the 83/9 counts;
   - UID/GID 10141 everywhere, with modes 0771/0700/0600;
   - the team's own replay of the registry: row sequence, previous-head chain, row hashes and canonical base64;
   - the 12-row type sequence, lifetime generation count 10, no pending transaction;
   - the 2 new journals: exactly the 23-byte AJ02 header, closed `UNUSED` with 0 records;
   - 1 archive batch with the 8 enrolled journals, each empty, plus its intent/commit records;
   - the request receipt and an empty `guard.lock`.
4. The registry head, row count and counters equal the pin.
5. The registry is append-only. The registry of the 75-file baseline (6 rows, 6,346 B) and the one after g105 native session 1 (9 rows, 7,376 B) are exact byte prefixes.
6. Every baseline file (74 plus the registry prefix, including the workspace) is unchanged in bytes, mode, UID/GID and mtime, and all 9 directories keep mode and owner. The baseline is the harness capture taken before g105 (`a2f09c3c…`).
7. The 6 new status files: 3 per new journal, in observed order, lifetime count 9 and then 10, unused journal, closed and drained only in the last one, same product source, no authority.
8. The owner's own archive/registry checker (`archive_verifier17.verify_archive_index`) runs on the same TAR with the pinned head and must give the same head and counters, 2 active and 8 archived journals, and 0 pending.

## Differences from the owner's m801 (82 of 92 entries are byte-identical)

The builder pairs every one of the 10 non-identical entries with the owner's
counterpart. Any field that is not in one of these named classes stops the build.

| # | Entry | Why it differs |
|---|---|---|
| 1 | `product-input-registry17/highwater.aj17` (same length, 8,409 B; 2,049 bytes differ) | Same 12 row types and field counts. The only differing fields are 20 device/inode numbers of the files, 6 random generation IDs of the 2 new journals, 3 request-nonce fields, 1 per-run request-receipt SHA, and 4 back-references to earlier row hashes. Row 1 is identical. Every row hash from row 2 on differs, because row 2 holds device/inode numbers and each later row covers the previous head |
| 2 | `product-input-lifecycle17/request-<nonce>.json` | Random name. Differing fields: request nonce, PID, process epoch, time, and the registry head of that run |
| 3–4 | `product-input01/<generation>.aj02` (×2) | Random generation names. Bytes are identical (header only) |
| 5–10 | `product-observations01/status-<nonce>.json` (×6) | Random names. Differing fields: status nonce, PID, process epochs, times, view epoch, per-session producer key, journal generation ID, and `inventory.logicalBytes` |

`inventory.logicalBytes` trails the owner's by 0, 1, 2, 3, 4, 5 bytes. That is
exactly the running total of the earlier new status files being 1 byte shorter
(shorter numbers). The 75-file baselines have the same total on both sides
(161,406 B). The builder checks this arithmetic.

## Run

From the tree root (the bind mount):

```bash
python3.14 -B planning/linuxport01/contract-l10/test-continuation-l10.py
```

```bash
python3.14 -B planning/linuxport01/contract-l10/verify-continuation.py --tar TAR --tar-sha SHA --pin-sha b5318c628ae0e1a2638988752baa18b2f3dcad682bb2c649e564dd06ef2c778d
```

Set `OWNER_M801_TAR` and `OWNER_M801_SHA` to also test that the owner's own m801 is refused by the team pin.
