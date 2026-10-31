# COCKPITVIDEO04: integrated host video, mission and payload

Contractor scope, 22 October 2026. Latest user authorizes an isolated native cockpit receiving host video, mock first then Android–SITL with concurrent mission and payload. No HeraHub/SDK, new APK, signing, frozen-source/candidate/ENDURE changes or evidence deletion. Vibecode Kit 6.3 applies with Builder and independent QA.

## Outcome

Use the existing development02 APK unchanged to operate the isolated survey/preflight/Fly/review cockpit while Android only receives/decodes video encoded by a separate laptop browser. Preserve all flight, authority, workspace, journal and provenance fences. Real ArduPilot SITL is a generic internal quad, not a calibrated Hera. Payload control/readback and camera imagery are synthetic; ACK is not an exposure or real device execution.

## Implementation boundary

New `pilot/cockpitvideo04` only. Reuse frozen FIELD02 modules and HOSTVIDEO03 topology. A curated fork of the FIELD02 app, bootstrap, UI and CSS is permitted where necessary for the new media panel and fixed APK origin 8872/8873. Do not edit original modules, old pins or receipts. Stage only the existing curated assets into this module's `.stage`, remove its generated stage after tests. Small exact-byte data-only workspace fork from repair01 is permitted under new evidence, with source manifest. All other writes confined to planning/cockpitvideo04, evidence/field02/cockpitvideo04 and new completion files. Frozen flight runtime may append up to two new SITL records under its existing append-only run directory; explicitly inventory them as new writes, never alter an older run.

The receiver must not load a publisher iframe, instantiate VideoEncoder or invoke local encoding probes. It must retain snapshot/onCapture contract, explicit viewer start/stop, lifecycle stop, fully visible canvas measurement and synthetic/non-radiometric labels. Source controls reside only in laptop browser. Preserve existing clock/profile/queue/credit thresholds and report bytes. Save a separate identity-bound topology/flight overlap sidecar; no rewriting performance reports. Selecting video must not grant payload/flight authority. Flight loss/reboot must invalidate payload rights durably, without automatic regain. Show source/session mismatch and stale video honestly.

## Acceptance

1. Mock: new routing/assets, no Android producer path, correct lifecycle, explicit starts, snapshot handoff; existing authority/mission contract regressions; raw report identity/overlap validation must reject wrong run/config/report SHA and not infer continuous source visibility.
2. Android unchanged APK on owned emulator-5582: cockpit loads, no crash, planning/preflight/Fly/review visible, source encoded on host only, Android receives/decodes. Existing persistence/native journal preserved unless a valid explicit workspace save adds a new record.
3. Real SITL nominal: saved corridor model compiles, preflight, explicit flight grant, upload/readback, Home/altitude validation, arm/AUTO, navigation/RTL/ground-disarm review. While active mission, perform synthetic payload discovery/select/grant, gimbal/readback and fresh decoded-frame capture with source/session/telemetry provenance. Save a measured 30 s video window overlapping flight and payload, ≥24 FPS, calibrated P95 upper ≤300 ms, explicit start→fresh ≤1500 ms. Report exact overlap, no claim that all 30 s are airborne.
4. Separate real SITL fault: observe active unexpired payload lease then explicit owned AP reboot via UI. Verify flight/boot invalidation and durable payload revocation before effect, no automatic regrant after reconnect/restart. Video continuity is independent evidence; do not treat continued pixels as live flight/control. Verify old authority cannot issue a payload command; invalid token/context test is distinct from replay of actual bearer token.
5. Independent raw review, exact baseline SHAs and clean owned process closure/resource guard. Missing required execution yields NOT_CHECKED/NOT READY, not a weakened gate.

## Budget and stop

At most 2 host sessions, 2 emulator cold boots, 2 remaining SITL admission slots (current seven s-prefixed directories; frozen cap nine), 1 nominal + 1 AP-reboot scenario. No automatic campaign retry. Resource admission: 31 one-second samples ≥29 GiB, no >256 MiB decline; runtime early stop <28 GiB or 15 s forecast below20 GiB, poll250 ms. Hard floor20 GiB, keep raw interrupted runs. Maximum20 min per host/emulator session and existing frozen AP540 s budget. New task evidence≤96 MiB plus bounded existing runtime append; keep original aggregate FIELD02 quota. No downloads, installs, SDK changes, full copies or new signatures. Start host producer near actual measurement to avoid wasting frozen128 MiB source-byte quota during AP setup. Source quota failure is preserved and does not authorize silent retry.

## Roles

Builder: implementation and mock tests, no live runtimes/UI/AP commands. Contractor: runtime admission, actual CUA/authorized ADB interactions, raw evidence and preservation. Independent QA: read-only source/evidence review plus separately authored bounded mocks, no live process/flight manipulation. AI-model baseline is not applicable to this deterministic transport integration; compare measured topology with previous HOSTVIDEO03 and retain setup/hardware differences.
