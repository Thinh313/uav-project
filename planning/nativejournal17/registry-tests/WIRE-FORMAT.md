# Registry17 wire format (Builder contract, not independent acceptance)

Path `files/product-input-registry17/highwater.aj17`, outside every archive batch. Maximum 8 MiB including magic. Every append is a single record <=4096 bytes, file fsync, then registry-directory fsync. Uncertain/torn records are retained and block further writes. All operations require the same caller-held root Guard.

Magic exact ASCII: `AERIS_JOURNAL_REGISTRY17_V1\n`.

Each ASCII row: `sequence\tpreviousSHA256\ttype\tcanonicalBase64Payload\trowSHA256\n`.

Sequence starts 1, previous SHA starts 64 zeroes. `rowSHA256 = SHA256(ASCII(sequence + "\t" + previousSHA256 + "\t" + type + "\t" + canonicalBase64Payload))`; newline and final tab/hash are excluded. Payload is tab-separated ASCII fields, encoded with standard padded canonical Base64. Integers are canonical nonnegative decimal (`0` or nonzero digit followed by digits), <= signed long maximum. No carriage return, duplicate fields, trailing bytes, alternate encoding or partial final line is accepted. Record types and exact payload fields follow.

`Original` tuple is five fields: generation32hex, originalBytes, wholeOriginalSHA256, disposition (UNUSED or CLOSED_VERIFIED), externalProofSHA256. An originals group is count1..8 followed by that many tuples in the exact recorded order.

| Type | Payload |
|---|---|
| ENROLL_BEGIN | backupSHA, receiverSHA, coldProofSHA, originalsGroup (exact eight UNUSED magic-only originals) |
| ENROLL_COMMIT | enrollmentIntentRowSHA, then exactly eight triplets generation, originalDevice, originalInode |
| REQUEST_RESERVE | nonce32hex, operation(PREVIEW/APPLY/RECOVER), implicitFirstCreditBit(0/1) |
| REQUEST_RECEIPT | reservationRowSHA, nonce, relativeReceiptPath, originalReceiptBytes, originalReceiptSHA256 |
| GEN_BEGIN | generation |
| GEN_COMMIT | intentRowSHA, generation, bytes(exact23), AJ02head(zero64), device, inode |
| APPEND_BEGIN | generation, nextAJ02sequence, beforeBytes, afterBytes, wholeNewRowSHA256, nextAJ02bodySHA256 |
| APPEND_COMMIT | intentRowSHA, actualElapsedNs, pendingOutcomeBit(0/1) |
| CLOSE | generation, sequence, bytes, AJ02head, disposition(UNUSED/CLOSED_VERIFIED/UNRESOLVED), wholeOriginalSHA256, proofSHA(zero64 for a source-observed close; independent external receiver proof remains required for archive adoption) |
| ARCHIVE_BEGIN | planSHA, originalsGroup |
| ARCHIVE_COMMIT | intentRowSHA, relativeArchiveDirectory, selectedIntentRecordName, intentWholeSHA, intentBytes, selectedCommitRecordName, commitWholeSHA, commitBytes |

Only one unresolved transaction is allowed. GEN_BEGIN increments reservedGenerations; GEN_COMMIT increments committedGenerations. APPEND_BEGIN increments reservedRecords; APPEND_COMMIT increments committedRecords. ENROLL_BEGIN reserves8 generations and one implicit initial administrative request credit. ENROLL_COMMIT commits8 generations, zero original records. The implicit request remains pending until REQUEST_RESERVE binds the first APPLY nonce and REQUEST_RECEIPT anchors its actual receipt. A subsequent REQUEST_RESERVE increments reservedRequests, maximum32; REQUEST_RECEIPT increments committedReceipts. Every success or failure reservation stays charged; no missing-file recount/refund. An unknown administrative reservation blocks new requests/input startup, but the current administrative archive lane may finish before its receipt. An exact already-open nonce/operation may only return its existing ticket for observation; changing operation or using a committed nonce refuses. Missing/mutated committed receipt refuses inspect. Receipt path must be exactly `product-input-lifecycle17/request-<nonce>.json`, regular/nlink1, bytes1..4096 and exact anchored SHA. Initial unindexed PREVIEW is external-only NON_DURABLE, no app receipt/accepted credit. Unknown APPLY without durable receipt is refused honestly, not retried under a false RECOVER identity. ARCHIVE_BEGIN increments reservedArchives; ARCHIVE_COMMIT increments committedArchives and relocates the indexed member paths. No reservation is refunded. CLOSE does not grant successful input/flight authority: odd/unresolved or failed close is UNRESOLVED, zero-record closed generation is UNUSED.

Committed archive directory is `product-input-archives17/<planSHA>`; each member retains `<generation>.aj02`. The selected `intent-[0..7].record` is the exact original lifecycle plan (SHA=planSHA); its members must exactly equal the archive reservation tuples. Selected `commit-[0..7].record` bytes are `AERIS_JOURNAL17_COMMITTED\t<planSHA>\t<planReceiverSHA>\n`. Their SHA/size/name and every member location are anchored in the registry outside the batch. Removing a whole batch or changing a selected manifest refuses inspect. Every original is regular, nofollow, nlink1, same recorded device/inode after rename. Native/full-file semantic/crypto receiver checks remain separate.

Append commit independently reads only the newly appended AJ02 row and verifies whole-row hash, length, sequence, elapsed monotonicity, kind/pair order, prior head, body hash and trailing hash. Cold inspect replays the complete registry and every original AJ02 chain; hot append reads registry delta/tail and target journal tail plus archive manifest existence/size, without rehashing archived originals. All index/control/pending/archive/source bytes are charged under combined original64MiB.

`expectedHostHead=null`: local-integrity observation only. A supplied64hex head must occur in the current valid descendant history. `ROOT` is only accepted for never-enrolled inspection or exact initial enrollment proof binding. Calling enroll again on an already committed exact initial baseline observes the current snapshot without writing or granting authority; an incomplete enrollment cannot be auto-committed. Complete filesystem rollback is not detectable natively without a fresh externally retained Root-known head. Do not interpret a self-consistent hash chain as authenticated tamper resistance.

Idempotent committed generation/append/archive APIs recheck current original bytes and bound ticket arguments; they do not rerun mutations or hide later truncation. Snapshot pending includes unresolved administrative request credit as well as journal/archive transactions.
