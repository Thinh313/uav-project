# SIM32-PIPE03 — private guarded pipeline

Engineering module; latest managed-shutdown/journal revision has **offline verification only**. Owner requested handoff14/10/2026; do not launch additional SITL automatically. No Fly integration, software signature, ENDURE restart, SDK or physical endpoint.

Suspension/stale uses a sticky epoch,3s progress deadline and wall/monotonic discontinuity checks before queued input/model/sensor publication. Duplicate/gap/regression ends the session before cached sensor echo. New session IDs are mandatory. Qualified clock domains use retained raw nonce/address and bounded brackets; never subtract Node/Python/guest counters without calibration.

The host fused RK4 extension retains strict float64 operations and original host math. `integrator-oracle.json` verifies exact encoded bytes/aux on1,370,468 earlier frames. Linux co-location was rejected at frame10 by the platform byte oracle. It is not selected.

Latest shutdown publishes DRAINING, blocks adapter admission, completes only an already-admitted fresh frame, captures an unadmitted pending datagram separately and closes without recreating LIVE. Stale/clock/duplicate gates still invalidate the epoch. The private journal has512MiB uncompressed/192MiB compressed caps,256FIFO slots and bounded258-row incomplete-tail preservation on writer/queue failure. Such failures remain incomplete; salvage is not an accepted mission.10offline tests passed; latest live shutdown/overload behavior remains NOT_CHECKED.

Before a future explicitly authorized run, require actual free space≥28GiB and full peak admission. Source snapshot/pins must be new. `matrix_v2.py` proposes12counterbalanced UI runs (2replicates×0/2/6CPU workers×native/fused), same AP hash/rate1200/speedup1/cap500ms, and stops new admission after a failed UI gate. It has not been run. Existing `phase_a.py`/`fused_faults.py` are historical helpers with occupied IDs; do not reuse them or overwrite receipts. A future fault harness must allocate fresh IDs and verify all stale/duplicate/managed-stop cases first.

Runtime ownership is constrained to container`aeris-sim32-pipe03`, loopback5784/5785/5786,UDP9002/9004/9005 and preview8799. No preview/runtime is running at handoff. Default source still names the native-derivative comparator; fused is opt-in via declared`SIM32_ENGINE=fused`. This is not deployment selection or a signed release.

The Darwin-only trace compactor runs after owned closure: retain header/events, check the unused tail is zero, reclaim its allocation and require unchanged full SHA/file length. No frozen/ENDURE file is compacted.36private closed traces reclaimed about2GiB with identical bytes. Full allocation is still budgeted at admission, rather than assumed sparse.

Read ../../delivery/COMPLETION-SIM32-PIPE03.md and ../../evidence/sim32-pipe03/verification.json before making readiness claims. Pacing1×, revised live runtime, repeated paired comparison, hardware calibration/native Hera and competitive superiority are open gates.
