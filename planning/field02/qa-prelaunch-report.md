# FIELD02 independent QA prelaunch handoff

22/10/2026. Separate Contractor QA agent; this is not human certification. Writes confined to `planning/field02/qa*` and `evidence/field02/qa*`. No Android/SITL/UI launched by this agent. Own HTTP checks used only8892/8893, then closed both listeners and WAL writer lock.

**Source and selected mock gates pass; Android/SITL/SAF mandatory live gates remain NOT_CHECKED by this review.** Current source hashes and every disposition are in `evidence/field02/qa-prelaunch-source-review01.json`. An updated source outside these hashes requires targeted recheck, not borrowing this verdict.

## Independently generated checks

| Evidence | Selected result | Actual scope |
|---|---:|---|
| `qa-client-session02.json` |10/10PASS| Volatile client epoch policy with injected monotonic clock; executed by Builder from QA-authored test, no Android |
| `qa-http01/results.json` |10/10PASS| Real FIELD02 HTTP/app/store lifecycle, wrong origin/CSRF, stale TTL, replaced epoch, closure; no flight connection |
| `qa-bootstrap-races04.json` |3/3PASS| Actual bootstrap in VM with controllable HTTP promises: pause during activate/heartbeat and nominal pause |
| `qa-flight-epoch01.json` |4/4PASS| Actual flight policy with mock link: background/replaced epoch denies a pending write; rejected concurrent request cannot rebind old operation; wrong binding/confirmation creates no cut |
| `qa-receiver01/results.json` |14/14PASS| Readonly retained FIELD01 delivery seed, independently altered TAR/sidecar/index, fully rehashed false run/boot/model/plan/coordinates, duplicates/truncation/replay; not FIELD02 flight or SAF |

These groups overlap at the contract level and are not added into a product-quality percentage.

## Findings and targeted repairs reviewed

- Stale flight groundspeed had a separate display predicate. FIELD02 now uses the same freshness/run/boot predicate for map, height, speed, distance and mode. Visual Android evidence remains required.
- The original bootstrap dropped background while foreground HTTP awaited. `qa-bootstrap-races01/02` retain the real failure on old source. Current queue gives background priority and rejects local client context immediately. `qa-bootstrap-races03` was an insufficient eight-microtask VM harness wait; selected04 uses a bounded host event-loop drain and passes, rather than relabeling03.
- Mutable global flight client context could be replaced by a rejected concurrent request. The operation now captures/freeze its own epoch only after busy admission. QA mock-link tests prove zero wire writes when the old operation resumes after revocation.
- Native `onPageFinished` now sends actual foreground state; it no longer unconditionally activates while background. Native import captures the host head before opening picker and refuses a changed head before CAS/save. These are source-reviewed, not yet Android runtime accepted.
- Host artifact links originally passed relative paths to a native exact-origin validator. UI now passes a full localhost URL on both raw/capture and combined delivery paths; native policy stays strict. No APK rebuild required for that host UI repair. Actual SAF picker/readback remains required.
- Combined delivery index defaults now match the FIELD02 sender/receiver used by host capture packages. The FIELD01 schema identifiers and raw row names are intentionally reused. A new FIELD02 archive must still pass the separate receiver.
- Runtime minimum admission duration now matches31 one-second samples (>=30seconds). Source review does not replace a live disk admission receipt.
- Actual reboot means an owned guest AP process restart with changed PID/StartedAt, retained ownership and no automatic reconnect. Post-reboot MAVLink boot is explicitly unobserved; do not call it a physical FC power cycle or successful mission continuation.

## Remaining live proof required by TIP

Actual Android full polygon/corridor touch journeys; independent encoded network frames rendered on Android; payload/capture correct feed and flight raw; video fault without blocking C2/WAL; actual SITL cut/reboot with incomplete review; persistence/restart with no authority; SAF save/import/readback and receiver exact byte/context acceptance; final protected fingerprints, disk and process closure. Android WebCodecs capability must be measured, with any fallback declared separately. No desktop frame-rate result may substitute.

No LLM runtime is used here, so no LLM superiority baseline is invented. Operator effort, commercial advantage, physical Hera/camera fidelity and production suitability remain unmeasured.
