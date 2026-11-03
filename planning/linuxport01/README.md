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
- Port done; `test-linuxport01.py` passes 19/19 on Linux (one check is
  skipped where the private authorization record is absent).
- Team QA gate written, scoped as source/mock only (not independent QA).
- Artifact cap raised from 13 to 20 MiB (see below).
- Install and cold-boot entries added (see below); install-stage candidate
  frozen in a separate private work tree.
- **Next blocker:** `root-install-l1.py --inspect` passes every entry check
  but the metadata admission refuses: 73,465,856 B needed vs the H5 cap of
  71,303,168 B (68 MiB). The owner authorized 100 MiB for H10; that is
  pending a decision.

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

The metadata cap stays at 68 MiB (H10's 100 MiB is not applied).
`test-linuxport01.py` checks that the policy differs from H5 only in these
keys and matches H10 minus its metadata increase.

Run the port tests (Python 3.14):

```bash
python3.14 planning/linuxport01/runtime-l1/test-linuxport01.py
```

`test-cap03.py`'s pin check compares against the owner's runtime-h5 record,
so it reports the ported files as different. That is expected.

## Not in this repo

Test evidence, the emulator spec, run logs and the owner's private bundles
are kept in the team's private repository, following the handoff rule that
BOM, customer data and test evidence stay private.

## Next steps

1. Owner confirms the 20 MiB artifact cap for `runtime-l1`, and decides on
   the metadata cap (100 MiB as in H10, or trim H6-H10 records from the
   team tree).
2. `--inspect`, then the real install (`m301`) and cold boot (`m302`).
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
đạt. Đang chờ quyết định trần metadata (thiếu khoảng 2 MiB so với 68 MiB).
Bằng chứng thử nghiệm để trong repo riêng của nhóm.
