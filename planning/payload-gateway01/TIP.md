# Payload Gateway + Real Media / MOCK01

User authorization: 21/10/2026, implement discovery → selection → explicit authority → camera/gimbal → original image → exposure geotag → review. Apply Vibecode Kit6.3, sequential Contractor/Builder/Verify phases in this chat. No independent human or agent QA is claimed.

## Outcome and acceptance agreed before build

In the existing curated PHONE06 glass cockpit, an operator explicitly discovers simulated RGB/IR devices, selects one, grants a finite mock lease, observes gimbal/ISO readback, captures an original synthetic JPEG, reviews exposure-position metadata and exports an integrity-checked package. Same gateway contract has an adapter seam; no vendor SDK driver or physical camera qualification is implied.

AC1: exact device/firmware/boot/discovery and station identity; selection never grants control. Unknown profile, wrong target, stale/reboot, unsupported action refused.
AC2: explicit device-scoped finite lease, token and command IDs; wrong station/token, replay, expired/revoked/disconnected authority rejected before adapter action. Lost feedback means UNKNOWN, not execution. No automatic reconnect/grant/retry, no flight API.
AC3: mock gimbal pitch/yaw degrees in declared body-relative frame and ISO whitelist; validate inputs and correlate readback. Thermal-look advertises no radiometry or ISO control. Adapter real mode is unavailable until qualification, never a mock fallback.
AC4: capture intent/ACK/event/file are separate. Exposure and source frame pinned at trigger; server checks admitted preview identity. Missing event/file, changed stream/boot, corruption or invalid GNSS cannot publish a valid capture. Original JPEG is unmodified; actualImages=0 always.
AC5: reuse BIG02 geotag/math and exact package format. Exposure-time mock GNSS brackets, WGS84 ellipsoid datum, clock uncertainty, unknown camera lever arm and spatial accuracy. Independent receiver implementation verifies hashes/math; integrity is not authenticity or mission success.
AC6: bounded durable journal and committed capture directory survive host restart; authority never survives restart. Journal corruption/read-only failure blocks new commands. Partial/uncommitted folders remain PENDING and are never published or auto-deleted. No quota eviction of evidence.
AC7: browser journey in the existing Fly/review shell, Vietnamese state/source labels, keyboard/focus/close, no overlap at1280×800 and narrow landscape. Reuse BIG02 H264 pipeline; no new latency/performance superiority claim. Hardware integration, Android runtime, field and production remain NOT_CHECKED.

## ADR and scope

Reuse existing BIG02 relay, codec pipeline, geotag and package modules by imports/read-only derivation, not edits. New gateway core and mock adapter live in `payload/gateway01/`; orchestration/tests in `planning/payload-gateway01/`; new evidence under `evidence/payload-gateway01/`; new completion report only. PHONE06 stage is a curated derived copy under `.local/payload-gateway01/stage`, not a project copy. No APK/signature/SITL/emulator/ENDURE restart or canonicalSOT update.

Host bridge binds loopback only, validates Host/Origin and nonce, finite JSON/binary body/timeout/rate/queue caps, explicit methods and asset allowlist. Secrets/lease tokens are not journaled. Local tokens are a mock session guard, not production authentication. No network camera address, proxy or SDK loading API.

Limits: no install/download; existing Node/Python/browser only. New evidence≤16MiB; stage≤32MiB. Admission20GiB+128MiB, runtime stop at that guard. At most2 browser journey windows plus one targeted repair; no video recording or per-frame disk writes. Server maximum15min. End server, owned tab and stage cleanly; preserve all runs and failures. User may restart preview with a new evidence directory; no overwriting runs. New journal writes fsync before authoritative actions; directory and package commit receipts fsync before publication.

Baseline: current manual API testing requires matching identity/rights/capture and export across pieces. This slice integrates those steps in one cockpit; time/user-effort advantage remains unmeasured. A direct LLM is not a comparator for deterministic authority/hash/geospatial correctness. Future AI features remain separate.

Verify source pin preservation, adverse cases, real HTTP methods/routing and browser actions. Report coverage and missing hardware gates, not a product-completion percentage. Mock SDK-shaped profiles do not constitute Sony/Phase One implementations.
