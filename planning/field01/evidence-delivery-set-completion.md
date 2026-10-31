# FIELD01 product delivery set completion

Implemented new files only for the set exporter, aggregate Python receiver,
documentation and executable checks. Root separately integrated the exporter into
its app/UI. This agent did not create another SITL, media, browser or Android run.

Actual retained delivery: `evidence/field01/delivery-set01`, 4589307 indexed bytes,
index SHA256 `e34da4df45ecb7427d3a3567344e2bdeec060f0024a17e38d765d3869c9c2482`.
The exact GUI-exported accepted raw flight TAR and the two actual retained
synthetic capture TARs are copied immutably without modifying their bytes.

Standalone stateful acceptance:
`evidence/field01/evidence-delivery-set01-receipt.json` reports
`ACCEPTED_DURABLE_DELIVERY`, accepted simulator execution, two synthetic JPEGs,
actualImages zero, no restored authority, and durable journal sequence 1/head
`3dcc1801565fd15bdf3c285ee60164fed6665221964f6fd250d33a3d23ffa9ee`.

Builder checks: **12 pass, 0 fail**, retained at
`evidence/field01/evidence-delivery-set-tests-2026-10-21T12-45-01-016Z/results.json`.
Tests cover actual accepted pair; immutable exact-byte export/no overwrite;
read-only validation with no ledger creation; durable receive and process-restart
replay; wrong mock-flight pair; wrong receiver/sender/index SHA; corrupt, missing,
duplicate and symlinked files; integrity-valid wrong run/boot/model/plan; invented
coordinates and false survey claims; wrong flight manifest SHA; input bounds;
renamed-set replay; corrupt/torn ledger; and retained stale lock.

All validation refusals tested occur before receiver state directory or ledger
creation. The Python aggregate receiver invokes the Node raw flight CLI and
existing Python capture validator read-only, then compares captured context/link
with accepted document/session/review and exact nearest raw host position records.
Only the overall replay receipt is committed after every constituent passes.

The actual RGB/thermal references match raw records 4234 and 5670 within about
30.46 and 33.58 ms. These are retained host reference matches, never physical
exposure accuracy or sensor-clock bounds. Sensor exposure accuracy and sensor
clock uncertainty remain UNKNOWN, survey qualification is false, physical flight
and image authenticity are not proven, and actual physical image count stays zero.

The aggregate exporter/receiver and their new tests share an author. Existing Node
raw decoder/replay and Python capture gate run separately, but this is not an
independent human review or cryptographic producer identity. Deterministic data
integrity work has no LLM runtime baseline; operator advantage remains unmeasured.

No project copy, dependency installation, external scratch directory or Docker
resource was created. Only selected bounded archives and small invalid variants
were copied within owned evidence. Normal receiver locks were released; the stale
lock test fixture and all evidence are intentionally retained. FIELD01 evidence
used about 149 MiB of allocated disk after these checks, below the 512 MiB budget
at that observation.

Slice status: READY for the checked host delivery set and receiver command.
Root-owned UI export and responsive/browser acceptance are separate checks.
Physical camera/GNSS/RF/Android/operational acceptance remains NOT_CHECKED.
