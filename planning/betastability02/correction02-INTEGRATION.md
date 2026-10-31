# Correction02 proposal: durable required prefix, live future remains live

Scope: proposal only while pinned04 campaign runs. Do not apply until owned
runtime is closed and retained. Keep original failed receipts. This is a
correctness repair, not permission to waive latency/counter/frame gates.

## Exact semantics

`traceBarrier()` captures `requiredThrough = traceSequence` at entry, before any
await. Flush until `traceAck >= requiredThrough`. Never wait for live queue to
be empty and never force accepted/ack/pending to look equal. With original
512pending bound and64rows/batch, at most9 flush completions are allowed;
no-progress/fatal still fails. A sample's VIEWER_FRAME span is recorded
synchronously before measurement-sample insertion, so a barrier requested by
saveReport after measurement includes every sample's span in the required prefix.

The host authenticates the existing role+nonce, validates UUID/config/serverBoot,
and checks its observed external stream sequence >= requiredThrough. Capture
`ackThrough` BEFORE awaiting host fullTrace.barrier, because newer rows accepted
during fsync are not necessarily inside that durable checkpoint. A compact reply
under4KiB must include only prefix identities + complete/head/hostThrough and
receipt SHA/path. Do not serialize the growing full blockmanifest in HTTP replies.
Full blockmanifest remains on disk and is verified by cold traceRange generation.

Suggested host route body:

```js
exact(q,['traceId','configId','serverBoot','requiredThrough']);
const traceKey=role+':'+q.traceId;
const ackThrough=externalTraces.get(traceKey)??0;
if(q.serverBoot!==serverBoot || q.configId!==relay.session?.configId ||
   !UUID_RE.test(q.traceId) || !Number.isSafeInteger(q.requiredThrough) ||
   q.requiredThrough<0 || ackThrough<q.requiredThrough)
  throw Error('TRACE_BARRIER_PREFIX_FENCE');
const b=await fullTrace.barrier('external-'+role);
const reply={traceId:q.traceId,configId:q.configId,serverBoot,
 requiredThrough:q.requiredThrough,ackThrough,
 durable:{complete:b.receipt.complete,fatal:b.receipt.fatal,
  hostThrough:b.receipt.events,hostHead:b.receipt.head,
  receiptFile:b.file,receiptSha256:b.sha256}};
if(Buffer.byteLength(JSON.stringify(reply))>4096)throw Error('TRACE_PREFIX_REPLY_BOUND');
return send(200,reply);
```

`prefixBarrier` in correction02-prefix-fence.mjs implements client-side capture,
flush/progress/budget, compact reply validation and truthful current live counts.
Root may embed these short functions or expose a new pinned helper module; if
browser import is added, serve/pin that explicit asset as well. Existing source
calls use same function and ignore return value until source closure; native
RPC/archive waits still receive durable acknowledgment.

Viewer report change:

```js
const prefix=await client.traceBarrier();
return client.json('report',{...snapshot,
 fullTrace:{...client.traceState(),prefix}});
```

Keep `fullTrace.accepted/acknowledged/pending` as the current live state. Fence
contains requiredThrough, ackThrough, currentLivePending and explicit scope.
Do not overwrite these counters or reinterpret pending future events as loss.
A report without a new prefix remains NOT_CHECKED/FAIL, not silently upgraded.

## Qualifier checks

Replace `pending===0 && acknowledged===accepted` with required prefix validation,
not just `ack>=required`:

- Match prefix traceId/configId/serverBoot to the report and actual viewer stream.
- Require durable complete=true, fatal=null, ackThrough>=requiredThrough>0.
- Preserve current live counter consistency; permit positive future pending.
- Verified contiguous host trace must contain external requiredThrough and no
  intervening external-sequence gaps within its exported range.
- For each report sample at/beside AUTO, existing four-stage join remains exact.
  Its VIEWER_FRAME must use that report's fence traceId and externalSeq <=
  requiredThrough. Track sample→report fence when collecting selected samples.
- Its host trace seq must be <= durable.hostThrough.
- The exported contiguous trace must include row seq=durable.hostThrough with
  sha256=durable.hostHead. Prefix anchor never proves original history before the
  exported range; keep originalPrefixVerified=false.
- Existing source/request/clock/HTTP/decode/canvas identities, durations, packet
  sequence, FPS/P95/maxgap/counter thresholds remain unchanged.

`verifyPrefix` helper and10 passing mock fixtures are design checks only. It
expects host rows already cryptographically checked by verifyTraceRange. Missing
required tail/middle, wrong stream, sample beyondprefix, wrongdurablehead and
forged counters all fail. Test case new frames during flush+fsync finishes with
required12/ack12/currentAccepted18/currentLivePending6 and is correctly valid.

## Buffered clock alias correction

Current recordSpan shallow-spreads data, retaining the live `clock` object.
Publisher's periodic Object.assign(clock,q) mutates queued historical frame rows.
Deep-copy at ingestion, before queue insertion:

```js
const frozenData=structuredClone({...data,context:{...traceContext}});
traceQueue.push({seq:++traceSequence,kind,atMs:performance.now(),data:frozenData});
```

Keep serialization limits and rejection paths. Do not rewrite historical rows or
patch source timestamps. correction02-clock-copy-tests.mjs exposes old shallow
alias and proves queued clock/context snapshot does not mutate on refresh.

## Verification after applying, before next pinned campaign

1. Run prefix, clock-alias, fulltrace integrity/fault and existing coverage tests.
   Update fixtures with real per-report prefix anchors; test missing requiredseq.
2. Add compact host reply test with large artificial diskmanifest (>2MiB) whose
   HTTP prefix still stays <4KiB; preserve full manifest on disk.
3. Make new pins only after these checks and after prior ownedruntime closure.
4. Retain pinned04 window results with original FAIL/classifier error. Mock
   proposal PASS is not Android/SITL readiness. Rerun fixed-build nominal campaign
   under remaining declared live-correction budget.
