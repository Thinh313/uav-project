# ADR-017 · Fault recovery on the frozen mission matrix

Accepted 2026-10-12 within explicit request. Reuse deterministic compiler/profile and durable per-attempt archive. A transparent local proxy captures writes before filtering, and observes upstream packets without sending its own heartbeat. This separates stale UI, delivered GCS heartbeat and actual autopilot behavior. Restart uses existing -w container only after fresh disarmed observation; lost mission is an expected refusal and deliberate reload, not a persistence claim.

Recovery remains download/review-only; application never resends AUTO on heartbeat return. Separate campaign schema binds suite, frozen bytes, reset identities, records and raw packet traces. Historical BENCH06 format/build remains accepted. UI imports evidence, with no simulator POST. Retaining-flash and in-air reboot need a separate runtime/HIL contract. Unsigned receipts check integrity, not origin authenticity.
