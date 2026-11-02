# JournalRegistry17 API handshake

Only Registry Builder edits `native/nativejournal17/src/vn/rtr/aeris/mission/JournalRegistry17.java` and its own JVM tests under `planning/nativejournal17/registry-tests`. Main Builder owns Guard, existing Lifecycle, receiver, InputJournal and host receiver.

Public dependencies already owned by main Builder: `JournalLifecycle17.Sync.directory(File)`, `JournalLifecycle17.Fault.at(String)`, `JournalGuard17.Boundary` (`fact`, `read`, `readRange`, `capacity`), `JournalGuard17.require(File)`. Boundary Fact has device/inode/links/regular/directory. All Registry public methods require caller holds the SAME root Guard across caller mutation and registry commit. Guard is a cross-process FileLock with 100ms acquisition limit. Do not acquire a separate lock inside Registry.

Registry path: `files/product-input-registry17/highwater.aj17`, append-only, at most8MiB, also counted inside original combined64MiB input/archive/control cap. No unlink, overwrite, reset or missing-index-as-fresh. Exclusive init only by explicit administrative cold enrollment. Each record bounded4KiB with strict sequence/hash chain and durable file+parent fsync. Partial/uncertain record poisons further writes; recovery may refuse honestly. Do not scan/hash64MiB archives on every input.

Suggested public API (return types immutable nested public structs; no private caller-class dependencies):

```java
JournalRegistry17(File files, JournalLifecycle17.Sync sync,
                  JournalLifecycle17.Fault fault, JournalGuard17.Boundary boundary)
static final class Original {
  public Original(String generation,long bytes,String sha256,String disposition,String proofSHA256)
}
static final class Snapshot {
  public final String head;
  public final long reservedGenerations, committedGenerations,
                    reservedRecords, committedRecords;
  public final boolean pending;
}
static final class Ticket { /* immutable token bound to exact root/head/intent */ }
Snapshot inspect(String expectedHostHead, boolean allowPending);
// expectedHostHead null => local integrity only, never claim external antirollback.
// expectedHostHead ROOT => only never-enrolled, no archive/previous registry footprints.
// explicit actual head => must exist in/anchor current valid descendant history.
Snapshot enroll(List<Original> observedOriginals,String backupSHA256,
                String receiverSHA256,String coldProofSHA256,String expectedHostHead);
Ticket beginGeneration(String generation);
void commitGeneration(Ticket ticket,long bytes,String aj02Head);
Ticket beginAppend(String generation,long nextSequence,long beforeBytes,
                   long afterBytes,String rowSHA256,String nextAJ02Head);
void commitAppend(Ticket ticket);
void closeGeneration(String generation,long sequence,long bytes,String aj02Head,
                     boolean durablyClosed,boolean unresolved);
Ticket beginArchive(String planSHA256,String expectedHostHead,List<Original> originals);
void commitArchive(Ticket ticket,String relativeArchiveDirectory);
```

Initial enrollment uses all eight exact old originals from independently verified cold backup. Header-only receives UNUSED, never closed-input credit. Nonempty requires CLOSED_VERIFIED external original-observation/crypto proof. Any unresolved/torn/unknown journal blocks rotation. Missing/mutated member, missing batch, wrong/rolledback index/host head must refuse. Index tracks every enrolled/new generation, append highwater and committed archive location independently of batch manifests. Counter rollback/refund prohibited: begin intent durably reserves generation/record credits, commit separately records actual completed effect. Original header-only journals have zero records. Reserved unknown credits remain charged after faults.

Caller writes AJ02 bytes+fsync between append begin/commit under the same Guard; finish must verify corresponding original tail using Boundary.readRange (not reread all archives). Registry must join stored byte length/head and member identities on cold inspect, reject truncated active originals or removed whole archives. Archive begin/commit binds full per-member original metadata into ledger outside batch tree. During explicit pending archive recovery, exactly one original old/new location is allowed; no ordinary input while pending. Commit can be idempotently observed, but uncertain intent is never automatically replayed.

Original native/global counters/quotas remain. External complete filesystem rollback cannot be detected natively without Root-known cold/head anchor; report that trust boundary honestly. Fault-test whole-batch removal, index deletion/rollback, hardlinks, pending writes, cross-instance interleaving under caller Guard. No actors/APK/signing in Registry tests.
