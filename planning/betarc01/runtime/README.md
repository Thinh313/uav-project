# BETA-RC01 isolated runtime

Implementation and mock handoff, **not Android/SITL or Beta acceptance**. Root owns all actors, admission, freeze/signing and final independent cold replay. The user authorized four gates in `../TIP-ADR.md`; all old source/candidates, ENDURE and public/private handoffs remain immutable.

## One selected runtime and four gates

- `root-native-rc01.py`: G1, slots g101/g102, original N02 adoption without install, explicit migration, two UNUSED native sessions and persistence. Its descriptor retains `nativeOnlyScope17`; AP, flight and payload remain refused. The original unknown N02 install is never relabeled successful.
- `archive/root_maintenance_rc01.py` (one directory above runtime): m101/m102 and m201/m202, cold controlled archival without Activity/new journal/AP. Uses the same WorkbenchRuntime/guardian/budget and a separate positive maintenance closure. Old receiver-only assertions cannot qualify used input history.
- `root-owner-rc01.py`: polygon g201/g202, corridor g203/g204, link loss g301, AP reboot g302, native restart g303/g304, integrated g401/g402. The same original owner, single transport writer, source-bound native input and managed drain remain.
- `scenario-rc01.py`: public Android controls, native touch and SAF. Polygon/corridor are selected through the real UI. A long760s resource slot requires a continuous600s airborne/video/payload interval, with manual input, release to HOLD and explicit payload checkpoints. Bootstrap/export/idle time cannot satisfy it.
- `acceptance_rc01.py`: G2 requires same-release G1; G3 requires G1 plus both shapes; G4 requires all prior gate kinds plus the original short-flight seven-role prerequisite. Final metadata completeness includes all seven kinds; neither metadata nor wrapper exit certifies original raw acceptance.

## Native lifetime accounting

All active/archive/index/control bytes and lifetime counters remain charged. Source-held remaining-generation plans plus a two-generation repair reserve cannot be lowered by CLI. Proposed finite schedule: G1 two UNUSED, explicit archive; polygon2 + corridor2, explicit archive after genuine original STATUS/ACK/P256/clock/RC replay; link1 + AP reboot1 + native restart2 + integrated2 = six active, with two reserved. A generation left unresolved by a fault cannot rotate. A missing archive/source proof or exhausted bound stops before Activity.

The Root storage-anchor is an external expected digest, not a substitute for byte replay. `qualify_existing` observes PRESENT APK, original package SHA, cold complete TAR, current archive/index and source capsules before admitting Activity. There is no install branch in the RC selected-app path. Full-flight native verification uses `VERIFY_NATIVE_INPUTS` with the current archive proof, never the UNUSED verifier.

## Expected faults

Link loss writes one source-scoped fresh cut request, closing the actual native/AP sockets without retransmission. AP reboot requests termination/drain of the positively owned original child. It never starts a replacement in the failed clock/frame context. A separately admitted `root-observe-reboot-rc01.py` r301/r302 context starts the same guarded backend/AP with no Activity, companion, command writer or grant. Its dedicated pinned receive-only intervals include GLOBAL_POSITION_INT33/SYSTEM_TIME2, so original CRC heartbeat and an actual AP boot-ms observation are required. Its new state path is explicitly cold-config, without `-w`; EEPROM/onboard-mission retention is not claimed, and the old state is not modified. A new PID or Root `newAPBoot` label alone does not prove observed AP boot-clock regression. Empty mock output deliberately produces no heartbeat claim.

Native restart requires original client-loss revocation before enrollment of a genuinely new process/epoch/key. A new UI may explicitly activate observation and close a fresh-ground interrupted review; it does not restore the old input/flight grant. Link/AP interruption uses the existing explicit incomplete abort UI. These cases terminate with FAILED/UNKNOWN physical drain plus an interrupted review; their cold fault-test acceptance is separate from a nominal mission PASS. Existing health, freshness and require_alive guards are not suppressed: if they stop before product response is observed, that case remains NOT READY.

## Mock checks only

From the repository root, these create no Android/AP process:

```sh
python3 -B planning/betarc01/runtime/test-runtime-rc01.py
python3 -B planning/betarc01/runtime/test-journey-rc01.py
python3 -B planning/betarc01/runtime/test-adoption03.py
python3 -B planning/betarc01/runtime/test-tar-shape03.py
python3 -B planning/betarc01/runtime/test-writer-order02.py
python3 -B planning/betarc01/runtime/test-native-contracts-rc01.py
python3 -B planning/betarc01/runtime/test-reboot-rc01.py
python3 -B planning/betarc01/runtime/test-maintenance-close02.py
```

The suites overlap and include static assertions, orchestration models, real filesystem/OnceStore and no-child Popen pipes. The maintenance regression couples the actual ResourceMonitor and shared ledger with actual close_maintenance: it retains CLOSED_NO_ACTOR_NOT_ACCEPTANCE/durablyDrained=false and proves no monitor thread or lease existed, rather than inventing a durable monitor drain. They do not qualify physical sensors, actual video intervals or flight safety. Temporary mock fixtures are removed.

Before HOLD only, Builder refreshes exact source/product/writer assets using `prepare-source-gate.py --node /usr/local/bin/node --write`; omit `--write` for read-only graph discovery. Do not refresh a held graph or source after freeze. Every additional selected old helper/asset is charged by inode to metadata unless it is already covered by the unchanged exact152 resource-role table; no new binary/vendor exemptions. The active scope is planning/betarc01 and evidence/betarc01; all11 artifact pools remain charged and new candidates append only within the existing E17 candidate pool.

Freshness250ms, HostHealth100ms, writer200ms, inputlease200ms, speedup1/cap500ms/all frames/fsync-before-sensor, disk10GiB+256MiB/forecast, artifact11MiB, metadata64MiB, native64MiB and exports192MiB remain unchanged. No SDK/dependency download or production signature. Actual launch requires reviewed candidate, source/guards/budgets, current power/disk/ports and explicit Root invocation with exact arguments; this README launches nothing.
