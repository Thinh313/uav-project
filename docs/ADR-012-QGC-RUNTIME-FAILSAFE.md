# ADR012 · Actual comparator serialization and in-flight simulator faults

Owner-authorized on2026-10-12. Use official QGC5.1.5 desktop as an external local test tool, independently of the product, to close application serializer/golden-corpus gates. Isolate its test profile and connect only explicit loopback SITL when required; no Qt/QGC/RAGAS application logic embedded in AERIS.

Keep structural source intake separate from simulator eligibility and application semantic roundtrip. Application-generated files become immutable provenance fixtures after observed save, with before/after comparison and hashes. QGC serializer may restructure simple sections or complex items; compare both the stored command snapshot and design metadata, not just Plan JSON formatting.

In-flight faults must control direction of heartbeats and telemetry. Inbound loss while outgoing heartbeats continue proves client stale-state handling, not GCS failsafe. Outbound GCS-heartbeat loss and full duplex loss exercise autopilot failsafe under observed pinned params. A passive observer must not send GCS heartbeats or commands that mask the fault. Track observed RTL/failsafe separately from command acknowledgements and mission completion, preserving interrupted-history boundaries after recovery.

No production SDK/HeraHub/physical aircraft is needed. No changes to production transport authority or operational flight settings; simulator-only fixtures and params are explicit. Preserve prior receipts and log actual failures/unknowns.
