# TIP-M0 · Survey planning kickoff and executable specification

Role: Contractor specification; implementation proceeds in Builder phase. Owner: user/AI Officer RtR. Priority: P0. Depends on: supplied paste/methods and confirmed survey preference. Working directory: `aeris/`. Authorization: user requested starting the project; no public release or hardware operations included.

## Outputs

Research captures/claims and baseline findings; project requirements/ADR/risk/roadmap; canonical product truth with SOT adapter; dependency-free local app; deterministic survey and rehearsal command engines; regression tests and browser evidence; completion/verify report.

## AC

- AC-01 / REQ-001: official RAGAS release/org and protocol captures have metadata/hash; claims contain exact spans; capture failures do not become facts.
- AC-02 / REQ-002: canonical confirmed/proposed/unknown truth preserved; adapter and SOT guard/baseline pass; fault injection detects advertised failures.
- AC-03 / REQ-003/004: independently computed survey fixtures, invalid/edge cases and trigger feasibility checks pass; UI reflects model/limits.
- AC-04 / REQ-005: rehearsal mission round-trip preserves semantics; malformed/wrong-version/invalid camera exports rejected.
- AC-05 / REQ-006/007: accepted ACK cannot complete flight-mode change; wrong-target/session/out-of-order data ignored/rejected; stale command and timeout tests pass.
- AC-06 / REQ-008/009: core workflow runs offline, UI no overflow at desktop/tablet/mobile; Inspect shows unavailable media honestly; mission/event export works.
- AC-07 / REQ-010: actual evidence saved and mandatory misses listed. Operational flight remains NOT READY.

Constraints: no RAGAS source copied/invented; no actual UAV command transport; no external UI assets; no guessed specs/model accuracy. Production Flutter/QGC choice deferred. Scope changes recorded in Blueprint/Decisions Log.

Verification: Node built-in tests; rendered browser workflow and fault injection; transfer Refinery/SOT kernels. Single-agent verification, not independent assessment. No pointless documentation-mirroring tests.
