# PACK15 · deployment packaging, capacity and signed software

v1.10.0. Authorized host-local engineering increment after GEO14. Single agent Contractor → Builder → Verify, not independent review or external publication.

| REQ | Acceptance |
|---|---|
| P15-01 | Primary signature/trust/expiry/rollback definitions captured and hashed through Refinery; only user intent appended to SOT |
| P15-02 | Versioned host preview / dedicated loopback simulator profiles; HeraHub remains planning-only unmeasured; external Node runtime explicit |
| P15-03 | Pure conservative storage scenario with retained source/receiver, journal, partial checkpoints, concurrent export, two software slots, quota/format/free-space constraints; assumptions stay estimates |
| P15-04 | Deterministic bounded streaming package, explicit file inventory/SHA, canonical signed manifest; no runtime/evidence/keys/dependencies in payload |
| P15-05 | Ed25519 verification against independent caller trust and expected manifest; expiry/future/sequence/revocation/key and byte tamper rejection; local development identity only |
| P15-06 | Verified staging and immutable publication, no overwrite; exact installed inventory; start re-verifies disk, external data root and observed capacity; no automatic download/activation/flight |
| P15-07 | Read-only operator UI for target/sizing and current package verification, stale/offline data invalidates conclusion; shared responsive controls |
| P15-08 | RFC vector, attack corpus, deterministic rebuild, install/restart/start smoke with separate data root and package, legacy record readability and preservation |
| P15-09 | Method kernels, canonical diff/gate, full checks and cleanup, reviewable artifact/runbook/completion with deferred device/production gates |

Non-goals: bundled Node/OS/container image, native APK or HeraHub install, internet updater, TUF conformance, official RtR signing authority, protected secure element, key custody/rotation/threshold, physical power-loss or commercial certification. Cryptographic validity authenticates only the supplied independent trust anchor. File hashes do not prove source quality. Time/sequence/pinned digest require trustworthy caller clock/policy; hostile root or concurrent privileged mutation is outside host-local boundary. Existing execution and dataset evidence stays outside software slots; no automatic cleanup/migration. Package profiles do not silently rewrite existing lifecycle policies.
