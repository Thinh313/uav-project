# ADR066 — isolated simulator input→AP→physics→render

Accepted15/10/2026 under the already approved simulator plan and storage-resume instruction. Extend in new pilot/simtrain53, not frozen app/candidate or prior52files. Node HTTP/MAVLink control and separate Python physics/controller processes avoid coupling physics integration to browser RAF. Docker holds only the pinned AP and clock observer, with bounded resources/read-only source mounts. A managed external controller bounds lifetime even if UI stops. New outputs exclusively evidence/simtrain53.

Use existing SitlLink read-only for observed firmware/profile/preflight and command correlation. Add scoped RC override serialization from pinned generated C headers. Only owned loopback endpoint target42/1 admitted; no generic arbitrary-command API. Explicit Guided takeoff→Loiter RC input→Land exercises actual AP with reference physics. This is the first training control slice; AUTO missions/instructor faults/calibrated Hera remain separate gates. Preserve1200Hz/speedup1/cap500ms and journal-before-send; no pose animation, frame dropping or precision reduction as performance fixes.

Use an expiring host challenge in each input request to bound transport age without assuming browser/Node clock synchronization. Separate session/boot and neutral-first leases; focus/stale/malformed/identity faults latch revocation. RC release is a simulator behavior and requires its own observed test, not a certified hardware policy. Acknowledgment, vehicle mode, physical motion and rendered pose are separate evidence links.

No new software signature, SDK, HeraHub/HIL or ENDURE rerun. Full18minute workload requires trace retention/capacity work; current bounded G1 preparation cannot be represented as council acceptance.
