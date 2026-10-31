# SIMTRAIN52 foundation — PARTIAL product delivery

15/10/2026. Approved plan remains unchanged. New implementation is isolated in `pilot/simtrain52`, `evidence/simtrain52` and separately budgeted `evidence/simtrain52-probe`; ADR065 records resource-gated sequencing. Single-agent specification → implementation → verification, not independent review. No completion percentage or council-ready claim.

Implemented a localhost WebGL2 training-yard preview, four-rotor reference model, close/range/top cameras, metric geometry, lighting/mist preview, recorded reference physics playback and RPM-derived audio. Separate keyboard input monitor implements calibration, dead zone/expo/invert, neutral-first, identity/session/boot/source/sequence/time fences and mode request/ACK/observation separation. No input moves the aircraft or reaches an autopilot. Manual/Guided/AUTO live routes remain absent and disabled.

## Verification

| Scope | Actual result | Evidence |
|---|---|---|
| AC01 inventory/admission | Host observed; small foundation admitted. G0 partial, actual projector/gamepad not checked. Initial short-live budget failed; later space increase admitted a bounded idle probe. Full workload not admitted. | `evidence/simtrain52/admission1.json` |
| AC02 input contract | 50 mock checks pass; malformed packet immediately zeros held input; 200 ms stale guard retained. | `contracts3.json` |
| AC03 offline oracle | 7,200 consecutive 1,200 Hz frames, three fixed-PWM cases; original sensor and auxiliary snapshots verified on readback. No skipped physics steps. | `model1/receipt.json`, `verification3.json` |
| AC04 scene/audio preparation | Art/reference playback implemented; no collision, Hera mesh/calibration, rain dynamics or live AP. High-end visual/performance acceptance remains NOT_CHECKED. | `browser4/*.png`, `pilot/simtrain52/scene.mjs` |
| AC05 browser/isolation | 35 functional checks pass on final code: WebGL2 draw, layouts, scope labels, input/ACK/observation/blur, replay end/mute, no flight mutation route or external asset requests. ANGLE Metal reports Apple M1 Max. | `browser4/receipt.json` |
| Protected data after incident | 20,249 SHA entries and 5,051 ENDURE path enumeration match after exact-byte restoration. | `verification3.json` |

Browser1 failed at the mode-request/ACK check; that run did not capture enough state to establish the cause. Its failure is retained. Diagnostic instrumentation was added. Browser2 passed; browser3 checked the malformed-input correction; browser4 checked the final independent-scroll cockpit layout. Later passes do not erase the initial failure or establish absence of transient timing faults. Stale input still revokes rather than extending authority.

Only renderer submission time was observed; it is not GPU completion, frame pacing, 60 FPS or physical projector acceptance. No acoustic listening/SPL or calibrated Hera flight response claim. Basic visual inspection of captured desktop/mobile views is not the planned three-person M05 rubric. All 25 full requirements and all 17 integrated scenarios remain unaccepted; individual preparation is mapped in `progress2.json`.

## Protected-path restoration incident

Initial baseline was present. Final verification1 found 121 absent paths, all missing rather than changed bytes, including fonts, old release packages, prior captures and retained packages. Cause remains UNKNOWN. Under the user's repeated exact-SHA restoration authorization, 121 paths (80 unique hashes, 62.60 MiB) were restored with exclusive creation from existing peers whose bytes match the original SHA. No reconstructed evidence, historical receipt edits, new signatures, trust selection or campaigns. Restoration plan, per-file fsynced journal, result and failed verification1 remain in `evidence/simtrain52`. Verification2 confirms current content/path matching. **Original paths were interrupted; uninterrupted presence is not claimed.**

New foundation source/evidence allocated about 17.3 MiB before the small completion/manifest additions, below the 32 MiB budget. Restored historical bytes are recorded separately. No project copy, dependency install, APK/emulator launch, Docker build, temporary scratch directory or unrelated deletion. One bounded new idle SITL instance ran after resource admission; its backend/container closed. No new image was pulled or built; required dangling-image prune reclaimed0B, never volumes/containers. The owned read-only preview remains at `http://127.0.0.1:8806/`; no old preview was restarted.

## Bounded idle ArduPilot probe

Under prospective TIP-SIMTRAIN52-IDLE-PROBE, resource observation2 (22.93GiB free) admitted one bounded probe with a separate256MiB evidence ceiling/1.5GiB peak reserve. An isolated pinned AP instance exchanged4,800consecutive servo/sensor frames at1,200Hz, speedup1 and cap500ms. No arm/mode/mission/RC command or published MAVLink port. WAL intent was fsynced before each local send; all4,800sensor+aux snapshots match the immutable original on readback, and each admitted frame has matching AP receive/parse stage events. Owned backend/container closed, state/raw retained. See `evidence/simtrain52-probe/idle01/readback.json`.

Measured idle receive RTF1.00259 over3.989host seconds does **not** establish G1. Receive gaps p95=6.276ms, p99=7.166ms and max22.515ms show burst/jitter that a whole-run average hides. Clock observer retains11fresh matched offset brackets and2startup timeouts; bracket widths p95=.869ms, max2.337ms. No exact host–guest point-clock conversion. AP frame4800 is an unadmitted shutdown tail; only0–4799are answered and counted. No active UI or controlled-flight load, no physical/Hera validation. This is G1 preparation, not a replacement for manual/assisted/AUTO acceptance.

## Next required action

Complete the isolated AP/backend→UI adapter with frame/session/boot/freshness contracts; couple input→ArduPilot→physics→render, then test default1× and jitter with active UI and controlled workloads. Preserve speedup1/cap500ms, journal all admitted frames, keep host/guest clock brackets and managed shutdown. Do not unlock front-end flags to stand in for the missing adapter.

Free space rose during this task; latest observed capacity exceeds the short-probe minimum, so initial storage blockage must not be presented as current proof. Full workload is still unadmitted: the conservative18minute raw/WAL/media/export worksheet requires39.32GiB free. The28GiB recovery request is a preliminary target, not full-campaign admission. Fixed AP observer/WAL capacities also require a retention design before a long integrated campaign. No new campaign starts from this short probe.

After actual G1 acceptance, proceed G2 manual/assisted/takeover, G3 AUTO survey/corridor and camera/review, live art/audio integration, instructor faults and the integrated/council gates. No full flight simulator or customer training readiness is established by this delivery.
