# M1 isolated external-FDM runtime adapters

27/10/2026. This is new versioned integration source, not the frozen candidate.
The Android app is the sole MAVLink writer. This backend consumes AP servo UDP,
integrates provisional physics, and returns sensor JSON; it has no MAVLink API.

## Selected immutable bindings

- AP: `runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03`.
- Profile: `runtime/betaintegrated01/dist/run-profile02.json`; copy its exact
  bytes/hash into the versioned native descriptor, never mutate it for a run.
- New AP uses exactly the 74 cached Copter objects and cached library archive,
  replacing only the stage observer object. Static non-PIE linking matches the
  baseline; the first dynamic artifact is retained **NONQUALIFIED**. Version03
  removes a non-atomic sequence read from a producer-violation diagnostic.
- `physics.py` has only a package-relative native-kernel import change from the
  selected optimized source. Its derivative kernel is byte-identical intake;
  `physics_reference.py` is the exact original pure-Python model. Builder checks
  compare 1,800 sensor JSON outputs across nine load/wind profiles byte-for-byte.
  That is offline model equivalence, not a full AP flight-algorithm differential,
  calibrated Hera dynamics, or measured realtime throughput.
- AP flight/model/pacer objects are reused unchanged: speedup1 and the actual
  SIM_Aircraft 500ms catch-up cap remain. Performance is measured, not inferred
  from these configuration values.

## Bounded receive and recording contract

`FrameAdapter.receive(raw, peer, send, clock_read=...)` validates exact 40-byte
servo format, magic18458, rate1200, contiguous frame fromzero, PWM bounds and
fixed peer. It streams one RX/INTENT/SENT group plus one stage row per admitted
frame. INTENT is fsynced before `send`; local return is not AP execution.
An uncertain/short send retains UNKNOWN, never retries. Invalid RX has a bounded
sidecar with exact received bytes or an explicit socket-truncation prefix flag.

ClockSocket polls at100ms using the already verified bounded correlator, at most
eight replies per poll. Its hard total durable-event cap is
`(maximumSeconds+15)*120+100`; exceeding it preserves a diagnostic and fails.
Every frame requires a fresh250ms bracket both before model admission and after
INTENT fsync immediately before send. Stage rows bind clockID and exact check
age to a single persisted host monotonic origin. Relative timing avoids the
old int64 aggregate overflow from summing absolute host timestamps.

AP observer emits unchanged64-byte fields to an inherited bounded pipe, one
enforced producer TID and global sequence. Writes are atomic and wait at most2s
under backpressure; pipe/drainer death fails rather than dropping/overwriting.
The parent-owned drainer segments, hashes, syncs and seals complete records.
Terminal records bind AP exit, EOF and final sequence. A partial64-byte tail or
failed seal cannot produce terminal success. AP console is retained up to the
8MiB cap plus the complete offending read chunk (at most64KiB), then fail-stop.

## Root-owned launch protocol

Only the Contractor/runner starts runtime. Builders and QA start no AP or Android.
All prerequisite source/executable identity, actual Android observations and
20GiB admission/10GiB+256MiB live floor/15s forecast must pass first.

Create a new caller-owned output directory and config containing:
`run,epoch,boot,evidence` (host absolute path), `maximumSeconds:60`,
`bind:["127.0.0.1",9012]`, and the selected profile's `load,wind,seed`,
`requestedSpeedup:1,capMs:500,APSHA256,parameterSHA256,clockprobeSHA256`.

Host:
`python3 -B -m pilot.betaintegrated01.runtime.backend --config ABS/run-config.json`

Owned cached ARM container: readonly repo at `/work`, readonly selected dist at
`/candidate`, this run's writable output at `/evidence`, fresh owned state at
`/state`, cwd `/work`, TCP127.0.0.1:5961→5760 and UDP127.0.0.1:9014→9004.
Execute exactly:
`python3 -B -m pilot.betaintegrated01.runtime.ap_supervisor --config /evidence/run-config.json`

Supervisor starts only the pinned clockprobe, waits at most10s for this run's
host clock-ready marker, then starts the pinned AP. Backend continues refreshing
the bracket. Each actual frame has the fresh receive/send guards. The marker
does not authenticate an AP or replace native firmware/capability discovery.
The generated AP command fixes JSON host192.168.65.254, sim-port-out9012,
home10.854/106.807/10m, rate1200/speedup1 and exact copied parameter files.

Stop finishes an already admitted frame. The next datagram is retained explicitly
as unadmitted, allowing independent proof that prior AP frames consumed sensors.
After backend result appears, supervisor terminates its own AP promptly and
drains to EOF before closure, preventing pending-servo retransmit ambiguity.
This is simulator process closure, not LAND or safe-ground evidence.

Capture backend and supervisor **live stdout outside the raw package**. Only
after successful file/directory sync do they emit commitAnchor/terminalSHA256.
Never infer a trusted anchor by reading it back from an imported package.

## Cold receiver and capacity

`verify_capture(...)` first invokes independent journal/stage byte verifiers,
then replays every admitted sensor packet using the original pure-Python model.
It reconstructs clock raw56-byte requests/responses/brackets and checks stage
ages from the timing origin, exact AP stage order for each admitted frame and
strict context/magic/rate/model-step semantics for one pending unadmitted tail.
All verdicts keep publicationAllowed/APExecutionAccepted false.

`capacity.estimate()` uses declared enforced maximums: four2048-byte host records
per frame, ten64-byte AP events per frame plusone pending frame, the clock event
cap, and160MiB for128MiB native raw plus metadata/logs. It budgets simultaneous
original, independent copy and export. These are format bounds, not averages.
60s fits the3GiB task allocation;5/15/30min do not. A30min run must be refused
under current budget rather than running without copies, dropping frames,
weakening fsync or changing speedup/cap. Actual launch needs live admission too.

No hardware, acoustic fidelity, external network/source authenticity, physical
power-loss durability, sustained1× or completed M1/Beta claim follows from source
presence or unit tests. Runtime/qualification results are separate receipts.
