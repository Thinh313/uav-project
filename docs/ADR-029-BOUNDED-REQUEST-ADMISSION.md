# ADR029 · Partitioned fail-fast HTTP admission

A single loopback Node service currently admits every expensive request. Bound server-owned route classes without adding a queue or whole-body buffers. Observation and explicit control get separate capacities; heavy read/write overload is429 with connection close and Retry-After. Auth, mission review and storage controls remain downstream and unchanged. No new operator-command endpoint or runtime AI authority.

Slot release requires both handler completion and HTTP terminal state; network disconnect alone does not release in-flight validation/fsync. Request deadline destroys transport while retaining raw/incomplete/committed ambiguity for existing validators. Event-loop stalls remain externally bounded by RESOURCE18 watchdog. Existing stream.pipeline and export lease finally supply backpressure/reserve release. No claim of per-client fairness or hard CPU deadline.

Metrics use fixed bounded per-class rings, no raw URLs/mission IDs/caller labels and no unbounded telemetry log. Engineering test tools write their own scoped measurement evidence. Avoid cache of integrity-sensitive responses. Thirty-minute actual soak and controlled host thresholds are declared before run; unavailable longer/device gates remain explicit.
