# ACCEPT13 · receiver acceptance and expanded end-to-end corpus

Version 1.8.0. Authorized by current user request; local engineering implementation. Single agent Contractor → Builder → Verify, no independent audit. No external release gate is invoked.

| REQ | Acceptance criterion | Required evidence |
|---|---|---|
| A13-01 | Expected manifest/record/source/profile/file inventory compared against freshly verified receiver bytes | core/service negative tests |
| A13-02 | Explicit accepted/conditional/rejected decision; scope acknowledgment, source review, reviewer declaration and note required; no physical acceptance from simulator evidence | unit + browser |
| A13-03 | Immutable chained decisions bind receipt, rubric and prior digest; restart and corruption fail loudly; original payload immutable | service restart/tamper tests |
| A13-04 | Same-origin/token API and stale plan/latest decision guards; no flight authority | API + wire checks |
| A13-05 | Wider bounded corpus: three BENCH06 cases plus three new safe survey polygons; compiler negatives and actual independent SITL completed flights and one interrupted run | frozen corpus + actual campaign |
| A13-06 | Each actual record → declared synthetic report/GeoJSON → streaming receiver → decision → identical re-export | end-to-end matrix |
| A13-07 | Missing/unexpected files, altered package, incomplete transfer, outcome/source/profile mismatch cannot yield accepted; interrupted case conditional only | adversarial tests + campaign |
| A13-08 | Visible freshness, history, equal controls, offline revocation and exported acceptance audit | browser at six viewports |
| A13-09 | Preserve prior history, protected storage and SOT provenance; bounded fixtures cleaned | regressions + kernel + cleanup receipt |

Expected contract is supplied by the recipient/operator, not automatically inferred as a client requirement from the incoming package. Exact metadata comparison is order-independent but duplicate-aware. SHA provides unsigned byte integrity only. Scope simulation-engineering is the only supported accepted/conditional scope. Physical capture, processing, coverage quality, signed reviewer identity, remote authentication, HeraHub/SDK/HIL and physical power-loss are NOT_CHECKED. Existing Home/editor semantics remain bounded. Dataset receipts remain byte-verification receipts, distinct from acceptance decisions.

Plans contain deterministic rubric and latest decision digest. Operator types first 12 characters of plan SHA. Decision publication recomputes fresh byte verification and rubric under store exclusivity; refuses stale plan, malformed history, incomplete/corrupt packages and pending cleanup. Metadata has bounded per-row and total history quotas. Accepted payload and acceptance audit remain protected canonical evidence under LIFECYCLE12; no deletion expansion.
