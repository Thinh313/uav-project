# BETA06: Android–SITL internal beta

22/10/2026. **OVERALL STATUS: NOT READY.** This is a scoped engineering verification report, not a beta release or a claim that AERIS can operate a physical Hera.

The interrupted preparation was resumed without restoring timing anchors, overwriting old receipts or resetting runtime quotas. The new generation passed actual Android video/lifecycle admission and native workspace/persistence checks. Its first SITL container exited before telemetry, so the full mission, media/payload overlap and airborne fault gates remain unmet. No further AP was launched after that failure.

## User outcome and supported configuration

The existing development APK ran on Android13/API33 ARM64 emulator-5582,4CPU/2GiB, WebView101.0.4951.61. A laptop companion and Chrome VP8-720P30-V1 synthetic RGB publisher supplied video. The unchanged APK SHA256 is `df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d`. No build, installation, new APK signature, production signature, new SDK download, vendor/HeraHub SDK, physical HeraHub or physical aircraft was used. The cached Android SDK/emulator runtime was used.

Actual achievements in this generation:

- 75.4855seconds of continuous foreground/current-client video admission:145samples,0lifecycle failures,3viewer and2publisher periodic clock renewals. Maximum sampled frame age40.6ms, client heartbeat age742ms and successful calibration RTT6.9ms, under the original20ms/60000ms bounds. These are admission samples, not a measured30s FPS/latency acceptance window or physical-camera exposure latency.
- Android SAF exported a new17,463-byte workspace file, independently read it from the document provider and imported the exact body/model/plan. Provider SHA256 `aed323fb19477f72440f9a4d90e7d66673f125b9cd976517dd1d9bf045681249`. Native journal and host WAL corroborate the import; the WebView reloaded, so its later null callback is not used as import proof.
- An explicit SAF cancel returned `SAF_CANCELLED`, retained the staged artifact and did not report a successful export. The lifetime picker count went10→13;3operations remain. No quota reset, app-data clearing or evidence deletion occurred.
- Native process restart2054→2856, then a different actual emulator guest boot and app PID2038, retained34journal records and19native files exactly. The task's original15native artifacts stayed unchanged. The KML model and inherited review history remained visible; these inherited reviews are not new G2 flight executions. No video, flight authority or payload lease was restored automatically.

## Mandatory requirement coverage

| TIP group | Actual result | Remaining gate |
|---|---|---|
|1. Source, pins, resource and preservation | PASS within checked baseline | No whole-repository completeness claim |
|2. Two full nominal AUTO/RTL/ground-disarm missions | FAIL: first G2 launcher attempt | N1/N2 not accepted; no telemetry or ARM in G2 |
|3. Mission + video/payload/capture overlap | NOT_CHECKED | Two30s FPS/P95/cold-start/recovery windows during actual AUTO, linked capture and gimbal |
|4. Deliberate airborne C2 cut | NOT_CHECKED | Exact live-lease revocation, raw UNKNOWN and correlated old-context rejection |
|5. Deliberate AP process reboot | NOT_CHECKED | Actual owned PID/start-time change, revocation and incomplete-flight review |
|6. Persistence | PARTIAL | Native process/coldboot PASS; managed host restart requires accepted N1/F1 and was not attempted |
|7. SAF and independent receivers | PARTIAL | Workspace export/import and cancel PASS; new nominal/fault raw packages, linked capture and wrong-SHA native negative remain unrun |
|8. Visible native UI | PARTIAL | Ground viewport/controls and persistence screens inspected; airborne/Home/fault screens unrun |
|9. Engineering handover | PARTIAL | Existing APK/source/pins retained; beta release blocked by mandatory runtime gates |

This table is not a product maturity percentage. Mandatory failures cannot be averaged away.

## Actual SITL failure and diagnosis

G2 request `sb9aef33470bc49bf84ff` is one consumed actual attempt. Docker events for exact container `314f2dd1deea89e6058d46b84687227ef0392ae7678f0ce25748a768775d25bc` show create→start→die(exit255)→destroy. Start-to-die interval86.668708ms. Raw MAVLink and runtime console files contain0bytes; there is no successful launch attestation or incoming firmware proof. The autoremove launch erased the container before subsequent inspect/log collection. **Actual exit255 cause remains UNKNOWN.** The final absence of the container is independently checked; its old closure error is retained literally.

Two distinct defects were identified:

1. The selected archived ARM binary has the expected SHA but mode0644. G2 bind-mounted and directly invoked it without checking executable metadata. This is a concrete qualification defect and plausible permission failure, not retrospective proof of the observed exit code.
2. Root's Connect receipt wait was30s, shorter than mandatory30s admission plus launch overhead. The later UI rejection and backend launch failure were collected read-only. This orchestration defect explains why the controller could time out before a terminal UI receipt; it does not explain the container death. No input was resent.

The original generation01 failure, G2 failure and all old ENDURE results remain separate. No nominal success, camera exposure, physical failsafe behavior, sustained1× pacing or24h reliability is inferred from this run.

## Bounded repair prepared after closure

New offline-only modules under `pilot/beta06g3` check exact SHA, regular/no-link file, ELF64 little-endian AArch64 and executable metadata before allocation. A bounded exclusive preparer created only `.local/beta06g3/arducopter`,7,172,336bytes, mode0755, with exact source SHA `1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41`. The original archive remains the same bytes and0644 mode. The artifact was not executed and is not a selected release candidate.

Builder checks and independent QA both passed the10 contract and10 preparer test groups. The independent artifact receipt confirms separate source/destination inodes, source0644/destination0755, exact bytes/SHA and323G2 pins unchanged; this is offline preparation, not an AP boot. The launch state-machine remains a contract prototype: boolean fsync flags are not actual durable runtime capture, structural ELF checks are not loader proof, and minimal argv checks are not full live-profile attestation. The executable preparer does not mean the launcher integration or AP boot is complete.

Next implementation must integrate descriptor-bound executable qualification and bounded durable early-exit stdout/stderr, events, inspect/wait receipts. The proposed create-before-start/container retention lifecycle needs its explicit finite runtime and owned cleanup policy before execution. Correct the receipt wait separately, retaining all flight/lifecycle freshness rules. G3 has no actual host, emulator or AP run in this task; no runtime budget was expanded after G2 failed.

## Closure, provenance and limitations

Host8866 closed with exit0/`EXPLICIT_STOP`, no payload evidence failure. Both emulator boots closed explicitly with exit0/no error. Controller exited; ports8872/8873/5582/5583/5972 are unbound and no owned SITL container remains. Minimum observed free storage during the two emulator runs was36.4979GiB, above the20GiB floor. Later independent post-artifact QA observed36.3159GiB; it also remained above the floor. Runtime image-prune receipt reports0B reclaimed. No project copy, dependency installation or broad cleanup occurred; Builder test scratch was removed, while valid evidence and the new engineering executable were retained.

Independent preservation rehashed4,528baseline paths without drift, including323G2 pins and the retained previous protected/G1/FIELD02 groups. This does not cure or conceal95pre-existing tracked missing paths shown by Git. Those paths were not restored or deleted in this task. Existing frozen source/candidate, ENDURE, trust, selection and canonical SOT were not rewritten.

VALUE EVIDENCE: actual scoped Android video admission and data durability measured; no AI runtime added, so a direct-LLM baseline is not applicable. Mock counts prove the named negative cases only, not reusable product certification or superiority to DJI. Market release, real payloads, real HeraHub, thermal measurement, hardware video backend and physical flight remain separate gates.

## Evidence entry points

- [Independent actual ground75s](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation02/qa-actual-ground75-n1-03.json>)
- [Actual launcher failure replay](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation02/qa-actual-launch-failure03.json>)
- [Independent SAF receiver](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation02/qa-saf-workspace-receiver03.json>)
- [Cancel and process persistence](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation02/qa-native-cancel-process03.json>)
- [Final preservation and closure](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation02/qa-final-preservation-closure03.json>)
- [G3 offline launch diagnosis](</Users/os/Downloads/AI technique/aeris/planning/beta06g3/LAUNCH-DIAGNOSTIC-TIP.md>)
- [G3 executable preparation](</Users/os/Downloads/AI technique/aeris/planning/beta06g3/BUILDER-ARTIFACT-VERIFY02.json>)
- [Independent executable artifact QA](</Users/os/Downloads/AI technique/aeris/planning/beta06g3/qa-offline-artifact02.json>)

Disposition: retain the scoped PASS results, fix the isolated launcher boundary, then perform a newly declared finite actual campaign with all required nominal/fault/media/SAF gates. **Do not label this BETA READY.**
