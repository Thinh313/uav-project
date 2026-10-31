# ADR073 — external same-user host thread samples

Use Apple libproc without installs or task_for_pid privilege, targeting the backend parent and its unique64-bit thread ID. ABI comes from the installed Apple SDK. Parent starts child before UDP readiness; child validates parent relationship and target query; parent stops/seals it before exiting. Bounded binary raw includes scheduled time, query start/end, return count/errno, target thread CPU/state/priority and observer CPU. No disk I/O on each sample. Missed ticks recorded; overflow stops with explicit error.

Filesystem wall/CPU intervals remain direct wrapper measurements (including possible preemption). Join only samples whose complete query brackets fall inside spans; partial intersections retained separately. States have no filesystem wait reason or exclusive host runnable-wait counter. NonCPU, state samples and guest runqueue counters remain distinct observations. No privileged tracing added. Main-thread observed CPU has kernel quantization; no observer-cost subtraction from flight results.

Primary ABI/semantics: local SDK sys/proc_info.h, libproc.h, mach/thread_info.h; Apple XNU osfmk/kern/bsd_kern.c fill_taskthreadinfo and thread-state definitions. https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/bsd_kern.c ; https://github.com/apple-oss-distributions/xnu/blob/main/doc/observability/recount.md .
