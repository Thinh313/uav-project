# ADR061 · retain pending journals; stage an explicit successor

Accepted for isolated HERARECOVER48 host mock15/10/2026.

HERAPERSIST47 correctly blocks HEAD.pending but cannot safely infer whether an unacknowledged result reached its caller. Deleting HEAD.pending or silently promoting a record would discard this ambiguity. Growing an immutable journal forever also cannot satisfy finite quota.

Use a byte-preserving evidence bundle with exact inventory/hash/size, bounded parsing and semantic replay. Source capture is read-only and compares two inventories; this is a snapshot consistency check, not an OS writer lease. Only static crash fixtures are exposed by the preview; users may import an offline export, with no arbitrary filesystem route. The live47 journal is never mutated or automatically read as a recovery target.

An operator explicitly selects an admissible record. Selection means choosing a draft/history reference, not asserting delivery/execution of an unacknowledged intent. The complete source archive and plan are retained in a new immutable generation. Its47 journal begins disconnected with default synthetic peer configuration; only a saved draft is carried. A receipt binds archive, plan and exact initial journal snapshot. Missing receipt means quarantine, never auto resume. Explicit subsequent writes use47's original intent/result semantics and limits;48 only stages and inspects the seed, never routes controls.

Quota counts all generations, including interrupted ones, with aggregate64MiB/max4 generations, journal16MiB and conservative allocation reserve. Rotation is a new retained generation, not compaction. No automatic cleanup, locks cleared, HEAD rewritten or old generation selected. Ready generations are not automatically made active in47/Fly. A later authorized handover can use a reviewed generation with a fresh handshake; exported archives do not establish external retention by themselves.

We deliberately retain bounded partial outputs when a write fails; no receipt is issued. Host free-space gate is checked before each publication. An external process can still consume space after statfs, therefore ENOSPC/unknown write failures stay quarantined. Tests inject these failures without filling the host disk. No authenticity or OS-level malicious-writer resistance is claimed from an unkeyed digest.
