# ADR-052 — compose safety observation under one revocable mock session

Accepted within user-authorized offline scope, 2026-10-14.

Version148 must not disappear in the older message subset. A union framer emits validated whole raw frames with byte receipt lineage. A central gate orders all target packets before submodules; foreign peer sequence does not advance AP sequence. Duplicate/reordered frames cannot refresh readback or discovery. Unsigned frames remain unauthenticated.

Reuse immutable M37 telemetry and F38 typed parameter reader. A36 preflight remains incomplete without its explicit inputs; F38 rich firmware mapping remains separate, because mAh/V cannot establish remainingWh or legacy enum equivalence. Do not disguise a synthetic fence/configuration supplement as wire readback. No fence upload is composed here because M37's REAL32-only completion contract cannot be safely borrowed for typed firmware parameters.

Only named PARAM_REQUEST_READ buffers are exposed, after an injected journal commit. One announcement/read cycle per adapter, 1500ms binding freshness retained. All readback/inspection witnesses revoked together on session loss, changed firmware/parameter, clock uncertainty or writer failure. No serialized authority, auto renewal or reconnect. Frame error policy is deliberately strict; this19-message subset is not a general live ArduPilot stream adapter.

Consequence: useful isolated composition and falsifiable corpus without touching frozen application. Actual firmware association and full-stream compatibility, persisted production journal, physical inputs, enforcement and flight are future gates; new tests cannot assert them.
