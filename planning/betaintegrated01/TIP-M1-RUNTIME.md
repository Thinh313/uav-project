# M1 runtime integration · 27/10/2026

User authorizes isolated adapter integration, a short Android–SITL check before
the 30-minute run, full frames, unchanged frozen source/candidate/ENDURE and
20/10GiB policy; no production signing. Development-only APK signing is within
the existing authorization and required for the owned emulator.

## Outcome and ownership

Contractor coordinates admission/executable closure, evidence, actual runner and
independent output verification. Builders implement scoped host/AP and Android
adapters. Independent QA reviews final outputs and performs mock/fault checks;
do not have multiple roles launch emulators/APs. Root alone authorizes launches
after reviewing concrete allowlist, budgets and mocks. Delegation is explicit
for these work packages, with no further hierarchy needed.

M1-MOCK's sealed files are immutable inputs. New implementation goes under
`pilot/betaintegrated01/runtime/`, `native/betaintegrated01/runtime/`; existing
foundation packages can be imported read-only. New plan/tests/receipts go under
`planning/betaintegrated01/m1runtime/`, `evidence/betaintegrated01-m1runtime/`.
Minimal new versioned AP instrumentation/build outputs may use
`runtime/betaintegrated01/`. No old path restoration, modification or replacement.

## Architecture and invariants

- Follow M0 selected architecture: Android-native sole MAVLink dispatch owner,
  external physics backend must not become a second flight writer. Old internal
  quad and external instrumented AP are regression inputs, not new candidates.
- Materialize precise runtime source/data/exec closure. No historical dynamic
  exec/wildcard executable resolution. Expected/observed AP identity, firmware,
  endpoint, model/config, run/epoch/boot and operator identity must agree.
- Adapt segmented journal, exact streamed stage costs and bounded clock behind
  real runtime seams. RX→INTENT fsync→sensor send→SENT/UNKNOWN remains.
- AP stage recorder must drain/segment without sampling/overwriting. New AP
  artifact requires source pins, format, independent decoder and differential
  evidence; old f2be/0116 artifacts unchanged. Single-writer vs multi-producer
  reservation/commit assumptions must be explicit and tested.
- Keep speedup1, cap500ms, full model frames and exact unchanged model replay.
  A local send, ACK, sealed segment or cold package never proves execution,
  publication, safe landing or power-loss durability.
- Native session must use lifecycle/provider adapter, no restored input lease,
  immutable closed elapsed and fencing old callbacks. New run requires confirmed
  resource closure. Do not erase old fences without replacement tests.
- Clock sender interval must fit 250ms freshness (propose100ms, bounded8pending),
  preserve exact correlation events, identify trusted wrapper inputs honestly.
- Emulator only: serial5582, cached API33 ARM,4CPU/2048MiB,1280x800/density160.
  Capture actual WebView/GPU/codec/API/AP/provider observations before grants.
  No real aircraft/physical provider/LAN/device or outside publication.

## Gates, budgets and stop

Window≤4h, implementation/fault cycles≤3 per repro family. New source/deps/build
forecast and run originals+copy+export must be explicit. No dependency download,
whole-project copies or SDK install. Cached toolchain/container image reused;
build scratch scoped/reusable and removed at completion. Never touch unrelated
processes, containers or volumes. Preserve failed run receipts; no auto retry of
uncertain flight dispatch, no lock deletion or campaign resume.

Entry20GiB, live floor10GiB+256MiB and15s forecast remain; request-size admission
can refuse even above20GiB. Global new runtime evidence≤3GiB/10,000 files; unit
evidence≤256MiB/2,000 files. Build peak forecast≤2GiB host (otherwise stop and
report to Contractor). Maximum4ownedhost/emulator starts and6AP starts total.
No starts by Builders/QA until Contractor accepts launch plan. Short check first;
5/15/30min only after prior acceptance, capacity and budget checks. No real host
disk filling, speculative memory pressure or altering guards to obtain PASS.

## Required reviewable outputs

1. Scoped source adapters and mock tests for real integration seams, versioned
   provider/run configuration and source/runtime executable allowlist.
2. AP artifact/observer format/source/differential or explicit blocker; no
   short internal-quad substitution sold as external candidate acceptance.
3. Development APK with build/signature/source closure; no production signing.
4. Independent mock/fault results and per-layer exact-frame cold receiver.
5. Actual short Android–SITL telemetry/session/journal/clock test with owned
   cleanup, then30min only if preceding gates/budget actually pass.
6. Honest final report: implemented vs wired vs actual tested, artifact identity,
   raw continuity, frame counts/jitter/clock, restart/closure, preservation and
   known gaps. M1/Beta remain NOT_READY unless their actual AC are satisfied.
