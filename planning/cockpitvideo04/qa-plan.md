# COCKPITVIDEO04 independent QA

Source/mock first. Runtime gates remain NOT_CHECKED until new actual evidence.

- **C01** Curated source/routing imports frozen flight, gateway and media algorithms; original sources/old pins remain exact. New host producer is never embedded or executed in Android. Verify: Source hashes/import graph plus receiver VM with forbidden local encoder sentinel.
- **C02** Explicit viewer start and lifecycle stop; late async start/capture after background cannot revive viewer or authority. Foreground and source selection never grant rights. Verify: VM races and counted command/authority callbacks.
- **C03** Snapshot/onCapture remains compatible: fresh decoded frame identity/time and payload target plus fresh flight telemetry are distinct provenance. Verify: VM snapshot identity, wrong feed/config, stale preview and capture-await revocation cases; no ACK/exposure claim.
- **C04** Video measurement captures exact flight run/boot once and never silently switches context mid-window. Verify: Wrong run/boot before save, reboot during measure and changed model/session must reject or mark unknown.
- **C05** Sidecar binds immutable raw report SHA, server/config/source identity and a distinct AP run/boot. Verify: Wrong SHA/path/source/AP identities, duplicate sidecar, missing raw/frame clocks and symlink/size refuse without accepted output.
- **C06** Measurement interval maps browser time to conservative host-monotonic bounds. Report exact overlap with actual AUTO/armed/ground observations and successful payload events. Verify: Boundary/interleaved wrong-run events, clock uncertainty, disjoint intervals and missing telemetry cannot become whole-window airborne or successful command proof.
- **C07** Flight fault validates current client, busy, action, scope and confirmation before effects; durable lease invalidation is awaited before owned AP reboot. Verify: Reuse final policy mock evidence with source binding; new app fork handlers inspected for order. Actual live lease requires runtime evidence.
- **C08** Actual unexpired lease is proven by pre-fault observation and durable pre/post receipt, not grant intent alone. Old actual bearer replay and invalid token/context negative tests are separately labelled. Verify: Later WAL seq/hash and monotonic TTL comparison, actual guest PID/boot/raw and zero accepted payload effects after fault.
- **C09** Native store/persistence/mission source stays truthful through host-origin routes, explicit save and review. No stale authority restored after restart/link loss. Verify: Actual Android store hashes/journal plus mission raw and UI evidence later; mock is not a substitute.
- **C10** Concurrent media and mission gates require a new measured 30s runtime window with complete outage denominator, unchanged clock/profile and all frames. Verify: Independent sample replay; separate source/display identities; first-config click-to-ready and fresh post-resume bounds.
- **C11** Nominal mission requires real generic AP SITL corridor upload/readback/Home/arm/AUTO/navigation/RTL/ground review with synthetic payload provenance. Verify: Raw independent verification; incomplete/faulted run remains not completed. No Hera calibration claim.
- **C12** Resource/cumulative evidence/source quotas, 2AP/2boots/2host caps and owned closure remain hard gates. Verify: Readonly admission/guard/closure SHA review. Any20GiB breach fails; no silent source retry or old evidence mutation.

QA owns only new qa-* artifacts, performs no live runtime actions and does not edit Builder source.
