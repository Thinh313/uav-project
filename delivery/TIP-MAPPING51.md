# TIP MAPPING51 · Mapping Readiness / KML / corridor

15/10/2026, user-authorized isolated mock/replay implementation. One agent specifies, builds and verifies sequentially; no independent review. Existing source/candidate/SOT/trust/ENDURE and completed modules remain frozen. New code only pilot/mapping51, evidence/mapping51, this TIP, ADR064 and completion. Host floor20GiB plus32MiB task budget; no dependency/install/build/SDK/APK/signature/SITL/emulator. Preview8805 and owned store .local/mapping51/operator, never the live49/50 stores.

## Scope and acceptance

- R1: bounded KML2.2 UTF-8 parser, multiple explicit features, Polygon/LineString/MultiGeometry, original source SHA and coordinates/altitudeMode retained. DTD/entity/network/unknown semantic geometry refuse. Holes and non-clamp altitude may be inspected but never silently flattened into a mission. Independent parser negatives and real browser imports.
- R2: explicit selected feature → polygon survey or segment corridor compiler. Camera footprint/GSD/overlap/minimum interval, bounded WGS84 local ENU, original-source/profile/options bindings. Corridor is conservative square-capped per-segment rectangular acquisition cover, with separate strips; transit connectors/turn dynamics/terrain/obstacles/airspace are NOT_CHECKED. No upload/flight command path. Rectangle analytic, axis/rotation/bend/corpus/property checks.
- R3: versioned synthetic camera/GNSS profile and strict mock observation contract. Camera/lens/calibration/shutter/focus/gimbal/storage/test image; separate vehicle navigation and payload RTK or prepared PPK recording. Freshness/session/boot/identity/clock fences. Unknowns block READY_FOR_MOCK. Calibration and test image fixture never become physical proof. RTK loss never silently changes strategy to PPK.
- R4: explicit plan review and typed confirmation bound to current plan/observation/session. Deterministic mock journey and replay distinguish trigger/ACK/exposure/file/quality, no fabricated images or operational acceptance. Stale/loss/reboot stops mock; no automatic resume. Historical/imported records do not restore authority.
- R5: bounded append-only own-root draft/review persistence with SHA chain and source reparse/recompile on cold read/import. Restart disconnects, invalidates all approvals, retains evidence. Corrupt/pending evidence remains blocked, no automatic delete/repair/retry. Owned process restart and storage fault checks.
- R6: usable local operator UI, aligned52px controls, map preview/feature selection/configuration/checklist/mock/review/export/import. Actual Chromium functional and1280/1024/360 QA, negative/stale-response/race checks, no external requests. Fresh operator store empty; mock presets explicit.
- R7: frozen-byte/inventory/pins and source provenance checks, requirement/AC counts, retained failures and honest NOT_CHECKED, owned scratch cleanup and final fingerprints.

## Decisions

KML parsing uses Python standard-library XML with explicit entity/DTD rejection and bounded namespace/schema subset; no new dependency. KML is AOI, not an executable flight mission. Only clampToGround can plan in this phase, at separately specified synthetic-flat AGL. Clamp's source Z is preserved and reported as ignored per KML semantics. Relative/absolute heights and holes require a future reviewed compiler, no guessed conversion. No network resolution or Google basemap.

Reuse frozen survey geometry by read-only import; no source copy or edit. First corridor version favors independent overlapping segment surveys over unvalidated smooth offsets at sharp bends; duplicate images/extra area and disconnected transit are disclosed. Thresholds are versioned engineering mock policy, not survey standards or aircraft defaults.

Design: IBM Plex Sans from frozen local asset; black#080a0c, panel#15191e, white#f5f6f7, secondary#b8c0c8, rule#39424c, yellow#e4c650. Stable left mission inputs, central measured plan view, right readiness; collapses in order on small screens. Plan is the focal element, no marketing hero/cards or decorative motion.
