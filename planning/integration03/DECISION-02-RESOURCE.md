# Resource decision02

2026-10-20. Contractor decision within the existing user authorization. User floor remains20GiB; no new user approval or deletion is required.

Preparation01 with the cached2048MiB emulator stopped cleanly at the21GiB engineering guard: minimum observed22,492,483,584bytes, above20GiB. No new app/AP/B/flight was started. The original receipts remain immutable. The emulator-correlated approximately2GiB transient was omitted from the forecast; RAM backing is plausible, not proven as the exclusive cause.

Preparation02 declares a different engineering reference: Android13/API33,1536MiB RAM,2CPU, same cached AVD, no snapshots/download. Startup admission is20GiB+1536MiB possible transient+768MiB remaining task writes+512MiB shutdown/external allowance=22.75GiB. Root must re-evaluate actual post-start remaining forecast before APK/AP/B. This is not a guarantee of the startup peak. QA independently checked this arithmetic and conditionally accepted the configuration.

Runtime shutdown guard becomes20.5GiB, explicitly replacing the earlier21GiB engineering reserve in this new namespace. The512MiB reserve includes≤8MiB shutdown receipts and a bounded≤40second owned emulator shutdown. Unknown/unbounded external writes are not guaranteed against. Every controller uses this guard; a sampled guard does not prove continuous global free space. Source/candidate/ENDURE/CREW02 and product freshness/durability/authority/performance gates are unchanged.

Actual postboot observation02 is retained, not turned into an arbitrary quiescence requirement. All UI/performance results must disclose1536MiB reference. No automatic1024MiB fallback or expiry relaxation. Three final SITL mission windows remain the cap; a diagnostic-only preflight window would require a separate causal decision.
