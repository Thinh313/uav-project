# Continuation contract for the state after g107 attempt 1 (team code)

This contract fixes the exact app-data state that the next team G1 may start from: the
89 files and 9 directories that the team's g107 run left. g107 failed at the start of its
first native session (the owner's ProductWriter 200 ms limit) after the AERIS app had
started; the app had begun a fourth journal generation, and the run was disposed before that
journal was closed. Old data was conserved.

**Team decision (2026-11-07), not the owner's:** keep that changed state, including the open
journal, as history and continue from it, as after g106 (contract-l12) and as the owner did
after g105. The state was captured read-only as `evidence/betarc01/m803`, attempt 6 (attempts
1–4 ended with the emulator 37.2.12 shutdown crash, −11 or −6, with the same TAR bytes;
attempt 5 failed before the emulator started). All captured attempts have the same raw TAR,
SHA-256 `5ddb603c…`. The pin holds the team's own exact values from that raw.

Passing the contract proves only that a TAR is this state. It grants no archive, resume,
APPLY or authority, and it is not G1, SDK qualification or flight acceptance. It does not
use the post-g103 75-file decoder (`reconcile_h7.reconcile`). It never closes or repairs the
open journal.

## The open journal

`files/product-input01/4ac33ff279f04d33b2e37276e794f780.aj02` (23 B, exactly the AJ02 header,
0 records). The registry has its `GEN_BEGIN` and `GEN_COMMIT` (rows 16, 17) and no `CLOSE`.
There is no pending transaction: the generation is committed, only never closed. The owner's
`archive_verifier17` and the app's `JournalRegistry17` both model it as an `OPEN` member; the
owner's verifier admits the state (4 active, 8 archived, 0 pending) and refuses it only if a
caller requires this generation to be closed. The app's next start inspects it (exact
identity, length, header) and begins a new generation beside it; nothing in the app closes
another generation, and only closed journals can be archived, so it keeps one of the 8
active slots. Its one status file (the STATUS reply of g107 command 23, byte-identical to the
object g107 stored) says lifetime 12, not closed, not configured, no authority.

## Files

| File | Purpose |
|---|---|
| `continuation_l16.py` | The contract: `verify(tar, tar_sha, pin, pin_sha)` returns a proof or raises `ContractError`. It is `contract-l12/continuation_l12.py` with the state shape moved on by the open fourth journal (see below) |
| `m803-continuation-pin.json` | The pinned values (SHA-256 `15039006…`), written once by `make-continuation-pin.py` |
| `make-continuation-pin.py` | Prepare-only builder. Checks every property below from team evidence before writing, and refuses to overwrite |
| `verify-continuation.py` | Command-line check of one TAR, prints the proof |
| `test-continuation-l16.py` | Mock tests: positives, the real earlier states and the negative cases (56) |

## Changes from contract-l12

| | contract-l12 (m802) | contract-l16 (m803) |
|---|---|---|
| Files / directories / entries | 87 / 9 / 96 | 89 / 9 / 98 |
| Registry rows | 15 | 17 (one more `GEN_BEGIN`, `GEN_COMMIT`, no `CLOSE`) |
| Lifetime generations | 11 | 12 |
| New journals (all exactly the AJ02 header) | 3, closed `UNUSED` | 4: 3 closed `UNUSED`, the last committed and open (no `CLOSE` row) |
| New status files | 9 (3 per journal, lifetime 9, 10, 11) | 10 (the same 9, plus 1 for the open journal: lifetime 12, nothing closed) |
| Conserved exactly, including mtime | the whole m801 state (82 files without the registry) | the whole m802 state (86 files without the registry) |
| Registry byte prefixes | 75-file baseline, after g105 session 1, m801 | the same three, plus the m802 registry |
| Owner checker must see active / archived journals | 3 / 8 | 4 / 8 |

Everything else is unchanged: the strict TAR reader, the exact pinned index, the team's
own registry replay, one archive batch of the 8 enrolled journals, one request receipt, the
empty `guard.lock`, UID/GID 10141 with modes 0771/0700/0600, the same product source for
all new status files, and the owner's `archive_verifier17` on the same TAR with the
pinned head.

## What the builder checks before writing

1. The m803 capture report matches the TAR, and that capture closed the SDK normally (emulator exit 0, guardian process exit 0).
2. Attempts 1–4 have the same TAR bytes (emulator −11/−6); attempt 5 has no TAR (failed before the emulator started).
3. The previous state, the team m802 TAR, is still admitted by contract-l12 with its own pin (`4689767d…`).
4. All 86 m802 files other than the registry are unchanged in type, mode, UID, GID, mtime, size and SHA-256. The 9 directories keep type, mode and owner; two of them have a new mtime because files were added to them.
5. Exactly 2 entries were added: the open journal and its status file.
6. The status file is byte-identical to the STATUS reply object g107 attempt 1 stored, and names the open journal.
7. The registry is append-only: the 6-, 9-, 12- and 15-row registries are exact byte prefixes (the first three equal those in the m802 pin).
8. The 10 status files follow the pattern above, the earlier 9 are grouped exactly as in the m802 pin, and the receiver is the same one the m802 pin names.
9. The owner's checker agrees on head and counters: 4 active and 8 archived journals, 0 pending.

## Run

From the tree root (the bind mount):

```bash
python3.14 -B planning/linuxport01/contract-l16/test-continuation-l16.py
```

```bash
python3.14 -B planning/linuxport01/contract-l16/verify-continuation.py --tar TAR --tar-sha SHA --pin-sha 15039006e060302d18acf0f45ce5304bdfb78d6fa1c4b8883f4016ee2f57ac95
```
