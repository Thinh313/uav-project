# ADR046 — preserve sensor bytes before local transmission

Status: private mock engineering implementation; no live/SITL selection. Original PIPE03/source/candidate/ENDURE remain byte-frozen.

The previous sender publishes UDP then constructs/enqueues the row. Process death there can leave a published sensor absent from raw capture. A daemon-writer deadline may also leave queued rows unsealed. A bigger quota alone does not close either window.

Choose single-owner framed WAL with record sequence, CRC32, chained SHA256 and declared counter/run/profile/model identities. Retain raw input, encoded computed row/snapshot intent, local send outcome and closure metadata. Complete intent precedes send; default mock policy calls fsync before publication. Archive is a bounded derived gzip written asynchronously from immutable preencoded bytes. Queue slots are reserved before computation. Worker failure preserves WAL and stops new admission; an archive failure never becomes complete merely because recovery succeeded.

Graceful signal handler only sets stop intent; normal code publishes DRAINING at checkpoints. It finishes one already-admitted fresh frame, continues stale checks and blocks new admission. Unknown send after SIGKILL remains unknown without a committed local-send result; mock receiver observations are separate scope evidence. Read-only recovery does not truncate, repair or resume the original WAL/flight epoch. Corrupt/torn suffix is retained and prevents a complete seal.

Limits: fsync return is an API observation, not tested physical-media survival. Power/OS death and all-storage failure remain NOT_CHECKED; admission/read failure prevents publication but cannot manufacture missing input receipt. A process-crash-only benchmark policy retains kernel-page-cache data under tested process death with the OS alive and makes no power-loss claim. Stronger flushing costs and queue reservation must be measured; no claim of realtime improvement from metadata or model microbenchmarks alone.
