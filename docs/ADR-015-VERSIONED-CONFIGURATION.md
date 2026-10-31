# ADR015 · pinned configuration observation and preflight

Build on independent MAVLink adapter and REVIEW04 archive. A read-only configuration is evidence with identity/version/age, not cached UI approval. The first profile is simulator-only Copter4.7.1 with the exact FS_GCS_ENABLE1/FS_GCS_TIMEOUT5/FS_OPTIONS16/MAV_GCS_SYSID255 values and wire types observed at REVIEW04. This is a four-parameter contract, not a complete autopilot configuration audit or Hera default.

Use one bounded explicit request for fresh AUTOPILOT_VERSION and four named PARAM_REQUEST_READs. Commit only complete observations from the discovered autopilot/session. A 30s monotonic freshness budget is an engineering policy for this local simulator; record UTC timestamps and age at evaluation. Re-read on demand. Mismatches are observed deviations; freshness timeout is uncertainty. A read timeout does not create write ambiguity and does not auto-retry/send flight commands.

Upload, ARM and AUTO independently require a matching fresh report; mode HOLD/RTL keep the existing control path. Disconnect, heartbeat gap, boot regression and changed observed parameters/firmware invalidate cached authorization. PARAM_VALUE equal broadcasts do not renew freshness; changed broadcasts invalidate until a complete explicit re-read. No parameter writer or general profile editor is introduced.

Freeze the pinned definition/ref/hash, observation/context/comparison in new record-v2 headers and guard events. Validate by deterministic recompilation/evaluation; legacy record-v1 is readable with an explicit legacy scope. Neither imported snapshots nor operator review affect a live profile. Recovered records may expose missing/blocked snapshot without reconstructing history. No migration rewrites sealed records.

UI extends existing RtR white/black/yellow design with a compact disclosure in preflight. Read-only action, age and expected/observed rows explain blocked readiness without additional flight authority or LLM decisions. No hardware integration or native rebuild required.
