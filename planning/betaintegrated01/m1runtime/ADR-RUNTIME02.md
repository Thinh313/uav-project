# Runtime02: actual01 findings and versioned repair

27/10/2026. Decision within the authorized isolated M1 runtime task. No frozen
source/candidate, ENDURE, M1-MOCK or runtime01 input is edited by these repairs.
Actual01 remains FAILED_RETAINED_PREFIX, never resumed or added to a later run.

## Observed facts and inference limits

- Emulator01 closed cleanly on forecast after a free-space drop of about1.9GiB
  in2s. No AP or CONNECT had run. The allocating process is UNKNOWN; do not blame
  the user, a cleaner, Docker or any unrelated process without evidence.
- Fresh admission passed before emulator02 and actual01. AP03 executable and
  installed APK04 hashes matched selected pins. Actual01 backend then failed
  `ACTUAL_HOST_DISK_FORECAST15_FLOOR10_RESERVE256`; root1Hz forecast remained
  roughly22GiB. Old guard did not retain the exact failing sample vector.
- Source proves the old guard retains only64 checks at per-record frequency.
  Its observation span can shrink to milliseconds under load while projecting
  that short rate over15s. Deterministic fault reproduction is required; the
  exact real failing allocation/rate cannot be reconstructed uniquely.
- Independent cold audit found34,033 full RX/INTENT/SENT groups and AP coverage,
  all exact reference sensor bytes, but34,032 STAGE rows. The old adapter counted
  after STAGE, so a post-SENT fault underreported the admitted/sent group and
  incorrectly called its diagnostic an unadmitted rejection. Do not repeat that
  label or call the last local send AP execution. The incomplete capture fails.
- Every native checkpoint was an explicit foreground/owner guard refusal. The
  controller's connected flag meant only intent attempted. It is not proof of a
  socket or firmware discovery. Source/Android ordering is consistent with action
  execution in onNewIntent before resume. New actual callback logs must prove the
  repaired order. No ARM/manual command was sent.

## Authorized repair, without guard reduction

Materialize only the small necessary journal/admission/adapter/backend derivative
under `pilot/betaintegrated01/runtime02`. Preserve the original M1-MOCK module
bytes and runtime01 paths. Keep entry20GiB, per-write floor10GiB+256MiB, forecast
15s, full frames, INTENT fsync before sensor, speedup1 and cap500ms unchanged.
The versioned guard retains a real15s history at bounded sampling cadence,
primes it from actual host readings before journal writes, performs current floor
checks at every write/send and reports its measured span/rate/free/requested/
forecast on refusal. No fabricated seed, runtime fault injection, monkeypatch or
fallback bypass is permitted. Startup order becomes backend/real prime/identity,
then container clock handshake, then AP. Keep the10s clock bootstrap timeout.

Separate frame-group admission/local-send completion from timing-row commit.
A failure after SENT must preserve the attempted timing and identify the already
admitted frame honestly; no resend or sampled/dropped frame is an allowed repair.

Use a minimal new Android Activity derivative and a bounded explicit-action
ticket. Only a fresh explicit intent queues CONNECT; consume once after foreground
resume, cancel stale/replayed/replaced/background tickets, and never read history
or ordinary resume as a new grant. Retain onPause socket closure, same-owner,
provider, source epoch and manual=false/no-media gates. Version the expected
descriptor and developer APK against the new run-profile hash. No production key.

## Verification and stop

Independent mocks must exercise true-window retention at high write frequency,
priming/floor/steady-decline/time gaps, post-SENT timing failure accounting,
explicit ticket TTL/replay/cancel and current-source reuse. Second actual attempt
requires a fresh admission and new run/epoch/boot, same AP/model/pacer and no
source edits during capture. It is the last host start in the current task budget
(two emulator starts + two host starts). On another failure preserve and hand off
PARTIAL; do not silently increase budgets or restart automatically.

The30min format bound requires about55GiB for simultaneous original/copy/export,
which current storage cannot admit. A successful short smoke will not close M1
manual/assisted/link/reboot/30min or full Beta/cockpit/media/hardware acceptance.
