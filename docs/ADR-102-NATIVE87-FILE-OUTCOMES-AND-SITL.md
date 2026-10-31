# ADR102 — isolated Android87 native file outcomes and SITL

Keep COCKPIT85/Native86 and old evidence immutable. Copy allowlisted assets only, reusing native84 host flight logic in newnamespace/ports/container identity. Distinct fixed offline entry documents for mock versus SITL; native instance resets on source switch, authority never persisted. Default Android cockpit uses actual observed SITL only when explicitly selected and authenticated against owned host bridge. Main Fly consumes qualified84envelopes; missing/stale/changed boot clears data.

Persist picker operation IDs, expected workspace/head/archive digest and outcome on separate bounded append-only DraftStore ledger. Publish completion only after native provider readback/staging verification. JS timeout is an unknown/pending outcome; later result is discoverable through explicit status without retry. Process restart retains unknown operations, does not infer success; explicit user-selected reconciliation checks original operation/digest and named staging generation before accepting any outcome. No automatic activation/deletion.

SDK86 cache reused read-only; AVD87 new. Development signing only. Reuse existing protocol/schema identities for retained archive/reviews, not new labels pretending hardware qualification.
