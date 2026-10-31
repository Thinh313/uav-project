# Native consumer priority preparation03

Outcome: a small isolated Owner candidate consumes up to16 already-queued FIFO messages before diagnostic CONTROL_LOOP_OBSERVATION fsync and periodic readonly network requests. It preserves the existing128-message bound, one socket/writer, all producer sequence/time/context values, all fsync-before-wire barriers, native200ms lease/input freshness,500ms loop guard, run deadline, foreground/close fences and no implicit regrant. The original selected160MiB Owner and APK05 are unchanged. There is no new diagnostic schema or capacity policy.

Exact product diff: `native/owner-order.diff` in the new evidence namespace. Original Owner SHA256 `85090127466f813592b43f3e14b50ae695fd23b70fd69a68a3b29f4fb8a45095`; candidate `0c43601e7bc3973c409e48ab90cfc96e5f945e9db7b85d863567d9b996ee4aaa`.

Builder command:

```
python3 -B planning/betaintegrated01/cockpit05-nativeio03/mock/run.py
```

It is one-shot/exclusive for its recorded mock03 destination. Root should not rerun without a separate evidence destination. The command compiles explicit source lists with the cachedJDK only and removes its small owned `.build` directory in finally. It does not build/sign/install an APK, load Android, open an OS socket, runAP/SITL or change userdata.

The tests execute the actual old/new Owner, unchanged Session/Authority/Flight/journal classes with a fake clock/connection and real filesystem fsync. A clearly test-only neutral Authority seed isolates queue scheduling; it does not prove actual preflight or a physical operator grant. Fifteen groups passed at `evidence/betaintegrated01-cockpit05-nativeio03/native/mock03/results.json`:

- Same135ms injected observation-fsync delay: old ordering loses the200ms lease, new ordering admits the already-queued timely producer observation first and remains fresh at the same final clock. Producer timestamp is unchanged.
- Already-expired lease cannot revive; own input durability220ms stall refuses an actual SessionLAND request before any additional network callback; no automatic consent occurs.
- Queued explicit action after the run deadline is refused. PendingCLOSE drains neither queued input nor action.500ms loop guard still fails closed.
- Callback-entered write error remainsTX_UNKNOWN, and seven existing actual Owner closure/failure regression cases pass.

Mock01 initially failed four assertions because the test searched encoded journal rows for plaintext payload fields. That harness assertion was corrected to decode the retained base64 payload. Failed receipts/logs and exact old harness snapshots remain; the product candidate was not changed for that repair. Mock02 passed13 groups; mock03 adds the explicitly requested deadline/close cases and strengthens the actualSession send refusal.

Limitations: this proves an ordering advantage under the declared injected delay. It does not identify whether the real141ms gap was fsync, scheduling or another wait, and it does not guarantee200ms service under hostwide/guestwide stalls or the input's own slow durable barrier. No native per-stage wall/threadCPU instrumentation was added, avoiding an unreviewed schema/quota change. Independent QA and a reviewed new APK/sourceidentity/resource contract are required before any future actual short/30minute campaign. The previous failed30-minute attempt remains NOT_READY; no interval is resumed or added.
