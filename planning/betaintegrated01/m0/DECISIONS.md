# M0 decisions · Beta Integrated01

26/10/2026. Contractor decisions from source inspection, architecture audit and
cold recorder analysis. This does not mark a product requirement passed.

## Selected architecture

1. The final candidate has one Android-native flight/payload dispatch owner,
   derived from Native98 DirectTransport95/UnifiedCore98. Do not select its old
   APK as the new beta; emulator-only, endpoint, artifact and one-Activity fences
   must be replaced by new versioned, tested provider/session equivalents.
2. MissionBeta's Android Activity is workspace/SAF host-page brokerage; its host
   owns flight. Keep this as an AUTO regression, not a second live control plane.
   SIM-STABILITY03 TrainingLink is also a separate host writer. Host-reference
   tests are useful but cannot qualify the final native candidate by themselves.
3. Retain mission92's document/revision/model/plan/mission binding and portable
   offline parser pattern. Its current validator explicitly fixes Home/camera/
   synthetic-flat datum, altitude10–30m and speed0.5–2m/s. A versioned beta
   derivative must declare profile/source/datum/geometry envelopes; do not
   silently loosen the old fixture contract or call it generic terrain support.
4. Select Workbench planning/readiness/analysis as adapted functions. One owner
   per PlanEditor/Preflight/Fly/Review panel, backed by the same domain. Historical
   text-based UI projections are reference recipes, not the chosen final boot.
5. Select BetaVideo03 media algorithms/worker/native source as source input for a
   media-only companion. Exclude its whole host flight server from selected boot.
   Explicit materialized modules and manifest replace dynamic historical pin/exec
   dependencies before any new runnable release is allowed.
6. Independent operator B needs an authenticated ingress and aircraft/resource
   arbiter that routes to the selected native dispatch owner. Current clientB is
   a contract, NOT_IMPLEMENTED. Two local lease tables are not global ownership.
7. Retain SIM-STABILITY03 reference physics, manual handoff policy, read-only
   scene/audio and raw oracle. Do not copy its whole phone/server as the beta;
   that application explicitly lacks missions and camera payload functionality.

## Source and runtime closure are different gates

The M0 source-reference inventory pins inputs for adaptation. It is not an APK
build closure or a final executable allowlist. A narrow virtual Native98
Java/static-assets closure may bind missing protocol source to an exact Git body
in the new intake. No frozen or canonical path is restored.

M1 starts with explicit mock-only modules and an audited mock input allowlist.
Actual build/runtime has a separate pre-dispatch gate: all projections materialized,
source/runtime/data dependencies explicit, executable allowlist complete, provider
and AP/model/config identity coherent, signing/build artifacts pinned and target
observations collected. An unresolved executable or directory wildcard blocks
that gate. A conservative source-reference union is never evidence of zero
unlisted executables. M0 can hand off source/design safely without asserting that
the final integrated runtime already exists.

## Cold target-profile interpretation

`target-profile01.json` pins16 cached prerequisites and reports current tool
versions, macOS ARM/32GiB/10CPU, API33 ARM image and target1280×800/4vCPU/2GiB.
The AVD file defaults to2CPU, so launch must explicitly receipt the4CPU override.
Its `runtimeAPI` field is the cached-image target, not an observation from a
running emulator. WebView/GPU/actual codec are NOT_OBSERVED. They are mandatory
first-launch probes, before any flight grant, and must be pinned for qualification.
This resolves a planning sequencing ambiguity without claiming a live M0 probe.

Baseline Native98 AP011627… (internalquad) and SIM32 APf2be… (external FDM) remain
separate regression configurations. The new external trace artifact is REQUIRED,
its candidate SHA is null, and actual launch stays blocked until it is built,
pinned and checked. No replacement of either original binary is authorized by
this record. Physical Xiaomi/HeraHub remain NOT_CHECKED; paired LAN is disabled
until authenticated provider and security tests exist.

## M1 blocker ledger

| ID | Confirmed finding | New-beta disposition |
|---|---|---|
| I01 | AP fixed128MiB/2,097,088events; AP03/AP05 exited94 | Segmented/drained observer, versioned binary, capacity admission and independent verifier |
| I02 | Clock request map holds1024 forever (~341s) | Bounded pending/completed state with durable correlation and late/replay handling |
| I03 | Whole-session stage and append/fsync timing arrays grow | Stream exact per-frame timing, bounded summaries; no timing/frame sampling to obtain PASS |
| I04 | WAL768MiB/recipient2GiB/AP300s/host90min reference budgets | New candidate policy with requested-duration/space admission, no mutation of old policies |
| I05 | Native DirectTransport95 deadline900000ms and raw32MiB | Explicit native-session/run policy plus segmented raw admission; keep source epochs and durability |
| I06 | Closed elapsed recomputed from current clock | First terminal timing boundary persisted, later reads immutable; closing vs closed separate |
| I07 | Review navigation template mismatched current page | Observe current page/target; a harness error still closes owned runtime safely |
| I08 | Three different flight writers and incompatible bindings | One versioned native provider, regression-only host writers |
| I09 | Fixture-specific mission schema | Versioned derivative with explicit capability/profile/geo envelopes in M2 |
| I10 | Final UI/runtime assembled through source substitutions | Materialize explicit adapters; executable dependency gate before actual run |

## Boundary and budget decision

M0 is source selection/configuration/analysis. It starts no emulator/AP/container,
performs no native/AP/APK build and reads no signing key. M1-MOCK may develop
bounded writer/clock/closure/provider validation without running a vehicle.
Long-run admission is not justified by20GiB free alone. Cold sizing includes
assumed bitrate/copy factors separately and is not a formal upper bound or an
actual soak result. No evidence deletion, guard reduction, frame loss or speedup
change is an allowed shortcut.

The result should be described as READY_FOR_M1_MOCK when the M0 input contract is
verified. Final runtime closure, the whole M1 milestone and BETA-SIM remain
NOT_READY until their separate acceptance is executed.
