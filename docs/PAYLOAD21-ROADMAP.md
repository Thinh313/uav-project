# PAYLOAD21 · Flight and payload roadmap slice

Owner authorization 2026-10-13 redirects the next increment toward flight/payload product capabilities. Immutable ENDURE20 continues separately. The selected application and original mission corpus are unchanged; PAYLOAD21 is an isolated reusable browser module and static simulation preview, not a new selected release.

Now: original-source RAGAS capability matrix / A/B preparation, exact camera and gimbal route identity, per-target capability/authority and command observation, fault-scoped synthetic three-payload console and explicit simulation review. Reproduction/runbook: `../pilot/payload21/README.md`; requirements: `../delivery/TIP-PAYLOAD21.md`; decisions: ADR-031; evidence: `../evidence/payload21`.

Next after ENDURE20 terminal acceptance: integrate the validated core with the existing Fly workspace under a new version/signature; preserve mission/source/profile/archive identities and no authority from recovered state. Add protocol-specific discovery and golden raw-message replay/ACK ambiguity tests, camera capture/stream status and gimbal manager status. Mission camera addressing stays behind actual ArduPilot/QGC corpus and new SITL assertions. Do not generalize current simulator compiler to hardware or claim synthetic receipts as images.

Then when supplied: observe as-built Hera/HeraHub/radio/payload firmware/API/input/video mapping; implement native transport/video/manual-input adapters; bench/disarmed → HIL fault campaigns → controlled flight with actual captures; common-device RAGAS A/B on declared tasks. Exact hardware support depends on those gates, not a marketing count/BOM option. Runtime AI tracking and specialized payloads (LRF/light/drop/speaker/LiDAR) each need explicit capabilities, authorization and separate evaluation.

Internal canonical SOT remains unchanged: no observed hardware fact or runtime parity has been gained. Authorized scope/decisions are recorded in the TIP/ADR; simulation tests remain evidence. No RAGAS source reuse, physical flight or external publication.
