# ADR028 · Bounded managed host runtime

Decision: extend the already digest-pinned UPDATE17 parent/IPC protocol. For candidates >=1.13, compile a path/port-specific Seatbelt policy in the external verified launcher. Fail on unsupported OS rather than fall back. Trust writer registration refers to the sandbox-exec process, which execs Node at the same PID. Child cannot write code/control/trust; parent retains ledger authority and writes immutable supervision receipts. Sanitize inherited environment to explicit runtime values; no key path is passed to child.

Use fixed V8 heap cap and an external ps/statfs/heartbeat watchdog rather than describing a heap cap as total process RAM. Bound failed shutdown and disable restart loops. Child observers gate new mutations; store quotas/reserve/fsync and replay remain the evidence commit authority. Current source preview explicitly lacks managed OS containment.

Use bounded Docker cgroup/tmpfs fault probes with existing simulator image (no data writable mounts, no install) to observe real kernel OOM/ENOSPC safely. These are isolated kernel probes, not measurements of AERIS performance or Android compatibility. MacOS managed candidate is separately exercised on the copied corpus.

Authorization: owner explicitly requested resources/isolation/fault recovery. No new dependency, system-wide configuration, SDK or external deployment. Single-agent self-verification, not independent review. Current published engineering sequence advances only after candidate canary; recovery never lowers sequence.

Verification refinement: missing-policy UI response incorrectly displayed OBSERVED_FIT. Repaired UI validation requires current observation/policy and boolean managed context; v1.13.1/sequence6 replaces selected5 through a new independently verified staged canary. Signed5/code/old generation retained. No in-place edit of signed artifacts.
