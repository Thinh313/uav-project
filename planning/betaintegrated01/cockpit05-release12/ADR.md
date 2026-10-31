# ADR RELEASE12: type expected touch cancellation without weakening dispatch guards

Decision: isolate native derivative and new package12, retain Observer11 runtime policy unchanged, attach an exact source-bound client-selection overlay, and qualify expected cancellation as a durable causal protocol. The old FAILED experiment stays FAILED. Direct user authorization covers native repair/development testing; production/Hera hardware remain separate.

Reason: prior input305 was fresh at decision yet an actual release/view fence changed before socket. Refusing stale held bytes was correct; treating every such pre-entry cancellation as terminal prevented the intended release/BRAKE/regrant flow. Recover only from a proven synchronous release cause and known pre-entry phase, not exception text or elapsed time. Queue-before-accept and IO-in-flight races both require explicit handling and full original evidence.

Linearization: before a tiny atomic socket-entry permit, release cancels; after permit/entry, transmission may have occurred and cannot be relabeled NOT_SENT. UI must not wait on fsync/socket locks. All generic guard, freshness, context, IO and callback failures preserve existing failure/uncertainty handling. A release mismatch due a foreign view is not expected touch cancellation.

Alternative rejected: skip TX_REFUSED in readers, increase freshness/lease/cap, resend held RC, restore authority, retimestamp old input, or rewrite frozen source. Reusing exact codec and host204 avoids unnecessary framework/runtime copies. Any changed API/schema is explicit in new client identity, selected source manifest and strict receiver, tested before actual.

Conditional long: one newly authorized short only;30 requires actual successful raw-qualified short, every-window feasibility and new admission. Failure means retain evidence and stop actual, never automatic retry or interval sum. This ADR is a scoped implementation decision, not a safety certification.
