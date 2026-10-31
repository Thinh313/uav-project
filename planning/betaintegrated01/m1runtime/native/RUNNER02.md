# Runtime02 Android intent-ordering correction

Scope: preserve runtime01 Java, APK04 and all old receipts. New Activity derivative
and a memory-only `PendingExplicitAction` policy correct the observed refusal when
Android delivers `onNewIntent` before `onResume`. Wire/journal/provider/session
algorithms and manifest remain exact runtime01/foundation inputs.

Only a fresh explicit intent can enqueue an action. Initial creation queues only
when savedInstanceState is null; history launches are ignored. Ordinary resume
never reads the old Intent or creates a new action. `onPostResume` posts a bounded
consume operation after foreground becomes true. `onPause`/`onDestroy` cancel
pending work and retain the existing close-owner policy.

Every explicit intent now requires a unique ASCII `m1ActionId`, for example:

```text
adb -s emulator-5582 shell am start -n vn.rtr.aeris.beta01runtime/.RuntimeActivity
  --es m1Action CONNECT --es m1ActionId actual02-connect-01
  --es launchBindingSHA256 <exact-root-private-file-SHA256>
```

Use another ID for CLOSE. During active capture, inspect `files/latest-state.json`
through `run-as`; do not issue STATUS Activity intents, since Android may pause
the Activity and the retained foreground guard must close the socket.

Pending state is one ticket, a bounded16-ID recent replay fence and a2-second
native-monotonic receipt-to-consume TTL. Invalid, replayed, cancelled, expired or
clock-regressed actions cannot dispatch an older ticket. This fence is not remote
authentication. It is not serialized or restored from history. Reuse after ID
window eviction cannot reopen an old run because the independent run journal
directory is exclusive and never reopened.

Logcat tag `AERIS_M1_INTENT` records QUEUED and CONSUMED action ID, native receipt/
consume clocks and foreground state. Actual Android ordering must be verified
from this trace; JVM helper tests alone do not prove callback delivery ordering.

Build05 substitutes only the runtime02 Activity plus its pending-action policy
for the old Activity, with expected-provider03 binding the new host profile.
It remains `manualCapability=false`, `NO_MEDIA_M1_RUNTIME`, the same development
certificate, no production signature and no completed M1/manual/Beta claim.
