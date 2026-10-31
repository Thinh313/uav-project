# Workbench01: additive mission planning and review slice

Accepted within user-authorized host/mock scope, 2026-10-24.

Use the frozen mapping51 KML parser, planner/readiness, ENU and mission55 polygon validation by read-only import. Do not fork or relax native92's narrower 10–30 m/0.5–2 m/s contract: this workbench has its own explicit 10–120 m/0.5–15 m/s HOST_MOCK_ONLY envelope and is not upload-compatible authority. Flat AGL is explicitly acknowledged, never inferred from KML Z or an unknown DEM. No flight socket exists.

Use deterministic optics, bounded grid-center union, synthetic pixel Laplacian/clipping, and a simple constant-power reserve model. These give explainable planning/review outcomes without a runtime LLM, dependency installation, photogrammetry suite or hidden asset download. Multi-view reconstruction/3D overlap, actual calibrated camera quality, real battery model and terrain following are deferred. A 100% binary sampled footprint coverage cannot prove mapping suitability or triangulation quality. Grid step and this limitation remain visible.

Authority is ephemeral UI workflow state, never serialized. The loopback service regenerates plans and validates synthetic bundle semantics but is not an operational permission server. SHA verifies integrity/internal consistency, not sender authenticity. Receiver is a separate CLI process reusing the same semantic implementation; Python math oracle is separately formulated by the same assistant, not independent external QA.

Mock runtime is stateless, request bound 2 MiB, ≤2 requests, parser timeout 3 s, ≤1,500 shot records, 32,000 grid bounding cells/8,000,000 cell-footprint tests. Bundle export also enforces receiver size limit. No background retry. Failure to evaluate/save retains in-memory records, revokes approval and tells the operator. No automatic evidence cleanup. Existing 29 GiB Android/SITL admission and frozen guards untouched; this small preview enforces the user's 20 GiB physical floor on API work.

Design QA briefly tried a same-origin iframe harness; main CSP correctly rejected it. Once direct CUA viewport capability was discovered, remove that harness and QA-only framing exception. Keep failure receipts; final server serves no frame route and retains frame-ancestors none throughout. Direct viewport reset after QA. Avoid permanent test-only product surface.
