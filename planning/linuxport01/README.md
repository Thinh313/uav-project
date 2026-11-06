# LINUXPORT01: Linux x86_64 port of the H5 Root harness

Team research branch `research/team-work`, based on tag
`research-handoff-2026-11-02-h10`. Nothing outside `planning/linuxport01/` is
changed.

## Goal

Recreate the m801 native-journal state (83 files, 9 directories) on our own
x86_64 Linux PC with an Android emulator, by replaying the migration instead of
copying files. A byte copy cannot work: `JournalRegistry17` checks each
journal's device and inode, so copied files fail with
`ORIGINAL_IDENTITY_CHANGED`.

The owner's Root harness (`planning/betarc01/runtime-h5`) only runs on macOS:
it reads laptop power with `pmset` and per-process disk use with `libproc`.
This folder is a copy of that harness with those two host readings ported to
Linux. "Host" here means the PC running the emulator, not the simulated drone.

## What changed

`runtime-l1/` is a copy of `planning/betarc01/runtime-h5/`
(`source/`, `root-native-h5.py`, `root-positive-h5.py`,
`prepare-source-gate.py`, `test-h5.py`, `test-cap03.py`), plus:

| File | Change |
|---|---|
| `source/aeris_runtime/host_power_platform.py` | New. macOS keeps `pmset -g batt` and the original parse; Linux reads `/sys/class/power_supply` (exactly one Mains `online` and one system Battery `capacity`, otherwise refuse). |
| `source/aeris_runtime/linux_disk11.py` | New. Read-only procfs/statvfs probe for the unchanged `darwin_disk11.HostDiskObserver`. |
| `host_health.py`, `monitor.py`, `power_worker.py` | Call `power_argv()` / `parse_power()` instead of hard-coded `pmset`. |
| `product_runtime.py` | Uses `LinuxProbe` on Linux. |
| `prepare-source-gate.py` | Entries point at `runtime-l1`. |
| `assets/product-input-closure.json`, `assets/pipeline-writer-pins.json` | Regenerated with `prepare-source-gate.py --write`. Writer contract unchanged: 246 sites, 14 owners, 60,686,336 B reserve. |
| `test-linuxport01.py` | New tests for the port. |

Not changed: battery entry 30 % and stop 20 %, disk floor 10 GiB + 256 MiB,
freshness and output limits, the artifact cap, and `darwin_disk11.py`.
`test-linuxport01.py` checks this against the original files.

## Status (2026-11-03)

- Android SDK and AVD set up on Linux x86_64 at the owner's tested versions
  (emulator 37.2.12, platform-tools 37.0.1, API 33 default x86_64 rev 2, KVM).
- The harness only accepts the owner's exact pre-migration app data (70 files
  from his `n02` run, owned by app UID 10141). Our own 8 journals could not be
  used. The owner's n02 data is now loaded on our AVD, and the app was given
  UID 10141 by filling lower UIDs with empty placeholder apps, so no check in
  the code changed.
- Port done; `test-linuxport01.py` passes 20/20 on Linux (one check is
  skipped where the private authorization record is absent).
- Team QA gate written, scoped as source/mock only (not independent QA).
- Artifact cap raised from 13 to 20 MiB and host metadata cap from 68 to
  100 MiB, both as the owner authorized for H10 (see below).
- Install and cold-boot entries added (see below); install-stage candidate
  frozen in a separate private work tree.
- `root-install-l1.py --inspect` for `m301` passes: metadata, artifact and
  disk all admitted. No emulator actor was started.
- **Next:** the real `m301` install run on the team AVD.

## Install and cold-boot entries

The owner ran two candidates: an H4 one for install and cold boot
(`m301`/`m302`) and an H5 one, frozen after `m302` existed, for
`m401`/`m402`/`g103`. The port does the same:

- `prepare-source-gate.py --stage install` pins `root-install-l1.py` and
  `root-qualify-l1.py` plus the team's loaded-state record. The default
  stage is unchanged and pins `m302` evidence, so it runs after `m302`.
- Runs keep the owner's slot names. They happen in a separate private work
  tree without his `m301/m302/m401/m402/g103` folders (and without his later
  H6-H10 slots, which the H5 inventory does not accept), so every slot folder
  there is the team's.

| File | Change |
|---|---|
| `root-qualify-l1.py` | Byte-identical copy of `runtime-h4/root-qualify-h4.py` |
| `root-install-l1.py` | `runtime-h4/root-install-h4.py` plus the 7 patches in `l1_patches.py`: the prior state comes from the team's loaded-n02 record instead of the owner's `m201` repair, and the package is expected healthy instead of broken (`pkg=null`) |
| `source/aeris_runtime/installclosure_h4.py` | One line: `validate_precheck` takes the expected package state from the precheck record; the default stays broken, as in the original |
| `prepare-source-gate.py` | `--stage install` |

The 70-file table, UID 10141, no clear/uninstall/wipe and no Activity/AP
checks are unchanged. Tests re-derive each entry from the original plus the
declared patches.

## Artifact cap: 13 -> 20 MiB (team decision)

The H5 cap of 13 MiB refused the freeze: the existing candidate pool was
already 16,216,064 B. The owner authorized 20 MiB for the isolated H10
runtime:

- `evidence/betarc01/AUTHORIZATION-CAPS03.json` (private record,
  SHA-256 `7fc88c9f…`, `artifactCapBytes: 20971520`)
- [`README.md:83`](../../README.md): "Artifact tổng **20 MiB** … đã được
  chấp thuận cho bản cô lập."
- [`docs/handoff/ARCHITECTURE.md:31`](../../docs/handoff/ARCHITECTURE.md):
  the 20 MiB cap applies to the isolated H10 runtime.

Applying the same value to `runtime-l1` is the team's decision and is
pending the owner's confirmation. It follows exactly how H10 changed the
artifact cap:

| File | Change |
|---|---|
| `candidate.py` | `CAP=20*MIB`, error names `ARTIFACT20MiB…` as in H10, comment citing the sources above |
| `assets/resource-policy.json` | `newIsolatedAPKAndArchiveReserve` 20 MiB for the campaign and all 3 cases; `requiredFreeBytes` and `taskHardPeakBytes` +7,340,032 B each (more disk reserved, not less); amendment block points at `AUTHORIZATION-CAPS03.json` |
| `test-cap03.py` | One line: expects `c.CAP==20*2**20` |

## Host metadata cap: 68 -> 100 MiB (team decision)

The `m301` admission preview refused at 68 MiB: 73,465,856 B needed
(12.8 MB current metadata, mostly the owner's later H6-H10 records, plus the
unchanged 60,686,336 B writer reserve) vs 71,303,168 B. The same owner
authorization (`AUTHORIZATION-CAPS03.json`, `metadataCapBytes: 104857600`)
set 100 MiB for H10. Applied exactly as H10 did:

| File | Change |
|---|---|
| `metadata_budget.py` | `CAP=100*MIB`, comment citing the sources above |
| `pipeline_contract.py` | Authorized cap check `100*2**20` |
| `lifecycle.py` | Error name `GLOBAL_HOST_METADATA100MiB_PROOF_ADMISSION` |
| `assets/resource-policy.json` | Now byte-identical to H10's: metadata 100 MiB for the campaign and all 3 cases, `requiredFreeBytes`/`taskHardPeakBytes` +7 MiB +32 MiB each (more disk reserved) |
| `test-cap03.py` | Two lines: expects `m.CAP==100*2**20` and the 100 MiB error name |

`test-linuxport01.py` checks that the policy equals H10's byte for byte and
differs from H5 only by the two cap increases.

Run the port tests (Python 3.14):

```bash
python3.14 planning/linuxport01/runtime-l1/test-linuxport01.py
```

`test-cap03.py`'s pin check compares against the owner's runtime-h5 record,
so it reports the ported files as different. That is expected.

## runtime-l9: H9 port for the g105 replay

`runtime-l9/` is the owner's `runtime-h9` with the same Linux host fixes as
`runtime-l1`. Only g105 changed the app data after g103, and the H9 chain
anchors directly on g103 (m701 → m702 → g105), so H6–H8 are not ported.

| File | Change |
|---|---|
| `host_health.py`, `monitor.py`, `power_worker.py`, `emulator.py` | Byte-identical to the `runtime-l1` fixes (these files are the same in H5 and H9) |
| `host_power_platform.py`, `linux_disk11.py` | Added, identical to `runtime-l1` |
| `product_runtime.py` | The same Linux disk-probe change as `runtime-l1` |
| `assets/reconcile-g103-originals.json` | Regenerated from the g103 evidence of the tree it runs in (same format and paths; 3 of 8 files are byte-identical to the owner's g103) |
| `assets/product-input-closure.json`, `assets/pipeline-writer-pins.json` | Regenerated; writer contract identical to the owner's H9 (254 sites, 14 owners, 60,686,336 B) |
| `prepare-source-gate.py` | Entries point at `runtime-l9` |

H9 already has the 20 MiB artifact and 100 MiB metadata caps, so no cap
change. `test-linuxport09.py` checks all of the above.

```bash
python3.14 planning/linuxport01/runtime-l9/test-linuxport09.py
```

## runtime-l10: H10 port for the read-only m801 capture

`runtime-l10/` is the owner's `runtime-h10` with the same Linux host fixes as
`runtime-l9`. It is used for the team's own read-only forensic capture
(`root-capture-h10.py --slot m801`) of the replayed state, and later for the
continuation contract and a new G1.

| File | Change |
|---|---|
| `host_health.py`, `monitor.py`, `power_worker.py`, `emulator.py`, `host_power_platform.py`, `linux_disk11.py` | Byte-identical to `runtime-l1`/`runtime-l9` (the first four are unchanged from H9 to H10) |
| `product_runtime.py` | H10 changed this file; the same one-place Linux disk-probe change as `runtime-l9` is applied |
| `assets/reconcile-g103-originals.json` | Byte-identical to `runtime-l9` |
| `assets/product-input-closure.json`, `assets/pipeline-writer-pins.json` | Regenerated; writer contract identical to the owner's H10 (257 sites in the same order, 14 owners, 60,686,336 B) |
| `prepare-source-gate.py` | The three H10 entries point at `runtime-l10`; the H9 maintenance entry stays as in H10 |

The H10 entries (`root-capture-h10.py`, `root-native-h10.py`,
`root-owner-h10.py`) and the new H10 modules (`command_results_h10.py`,
`forensic_h10.py`) are unchanged. `test-linuxport10.py` checks all of the above.

The owner's tests hard-code `/usr/local/bin/node`, and the three
`test-command-*.mjs` helpers import `../command_h10/` relative to their own
folder, so as shipped they do not run from `runtime-l10`. They are left
unchanged.

```bash
python3.14 planning/linuxport01/runtime-l10/test-linuxport10.py
```

## contract-l10: continuation contract for the m801 state (team decision)

`contract-l10/` is new team code for the owner's step 2 in
`docs/handoff/NEXT-MILESTONE.md`. It pins the exact 83-file / 9-directory state a
new G1 may start from. It keeps the owner's strictness but pins the team's own
values, taken from the team's read-only m801 capture. A TAR passes only if:
- all 92 entries match exactly (type, mode, UID/GID, size, SHA-256, mtime);
- content checks pass: registry replay, lifetime generation 10, the two new journals empty and closed, the eight archived journals, append-only registry prefixes, the conserved 75-file baseline including the workspace, and the six new status files;
- the owner's `archive_verifier17` agrees on head and counters.

It grants no authority and is not G1. See `contract-l10/CONTRACT-L10.md`,
including the table of the 10 entries that differ from the owner's m801 (82 of 92
are byte-identical). The pin holds only paths, sizes and SHA-256 values; the raw
data stays in the private repository.

```bash
python3.14 -B planning/linuxport01/contract-l10/test-continuation-l10.py
```

## runtime-l11: G1 from the continuation contract (team decision)

`runtime-l11/` is `runtime-l10` plus the owner's step 3 (a new G1). The owner's
G1 chain is two SDK cold boots of one candidate and then the G1 slot on the same
candidate (H8: m601/m602 then g104; H9: m701/m702 then g105). Those entries admit
the app data with `reconcile_h7.reconcile`, the post-g103 75-file decoder the
owner forbids for the 83-file state. runtime-l11 keeps the same entries and
checks but admits the data with `contract-l10` instead, for new slots only:
`m901`/`m902` (qualification) and `g106` (G1). This is a team decision, not the
owner's. A separate folder keeps `runtime-l10` equal to the m801 candidate.

Every changed file is its original plus the exact replacements in
`l11_patches.py`; `test-linuxport11.py` re-derives each one.

| File | Change |
|---|---|
| `mission16.py`, `rc01.py` | Slots m901, m902, g106; g106 is a `native` case like g105 |
| `product_runtime.py` | `close_maintenance` accepts m901/m902 and checks them with `continuation_l11.verify_sdk` |
| `product_native09.py` | One branch for the new app-record type `nativeLifecycleContinuationL11` |
| `continuation_l11.py` (new) | Team code: qualification-proof check, SDK boot check, G1 start (`resume_continuation`) and cold domain check, each a copy of the owner's with the contract as the data admission. It does not import `reconcile_h7` |
| `root-qualify-l11.py` (new) | Owner `runtime-h9/root-reconcile-h9.py` plus 9 patches |
| `root-native-l11.py` (new) | Owner `root-native-h10.py` plus 4 patches |
| `prepare-source-gate.py` | Entries point at runtime-l11; the two new entries replace `root-native-h10.py` (it only accepts the used slot g105, and the owner's graph allows at most 8 entries); `contract-l10/continuation_l10.py` and its pin are pinned read inputs |
| `assets/product-input-closure.json`, `assets/pipeline-writer-pins.json` | Regenerated. Writer sites 257 -> 261, all four in `continuation_l11.py`; owners, reserve and leaves unchanged |

No cap, guard or other module changes. Nothing here is G1 acceptance.

```bash
python3.14 -B planning/linuxport01/runtime-l11/test-linuxport11.py
```

Known bug (found by the team's first g106 run, fixed in a later folder):
`continuation_l11.resume_continuation` passes the current 83-file capture as
`case['backup17']`, the snapshot whose files `native17.archive_check` requires to be
byte-identical after every stage. The owner's `resume_existing` passes the g103
pre-APPLY original (`adoption17.retained_originals17`). The 83-file capture contains
the append-only registry, so the check refuses the registry's normal growth after the
first native session.

## runtime-l12: capture of the post-g106 state, artifact cap 40 MiB (team decisions)

`runtime-l12/` is `runtime-l11` plus two changes, each declared in `l12_patches.py`
and re-derived by `test-linuxport12.py`:

1. **Slot m802**: a read-only forensic capture of the app state left by the first g106
   run (87 files). This follows the owner's handling of g105: keep the changed state as
   history, capture it, then write a new contract for it. The capture code is unchanged.
2. **Artifact cap 20 -> 40 MiB.** The team researcher authorized this, not the owner
   (private record `evidence/linuxport01/AUTHORIZATION-L12-ARTIFACT40.json`). It is
   needed because the remaining steps take two more candidate freezes and only one fit
   under 20 MiB. The cap is applied the same way the owner's H10 raised it from 13 to
   20 MiB: `candidate.CAP`, the error names, and +20 MiB in the reserve category, hard
   peak and required free disk of every case and the campaign (more disk reserved, not
   less). The owner's amendment block in `resource-policy.json` is unchanged; a team
   block sits next to it. Earlier folders and candidates keep their caps.

| File | Change |
|---|---|
| `mission16.py` | Slot m802 (180 s) |
| `product_runtime.py`, `forensic_h10.py` | The forensic close path accepts m802 as well as m801 |
| `candidate.py`, `assets/resource-policy.json` | Artifact cap 40 MiB, as above |
| `root-capture-l12.py` (new) | Owner `runtime-h10/root-capture-h10.py` plus 7 patches: slot m802, prior slot g106, run `beta-rc01-forensic-capture02`, team prerequisite/intent formats |
| `prepare-source-gate.py` | Entries point at runtime-l12; `root-capture-l12.py` replaces `root-capture-h10.py` (it only accepts the used slot m801) |
| `test-caps03.py` | Owner test copy; only the three cap numbers change |
| `assets/product-input-closure.json`, `assets/pipeline-writer-pins.json` | Regenerated. Writer sites stay 261; the health contract differs only in the cap and the `candidate.py` SHA |

The bug above is not fixed here; runtime-l12 is only for the m802 capture.

```bash
python3.14 -B planning/linuxport01/runtime-l12/test-linuxport12.py
```

## contract-l12: continuation contract for the post-g106 state (team decision)

`contract-l12/` pins the 87-file / 9-directory state left by the team's first g106 run,
taken from the read-only capture m802 (normal SDK close). It is `contract-l10` with the
state shape moved on by one closed, unused native session: 96 entries, 15 registry rows,
lifetime generation 11, 3 new empty journals, 9 new status files. The whole m801 state
except the registry must be unchanged, including mtimes, and the 6-, 9- and 12-row
registries must be exact byte prefixes. The owner's `archive_verifier17` must agree
(3 active, 8 archived, 0 pending). It refuses the m801 state and every earlier one, and
contract-l10 refuses this state. It grants no authority and is not G1. See
`contract-l12/CONTRACT-L12.md`. The pin holds only paths, sizes and SHA-256 values.

```bash
python3.14 -B planning/linuxport01/contract-l12/test-continuation-l12.py
```

## Not in this repo

Test evidence, the emulator spec, run logs and the owner's private bundles
are kept in the team's private repository, following the handoff rule that
BOM, customer data and test evidence stay private.

## Next steps

1. Owner confirms the 20 MiB artifact and 100 MiB metadata caps for
   `runtime-l1`.
2. The real install (`m301`), then a proof file and the cold boot (`m302`).
3. Freeze the default-stage candidate, then `m401`/`m402` and `g103`.
4. Compare the resulting state's structure with m801 (83 files, 9 directories).
5. Then the owner's main priority: an end-to-end Android–SITL flow.
6. Remaining known gaps: `test-h5.py` has author-machine paths and inode
   coupling; `_sim32_kernel` (darwin `.so`) and the ARM64 externals are only
   SHA-pinned.

## Tóm tắt (Tiếng Việt)

Nhánh nghiên cứu của nhóm: chuyển harness Root H5 sang Linux x86_64 (chỉ đổi
phần đọc pin/nguồn và dung lượng đĩa của máy chủ), giữ nguyên mọi ngưỡng an
toàn. Nhóm áp trần artifact 20 MiB anh đã duyệt cho H10 (chờ anh xác nhận cho
`runtime-l1`). Đã nạp dữ liệu n02 của anh vào AVD nhóm với UID 10141, thêm
entry cài đặt/cold boot từ H4, freeze candidate giai đoạn cài đặt, test 19/19
đạt. Áp thêm trần metadata 100 MiB anh đã duyệt cho H10; `--inspect` của m301
đạt. Bước tiếp: chạy cài đặt m301 thật trên AVD nhóm.
Bằng chứng thử nghiệm để trong repo riêng của nhóm.
