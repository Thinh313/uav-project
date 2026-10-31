# AERIS57 · Integrated engineering simulator

Open http://127.0.0.1:8809/. Source/evidence isolated from the frozen app/candidate/ENDURE. Reuses immutable SIMTRAIN53 backend on8807 and VISUAL56 assets/renderer. No install, APK or new signature.

Start `node pilot/aeris57/server.mjs` from project root only when8809 is free. Existing backend8807 is already running at handoff. If it is stopped, start `node pilot/simtrain53/server.mjs` only after verifying that no other owned run/port is active. Do not start old ENDURE/physics helpers. UI load never launches/arms a vehicle. Fixed loopback backend, no arbitrary endpoint or real radio path.

## Use

1. **Nhiệm vụ:** choose a KML example or upload≤256KiB, inspect, explicitly select a feature and flat-datum assumption, then save/compile. Polygon/corridor metrics use mapping51. The plan remains offline; no upload/AUTO. In QGC subtab compare two files or use the run5 camera-placeholder negative example. The MISSION55 oracle preserves semantic differences/unknowns.
2. **Preflight:** choose reference3kg empty or4kg central/offset, calm/gust(seed32). Open a new explicit SITL session. Wait for EKF/GPS/Home; read configuration again when ready (30s TTL). Cold alignment can take40–50s. Never force arm or bypass failed checks.
3. **Cất cánh & nhận quyền ·5m:** this explicit gesture performs GUIDED climb, observed LOITER and fresh neutral-first input handoff. Keep the Fly tab/window focused. Input W/S,A/D, arrows; mouse controls camera only. Buttons show observed mode/arm/physics; no UI-generated flight path. Current keyboard is an engineering training input, not HeraHub/gamepad acceptance.
4. **LAND:** always in header. Clear local keys/lease before request. Wait for observed ground/disarm, then end. Switching workflow panel or losing focus releases input; reclaim explicitly while airborne armed LOITER. Rights never revive from a later packet or restart. If unclear/stale, do not retry a flight POST; inspect state/logs and use the original backend runbook.
5. **Review:** wait for closure/automatic original-model validator, select the run and read all five raw files to check SHA. RTF whole-run and5s values remain visible, including misses. Hash is not signature/Hera acceptance. Workspace journal export carries no authority.
6. **Năng lực:**17 groups link actual retained reports, source SHA, scope and remaining limits. Native/HeraHub/payload/storage/release modules are not advertised as production integration merely because a report exists.

## Bounds and handoff

Each run≤120sim/150host seconds; LAND well before expiry. Physics1200Hz, speedup1, compensation cap500ms, full WAL frames. Presentation capped60Hz explicitly; it may interpolate/coalesce display snapshots only. Backend enforces≥24GiB fresh start and20GiB floor/headroom,4GiB retained-evidence quota plus1GiB reservation. Workspace≤16MiB/512 append-only records; no auto-delete/prune. Pending/uncertain journal blocks new starts pending review. LAND/release/end may still reach canonical backend if the separate workspace audit is full; audit failure remains visible.

After preview restart, plans/journal survive but live ownership/leases do not. Do not adopt a still-running foreign session silently. Review/close it through its owning backend; no automatic stop/retry. Current handoff has no active AP/controller; only preview servers remain.

Qualification is **PARTIAL**. Two integrated closures have raw/original-model acceptance; two unarmed deadline runs remain failed. Four actual starts are counted from the ledger, correcting the earlier manual count. Pacing is inconsistent and fullG1 remains unaccepted. No AUTO survey, goto/RTL, camera/gimbal/media live integration, Hera calibration, real hardware,18minute rehearsal or projector validation is claimed. Latest camera-framing/checklist display refinements received browser/mock checks, not another coupled SITL run.

See delivery/COMPLETION-AERIS57.md, TIP-AERIS57-UNIFIED-SIMULATOR.md, ADR068 and evidence/aeris57. QA command: `node pilot/aeris57/qa.mjs qaN` with a fresh bounded attempt name; uses mock transport plus real offline libraries, no AP. `verify_live.py` reads only the retained four-run ledger and refuses receipt overwrite.
