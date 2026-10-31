# Product requirements · v0.3

Owner: chủ việc, phụ trách AI RtR. Maintainer: Codex. Date: 12/10/2026.

## Confirmed intent

Build a comprehensive drone software product, improve feature quality/performance/UI/UX to commercial competitiveness with DJI. The first workflow, selected in this chat, is **survey and mission planning**. Use an independent new architecture without RAGAS application source; use public RtR documentation for black-box comparison. These are requirements, not proof of product capability.

Installation target clarified by user: **Hera handheld controller**. Supplied specification set identifies HeraHub 2.0 as the GCS candidate with Android 13 and a nominal 1280×800 panel. See [HERA-CONTROLLER-BASELINE.md](HERA-CONTROLLER-BASELINE.md) for source claims, conflicts and HERA-01–06. Exact hardware revision/density/input transport remain unknown; browser review is not an Android installation.

## M0 acceptance matrix

| ID | Requirement | Acceptance/evidence |
|---|---|---|
| REQ-001 | Reproducible evidence baseline | Official source files, capture metadata/hash, claims→span→snapshot; latest release verified by API response. |
| REQ-002 | Internal truth preserves status | User-selected workflow stays confirmed; architecture/budgets/unknowns retain proposal/claim labels; source drift and exposed claim caught. |
| REQ-003 | Survey geometry engine | Rectangle in local metres; serpentine transects cover the rectangle under the documented footprint model; area/spacing/distance/nominal time/photo count tested against hand-derived cases. |
| REQ-004 | Camera feasibility | Camera dimensions/overlap/altitude/speed validated; insufficient shooting interval visibly blocks export/rehearsal. No fabricated camera spec. |
| REQ-005 | Semantic mission round-trip | Versioned rehearsal-only package validated on import; repeated generate/export/import preserves inputs and deterministic results. No `.plan` compatibility claim. |
| REQ-006 | Honest command lifecycle | Target/session and fresh telemetry checked; ACK does not complete a mode-changing command; independent telemetry reconciliation, rejection and timeout exercised. |
| REQ-007 | Data freshness and fault rehearsal | Pause telemetry, lose video independently, reject command and timeout; stale readings marked and new commands gated. |
| REQ-008 | Usable local workspace | Plan/Fly/Inspect/Review, keyboard access, desktop/tablet/mobile layout; no external assets or network dependency for core workflow. |
| REQ-009 | Evidence export | Rehearsal event log includes timestamps, sequence, aircraft/session and command stages; exported file identifies simulation. |
| REQ-010 | Traceable handoff | TIP, implementation files, actual test outputs, completion report, missing inputs and explicit NOT READY for operational flight. |

## Next integration requirements (not implemented in M0)

REQ-101: independent architecture and measured HeraHub/vehicle compatibility matrix; RAGAS black-box A/B baseline. REQ-102: WGS84 projection, polygon/concave handling and vertical datum/DEM coverage. REQ-103: QGC `.plan` semantic round-trip using versioned fixtures. REQ-104: MAVLink mission transaction/camera commands against ArduPilot SITL. REQ-105: certified controller/video/RTK/payload integration with HIL. REQ-106: operator usability/performance benchmarks. REQ-107: signed releases/SBOM/migration/rollback. REQ-108: controlled flight acceptance. Each will need scoped TIPs and evidence.

No target performance, timeline or budget from the pasted proposal is a measured result or committed constraint. Configure performance budgets after hardware baseline.

## SURVEY01 delta · 0.3

AC-G1 implements bounded WGS84/ENU polygon design, clipping/concavity, ideal camera/GSD/overlap/heading and honest altitude prerequisites. REQ-102 remains partial: DEM/geoid/operational altitude checks are not implemented. AC-U1 adds touch/coordinate editing, named local library and v2 round-trip. Unlike M0, structurally valid drafts with missing terrain/camera readiness may be saved/exported locally; they cannot enter simulated upload. AC-I1 adds package SHA-256 identity, separate ACK/readback and mission progress/persistence in a local rehearsal session; REQ-104 remains not integrated with MAVLink/SITL. Native Hera capability/input adapters are contracts/replay seams, not installed hardware. AC-B1/AC-S1 add BOM source/variant provenance and owned project SOT. Exact acceptance and evidence: SURVEY01-CONTRACT and COMPLETION-SURVEY01.

## FLIGHT01 / owner architecture correction

REQ-109: independent new application source, no RAGAS source reuse. REQ-110: reproducible A/B scenario/config/build records; missing comparator runs stay NOT_CHECKED. REQ-111: AI-native development through inspectable contracts and executable evaluations, without conflating development AI with autonomous vehicle authority. REQ-104 gains a real loopback ArduPilot SITL slice; remaining M2/hardware/field gates stay open. See TIP-FLIGHT01 AC-01–10.

SURVEY02 v0.5: unified real-SITL Plan/Fly/Review, source-bound offline vector/DSM bundle, explicit virtual altitude mapping and read-only full-mission recovery. See SURVEY02-CONTRACT.md for limits. No native/HIL/operational flight acceptance implied.

HERA03 v0.6: installable read-only diagnostic APK, bounded native input/lifecycle model, local SAF export and strict unattested report intake. Native execution/HeraHub integration remains NOT_CHECKED without an observed device. See HERA03-NATIVE-CONTRACT.md.

REQ-QGC01: Interoperate with source-bound QGC mission plans without requiring HeraHub SDK or reusing RAGAS source. Bounded acceptance: exact original import/export, current/legacy SimpleItems, cached Survey snapshot, explicit supported-profile reasons, standard survey export and simulator-only envelope. Verification: TIP-QGC01 AC01–08 / QGC01-CONTRACT / evidence/qgc01. Universal QGC/regeneration/application parity and field flight are separate gates, not implied by this increment.

REQ-QGC02: verify actual QGC desktop serialization with source hashes and semantic differences, and independently demonstrate in-flight GCS failsafe versus telemetry-only loss in SITL. Acceptance TIP-QGC02 AC01–08. Compatibility differences are explicit OPEN issues, not failed evidence collection; no silent Home/camera rewrite. Source-bound operator review after interruption is separate from read-only recovery and never implicitly sends AUTO. Hardware/field gates remain separate.

REQ-QGC03: create a hash-bound reviewed camera/Home/height derivative while preserving raw source; expose all camera/height/sequence changes; actual QGC roundtrip and SITL evidence required. Unsupported frame/datum/fence/jump behavior must fail. References TIP-QGC03/ADR013/QGC03 contract; scope simulation only.
