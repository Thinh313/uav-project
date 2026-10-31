# Survey & Inspection Workbench 01

2026-10-24. Authorized additive host/mock product slice. No frozen source edit, Android, SITL, aircraft transport, SDK, package signing or production release.

## Outcome and design
One application: bounded KML selection → camera/AGL/overlap/heading/speed → compiled polygon/corridor → mock readiness and sortie budget → explicit simulated acquisition → coverage/photo review → refly proposal → integrity-checked workspace export/import. Reuse mapping51 parser/planner/readiness, survey ENU, mission55 area and synthetic camera profile. No copied app or dependency install. New code only pilot/workbench01, planning/workbench01, evidence/workbench01 and dedicated delivery report.

Visual plan: map is primary workspace, compact 56 px header, detached centered left/right glass rails, aligned 24 px outer gutters, bounded inspection panel, bottom telemetry aligned with logo. Black #101719, white #f4f6f5, muted #a9b9b3, yellow #efc54a, error #ffaca4. Barlow existing font, weights 500/600/700. Map is explicit synthetic vector cartography, no claim of satellite/DEM coverage. Glass has contrast-preserving veil; dialogs scroll within viewport; touch controls ≥48 CSS px (native dp NOT CHECKED). No fake video or real-media claim.

## AC
- A1: reuse bounded KML parser, select feature explicitly, compile polygon/corridor; reject self intersection, unsupported holes/altitude/network entities. Preserve units/source/datum. No flattening real terrain.
- A2: editable route, optics/overlap/interval/blur estimates; constant-power synthetic energy budget with explicit Home/wind/payload, leg grouping and reserve; impossible leg is blocked, not silently accepted. Unsupported aircraft calibration UNKNOWN.
- A3: no start before plan-bound synthetic readiness + consent; edit/link loss/restart revoke approval. No command transport.
- A4: planned footprints and sample-based area union; acquired vs quality coverage separated; exposure+pixel hash/identity/time/pose needed; missing/ACK-only/blur/clipped/tilt/stale/wrong binding/replay never pass quality. Cell grid resolution and sampling limitation reported; overlaps do not double-count area.
- A5: missing/rejected cells produce proposal only, separately confirmed; original review retained; no auto flight/resume. Not photogrammetric reconstruction, no claim of RTK/PPK or geodetic accuracy.
- A6: workspace bounded, versioned, SHA-bound; receiver regenerates derived results and verifies per-image synthetic pixels. Tamper/stale binding/unknown schema fail; no restore of authority. Save failure visible, no false persisted success.
- A7: consistent Plan/Preflight/Fly mock/Review cockpit; day/night, keyboard, responsive 1280x800/1366x768/1920x1080 and narrow viewport, dialogs, alignment and no overlap checked using actual browser where possible.
- A8: full protection before/after using G17 referenced 12,925 protected identities, 8,527 history entries and handoff/reuse pins; retain preexisting missing paths outside baseline. ≥20 GiB physical floor; task cap 16 MiB retained (screenshots included). No changes to existing evidence.

## Phases and verification
Contractor TIP → same-agent Builder → separate verification phase (not independent agent review). Analytic fixtures and independent Python brute-grid/area oracle, adversarial Node cases, browser user journey including reload/import and fault scenarios. Runtime AI is absent: direct LLM benchmark not applicable to deterministic surveying; manual spreadsheet/CLI comparator and operator benefit not measured, no superiority claim. READY only host/mock after required AC. Real data/hardware/native gates deferred explicitly.
