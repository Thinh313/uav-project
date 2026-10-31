# Blueprint · M0 and target architecture

## Scope/authorization

User instructed starting the project after reviewing the method and selected survey planning. M0 is an isolated local engineering workbench, a reversible first increment. No production platform decision is being inferred from this authorization.

## ADR-001 · Workbench before source access

Decision: use dependency-free browser ES modules for the M0 executable specification, with pure mission/command engines and a local static Node server. This makes fixture-based behavior inspectable without a controller. Historical M0 choice; ADR-008 now selects an independent architecture. Final HeraHub packaging remains a measured hardware/runtime decision.

## ADR-002 · Survey model

Only axis-aligned rectangular surveys in local coordinates, metres, flat ground, ideal nadir camera. Camera fields are synthetic until supplied/calibrated. Footprint width/height = altitude × sensor dimension / focal length. Side/forward spacing = footprint × (1 − overlap). Transects start half a footprint from the edge; use ceil of the remaining width divided by nominal spacing plus one, distributed evenly across the usable span. A narrow site uses one central transect. Shots include both endpoints and are spaced no farther than the nominal trigger distance. Distances include inter-transect connectors. Nominal duration = route distance / speed; turning/climb/wind/launch/return/battery reserve are excluded and visible. No estimation of flight safety or battery feasibility.

## ADR-003 · State and simulation

Core accepts aircraft/session-scoped timestamped telemetry, monotonic local receive times and a bounded freshness window. M0's synthetic sample and ACK use the same local clock; future samples and samples captured before ACK cannot certify execution. Remote clock synchronization/mapping is deferred. Only rehearsal mode change commands are supported. Request→sent→accepted/in-progress→observed execution, or rejected/timed-out. Matching ACK cannot alone assert actual flight-mode change. Wrong aircraft/session and out-of-order telemetry do not update vehicle state. No transport or autonomous AI command generation in M0.

## ADR-004 · Product truth

External facts are sourced claims with exact spans and captures. Internal decisions live in a canonical JSON with explicit owner/status/evidence. A deterministic adapter produces YAML; baseline, provenance guard and digest-bound gate use unchanged transfer kernels. Gate checks integrity, not substantive product truth or authorization to fly.

## Design plan

The M0 visual direction was rejected by the user. UX01 supersedes it: black working stage, white editable inspector, scarce secondary yellow, locally bundled IBM Plex Sans and coherent SVG icons. The local survey canvas remains central; persistent action/validation and explicit command states support the operator. See [UI/UX research](UIUX-RESEARCH.md) and [design contract](UIUX-DESIGN-STANDARD.md) for source applicability, tokens, interaction rules and measured acceptance criteria. Vietnamese UI for project review; localization architecture deferred.

## ADR-005 · Hera controller target

The user identifies Hera as the installation target. Use the supplied HeraHub 2.0 specification as a source-backed model candidate for controller-first landscape UX, with Android 13 as a document claim. Preserve source history without blocking software on brightness; the user treats it as adequate. Discover runtime capabilities instead of fixing budgets from nominal core/storage specs, and separate panel pixels from dp/CSS. Native transport/input/video/lifecycle services and UI must have explicit interfaces; RAGAS is a black-box A/B comparator; native HeraHub services/SDKs are evaluated before packaging. Keyboard focus in the web workbench cannot establish physical RC routing. Do not invent bindings, decoder budgets or a signed APK. Scope and gates: `delivery/TIP-HERA01.md`, `docs/HERA-CONTROLLER-BASELINE.md`.

## Structure

`app/core/mission.mjs`: deterministic validation/planning/package import. `app/core/flight.mjs`: command/telemetry state. `app/app.mjs`: UI, local rehearsal adapter and event log. `app/index.html`/`style.css`: presentation. `tests/`: core regressions and browser scenarios. `tools/server.mjs`: loopback static allowlist. `research/`: primary captures/claims. `sot/`: canonical→adapter→registry→check. `evidence/`: dated execution receipts.

## Target architecture, conditional

Vehicle/autopilot + Ghidorah → versioned vehicle/payload adapters → deterministic flight/mission/media services → Field UI + local data → optional Operations sync. Independent new GCS application source; reuse of RAGAS application source is excluded by the owner. MAVLink and independently inspected open dependencies remain available. Onboard AI inference and UI are distinct subsystems. AI mission assistance produces drafts validated by deterministic logic and operator review.

## Decisions log

D-001: survey priority — user, this chat. D-002: preserve AERIS as working name — maintainer, reversible. D-003: M0 workbench/protocol model — Contractor proposal within kickoff scope. D-004: use transfer v6.3 rather than installed v6.2 quotas/approval keywords — established method from prior turn. D-005: single agent, separate specification/build/verify phases — no authorized delegation; no independent-review claim. D-006: supersplat is not assumed to be GCS source — repository listing does not establish relevance.

D-007: the transfer Refinery CLI's denominator bite assumes a rollup domain. This non-rollup technical reference domain publishes no market distribution/coverage. Preserve the failing full-suite receipt and apply the unchanged individual bites through a project wrapper with denominator marked N/A. Capture/span/tier/determinism and derived-cell/aggregate tamper checks remain mandatory; no source rule is weakened.

## ADR-006 · Version-scoped HeraHub integration research

User confirms HeraLink → HeraHub naming and deprioritizes numeric brightness differences. HERA02 separates Intel and Android generations and manual/release versions. Target Android/ARM64 integration contracts with runtime discovery for input, decoder, link, power and storage; preserve unknown SDK/endpoints and observed state. Existing web app is unchanged; selecting production stack, building APK or wiring transport remains a separate scoped implementation. Reports: `HERAHUB-SOFTWARE-RESEARCH.md`, `HERAHUB-INTEGRATION-BACKLOG.md`.

## ADR-007 · SURVEY01 WGS84 workflow and owned Hera BOM

User authorizes the proposed survey workflow and project SOT with 0.BOM26.xlsx. Implement bounded WGS84/ECEF/ENU polygon design logic, explicit unknown elevation/AGL states, separate draft/library and simulated onboard mission readback, and capability/input seams. No native stack or transport is selected. Keep the legacy rectangle core/tests; v2 package does not silently geolocate v1 or claim QGC parity. Extend the existing SOT with immutable BOM mirror and variant-scoped internal context, not a competing truth store. Runtime installed configuration remains unknown. See SURVEY01-CONTRACT and TIP-SURVEY01.

## ADR-008 · Independent GCS, AI-native development, black-box A/B

Owner explicitly excludes RAGAS application source on 2026-10-12. This supersedes conditional reuse language in ADR-001/005/006 and the old M1-SOURCE prerequisite. RAGAS public documentation/releases are comparator evidence, never the new implementation source. Preserve full flight/mission/payload/media ambition and survey priority.

Build independent deterministic core → versioned vehicle/transport/payload adapters → controller UI/local records, with native HeraHub lifecycle/input/video services through explicit contracts. FLIGHT01 adds a dependency-free bounded MAVLink dialect generated from captured official XML, Node TCP development bridge, compiler and observed command/mission transactions. The transport accepts only a fixed loopback simulator, and HTTP writes require local host, same origin, JSON, current token and session. Android transport/video/input remain future implementations behind the same interfaces; this is not an APK stack selection.

AI-native development: typed/validated module contracts, reproducible simulator scenarios, machine-readable journals and negative tests enable AI-assisted changes with deterministic verification. No cloud AI service, model inference, runtime assistant or autonomous flight-command generator is installed by this increment. Runtime AI proposals must remain drafts accepted through validation/operator authority.

A/B uses version/config-bound missions and task outcomes, identical conditions where supported, and provenance-scoped differences. AERIS measurements never fabricate RAGAS results. See `AB-EVALUATION.md` and `FLIGHT01-CONTRACT.md`.

## ADR-009 · SURVEY02 geographic workflow

Default UI unifies Plan/Fly/Review with actual SITL transport. Independent source-bound OSM vectors/Copernicus DSM and hash-pinned offline assets enter a versioned request envelope; server recompiles trusted data. Explicit virtual simulator altitude policies keep EGM2008 DSM separate from operational launch/geoid claims. Recovery reads the entire actual mission and never restores execution history or sends commands automatically. See SURVEY02-CONTRACT.md and HERAHUB-NATIVE-INTAKE.md. Owner authorized on 2026-10-12.

## ADR-010 · Native read-only diagnostic foundation

HERA03 uses a pure-native Android Java diagnostic module built by existing javac/d8/aapt2 tooling. Public Build/Window/InputDevice/MediaCodecList APIs and SAF are sufficient for an installable diagnostic artifact without proprietary SDK. Versioned source-bound capture/import separates self-reported device evidence, replay and unknown integration fields; no WebView/vehicle transport or production framework decision. Exact device/runtime gates remain open after user confirms no SDK/device connected. See HERA03-NATIVE-CONTRACT and HERA03-DEVICE-RUNBOOK.

## ADR-011 · QGC interchange

Separate exact source intake/export from a strict simulator execution profile; use pinned QGC serializers/fixture as format references. Cached Survey Items are an explicitly reviewed stored-command snapshot, not a polygon regeneration claim. See ADR-011-QGC-INTERCHANGE.md / QGC01-CONTRACT.md. User prioritizes this branch while SDK/controller are absent.

## ADR-016 · BENCH06 mission matrix and A/B preparation

Continue hardware-free roadmap work using a source/runtime-frozen corpus, actual dedicated simulator attempts and a read-only evidence page. Generated polygon cases complement exact pinned QGC lineage; unsafe connectors and unresolved datums remain rejected. Ordered command-mode proof qualifies trial outcomes; independent socket-write capture qualifies negative requests despite bounded journal retention. No comparator/physical/flight authority is inferred from a package. See ADR-016-MISSION-BENCHMARK.md and BENCH06-CONTRACT.md.

RECOVERY07 extends the frozen BENCH06 matrix with controlled loopback packet loss, TCP close, disarmed -w reset/reload and conservative recovered-attempt review. No SDK/device dependency or automatic command/resume. Contract docs/RECOVERY07-CONTRACT.md; ADR-017; dedicated new evidence namespace.

JOURNAL08: durable ArchiveStore I/O, recorder-v3 spool hash checkpoint, reserved capacity, exclusive writer and logical segment lineage. Corrupt original bytes retained; partial/segmented evidence remains UNKNOWN. Inventory paginated without deleting history. Host crash/replay and measured disarmed recording are separate gates. ADR-018 / JOURNAL08-CONTRACT.
