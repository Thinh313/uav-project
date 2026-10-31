# UPDATE17 · staged updates and evidence-preserving layout migration

v1.12.0, host engineering after TRUST16. Single-agent Contractor → Builder → Verify, no independent audit or external release.

| REQ | Acceptance |
|---|---|
| U17-01 | Independent bootstrap pins and signed candidate/current trust bind an explicit digest-confirmed update plan; owner intent only added to SOT |
| U17-02 | Quiescent source stores required, bounded streaming independent copies and observed disk/metadata reserve; no source write, hardlinks or deletion |
| U17-03 | Layout schema1 →2 produces immutable typed catalog/source fingerprints; record/spool/media/receipt/checkpoint/decision schemas and bytes remain original |
| U17-04 | Explicit PLAN→STAGED→VALIDATED→CANARY_PASS→ACTIVATE_INTENT→ACTIVE/ABORTED phases replay under exclusive journal lock; corruption/gaps/unfinished phases never look active |
| U17-05 | Candidate canary uses independent full verification, parent IPC registration, read-only API and healthy idle store/record checks; candidate data/source bytes verified again after stop |
| U17-06 | Activation rechecks source, candidate, signatures, schema and phase before monotonic trust selection; active start/restart verifies current exact selected release and layout digest |
| U17-07 | Pre-selection failures preserve current selection/source and permit explicit abort; post-selection interruption requires exact digest forward reconciliation, no old release fallback |
| U17-08 | Fresh read-only UI/API exposes phase/schema/verification/evidence scope; missing/corrupt/offline clears success; no update or flight mutations in UI |
| U17-09 | Real corpus copy/migration and installed process/restart, failures/SIGKILL/forward recovery, full regression, prior evidence preservation, SOT gate/report/cleanup |

Layout2 is a new data-container schema and provenance catalog, not an in-place conversion of sealed execution-record fields. The catalog records migration-time original bytes; ordinary later append-only revisions are validated by existing stores. It is not a claim that future files equal the original snapshot. Runtime validates layout/catalog identity before writers; activation additionally checks every staged/source byte. Original retained source is the recovery evidence, kept outside the new generation. No automatic prune, migration rollback, runtime AI authority, flight connect or SDK/HeraHub requirement. Host Node/OS/filesystem/clock and external bootstrap/root pins remain trusted; official signer/independent review, hardware counters/secure boot, physical power loss and real target service isolation remain NOT_CHECKED. Update journal is engineering host-local integrity, not authenticated proof against privileged host replacement. Failed canary is not a release selection; once selected, recovery requires the selected healthy candidate or a separately authorized higher-sequence compatible recovery build.
