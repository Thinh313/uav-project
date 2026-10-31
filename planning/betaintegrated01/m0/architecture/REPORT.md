# M0 architecture and route audit

**Static audit complete. Final architecture proposed; beta integration is not implemented or qualified by this report.**

## Main decision

Use a Native98-derived Android shell and shared native flight/payload dispatch for the final beta. Reuse mission92/offline94 portable document/parser/compiler at its boundary; adapt Workbench planning/analysis, BetaVideo03 media and SIM-STABILITY03 physics/lifecycle/manual behavior through explicit contracts. Keep the original applications frozen and available as reference cases, but do not select multiple flight writers in one run.

MissionBeta01 is a useful actual AUTO/workflow baseline, but its Android Activity only brokers host pages/workspaces/SAF. The host owns the live MissionLink. This differs materially from the final controller goal and must be stated rather than treating both as equivalent native flight implementations.

## Source-backed paths

- **ROUTE_NATIVE_FLIGHT**: Native98 bundled cockpit.mjs → Controller82.host → Controller95.action/DisplayLink84 → Socket95/native95 → Native82Bridge direct95 request → DirectTransport95/UnifiedCore98 → native TCP5937→AP. Evidence A01, A02, A03, A04, A05, A06, A07, A08, A10, A14.
- **ROUTE_MISSIONBETA_FLIGHT**: MissionBeta Activity loads localhost8896 → projected Workbench mountBeta → fetch /api/beta/flight → host session.command/connectOwnedSitl → MissionLink port5984 → host TCP→AP. Evidence A16, A17, A18, A19, A20, A21, A22, A23, A24, A26, A27.
- **ROUTE_SIM_MANUAL**: phone cockpit GatewayClient → POST /api/action → host TrainingLink manual authority → simtrain53 base port5870 → AP external reference physics. Evidence A41, A42, A43, A44, A46.
- **ROUTE_VIDEO**: BetaVideo03 publisher worker → macOS synthetic native encoder → host media relay8895 → Android WebView video-worker → viewer clock/trace window → saved report + seal/qualification. Evidence A35, A36, A37, A38, A39, A40.

## Retain/adapt/retire decisions

| ID | Area | Decision | Selection and required repair |
|---|---|---|---|
| D01 | Android shell/transport | ADAPT | Native98 ShellActivity, DirectTransport95, UnifiedCore98, NativeSend98, RawJournal95 and existing SAF/store components. Create new package/origin/provider context in isolated beta; versioned session lifecycle, trusted pairing and committed mission/boot binding; retain all current safety fences until replaced by tested equivalents. |
| D02 | Mission model/compiler | RETAIN_AND_ADAPT | mission92 document/binding and offline94 portable KML/compiler as native boundary; Workbench01 core geometry/readiness/analysis as explicitly adapted functions. One canonical selected document; one audited conversion from Workbench plan schema; preserve plan/model/mission digest relationships and independent roundtrip/geo oracle. |
| D03 | Cockpit ownership | ADAPT | Native98 cockpit surface/layout85/layout86, Controller82-derived single page/domain owner; Workbench form/editor behavior extracted through a new explicit component API. Single PlanEditor, PreflightPresenter, FlyPresenter and ReviewPresenter backed by the same mission/flight state. Retire mock animation for actual modes; replace brittle runtime text projection with pinned explicit adapter/component assembly. |
| D04 | Host simulator lifecycle/physics | RETAIN_AS_REFERENCE_THEN_ADAPT | Exact9-file SIM-STABILITY03 overlay, pinned external reference physics, runtime/projection and durable review behavior. M1 may use the host reference writer only in an explicitly reference-only test configuration. Final beta host owns AP/FDM/recorder/faults but must not concurrently write flight intents when native provider is selected. Port neutral-handoff/session policy behind the native FlightProvider contract with fresh qualification. |
| D05 | Media | RETAIN_AND_ADAPT | BetaVideo03 publisher/worker demand and shutdown, viewer/decoder worker, clock/full-trace/independent oracle functions. Extract a media-only companion API; explicit manifest replaces hidden historical-pin dependencies; native WebView origin/worker routes and actual trace-sealing state repaired/retested. Record synthetic source identity; actual codec backend stays unknown until probed. |
| D06 | Payload/crew | ADAPT | UnifiedCore98/PayloadCore97 native dispatch plus existing crew/session contracts and independent-client corpus. Define one resource authority service per aircraft/session; B authenticates independently and submits per-payload intent through an explicit ingress to the selected native dispatch owner. Broker role/scope must never grant B flight control. Pilot/background/loss fences invalidate pending B dispatch. Verify manager/device ownership and contention independently. Do not combine unrelated local leases as global authority. |
| D07 | Observer/3D/audio | RETAIN_AS_READONLY | SIM-STABILITY03 observer/scene/audio and licensed assets. Bind same release/session/boot/clock, stale freeze/mute and actual visual/audio performance; no observer screenshot counted as camera exposure. |
| D08 | Prior applications | RETIRE_FROM_SELECTED_BOOT_NOT_DELETE | Keep MissionBeta01/BetaVideo03 whole-app launchers, Workbench standalone mock Fly and SIM phone cockpit as historical/reference applications only. One candidate entrypoint/manifest; no fallback to a legacy app or hidden old launcher when a candidate action fails. |

## Blocking seams, not finished functions

- **B01 / P1_INTEGRATION**: Three incompatible live-control owners. Select one provider/writer per run. Final target is native; host reference path remains labeled test-only until policy ported. (refs A07, A22, A43).
- **B02 / P1_CONFIGURATION**: AP/port/model identity mismatch. New versioned provider descriptor with exact AP artifact/config/model and authenticated endpoint; never weaken/rip out old guard. (refs A10, A11, A12, A14, A21, A44).
- **B03 / P1_LIFECYCLE**: Native one-shot Activity lifecycle. Explicit fresh session after confirmed closure, no authority restore, late callback fencing; keep failed raw immutable. (refs A13, A15).
- **B04 / P1_UI_INTEGRATION**: Competing UI controllers and projected text substitutions. One selected UI owner and model; replace runtime source surgery with exact adapter/component assembly and geometry/state tests. (refs A26, A27, A28, A29, A30).
- **B05 / P1_CLOSURE**: Hidden runtime file/projection/compiler dependencies. Closure includes literal fs/asset/pin/Python/native-binary dependencies, not imports alone; portable Android parser selected. (refs A30, A32, A35, A36, A37, A48).
- **B06 / P1_RUNTIME**: Current external manual slice does not implement missions/payload. Do not ship its whole app as the multi-task beta. Extract behavior/physics only, then actual native integration gate. (refs A41, A42).
- **B07 / P1_RECORDER_AND_TIME**: Closed elapsed and long trace failures remain. M1 recorder capacity and closure-clock repair with mock then bounded actual requalification. (refs A45, A48).
- **B08 / P1_CREW**: Local native policy is not global dual-operator authorization. M3 explicit independent-client ingress/resource authority; no unproven sum of local leases. (refs A07, A09).
- **B09 / P1_MEDIA**: Media source platform-specific and trace-seal UI incomplete. Pin exact encoder prerequisite; repair saved-window/sealing transition and test full selected workload; no camera-hardware claim. (refs A37, A38, A39, A40).

## Smallest coherent assembly

1. New native beta shell loads a single packaged origin and one selected controller; it retains native durable storage/SAF and direct-flight policy modules.
2. A FlightProvider descriptor binds AP artifact/config/model/endpoint and fresh session/boot identity. Existing ranchu/localhost/binary guards remain in legacy source; replacements live only in a new version with equivalent or stricter validation.
3. The final host simulator runs AP/FDM, sensor/camera peers, recorder, fault proxy, ground-truth observer and media. It does not expose a concurrently selected host flight-write controller.
4. Native-selected dispatch remains the only flight intent writer. Independent B submits only scoped payload intent through an authenticated, versioned ingress; global per-resource ownership must be implemented and verified, not inferred from local Native98 lease state. Broker deployment can migrate to controller/onboard hardware later without changing domain contract.
5. Workbench functions produce/inspect one selected mission document; a single presenter owns each Plan/Preflight/Fly/Review surface. Native92 vs Workbench workspace schema conversion is explicit and tested. No runtime string replacement becomes an undocumented product dependency.
6. Media source/decoder/clock/trace remain separate from flight throughput. Observer graphics/audio never control aircraft and never count as camera exposure.

M1 may preserve the proven host-manual path as an explicitly reference-only harness while recorder/lifecycle regressions are repaired. Passing that harness will not qualify the new final native provider. The ported native/manual path needs its own Android/AP gate.

## Evidence index

- A01: `native/native98/src/vn/rtr/aeris/native98/ShellActivity.java:12` — Native98 creates one Android bridge, unlike the NativeWB02 host-workspace shell.
- A02: `native/native98/assets/cockpit.mjs:173` — The native cockpit creates Controller82 after its own renderer initialization.
- A03: `native/native98/assets/runtime82.mjs:4` — Controller82 selects direct controller only outside its local planning branch.
- A04: `native/native98/assets/runtime82.mjs:27` — host(action) dispatches to the direct controller when selected, not necessarily a remote GCS.
- A05: `native/native98/assets/direct95/socket.mjs:4` — Direct JS adapter crosses the native storage/operation bridge.
- A06: `native/native98/src/vn/rtr/aeris/native98/ShellActivity.java:31` — The bridge routes direct95 actions to directAction95 on its I/O executor.
- A07: `native/native98/src/vn/rtr/aeris/native98/DirectTransport95.java:8` — One native DirectTransport owns a shared UnifiedCore for flight and payload.
- A08: `native/native98/src/vn/rtr/aeris/native98/DirectTransport95.java:10` — Native transport journals around the native send boundary; static code is not runtime fsync evidence.
- A09: `native/native98/src/vn/rtr/aeris/native98/UnifiedCore98.java:3` — Current core explicitly treats one native transport as serialized policy owner.
- A10: `native/native98/src/vn/rtr/aeris/native98/DirectTransport95.java:8` — Native endpoint is emulator-host-specific; it cannot be inherited as real-phone pairing.
- A11: `native/native98/src/vn/rtr/aeris/native98/ShellActivity.java:8` — Simulator launch assertion is currently restricted to the owned emulator hardware string.
- A12: `native/native98/src/vn/rtr/aeris/native98/ShellActivity.java:8` — Native98 pins a particular owned AP artifact; this is not the SIM-STABILITY03 external-physics artifact.
- A13: `native/native98/src/vn/rtr/aeris/native98/DirectTransport95.java:8` — Current generation is one-shot per Activity; lifecycle/reconnect must be implemented as a new version, not by removing the fence.
- A14: `native/native98/assets/direct95/socket.mjs:7` — JS adapter independently pins its emulator endpoint; both Java and JS bindings need a coherent provider contract.
- A15: `native/native98/src/vn/rtr/aeris/native98/ShellActivity.java:58` — Native background closes transport and payload; lifecycle behavior is explicit.
- A16: `native/missionbeta01/src/vn/rtr/aeris/missionbeta01/ShellActivity.java:3` — MissionBeta Activity documents that it is not the flight driver.
- A17: `native/missionbeta01/src/vn/rtr/aeris/missionbeta01/ShellActivity.java:10` — MissionBeta bridge owns workspace/SAF broker actions, not Native98 wire authority.
- A18: `native/missionbeta01/src/vn/rtr/aeris/missionbeta01/ShellActivity.java:11` — MissionBeta loads the localhost companion page; the selected WebView origin is not an APK-bundled standalone flight page.
- A19: `pilot/missionbeta01/server.mjs:5` — MissionBeta server owns the host flight/payload session factory.
- A20: `pilot/missionbeta01/session.mjs:38` — MissionBeta session opens a host-owned SITL transport in actual mode.
- A21: `pilot/missionbeta01/actual-transport.mjs:25` — Host AUTO session has another GCS link at5984 and internal-quad source label.
- A22: `pilot/missionbeta01/link.mjs:12` — MissionLink is an actual host socket writer, not a passive telemetry adapter.
- A23: `pilot/betavideo03/beta-client.mjs:8` — Video03 client sends its flight/payload action routes to the companion.
- A24: `pilot/betavideo03/server.mjs:68` — Video03 server calls session.command for flight requests.
- A25: `pilot/betavideo03/server.mjs:12` — Video03 still includes the host control session; media reuse must not retain that second flight writer.
- A26: `pilot/missionbeta01/ui-projection.mjs:7` — Projection replaces the Workbench mock Fly body with BetaWorkbench controls.
- A27: `pilot/missionbeta01/ui-projection.mjs:11` — Projection installs a second controller into the Workbench closure; it is an explicit integration seam.
- A28: `pilot/workbench01/ui.mjs:2` — Original Workbench has its own mock workflow owner.
- A29: `pilot/workbench01/ui.mjs:42` — Original Workbench Fly animation is scripted timing and must not drive actual AP pose.
- A30: `pilot/workbench02/project-ui.mjs:4` — Workbench02 assembles the current UI with pinned text substitutions; import-only closure scanning is insufficient.
- A31: `pilot/workbench01/core.mjs:28` — Workbench planning domain is reusable independently from its mock Fly renderer.
- A32: `pilot/workbench01/kml.mjs:3` — Workbench host parser spawns mapping51/kml.py, so it is not directly portable Android code.
- A33: `native/native98/assets/offline94.mjs:1` — Native98 already has portable offline KML parsing/compiler entrypoints.
- A34: `native/native98/assets/mission92.mjs:12` — Native98 mission document has explicit model/compiler binding validation.
- A35: `pilot/betavideo03/media-projection.mjs:2` — Video03 media service is a runtime source projection of older server code, not an ordinary static import only.
- A36: `pilot/betavideo03/media-projection.mjs:35` — Media projection reads a historical evidence pin at runtime; closure requires this pin or a deliberately regenerated beta manifest.
- A37: `pilot/betavideo03/native-publisher.mjs:19` — Native H264 source is a macOS host binary, a separate runtime prerequisite from the Android APK.
- A38: `pilot/betavideo03/native-publisher.mjs:7` — Publisher source is explicitly synthetic and platform-specific, not a real aircraft camera.
- A39: `pilot/betavideo03/viewer.mjs:27` — Decoder/render workload runs in a dedicated worker, appropriate to retain as a seam.
- A40: `pilot/betavideo03/media-panel.mjs:33` — UI collection and saved trace-window state jointly affect the ability to seal/qualify; reported blocker needs regression on the chosen revision.
- A41: `snapshots/simstability03/pilot/simhand01/server.mjs:31` — The SIM-STABILITY03 host explicitly does not implement missions.
- A42: `snapshots/simstability03/pilot/simhand01/server.mjs:71` — SIM config advertises its manual-only scope; it cannot be the complete beta mission/payload app unchanged.
- A43: `snapshots/simstability03/pilot/simhand01/link.mjs:10` — SIM reference link is a host-side manual control plane.
- A44: `pilot/simtrain53/link.mjs:11` — SIM reference host link uses an external-physics port different from the Native98/internal-quad binding.
- A45: `snapshots/simstability03/pilot/simhand01/server.mjs:30` — Closed-session time continues to derive from current now; repair is pending in a new revision.
- A46: `snapshots/simstability03/pilot/simhand01/link.mjs:21` — Manual neutral/mode handoff algorithm is a valuable tested behavioral reference, not directly Android-compatible code.
- A47: `snapshots/simstability03/pilot/simhand01/observer.mjs:5` — The licensed scene/audio observer is explicitly read-only.
- A48: `snapshots/simstability03/pilot/simhand01/projection.py:43` — AP/physics execution is itself projected from simtrain53; source pins must cover the projection input and generated artifact.

## Limits and integrity

Read 29 existing files and recorded 48 source references. Every input SHA was rechecked before writing the report. No product module was imported or executed, no endpoint connected, and no source/candidate/ENDURE path changed. Reports are written only under the assigned new M0 architecture scopes. This is an architectural recommendation and static evidence, not runtime PASS, complete dependency closure, hardware integration or human/flight acceptance.
