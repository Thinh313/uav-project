# INTEGRATION03: AERIS Integrated Alpha

2026-10-20. Personal Vibecode Kit 6.3. Contractor/root; implementation and independent QA assigned to the existing Builder and QA agents. User requests one substantial product milestone and authorizes continued isolated engineering development. Existing development signing and ADB/UIAutomator/root permissions apply only to emulator-5582. No production release, real aircraft, new SDK download or ENDURE launch.

## Product outcome and honest boundary

An engineer uses one Android cockpit to import and validate a survey mission, preflight, upload/read back, fly AUTO in ArduPilot SITL while an independently authenticated second operator controls synthetic payloads, inspect the same flight in a high quality 3D observer, then review/export an independently checked evidence package. Persistence/restart must retain evidence and restore no authority. This closes integration and reliability gaps, rather than adding another standalone laboratory.

This milestone unifies P2 and a bounded P3 vertical slice, plus the read-only visualization part of P4. Full manual/assisted training, external-physics 1× acceptance, collision/sensor-loss safety, calibrated Hera/load/battery/acoustics, real Phase One, HeraHub and production remain explicit separate gates. Do not label a 3D observer as a completed training simulator. Baseline CREW02 failed final preflight and lacked final SAF/coldboot/accepted-review proof; retain all failures. LLM baseline is not relevant to deterministic transport and geometry; comparative advantage against DJI/Ragas is unmeasured.

## Isolation and architecture decision

- New namespaces only: native/integration03, pilot/integration03, planning/integration03, evidence/integration03*, delivery/COMPLETION-INTEGRATION03.*. Baseline evidence/integration03/protected-baseline.json locks legacy, P1 and all CREW02 final files. No old source, canonical SOT, candidate, trust or ENDURE mutation.
- Prefer a pinned dependency/build overlay over a whole application copy. Old dependency bytes are read-only; new package vn.rtr.aeris.integration03. New Android key identity requires new public pin/admin receipt. Private keys stay outside evidence/APK/VCS; existing engineering B key may be reused read-only. No trust-all, TOFU or plaintext fallback.
- Android remains sole GCS and sole wire policy/WAL owner. Preserve mTLS, independent role/scope/CAS/consent, no authority restoration, generation-wide 1001 fence, command routing, full raw framing, fsync-before-transmit and speedup1. No hidden retries, expiry extension, dropped frames or forged clocks. A 3D observer never becomes another GCS.
- QGC intake is a distinct versioned source, retaining original bytes and semantic document, not a lossy KML disguise. Existing KML/corridor compiler is reused. Unsupported fence/rally/terrain/complex/unknown executable semantics must be explicit read-only/refusal, never silently stripped. Existing camera/Home/datum/geometry oracle code may be reused read-only and independently invoked.
- Full-quality 3D uses pinned licensed visual56/Three assets read-only through an owned loopback observer. New live data channel is bounded, read-only, same run/plan identity, source age and stale handling; no physical execution or camera imagery inferred from ACK. Audio opt-in, rotor/RPM estimate explicitly synthetic, no calibrated SPL claim. No new assets/install/download. Android may use lightweight lazy tier only if budget permits; host/projector is the mandatory high-quality observer tier.
- First repair stage instruments native receipt/WAL/queue/JS continuation/next-intent using separate clock domains and bounded ring metrics, without per-metric fsync on the hot path. Measure baseline, remove demonstrated redundant presentation/continuation work, keep a forced >3000ms cohort adversary failing. Never extend cohort3000ms or restamp first receipt. UI Home/AUTO eligibility and actual handler share the same conditions and explicit reason, without automatic refresh/arm/AUTO.

## Mandatory acceptance matrix

| AC | Required outcome | Independent evidence |
|---|---|---|
| I01 | Cause-oriented preflight repair, type/freshness and 3000ms guards unchanged | Stage trace; fixed aged-history baseline/repair comparison; 3 successive declared cohort trials including owned load; forced-stale/type/over-span adversaries fail closed |
| I02 | KML polygon and corridor plus supported QGC simple-survey intake into one model | Held-out originals, retained bytes/digests, round-trip semantic diff; independent geodesic/Home/datum/camera oracle; unsupported inputs refuse operational upload |
| I03 | Final Android composition nominal AUTO mission with active independent B and accepted review | Native raw + independent AP observer: preflight, exact upload/readback, explicit fresh preflight, post-arm Home, AUTO/NAV/ground/disarm; review raw binding and full/compact truth |
| I04 | Multi-payload exact routing and dual-operator transfer | A device1 pitch/yaw on wire; recipient B explicit consent then capture in the same accepted session; front/center/rear camera targeting and B device2; request/ACK/execution kept distinct |
| I05 | Real B partition and pilot loss fail closed | B pending action UNKNOWN/revoked within3000ms+250ms; fresh rejoin without rights; A stays active in B-only loss; A foreground loss stops common heartbeat and observed AP failsafe/ground; no auto reconnect/resume |
| I06 | High-quality read-only live 3D observer of actual native flight | Same run/plan/pose source identity; raw vs pose/axis/quaternion checks, source stale/disconnect indicator, bounded frame/latency metrics, opt-in estimated audio; no fabricated terrain/camera/physics claim |
| I07 | Correct selected-run raw SAF export and independent receiver | Visibly verify selected run before export; provider/stage exact hash, receiver/run/nonce/snapshot checks; corrupted/wrong receiver/run rejected; raw/peer audit/source/public policy hashes bound |
| I08 | Final app process restart and emulator coldboot preserve evidence, no rights | Private before/after hashes, closed journals, fresh boot/session and no grants/pending replay; older protected app private baseline retained |
| I09 | Usable final UI | Survey/preflight/Fly/review, both operator selection/ownership, correct stale/Home reasons, blur-glass alignment, no P0/P1 overlap/inaccessible required controls at1280×800 and companion/projector; screenshot + actual interaction |
| I10 | Reproducible preservation and managed closure | All protected hashes before/after, source/dependency/APK/devcert pins, bounded resource receipts, owned PIDs/listeners/containers closed; no outstanding mandatory AC or P0/P1 |

Mock, real Android, actual SITL, independent decoding and visual inspection are separate evidence classes. No count or elapsed time substitutes for an outcome. READY only when all mandatory AC pass; otherwise NOT READY with retained cause and exact remaining gate.

## Resource admission and bounded work

User floor is20GiB, not a universal26GiB admission. Before each phase record actual free space and bounded maximum new writes plus shutdown and external-drain allowance. No new SDK/AVD image. Cached Android13/API33 AVD only. Do not delete evidence or third-party/user data.

- Offline source/mock/build phase: ≤160MiB new source/artifacts/staging; reuse one owned build staging and clean it after each build. Retain signed development APKs; delete only task-owned unsigned duplicates after entry equivalence. ≤3 causal builds before Contractor reassessment.
- Android/SITL integration phase: forecast ≤768MiB new raw/SAF/private copies/AVD growth in aggregate, plus512MiB shutdown/external-drift margin. Admission = floor + remaining phase forecast + margin, evaluated live. Guard at21GiB for graceful owned closure, never knowingly write below20GiB. Guard samples are sampled evidence, not continuous global-free proof.
- At most3 planned new SITL windows≤900s each (nominal polygon, nominal corridor/B partition, A-loss). Causal failure stops dependent flight; repair/retest requires recorded Contractor budget decision and preserved failed evidence, never automatic run retry. Observer and B ≤128MiB Node heap each; AP2CPU/512MiB, Android2CPU/2048MiB. No external SIM32 physics campaign in this milestone.
- Root owns runtime/ADB launch/stop and final acceptance. Builder may run bounded offline mocks/compilation after baseline PASS and this TIP; announce source ready before APK build. QA owns held-out corpus and independent disposition; no production edits. Independent work may run in parallel without extra agents.
- Task graph: preservation → trace/mock/repair → shared intake/model + observer → independent held-out → final build → preflight cohorts → Android/SITL nominal/fault → SAF/process/coldboot → full preservation/closure/fingerprints/Completion. New failures do not erase earlier proof or silently lower gates.

## Delivery

Completion/Verify states user outcome,10AC coverage, scenario pass/fail/untested, technical health, value evidence, source/APK/runtime pins, actual resource use, limitations and READY/NOT READY. Hardware/P5/P6 and fullP4 remain separate. Do not report DONE from source presence or an attractive screen.

## Pre-source clarification01

Supported QGC simple survey means executable SimpleItems. ComplexItems, fence/rally or unknown executable semantics remain review-only/refused; extension bytes retained. Full-quality observer engineering configuration: foreground1280×800, pinned visual56 GLB/HDR/shadows,30s RAF sample with p95≤33.4ms and p99≤100ms. Native-source pose age nominal≤1000ms, stale indication after1000ms and no unbounded motion after2000ms (may hold clearly labelled last pose). CPU/RAF measures do not certify GPU present time or commercial display performance. These are Contractor engineering gates fixed before implementation, not customer signoff.
