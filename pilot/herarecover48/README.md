# HERARECOVER48 · journal recovery and retained workspace quota

Isolated successor/companion to47. Start from project root: `node pilot/herarecover48/server.mjs`, localhost8802. Persistent staging root `.local/herarecover48/operator`. No build/install/sign/APK/SDK/SITL/emulator. Existing44 host JVM JAR and immutable45/46/47 models are reused. Existing47 preview/store on8801 and46 on8800 remain separate.

## Operator flow

1. Load one of three static, real host-JVM crash fixtures from47 or import a bounded48 evidence bundle. Optional expectedSHA should come from a separate trusted source; without it the check proves self-consistency only. No arbitrary filesystem import API or active47 journal snapshot is exposed.
2. Inspect HEAD/HEAD.pending/unpublished record classifications. HEAD publication is not proof that the caller received an acknowledgement. Choose a candidate explicitly; no default choice. Every raw record is SHA/length/header/name checked, every capsule replayed and adjacent transitions checked. A root anchor is labelled unauthenticated; source producer authentication is not provided by unkeyed hashes.
3. Review plan and check the explicit retention acknowledgement. Staging saves all source bytes in archive.json, plan.json, then uses47 intent/result commits to save only the selected historical draft in a new disconnected mock journal. If no draft exists, use default synthetic config. Old calibration, mapping-apply/save authority, telemetry and pending intent are not executed or hydrated as live control state. The synthetic peer stored config is default, not restored from old apply/save state.
4. The archive/plan/journal are read back before ready.json is issued. The PENDING directory is atomically renamed to a generation UUID. Only the final named generation with a fully verified receipt is READY_STAGED_NOT_ACTIVE. No automatic selection of this journal in47/native/Fly occurs. Inspection creates a fresh disconnected in-memory session every time, without appending to the stored seed.
5. Restart server and click **Kiểm hồ sơ** to revalidate archive, plan, seed inventory, head and draft. Export the source bundle and verify at the receiving side. A download alone is not evidence of off-host retention.

## Quota and faults

16MiB per source journal,514 entries maximum,256KiB capsule;24MiB encoded bundle;64MiB aggregate staging allocation;4 retained generations maximum. Aggregate counts all files/directories and incomplete generations. Before stage reserve the projected archive/journal growth plus16MiB; maintain host20GiB free floor. Check before file publications, retain errors without success receipts. All numbers are bytes, UI MiB/GiB.

When full: refuse new generations, export/verify evidence and arrange separately authorized retention/cleanup. Rotation means another retained generation, not compaction. This module has no delete API, cleanup scheduler, HEAD promotion, LOCK removal or automatic retry. A PENDING generation after a crash blocks further stage operations; it must be retained and reviewed in a later explicit recovery procedure. Do not delete/rename it to bypass admission. Existing47 mutation quota and epoch limits remain unchanged. Ready seeds are immutable for48 verification; later actual use/migration requires an explicit handover, not pointing47 at the seed silently.

Writes are serialized within the owner process and the atomic PENDING-directory creation excludes a second stage. Source capture compares two read-only inventories; it is not an OS writer lease. Only offline exports/static fixtures are supported. Do not externally modify the staging root or run another owner against it. Filesystem adversaries and real host power-loss behavior are outside this host/mock acceptance.

## Evidence

Final host suite72, parser/quota corpus24, actual owned process SIGKILL10, browser final30 checks including actual server restart, lost response, import digest checks and3 screen widths. Earlier failed runs retained: incorrect test assumption about fresh RAMsession, catalog error-name shadowing (fixed), missing frozen dependency and sandbox localhost denial. See Completion report for final receipt IDs, exact totals and preservation results.

An external missing-path incident53files was detected during this task; all were restored from protected exact-SHA copies with explicit user permission. The incident/receipts are retained. No claim that original paths were continuously present, no rewrite of ENDURE history or new24h acceptance.
