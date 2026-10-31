# NATIVE84 — Fly telemetry and Android review history

Status: DONE within scoped validation; see COMPLETION-NATIVE84.html. Dependencies: accepted NATIVE83; no changes to that baseline.

## Scope and acceptance

| REQ | Acceptance |
|---|---|
| R1 | Primary Fly shows observed owned ArduPilot SITL mode, armed state, position, height relative Home, MSL, speed, heading, GPS and Home distance. Never substitute plan/mock values. |
| R2 | Host source age and Android receipt age remain separate clock domains. Duplicate/out-of-order envelopes do not refresh data. Unknown/stale/loss/background remove current marker and current values. No historical selection grants authority. |
| R3 | A north-up local geographic view projects actual WGS84 positions and compiled NAVs around reviewed Home with explicit metre scale. The scene is a schematic, not terrain imagery. |
| R4 | Closure persists a bounded, digest-bound observed track plus session/boot/run/Home/plan lineage in the Android SITL journal. Full raw remains referenced host evidence. No photos inferred. |
| R5 | Review lists a bounded page of committed chain records, selects an exact record token/SHA, distinguishes accepted/aborted, validates history after restart and refuses pending/corrupt/stale-head selection. No automatic deletion or restoration of authority. |
| R6 | Mock/adversarial tests precede Android development APK and actual owned SITL UI mission; primary Fly and history/restart are exercised on Android. Required unrun tests remain NOT_CHECKED. |
| R7 | Protected manifest union including NATIVE83 remains byte-identical before/after; disk stays above 20 GiB; owned runtime and scratch downloads are closed/removed. No production key/signature, HeraHub or ENDURE campaign changes. |

## Design and decisions

Continue the RtR white/graphite/yellow glass system and Barlow medium/semibold typography. Main Fly becomes a calm north-up mission canvas: planned route in muted yellow, observed track white, aircraft heading arrow, Home and metre scale; no invented satellite/video backdrop under geographic telemetry. Glass islands remain centred and 48 px touch targets. Review is a focused glass sheet with list and selected record summary. Engineering controls remain explicit in SITL tools, separate from display-only Fly.

One presentation owner paints the main operational HUD after baseline mock render. Host-monotonic sample ages are measured on the host, receipt staleness on Android/WebView monotonic time; they are never directly subtracted. Presentation freshness is not an authority lease. No autopilot algorithm or mission acceptance gate changes. Track is full within a 1,200-point bound; overflow fails storage/acceptance rather than silently dropping samples. Display envelopes may show a bounded tail explicitly; authoritative closure retains the full bounded track.

Process: existing user request authorizes this isolated development build and emulator/SITL verification. Single agent separates specification, build and verify; no independent QA claim. No new checkpoint needed for already authorized scope. Jev OFF.

## Verification decisions

Final10 only refines disconnected-target display classification; Java Dex/bridge/flight gates and other assets identical09. Full AUTO09 plus targeted Android10 loss/history/app/cold restart accepted; Full AUTO10 explicitly NOT_CHECKED. GPS3D qualification, canonical-key digest with explicit legacy read, and visible scale verified. No camera media inferred. All original raw/failed attempts retained.
