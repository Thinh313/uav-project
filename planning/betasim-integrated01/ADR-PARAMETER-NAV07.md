# PARAMETER-NAV07: response-paced reads and disarmed readiness

Contractor decision, 2026-10-31. Scope: isolated BETA-SIM; no original source/candidate/ENDURE edits.

R04's actual three-segment transport prefix contains 117 valid named parameter requests (three sets of 39), but only 24 requested names returned. The pinned ArduPilot GCS_Param.cpp has request capacity20 and reply capacity5. This supports queue overflow as a causal explanation; internal queue occupancy was not recorded. Ten request/interval commands and their ACKs prove inspect passed its initial identity/heartbeat stage. No ARM or mode command was sent. Final UI predicate was not captured; ROOT_OBSERVATION_DEADLINE is the actual failure.

R04 preflight was clicked near AP boot15.8s, before first Home around19.488s. Final EKF flags167 still lacked POS_HORIZ_ABS16 near AP26s. Startup readiness is not proven to converge; a sensor, firmware or physical-model defect is not ruled out.

Implement one durable, exact39 typed read cohort with at most4 outstanding names. Only a fresh, correctly targeted CRC-verified response with exact expected type/bits, causally after that request, advances its name. No resend, full-burst reset, timer reset or wrong-target advancement. Wait outside shared TX scheduling so heartbeats/manual intents are not blocked. Preserve fsync-before-send, global RPC/TX/resource bounds, all39 and10s freshness; inspect's original8s deadline stays absolute.

Add an explicit disarmed, read-only navigation-readiness phase between connect and operator preflight: maximum30 monotonic seconds within the existing case deadline and existing API-poll budget, without deadline reset. Require unchanged live heartbeat, GPS, Home, land, battery/EKF(mask55), prearm and all39 typed/fresh parameters before existing preflight. No ARM, mode or parameter writes to warm up. A failed readiness is a retained failed case, not acceptance. It must expose its last actual failed predicate from original API-state response bytes within existing diagnostic bounds.

Version external RootWire/companion/entry/scenario files so all prior candidate references remain byte-exact. Copy no whole project, install nothing. Mock causal finite AP queues, delayed/missing/duplicate/wrong-target/type/stale responses, heartbeat progress and owner/fsync failures. QA independent source gate before a new frozen candidate and a single new short actual attempt. Ten-minute run only after independently accepted actual short. Artifact union8MiB is explicitly authorized; other guards unchanged.

Outcome remains NOT READY until the integrated actual acceptance is proven. These source changes do not establish convergence, physical Hera capability, media quality or full beta readiness.
