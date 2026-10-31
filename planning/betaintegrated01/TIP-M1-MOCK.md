# TIP-M1-MOCK · Durable run foundation

Outcome: a bounded, mock-verified foundation for a new native-provider beta. This
is the first implementation tranche of M1, not completion of the30min actual
Android–AP requirement. Read M0/DECISIONS.md and the recorder/M1-DESIGN.md.

## Scope and boundaries

Write new source only under `pilot/betaintegrated01/`, `native/betaintegrated01/`
and scoped planning/evidence paths. Original code/candidate/canonical/ENDURE,
previous runs/binaries and source pins remain immutable. Avoid full-project
copies and dynamic execution of old launchers. No SDK install or external API.
No host/AP/Android launch or APK/AP/native-library build in this mock tranche.
Pure-Java unit compilation/execution with the already pinned JDK is permitted as
mock verification only: use the new native component's reusable `.build`, ≤32MiB,
delete task-created class files at completion, no Android API/classes/socket.

## Work packages

1. **Versioned provider descriptor and session lifecycle:** distinguish native
   internalquad regression, external-FDM reference and new candidate. Candidate
   artifact/profile mismatch, null expected hash, foreign endpoint/boot/operator,
   stale input, revoked context and unknown dispatch must fail. Do not strip
   Native98 fences. A fresh session is allowed only after exact closure with no
   restored lease; one-shot Activity logic is not the final policy.
2. **Terminal timing:** separate requested stop, closure start, resources closed
   and durable-review commit. Closed elapsed must remain stable across reads,
   restart and wall-clock changes; late old callbacks cannot affect a new run.
   A timing helper alone cannot label physical state safe.
3. **Segmented durable journal:** bounded records/frame groups, global sequence,
   run/epoch and previous segment binding, exclusive create/seal, file+directory
   synchronization and failure seal. RX→INTENT→fsync→sensor send→SENT/UNKNOWN order
   stays explicit. Segment seal is not session completion. Independent receiver
   must detect missing/reordered/tampered/late-appended segments.
4. **Bounded stage/clock memory:** separate pending from retired/replay state;
   keep exact correlation/timing in streamed records and bounded statistics. Do
   not silently evict evidence, reuse an old clock ID or sample away frame data.
5. **Admission policy:** duration/rate/event/frame/row bounds, exact declared
   sources and capacity. Existing thresholds20GiB entry,10GiB+256MiB floor and
   forecast15s remain; every requested run accounts original/copy/export peaks.
   Conservative bounds and empirical estimates are different inputs. Undefined
   or insufficient bounds refuse actual launch.

## Mandatory mock/fault checks

- Segment rotate at legal boundaries; no frame gap/duplication; global chain and
  context survive rotation. Crash between reserve/append/fsync/send/SENT/seal
  gives the correct durable-prefix/UNKNOWN classification, never synthetic SENT.
- EIO/short write/fsync/directory-sync failure, quota/no-successor, pending seal,
  damaged manifest and foreign run/context preserve evidence and block publish.
- Actual writer order is observed through a fault-injected filesystem/send seam;
  a test mirroring a boolean flag is insufficient.
- Independent cold reader reconstructs complete/partial groups and rejects
  missing/duplicate/symlink/path-traversal/context mismatches. Native-side format
  and AP-stage format stay distinct and are each versioned.
- More than1024 clock exchanges, timeouts, late duplicate/reordered response,
  host/guest wall jump, suspend/stale and boot change: bounded memory, retained
  history, honest uncertainty and no automatic authority restoration.
- Closed time immutable; unknown closure not falsely complete; new session/late
  callbacks/racing revoke and duplicate terminal action are generation-fenced.
- Admission arithmetic overflow/unit mismatch and all duration profiles refuse
  absent capacity; no real disk fill or memory pressure on the user's host.

## Budgets and stop rules

M1-MOCK: one bounded implementation window≤4h, at most3 repair/check cycles per
repro family, ≤256MiB/2,000 files new test outputs,0 AP/Android/APK-or-native-build/sign/install.
Use an exclusive evidence root per check cycle and preserve failures. Unit stress
may use more than1024 tiny events but not millions of filesystem files. No frame
loss, fsync bypass, changed speedup or cap500ms. If disk forecast/floor fails,
stop writes and retain prior outputs; do not ask to delete unrelated data.

After mock foundation passes, a new TIP-M1-BUILD/ACTUAL must bind selected source,
explicit executable/runtime closure, AP instrumentation artifact and Android APK.
Proposed initial actual allocation: ≤4 owned host starts, ≤6 deliberate AP starts,
short smoke first;30min only after capacity and original/copy/export budgets pass.
No automatic retry of a possibly dispatched flight command. Actual WebView/GPU/
codec/AP/profile observations are required before grant. Final release and
long-run policies must be versioned rather than editing old receipts.

M1-MOCK DONE requires Builder source/test/report, independent check of output and
boundary/preservation. M1 itself still needs actual native-authority manual,
assisted, link/reboot and30min frame/clock/runtime proof on the new candidate.
