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
- 8 AJ02 journals created on our AVD with the original development APK.
- Port done; `test-linuxport01.py` passes 11/11 on Linux.
- Team QA gate written, scoped as source/mock only (not independent QA).
- **Blocked:** the candidate freeze preview refuses with
  `CANDIDATE_PREFLIGHT_ARTIFACT13MiB_DISK10GiB`. The existing candidate pool
  is already about 16.2 MB, above the H5 cap of 13 MiB. Awaiting the
  owner's decision: use the 20 MiB cap approved for H10, or port from H10.

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

1. Resolve the artifact cap with the project owner.
2. Freeze the `linuxport01-l1` candidate, then `--inspect` with new slot names.
3. Install/qualification run, then the native migration on our AVD.
4. Compare the resulting state's structure with m801 (83 files, 9 directories).
5. Then the owner's main priority: an end-to-end Android–SITL flow.
6. Remaining known gaps: `test-h5.py` has author-machine paths and inode
   coupling; `_sim32_kernel` (darwin `.so`) and the ARM64 externals are only
   SHA-pinned.

## Tóm tắt (Tiếng Việt)

Nhánh nghiên cứu của nhóm: chuyển harness Root H5 sang Linux x86_64 (chỉ đổi
phần đọc pin/nguồn và dung lượng đĩa của máy chủ), giữ nguyên mọi ngưỡng an
toàn. Test 11/11 đạt. Đang chờ anh quyết định giới hạn artifact 13 MiB trước
khi freeze candidate và chạy lại migration để tái lập trạng thái 83 file.
Bằng chứng thử nghiệm để trong repo riêng của nhóm.
