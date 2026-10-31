# TRUST16 · bootstrap, keys and release continuity

v1.11.0. Host-local engineering after PACK15. Contractor → Builder → Verify by one agent; no independent security audit or external release.

| REQ | Acceptance |
|---|---|
| T16-01 | Primary root-rotation/version/persistence definitions captured with provenance; only owner intent added to SOT |
| T16-02 | Independent bootstrap entry and bounded, pinned dependency closure verified before dynamic import or installed application execution |
| T16-03 | Strict engineering root metadata, separate root/release/approval keys, unique threshold signatures; old AND new root quorum for consecutive rotation/revocation |
| T16-04 | Mode0600 private keys, explicit non-overwriting generation/signing and public-only distribution; no production identity inference |
| T16-05 | Exclusive durable trust ledger, immutable hash-linked events, head/tail consistency and monotonic observed clock; interrupted commit fails closed and explicit digest-bound forward reconciliation preserves bytes |
| T16-06 | Signed release authorization binds root, package/manifest/build/sequence; separate release and approval quorum, full byte checks and durable high-water mark before installation |
| T16-07 | Start checks current root/authorization/ledger/slot again, holds trust writer lock for child lifetime; sequence/build downgrade and same-sequence substitution blocked across restart; no automatic fallback |
| T16-08 | Read-only fresh security view; expired/corrupt/missing/pending evidence clears previous readiness; no UI key/install/flight mutations |
| T16-09 | Actual local release→rotation→upgrade→restart and adversarial/fault corpus, full regression, historical evidence preservation, SOT/kernel/report/cleanup |

Trust boundary: operator must verify the standalone bootstrap entry hash and dependency-descriptor hash through an independent trusted channel BEFORE invoking Node. The original signed root digest is an explicit external argument, never inferred from a candidate package. Reviewed host Node/OS, directory ownership, filesystem and clock are trusted. Local administrator replacing entry, all anchors and ledger together, runtime preload/injection or concurrent privileged file changes are outside the boundary. No device secure boot, hardware monotonic counter, HSM/offline custody attestation, trusted time service, remote updater, TUF compliance or official RtR signer. Separate local keys demonstrate role enforcement, not separate people or an independent approval. Interrupted commit blocks start; reconciliation completes only the exact validated forward transaction and never lowers history. Failed upgrade remains blocked until its selected package is available; intentional recovery uses a newly authorized higher sequence/build, never silent rollback. Existing PACK15 caller-policy tooling remains explicitly legacy engineering and cannot bypass this separate bootstrap service boundary. SDK/HeraHub/physical-power-loss and field gates remain NOT_CHECKED.
