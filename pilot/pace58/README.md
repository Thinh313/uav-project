# PACE58

Experimental isolated pacing adapter for AERIS57. Current gate **NOT_READY_G1_STABLE_1X**. Read `../../delivery/COMPLETION-PACE58.md`, scoped TIP and ADR069 before operating.

Preview/API: `node pilot/pace58/ap-server.mjs` on8811 and `node pilot/pace58/server.mjs` on8810, from repository root. They do not automatically start SITL. Existing53/57 services are independent. Browser start is deliberately disabled in this benchmark derivative. All five reserved experiment IDs have been consumed; do not replay their POST/start or runtime helpers. No automatic retry/restart/adoption of authority.

All actual control is simulator-only to attested127.0.0.1:5871, fixed AP42/1, owned container `aeris-pace58`. Physics/clock ports9002/9004/9005 are exclusive with idle SIM53. Model1200Hz, speedup1, AP catchup cap500ms and per-frame fsync-before-send remain fixed. New profile experiments require a fresh plan, reservation/nonce, source pins, disk/quota admission and evidence; this module is not a production control release.

Read-only analysis helpers refuse overwriting receipts. `analyze.py <namespace> <run> <new-output.json>` reads closed traces. `raw_verify.py <run...>` writes an exclusive raw-diagnostic receipt; existing ones must be retained. `preserve.py <new-label>` checks prior protected hashes. `final_verify.py` writes an exclusive machine report. `derive.py` is initial derivation provenance, not an updater; its exclusive writes intentionally prevent re-running over current code.

`compact.py` stores every diagnostic row in bounded contiguous arrays; no ring overwrite. `UITiming` records actual draws over the whole run, with explicit overflow, separate from physics and the immutable scene's startup-only metrics. Footer timing refers to the retained run when idle. `gc_observer.py` never forces/disables GC in runtime; only its standalone mock test forces a collection. No measurements restore a lost input lease.

`bench.mjs` is an explicit synthetic-neutral local test driver, not a human/HeraHub input source. Its cleanup LAND is a distinct action, never retry of failed input. If canonical safety guards reject cleanup, it preserves a failure/abort receipt and requests the owner stop circuit; that is not mission completion or observed LAND. `raw-diagnostic.json` PASS is never sufficient for pacing/mission/ENDURE PASS.
