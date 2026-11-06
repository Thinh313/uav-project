# Continuation contract for the state after g106 attempt 1 (team code)

This contract fixes the exact app-data state that the next team G1 may start from: the
87 files and 9 directories that the team's first g106 run left after its first native
session. That run failed afterwards because of a bug in the team's own
`continuation_l11.py` (see `../README.md`); the data itself was conserved.

**Team decision (2026-11-06), not the owner's:** keep that changed state as history and
continue from it, as the owner did after g105 (read-only capture m801, then a
contract). The state was captured read-only as `evidence/betarc01/m802` (second attempt;
the first one ended with an emulator shutdown crash). Both attempts have the same raw TAR,
SHA-256 `76330541…`. The pin holds the team's own exact values from that raw.

Passing the contract proves only that a TAR is this state. It grants no archive, resume,
APPLY or authority, and it is not G1, SDK qualification or flight acceptance. It does not
use the post-g103 75-file decoder (`reconcile_h7.reconcile`).

## Files

| File | Purpose |
|---|---|
| `continuation_l12.py` | The contract: `verify(tar, tar_sha, pin, pin_sha)` returns a proof or raises `ContractError`. It is `contract-l10/continuation_l10.py` with the state shape moved on by one closed, unused native session (see below) |
| `m802-continuation-pin.json` | The pinned values (SHA-256 `4689767d…`), written once by `make-continuation-pin.py` |
| `make-continuation-pin.py` | Prepare-only builder. Checks every property below from team evidence before writing, and refuses to overwrite |
| `verify-continuation.py` | Command-line check of one TAR, prints the proof |
| `test-continuation-l12.py` | Mock tests: positives, the real earlier states and the negative cases |

## Changes from contract-l10

| | contract-l10 (m801) | contract-l12 (m802) |
|---|---|---|
| Files / directories / entries | 83 / 9 / 92 | 87 / 9 / 96 |
| Registry rows | 12 | 15 (one more `GEN_BEGIN`, `GEN_COMMIT`, `CLOSE`) |
| Lifetime generations | 10 | 11 |
| New journals, all empty and closed `UNUSED` | 2 | 3 |
| New status files (3 per new journal, lifetime 9, 10, 11) | 6 | 9 |
| Conserved exactly, including mtime | the 75-file baseline (74 files without the registry) | the whole m801 state (82 files without the registry), which contains that baseline |
| Registry byte prefixes | 75-file baseline, after g105 session 1 | the same two, plus the m801 registry |
| Owner checker must see active / archived journals | 2 / 8 | 3 / 8 |

Everything else is unchanged: the strict TAR reader, the exact pinned index, the team's
own registry replay, one archive batch of the 8 enrolled journals, one request receipt, the
empty `guard.lock`, UID/GID 10141 with modes 0771/0700/0600, the same product source for
all new status files, and the owner's `archive_verifier17` on the same TAR with the
pinned head.

## What the builder checks before writing

1. The m802 capture report matches the TAR, and that capture closed the SDK normally (emulator exit 0).
2. The first m802 attempt has the same TAR bytes.
3. The previous state, the team m801 TAR, is still admitted by contract-l10 with its own pin (`b5318c62…`).
4. All 82 m801 files other than the registry are unchanged in type, mode, UID, GID, mtime, size and SHA-256. The 9 directories keep type, mode and owner; two of them have a new mtime because files were added to them.
5. Exactly 4 entries were added: the third journal and its 3 status files.
6. The entries are identical to g106's own export after its first native session.
7. The registry is append-only: the 6-, 9- and 12-row registries are exact byte prefixes.
8. The 9 status files follow the pattern above, the earlier 6 are grouped exactly as in the m801 pin, and the receiver is the same one the m801 pin names.
9. The owner's checker agrees on head and counters: 3 active and 8 archived journals, 0 pending.

## Run

From the tree root (the bind mount):

```bash
python3.14 -B planning/linuxport01/contract-l12/test-continuation-l12.py
```

```bash
python3.14 -B planning/linuxport01/contract-l12/verify-continuation.py --tar TAR --tar-sha SHA --pin-sha 4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45
```
