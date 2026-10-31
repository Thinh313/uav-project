# IO59 — syscall and host wait attribution

Authorized by user15/10. Single agent separates specification/build/verification; no independent reviewer claim. New pilot/io59 and evidence/io59 only. PACE58/frozen/candidate/ENDURE/canonical SOT remain read-only. No new signature, SDK or device.

REQ1: instrument each WAL os.write and fsync including magic/emergency writes with wall/threadCPU, frame/kind, byte offset, requested/returned count, errno. Exact existing CRC/hash-chain format and fsync-before-send policy. Bounded contiguous trace, fail loud on overflow; no ring or frame drop.
REQ2: absolute-deadline10ms thread and separate-process wake probes, record elapsed CPU and missed deadline counts. Report nonCPU time as offCPU proxy (I/O block/GIL/preemption), wake lateness as scheduling/host-contention proxy. Exact kernel runnable-wait attribution UNKNOWN. Measure observer cost with mock and clock calibration.
REQ3: mock normal/short/zero/error/flush fault and blocking tests, exact physics/frame conservation and durable-before-publication. Mock gate before actual SITL.
REQ4: at most2 actual starts with explicit nonce reservations, same AP SHA,1200Hz/speedup1/cap500ms, UI1920x1080. Fresh24GiB admission, stop at20GiB+768MiB, cumulative new budget1.5GiB. Preserve every failed attempt. Standard preflight/arm/takeoff/neutralhold20s/LAND/disarm, authority guards unchanged.
REQ5: independent original-model sensor+aux oracle for every admitted frame, raw WAL/AP correlation, clocks, per-syscall jitter and full5s/whole RTF. PASS integrity never implies PASS pacing or Hera calibration.
REQ6: point-in-time preservation before/after with cumulative PACE58 manifest; completion and fingerprints. No optimization changing durability or numerical platform without new evidence.

No architecture approval pending: scoped derivative instrumentation is directly authorized. No new package install/build.
