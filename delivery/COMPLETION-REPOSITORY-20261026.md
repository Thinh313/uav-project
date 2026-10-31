# Repository consolidation and product assessment

26/10/2026. **Repository maintenance verified; product remains engineering alpha,
integrated beta NOT READY.** This source publication does not certify a flight
release, create an APK/signature or qualify ENDURE.

## What changed

- Added a current status entry at the top of README, preserving historical notes.
  Added `docs/REPOSITORY-GUIDE.md` and the evidence-based product assessment
  `docs/PROJECT-STATUS-2026-10-26.md`.
- Consolidated previously uncommitted native/host/planning/research milestone
  sources and reports. No frozen application/candidate bytes were merged or
  refactored. Milestone namespaces remain explicit rather than being advertised
  as one qualified release.
- Saved9 exact changed source/configuration files from tested isolated
  SIM-STABILITY03 receiver03 in `snapshots/simstability03`, with base/final SHA
  and parent manifest. This makes the corrections reviewable from Git without
  selecting them or copying a whole project.
- Excluded generated `.stage`, engineering ZIP/tar archives, Python tool caches
  and planning logs from future Git additions. Files remain intact on the host,
  including132 protected staging entries. Existing evidence ignore policy and
  signing-material exclusions remain in effect.
- Kept97 existing tracked missing paths unstaged. No missing font, protocol
  definition, evidence image or canonical BOM was restored or committed as an
  intentional deletion. The broader retained baseline has165 preexisting missing
  paths, a different denominator.

## Verification

| Check | Result |
|---|---|
| Original workbench `npm run check` | PASS, syntax only |
| Selected source syntax | 1,990 JS/MJS modules and1,059 Python ASTs: PASS |
| Overlay provenance | 9 files match final source SHA; base checkout SHA also checked |
| Selected-source policy | No staged APK/archive/private-key/cache/runtime/ENDURE path;2 legitimate relative source links checked |
| Secret pattern scan | No findings after checking a false match inside a public web URL; heuristic scan, not security certification |
| Protected legacy | 17,117 identities unchanged;165 preexisting missing remain recorded |
| Previous SIM-STABILITY03 seal | 1,620 entries unchanged |
| New documentation | 28 local links valid; maintenance whitespace check PASS |
| Git deletion scope | 0 staged deletions;97 prior working-tree deletions retained |
| Runtime/hardware | NOT RUN: no Android/SITL/build/SDK/signing in this task |

The first QA pass rejected2 intended relative symlinks and matched `sk-` inside a
public URL word. The checker was corrected to verify contained staged link
targets and token boundaries. The initial FAIL receipt is retained separately;
the source and captured web page were not changed to satisfy it.

Historical captured HTML, exact source overlays and milestone reports retain
their original whitespace. The broad `git diff --check` diagnostics are retained
on the host; no wholesale formatting was applied to hash-bound source/evidence.
Maintenance documents themselves pass the focused whitespace check.

This work used one assistant switching maintenance and verification roles;
no independent human or agent review is claimed. No scratch/project copy,
dependency install or new build cache was created. No files, evidence,
containers or volumes were deleted.

## Product disposition

Read [current assessment](../docs/PROJECT-STATUS-2026-10-26.md). Strong isolated
Android–SITL/manual/AUTO/storage results exist, while release-wide mission plus
video/payload stability, long simulator capture, final fault/reboot, hardware and
real-media qualification remain open. Priority is one reproducible internal-beta
release before expanding feature breadth. No total maturity percentage is claimed.

Detailed host-local QA: `evidence/repository-maintenance-20261026/verification02.json`.
Git commit/remote receipts are recorded after publication in the same host-local
directory. Large archives and raw evidence are intentionally outside this push.
