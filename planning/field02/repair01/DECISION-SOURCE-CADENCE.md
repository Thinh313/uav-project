# L2 re-evaluation: one bounded source cadence repair

22/10/2026. User authorized fixing FIELD02 cold-start/FPS and Android–SITL. Original repair01 limits remain for Android launches(2), new AP requests(2), resource floors, profiles and acceptance thresholds. No additional native build, signing or external publisher topology.

Decoder lifecycle and presentation cycles have produced retained actual evidence, including failures. Final presentation06 actual window:686frames/30s=22.8659fps FAIL24, p95upper171.976ms PASS300, initialReady490.9ms PASS1500, relay500ms recovered555.9ms PASS2000. Do not call this overall PASS.

Newly isolated source scheduling defect: publisher uses a4ms polling timer, compares elapsed to1000/30 minus0.5ms and sets last=t on each eligible callback. Polling/dispatch quantization accumulates instead of preserving the30Hz phase. Actual final06 snapshots show823 eligible checks in approximately30s (~27.43Hz), latest64 eligible-gap median35.7ms, and123 credit skips. This is distinct from decoder resets or UI observer work. It is a candidate explanation for part of the remaining deficit, not a guarantee of24fps under variable host load.

Approve exactly ONE source scheduling repair and one new bounded30s Android window before the already-authorized AP scenarios. Preserve all earlier FAILs. Maintain absolute30Hz phase, render at most one fresh raw frame per eligible callback, skip and explicitly count missed raw schedule slots after lateness; never emit catch-up bursts, duplicate frames, fabricate timestamps, discard encoded dependencies or change1280×720/30fps/4Mbps VP8/profile/caps/clocks. Source timestamp remains actual capture monotonic time. Missed raw slots and credit-admission skips must be separately observable.

Mock verifies long-run quantization/drift, early callbacks, multi-period delay, no catchup, backward/nonfinite time, identity/epoch stop and unchanged credit/queue policy. Separate QA reviews before live. No further source or presentation algorithm retry in this repair after this single change without genuinely new evidence and a new scoped decision; a low FPS result must remain FAIL.

This is Contractor re-evaluation within existing user authorization, justified by new measured source timing. It does not lower any gate, erase attempts or grant hardware/production authority.
