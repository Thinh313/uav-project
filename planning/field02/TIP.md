# FIELD02: Android integrated operator journey

Authorized 21/10/2026: implement the proposed FIELD02 milestone without Xiaomi or production signing. Vibecode Kit6.3. Contractor root specifies and verifies; separate native/host Builders implement; QA agent reviews source and counterexamples. Agent review is not human or hardware acceptance.

## Outcome and architecture decision

One Android development app provides KML polygon/corridor planning, canonical compile/preflight, explicit mission authority, SITL AUTO, independent network media and payload mock, durable review and Android SAF handoff. Existing FIELD01 is the technical baseline. The least new machinery is a strict loopback WebView client with an explicitly identified host simulator companion, not a rewrite of the frozen native-direct transport. This milestone must never be called a standalone Hera flight controller or native-direct MAVLink acceptance. No runtime AI is used: an LLM comparison is not applicable; user-effort/commercial superiority remain unmeasured.

New code only native/field02 and pilot/field02; planning/field02 and evidence/field02; own runtime state .local/field02. Read existing dependencies unchanged. No writes to FIELD01, PHONE07, old candidate/source/ENDURE/trust/SOT. baseline preservation-before01.json covers1,486 existing files with zero admission drift;95 Git-deleted paths already existed before this task and are not restored automatically.

Host control127.0.0.1:8872/media8873, Android reaches only explicit adb reverse; AP own container aeris-field02 loopback5972. Never connect any real aircraft. Stage only curated assets into own.stage, not a project copy. Cached Android emulator/system image and cached pinned ArduPilot only, no downloads/install.

Native: new package vn.rtr.aeris.field02. Only trusted main-frame loopback content may request SAF operations through bounded custom URI, no broad JavaScript bridge across media iframe. Native HTTP verifies immutable download SHA and SAF readback. Workspace mirror/import verifies schema/digest and host idle/CAS; no authority restoration. Lifecycle callback plus native background signal and host3s watchdog revoke permissions without automatically commanding/aborting AP. Foreground activation starts a new fenced client epoch, requires explicit flight/payload authority again. Session/boot/run/model/plan identities cannot silently switch.

## Required acceptance

1. Android runtime boot and truthful topology label; no placeholder telemetry or physical-camera claims. Native crashes/ART errors are FAIL, missing test is NOT_CHECKED.
2. Same saved KML model: polygon and corridor edit/compile/preflight/upload/readback/Home-after-arm/AUTO/ground/review on emulator with real cached AP. Camera item and datum semantics retained; unsupported input refused. No parameter writes.
3. Actual independent publisher→network→Android viewer decoded frames, with source/device/boot/config identity and freshness; selected capture binds correct feed and flight. Android WebCodecs capability is measured before codec choice. If unavailable do not call an in-process canvas network video; propose an explicit bounded implementation and preserve the original requirement or mark the affected AC NOT_CHECKED. Desktop FIELD01 timing is never copied as Android performance.
4. Payload mock discovery/selection/lease/readback/repeated command/capture during flight; stale/wrong target/loss/reboot/session ends revoke permissions. Video source selection never grants control. JPEG/thermal-look always synthetic, sensor exposure/GNSS accuracy unknown.
5. Actual SITL C2 cut and actual owned AP reboot while running: raw keeps source/PID/container/boot identity and incomplete conclusion. Distinguish a mock injection, a TCP cut and a guest AP reboot. Media failure/pressure does not block C2 or WAL. All displayed live quantities share proper flightFresh; no stale numeric speed after other fields become unknown.
6. Native lifecycle/process restart: verified saved model/plan/KML/media/reviews survive, no automatic reconnect/grant/AUTO. Interrupted/pending files kept, no silent evidence cleanup or false completed review.
7. Android SAF export/import: actual picker/save/readback, same exact bytes and independent receiver acceptance; tamper/truncation/replay/old-flight rejection. Import applies only idle verified mission under CAS, no rights recovered. A download on host is not SAF evidence.
8. Android touch workflow/UI on declared emulator size, night/day, dialogs/scrolling/focus, metric alignment; same main Fly shows source/age and review. Screenshot evidence, no claim every device/GPU is qualified.
9. Final resource/process closure and fingerprints: protected hashes unchanged; evidence within budget, host remains above20GiB; development certificate only, no production/ENDURE release action.

Mandatory AC failures or NOT_CHECKED prevent overall FIELD02 READY. Individual completed host/native slices can be reported honestly without declaring the complete milestone done.

## Budgets and order

Mock/source/receiver checks first. 31 stable admission samples at or above29GiB before combined emulator/SITL launch, staged build only with20GiB+declared forecast+reserve. Runtime guard21GiB, hard floor20GiB. Reuse cached image read-only and own bounded AVD; no old userdata mutation. New evidence aggregate512MiB; native/asset stage32MiB; APK16MiB; no whole project copies or dependency downloads.

At most2 development builds. At most4 new SITL attempts, each≤600s: nominal polygon, nominal corridor, real C2 cut and actual AP reboot. Any failed/aborted attempt still consumes one. No retry POST/uncertain command; no auto campaign resume; stop before arm if resource/source/session gate fails. Targeted code repairs are bounded to2 cycles per component; with no new cause, re-evaluate instead of looping. Controller/resource logs bounded. Root explicitly coordinates launches/UI to avoid concurrent control.

Native and host source packages may be implemented in parallel; source/API agreement and independent adversarial checks precede live runs. No build/emulator/SITL process without a recorded owned launch and source pins. Root may write verification scripts/docs but not production code in Contractor role.

Stop only owned processes/mappings/package/container; keep all evidence. Remove own build/stage/cache before delivery, prune dangling Docker images only (no volume/container pruning). Keep signed development APK and exact source manifest. No hardware, customer communication, external publication, production signing or new24h soak.

## Verify report

Record implemented/total9AC, scenario pass/fail/untested, P0/P1, actual Android versions/codec/clock/source configuration, raw/receiver findings, disk and process closure. Ready means only the defined engineering scope. Preserve all failed attempts and do not retroactively pass FIELD01 or old ENDURE evidence.
