# M1 offline lifecycle: fault injection before another actual run

2026-10-20. User needs time to clear disk and explicitly authorizes useful implementation without new large storage. Scope is mock/replay only even if free space changes. No Docker/AP/Android/ADB/browser server, APKbuild/signature/SDK/download, physical link or flight. Keep userfloor20GiB; measuredentry~24GiB permits bounded source/mock work. Personal Vibecode6.3 Contractor/Builder/independentQA.

## Outcome

Complete the missing lifecycle verification of the actual new controller, not just its bootstraphelper and AST. Before spending another AndroidSITL window, prove that startup/readiness/observer/peer/resource/shutdown/storage failures cannot leak owned resources, hide failure as clean completion, retry a mutation, or rewrite evidence. Existing bootstrap04 helpergate remains valid in its scope; it did not dynamically execute the whole runtime04 top-level lifecycle.

Root review identifies areas to investigate, not accepted productbug/rootcause claims: failure before/after peercreation and its consolefile; primary bootstrap/observer failure racing later probe/cleanup failure; closurewrite/fsync failure; alreadyexited/OOM/missingcontainer vs controlledstop. Only a reproduced actual-code mock failure authorizes targeted repair in a new derivative. Old actualEOF cause stays UNKNOWN.

## Frozen boundary

Do not edit runtime.py, runtime04.py, bootstrap04.py, oldmock/QA/source-ready receipts, native source07/APK04/observer, candidate/canonicalSOT/ENDURE. Newfiles only `planning/integration03/runtime/*05*`, new `evidence/integration03-lifecycle05`, owned `.local/integration03-lifecycle05` scratch if needed. A single small runtime05.py derivative is permitted only after a demonstrated gap, with exactbaseSHA/diff and focusedregression. No wholeprojectcopy or new app architecture.

## Implementation and verification

Builder builds an injected harness that executes the actual runtime04 top-level code under controlled fake Docker/probe/socket/clock/process/thread/filesystem boundaries. A local Python test process is allowed; no external Docker/Node/adb/AP process or real socket. Do not build a parallel idealizedcontroller that merely copies expected results. If AST/root-binding transformation is needed, disclose it; do not change testedbranches/cleanup/error/commandarguments. No simulated result enters the actual runtime runs namespace. Test IO goes only to marked bounded mockscratch/evidence, removed on finish.

Exercise nominal safe-ground closure, bootstrap refusal/EOF beforepeer, AP spontaneousexit/OOM, unexpectedidentity, partial startup/Popen/threadfailure, observerfault, resource/deadline shutdown, pendingstopwithoutfreshground, plus write/fsync/capture/close/terminate/wait/kill/stop failures. Exactvalues/order belong to independentQA corpus. Require causal receipts and assertions that intendedbranches were reached, not an upstreamschema refusal credited for a downstreampredicate.

Acceptance:

1. Actual controller lifecycle runs under injected boundaries and produces clearlysynthetic evidence outside operationalrawnamespace; fixtures and every transformedrootbinding pinned.
2. Owned AP/peer/observer/socket/console cleanup attempted in safe declaredorder on partialstartup and failure; wrong/replacementcontainer not stopped. A cleanupfault does not skip later cleanup. Unknownclosure remains visible.
3. First observed failure and secondarycleanup errors retained without false rootcause or success. Missing/failed closure persistence is unsealed/error with nonzero verdict, never a clean `CLOSED None` accepted by caller.
4. One bootstrapconnect/0TX/no mutationretry; native flight/WAL/frame/1500ms/3000ms/speedup1/cap500ms/900s/groundstop semantics and APargs unchanged except narrowlyapprovedrepair. No authorityrestore or fake actualflightresult.
5. New derivative, if required, passes same focused scenarios and independently selected adversaries; oldfailedsource/traces retained. No patch solely to satisfy incorrectfixture.
6. All oldpins exact, source/lineage/independentQA and cleanup receipts; M1 stillNOTREADY because actualmission/crew/SAF/airborne/restart gates notrun.

Boundedbudget: ≤512KiB newsource/tests,≤16MiB evidence,≤20MiB scratch cleaned,≤40 deterministic scenarios total planned before reassessment; no broad repeat of existinggreen suites. Keep valid outputs; halt for cause review on unexpectedhostaccess or actual dependency launch. Report numerical coverage without doublecounting reruns/assertions as productfeatures.

When complete, hand off one coherent offlineverification result and exact remaining actualgates. No automaticresource waiting/launch or ENDUREaction. No claim of hardware/DJI/RAGAS superiority. Deterministic lifecycle repair has no meaningful directLLM baseline; value is measured faultdetection/closure honesty, runtimebenefit remainsunmeasured.
