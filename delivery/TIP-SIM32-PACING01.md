# SIM32-PACING01 — offline trace diagnosis

Owner request13/10/2026: analyze existing traces to address default1× pacing; no new SITL below20GiB; preserve frozen source/candidate/ENDURE. Scope of this increment is offline diagnosis and a concrete next-experiment design. Even though current free capacity is now about43GiB, no runtime experiment is part of this task.

Sequential Contractor→Builder→Verify by one agent, not independent audit. Reuse project instructions/methodology; no dependency installation/build or whole-project copy. Current SIM32 source and all previous receipts also remain unchanged. New analysis scripts/receipts/docs only.

REQ-T01: replay timing fields from all7 selected raw traces; verify full uncompressed raw SHA, counts, servo sequence/rate, monotonic host intervals, declared launch pacing and exact-count RTF. Do not run a physics model or overwrite earlier receipts. Preserve previous inclusive-first-step RTF separately.

REQ-T02: derive receive-gap/physics distributions, model10s windows, ground/airborne and following-snapshot/disk-check cadence groups, full signed target-time accounting and tail counts. Respect alignment: previous frame work can influence next receive gap. Do not label gap-minus-step as network latency; do not use independent samples to claim causality.

REQ-T03: confront pacing/control-flow explanations with pinned source available locally and primary header inspection. Mark AP sleep/host scheduling/VM transport/GIL/cgroup causes unconfirmed without actual stage timestamps and paired clocks. Keep declared1.10 and default1 configuration results distinct; no clock scaling, frame skipping or hidden pacing change.

REQ-T04: deliver priority correction plan with required instrumentation, isolated future experiments and unchanged numerical/authority/evidence gates. No production edit, firmware build, new SITL, release/signature, Fly integration, ENDURE launch or cleanup of unrelated user data. Before/after preservation and analysis fingerprints required; every unrun gate NOT_CHECKED.
