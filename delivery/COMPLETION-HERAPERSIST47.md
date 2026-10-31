# HERAPERSIST47 completion · 2026-10-15

STATUS: DONE within host workspace/mock/replay scope. OVERALL: READY for host engineering review; physical MCUflash, Android/HeraHub/SDK/flight and fullpowerloss NOT_CHECKED. Single-agent sequential verification, not independent review.

Delivered successor47 over frozen46/45. Newlocalhost8801 with durable store `.local/herapersist47/operator`; old8800 RAM preview untouched. There is no automatic migration of old46RAM. Existing44host-JVM journal reused read-only; no APK/native build/install or software signature.

## Requirements and evidence

R47-01..08: implemented8/8 within scope, not product readiness percentage.

| Requirement | Verification |
|---|---|
| R47-01 | Baseline46+allpriorSHA/inventory, finalpreservation/floor/budgets, exclusiveappend receipts |
| R47-02 | Versionedsealedworkspace/operationepoch, typed draft, semantic46/45replay;19 adversarial tests cover rehashedfalse state/context/type/lineage, distinctprefix/expectedSHA |
| R47-03 | Two-phaseintent/result, journalCAS/OSlock/fsync/exactreply/token/revision, immutableprefix andlegalphase transitions;15 modeltests andactualJVM tests |
| R47-04 | Reload/newprocess→freshdisconnected runtime with history/storedmockconfig/draft; oldcalibration/intent never resumed; partial records preserved with interruption annotations |
| R47-05 | Durable toolbar, save/open draft, head/status, checkpoint export/readonly import, same52pxcontrols and viewportchecks |
| R47-06 | JVM25: actualCAS, threeown SIGKILL positions, pendingheadquarantine, corruptedfile/symlink refusal; before/after/lostreply faults, orphan-withoutHEAD andquota checks |
| R47-07 | Browser22 on finalsource: actual different NodePIDrestart/sameport, exactoldcheckpoint before newactions, freshhandshake/newepoch/unchangedprefix, mappingrestore/readback, networklostresult, recipientdigest refusal and1280/1024/360 layout |
| R47-08 | Protected45 cold76cases, protected46export replay, ownJVMrestoredreplay, syntax/finalfingerprints, scopedcleanup |

Tests do not infer physical execution or persistence from ACK. Mockpeerflash is derived by replaying captured46logicaloperations and is distinct from realhardware. Arbitrary unsaved editor edits are not journaled; explicitSaveDraft or successful draftvalidation commits typed draft. Afterrestart restored draft must be opened/checked/applied again; no ready flag/input privilege restored. Checkpointimport remains readonly, not a restore-to-live endpoint.

## Storage and recovery limits

Immutable44journal algorithm unchanged. Intent commits before logicalmutation, result commit before success. At resultfailure, lastdurableintent survives as unknown/interrupted; fullresult not committed is not claimed recovered. On newruntime oldpendingintent is annotated and never rerun. Lost reply after actualcommit reconciles by explicitload/replay, freshsession and lateruseraction; no HTTP/campaign retry. Journal HEAD.pending is disclosed and blocks writes; it is never deleted or auto-selected. Orphan record withoutHEAD is quarantined. Corruptchain/file preserves bytes and refuses restore.

Capsule256KiB/8epochs/128ops each/16markers; store16MiB. Atcapacity stop/export rather than delete or silently drop. Existing immutable journal physicalquota remains64MiB but47's admission imposes16MiB first. Body and semanticprefix/phase checks supplement fileSHA/CAS. Local hashes are not authentication; an externally supplied expectedSHA is necessary to identify original history against fully re-sealed replacements. No trustedhardware/root key claim.

## Cleanup and scope

QA own Nodeprocesses/JVMchildren/Chromium closed. `.local/herapersist47-qa1`, `.local/herapersist47-browser1`, `.local/herapersist47-browser2` and orphan test store removed after retaining receipts/neededstore copies. No projectcopy/tmp/install/AVD/Docker/newbuild output. Operatorstore is deliberately persistent productdata and must remain. Preview finalPID/URL/source identity recorded separately if launched. No source/candidate/SOT/trust/ENDURE changes, SDK, signature, APK, SITL, flight command or externalpublication.

No real hostdisk exhaustion or physicalpowercut was induced. Actual evidence covers hostprocessdeath and injected storage faults; Android/provider/filesystem powerloss behavior remains NOT_CHECKED. ENDURE24h status not promoted. Next work: explicit recovery/export/retention tool for pending/quota conditions and hardware integration only after protocolunknowns are resolved.

Final verifier31/31, JavaScriptsyntax10/10,0errors. Finalpreview PID47479/8801/store path recorded in preview.json. Operationdata also bounded200000bytes; oversizedimport/action may be refused bycapsulequota before execution, retaining acknowledged history. Persistentoperatorstore is intentional; QA storecleanup verified.
