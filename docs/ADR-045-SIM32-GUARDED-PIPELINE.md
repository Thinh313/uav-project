# ADR045 — sticky epochs and explicit clock domains before performance

PACING02 exposed queued input resuming physics after suspension, duplicate sensor replies shifting AP frame lineage, and missing clock calibration. New private backend uses immutable per-run epoch and terminal marker; own-clock3s age and realtime/monotonic discontinuity are checked before model and before send. Invalidated sessions never become live again. No control or frame replay as recovery.

Known clock replies may arrive late or out of order: preserve and correlate using bounded request IDs, retaining uncertainty. Unknown identity is not reclassified as harmless timeout. Node hrtime, backend monotonic and guest monotonic are explicitly named; bracket calibration is required before cross-domain interpretation. Wall timestamps identify records, never set model timestep.

Reject duplicate servo packets before cached echo. This conservative prototype policy keeps supported healthy transport one-to-one and exposes unsupported recovery honestly; it does not rewrite AP retries or pretend a terminal rejected input is a completed physics step. Aborted in-flight computation is preserved separately from committed raw/sensor outputs.

After guard/correlation gates, experiment with guest loopback AP/model to remove Docker VM boundary round trips. AP binary/pacer unchanged; immutable C kernel may be compiled for Linux in a new fixed image. Architecture/libm/compiler differences are confounds, and adoption requires encoded-byte oracle against original host reference. Record failing alternatives instead of relaxing gates. No source/candidate/ENDURE writes or production signing.

## Optimization decision after actual phase-A gate

Guest kernel built in separate fixed image and rejected by byte oracle: gust wind differs at frame10 (macOS/Python3.14 vs Linux/Python3.12/libm; precise math cause not isolated). No guest SITL/control path selected. Same-host strict fused RK4 implemented instead: one argument parse plus four numeric derivative stages; unchanged double precision, compensated dot, operation association, host libm, original Python normalization/contact/wrench/battery/aux math. Immutable Python full-byte oracle verified across1,370,468 prior captured frames; exact count in integrator-oracle.json is authoritative. No relaxed threshold.

Predeclared paired actual UI matrix: guarded native derivative vs fused RK4,2replicates per added host CPU load0/2/6,12cases total, offset/gust seed32 survey7m; balanced load/order, same AP hash2CPU384MiB, rate1200Hz, speedup1,500ms cap. Both engines retain guards, calibrated domains, full raw+stage capture, same journal/renderer. Engine baseline label is optimized (prior native derivative), not pure Python reference. UI failures/timeouts and terminal epochs remain in denominator; no retry. This measures host configuration and observed temporal association, not hard realtime or calibrated Hera.
