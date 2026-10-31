# M1-MOCK clock and lifecycle foundation

This foundation is isolated and **unwired**. It has no Android Activity, socket,
transport, input dispatch, AP instrumentation or flight commands. Test evidence
applies to these pure logic classes, not to an integrated candidate or a physical
aircraft. Full M1 still requires its separately admitted build and actual run.

## Bounded clock API

`pilot/betaintegrated01/clock/correlation.py` exports immutable
`Context(run, epoch, boot)` and `BoundedCorrelator(context, peer, sink, **policy)`.
The sink must durably retain each event before returning. For a composed writer,
use `lambda row: journal.append_event('CLOCK', row)` **between frame groups**.
Sink failure poisons the correlator. It cannot return another calibration.

- `register(id, host_monotonic_ns, context)` records a request before publishing
  its pending state. IDs must strictly increase within a generation, including
  after bounded tombstone eviction. Exhausted uint64 requires a new generation.
- `receive(raw, peer, host_monotonic_ns, context)` accepts exactly seven little
  endian uint64 fields: request ID, guest receive/send monotonic ns, cgroup usage
  us, periods, throttles and throttled us. This is a mock application contract,
  not an authenticated wire protocol.
- `tick`, `invalidate`, `calibration` and `snapshot` expose timeout, failure and
  observation state. `calibration` returns `None` during bootstrap or after its
  freshness budget. Stale or retired packets never refresh a bracket.
- Request/response, rejection, timeout and retirement events stream immediately;
  no session-wide row array is retained. Exact well-formed packet bytes are in
  each response event. Rejected packets up to4096bytes retain bytes. Larger
  rejected packets retain length/SHA and explicitly declare bytes unretained;
  a transport raw journal must retain them if its corpus requires that evidence.

The host-minus-guest offset interval is `[hostSend-guestReceive,
hostReceive-guestSend]`. Negative width or guest send before receive rejects the
packet. This is a latency-derived interval, not a point estimate or UTC clock.
Monotonic observations and UTC wall clocks are not interchangeable. Foreign
run/epoch/boot/peer, uint64 overflow/bool/float values, clock regression, suspension
gap or guest discontinuity cannot produce fresh calibration. Matched reordered,
late and duplicate packets remain evidence with `freshCalibration:false`.

Response keys include `status`, `freshCalibration`, four clock boundaries,
`offsetLowNs`, `offsetHighNs`, `uncertaintyNs` and cgroup counters. Unknown/retired
IDs have only their status and `freshCalibration:false`, avoiding invented times.
Snapshot counters are copies: pending/recent/peaks, configured limits, journal
event count, failure and `calibrationState`. A caller must call `calibration(now,
context)` to establish freshness; snapshot never claims that a bracket is fresh.

Defaults are engineering policies, not measured Hera limits:8pending,
64recent,300ms timeout,250ms freshness,2s maximum observed host gap and50ms maximum
disjoint bracket step. They are configurable and bounded. All protocol times are
uint64 monotonic ns. `max_offset_step_ns` is a discontinuity guard, not a claim
about a remote oscillator's physical accuracy. Peer/context matching is structural
only and cannot authenticate or grant control.

## Pure Java provider and lifecycle

Package `vn.rtr.aeris.betaintegrated01` contains:

- `ProviderDescriptor`: immutable versioned expected mode/profile/AP SHA/model
  SHA/config SHA/endpoint/firmware and `validateObserved(Observation)`. Null
  unbuilt candidate hashes cannot produce a Binding. Internal baseline AP,
  external reference AP and a future candidate are distinct modes; neither known
  baseline can silently become a candidate. Endpoints are structurally restricted
  to explicit loopback/emulator TCP descriptors. No connection occurs. Observation
  is caller-supplied, therefore **not authentication or aircraft-safe evidence**.
- `RunLifecycle(Context, Clock, DurableSink, durationNs)`: `begin(binding)` →
  `activate` → optional neutral-bound short lease/input policy → `requestClose` →
  optional `activityStopped` → exact `resourcesClosed(true)` →
  `reviewCommitted(SHA)`. The context argument is required for every mutation.
  Run/epoch/boot/operator/generation/profile fences are exact. Input is copied,
  finite, bounded and timestamp/sequence checked. It is explicitly not dispatched.
- `snapshot()` and `history()` remain readable after a durable-sink failure and
  show `FAILED_UNCOMMITTED`, failure and zero authority. They do not invent
  resource closure or review commit. Elapsed freezes at an observed activity stop
  or, absent that observation, the resource-close boundary. Timing never proves
  LAND or a safe aircraft. UTC jumps cannot extend a monotonic deadline.
- Reads track observed monotonic time. An observed expired lease cannot revive
  after a later regressed clock read. Expiry is durably recorded before clearing;
  failed expiry commit returns diagnostics with no authority.
- `newSession(oldContext, nextContext, nextDurableSink)` returns a **new** lifecycle
  only after the prior one is SEALED. It consumes one successor attempt, including
  an unknown/failed successor-sink commit, preventing retry forks. Next sink must
  differ; run/epoch/generation must be fresh. The observed AP boot may remain the
  same between sessions. The new run stays NEW until an explicit provider binding
  and activation; no lease, neutral token or callback is restored. The old sealed
  journal is never appended or reopened. Historical close/elapsed stays stable.

This is a local serialized policy object. A future transport/provider owner must
enforce singleton ownership across independent instances, establish observed
bindings from actual executable/device/connection observations and journal any
restart reconstruction. `History` intentionally has no authority restoration API.
The200ms input/lease TTL and declared firmware4.7.1 are mock policies, not a
generic device compatibility or real-Hera calibration claim.

## Reproduce checks

Python: set `CLOCK_EVIDENCE` to a newly created exclusive evidence directory and
run `python3 -B planning/betaintegrated01/m1mock/clock_lifecycle/test_clock.py`.
It commits2049exchanges to one fsynced stream, checks4100events and bounded memory,
then covers malformed/foreign/reordered/late/duplicate, sink fault and clock guards.

Java: compile only these two source classes and `LifecycleTest.java` with the
already pinned JDK `javac --release 8 -d native/betaintegrated01/.build/...`.
Run `LifecycleTest`; remove only task-owned class output afterwards. No APK or
Android runtime is needed. Entry20GiB and live floor10GiB+256MiB /15s forecast
remain unchanged; these subsecond tests generated less than3MiB of evidence.

Cycle01 Java's immutability assertion correctly received
`UnsupportedOperationException` but its helper caught only other rejection types.
That test-helper error was retained and fixed in cycle02; product source was
unchanged for that repair. Java26 emits obsolete Java8-target warnings; successful
compilation establishes Java8 API/source compatibility, not ART execution.
