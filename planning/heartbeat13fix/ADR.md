# ADR: isolate exact sealed-history verification from the control event loop

Status: accepted for one isolated G13 runtime verification after final source/mock gate. Phase A acceptance is limited to the measured mock and fault-injection scope below.

## Context

G12 heartbeat1103 exceeded the existing1000ms deadline before F1 ARM. Actual logs establish local timeout and host authority expiry, but cannot identify the initiating request stage. The host performs synchronous sealed-review ancestry/file/SHA verification during each state request on the same Node event loop as lifecycle requests. Historical references must remain verified; removing their hashes, caching by metadata or extending heartbeat limits would change the safety contract.

## Decision to verify

Move the existing exact read-only sealed-history implementation to one bounded owned worker. Retain full validation of the same bytes and records, original origin/CSRF/client identity,1000ms request deadline,750ms heartbeat cadence,3000ms TTL and every existing durability/frame/resource guard. A stale/superseded worker result cannot become a current history or flight-freshness assertion. Recompute response-time client/flight ages after asynchronous work; actual validation/worker failure remains fail-closed. Close/cancel the worker explicitly. Declare separate serialized input/result/queue bounds and transient copies; they are not a hard JavaScript-heap ceiling. The existing224MiB maxInFlightBytes policy is a disk-write-overlap allowance, not a universal RAM guarantee. Existing verifier transient artifact reads remain unchanged and must be disclosed.

The initial hypothesis is narrowly tested with an injected unrelated history-read stall. An old-fails/new-passes result demonstrates that modeled mechanism, not the unknown historical cause of G12. Genuine delay in a heartbeat's own required write/fsync or response still must trigger the original deadline and authority loss. Raw MAVLink recording and sensor/command ordering remain unchanged. Async journal refactoring is deferred unless separately justified by measurements.

Add bounded client/host lifecycle request correlation and phase timing without logging tokens or full request bodies. Diagnostic timestamps from browser, Node and Python retain separate domains; no subtraction across clocks without a valid mapping. A diagnostic ID grants no authority.

Independent QA exposed a required parallelism fence: on the unfenced prototype, a pending history verification that later failed could be overtaken by an actual mock payload join. Preserve that witness. Before an effectful control dispatch, await the already-pending FULL state-verification promises, including their final head/run/freshness checks, and revalidate the request's client context. Genuine history failure retains the existing campaign latch; known supersession refuses the read/control without effect or automatic retry. Heartbeats and UI observations bypass this control fence. Do not lock out telemetry for the duration of long flight operations or add another duplicate history task merely to wait for the existing check.

The Native snapshot helper validates and canonicalizes the before receipt, schema and referenced journal before any after-journal write. Preserve G12's partial snapshot and caller error; do not repair old receipts. Reuse the exact installed development APK because changed JS is host-served. No new build or signature.

## Alternatives

- Extend deadlines or retain authority after failed heartbeat: rejected, changes the user-required guard.
- Metadata-only history cache: rejected, does not provide the existing byte/SHA check.
- Rewrite transport, journaling and flight simultaneously: deferred, obscures attribution and increases regression scope.
- Separate control server/process: deferred, introduces authority synchronization and an additional process beyond the current finite campaign.

## Acceptance and disposition

Require effective old/new HTTP-handler comparison, independent deadline/session/durability/worker/tamper/context and close tests, equivalent strict journal replay, unchanged guard/source checks and a pristine G13 gate. Then Root may perform one fresh finite Android–SITL campaign. Any actual failure is retained and reported; neither modeled performance nor N1 alone certifies the full milestone. Contractor records the concrete measured acceptance before production integration/freeze.

## Contractor acceptance of Phase A (23 October 2026)

The fd02 effective HTTP comparison activated the same 1250ms sealed-history read fault in both variants: the original heartbeat exceeded its unchanged deadline (1005.10ms), while the worker variant completed in7.00ms. Injecting1250ms into the heartbeat’s own required durable barrier still failed at1002.67ms. Healthy-load maxima89.66ms and92.03ms both passed; no idle-speedup claim is made. These are synthetic fault measurements, not proof of the initiating G12 fault.

Independent acceptance retained the unfenced parallelism failure, then verified nine affected control-fence scenarios (receipt3471823c11d345b88691f228f85b6a97ef2d04a53087b0a91c6440c7d7d8289a). A final targeted test of the actual existing Flight.observe send guard (receipt8fe1168c9ed4584c3d4d7273113ce3f0480b1ece3a97375e35755cbc9cb5de13) blocks the next non-heartbeat send after an observed worker death; id0 heartbeat and existing abort cleanup remain available. Worker exit diagnostics retain observed numeric status rather than inventing zero. Native snapshot validation and bootstrap deadline/epoch tests also passed independently.

Root authorizes freezing this minimal worker/diagnostic/snapshot repair for the single finite G13 campaign already specified in TIP. No asynchronous journal integration, deadline increase, cache-only verification or additional automatic campaign is authorized. Android–SITL, actual link loss, reboot, persistence and full preservation remain NOT RUN for G13 until their raw evidence passes independently.
