# INTEGRATION03 · AERIS Integrated Alpha

Status: **NOT READY / RESOURCE STOP**. This report records work delivered and remaining mandatory acceptance. It is not a completed flight or production release.

## User outcome

One isolated Android composition now includes distinct QGC SimpleItems intake preserving original bytes and per-item height/speed, shared KML/corridor planning, existing preflight/upload/readback/Home/AUTO path, independent mTLS operatorB with multi-payload contracts, and a read-only host3D observer using pinned licensed Visual56 assets and opt-in synthetic rotor audio. This milestone adds integration and repairs; source presence and offline tests do not prove the complete user journey.

The latest engineering APK03 was development-signed, signature verified, installed byte-exact on emulator-5582, and opened in direct read-only mode with its saved mission. Its final actual flight, handoff and restart gates remain unaccepted.

## Requirement coverage

| AC | Disposition | Evidence and remaining gate |
|---|---|---|
| I01 | PARTIAL | APK02 three actual aged cohorts1505/1639/1704ms with3000ms guard unchanged. Its later20k EVENT_BOUND failure retained. Final native-backed repair independently processes24317mixed frames, default20001refuses, bounded288diagnostics, exactcounters/evictions, adversarialguards and immutable nativeprefix lookup. FinalAPK03 actual>20k plus3cohorts NOT RUN. |
| I02 | PASS SCOPED | Heldout semantic/geodesic/Home/datum/camera checks and supportedQGC source retention. APK01 QGC raw/32item roundtrip; APK02 unequal peritem heights17.25/23.5/14.75m andspeed1.75 correspondence. Compiler/intake unchanged by final transport repair. Complex/fence/rally/unknown executable semantics refuse. QA originalH01 belowminarea correctlyrefused; supplementalH01b is postinspection, not unseen. |
| I03 | NOT RUN FINAL | Nominal finalAndroid AUTO→ground/disarm→acceptedreview still required. Both new actual run windows stopped unarmed; no accepted mission claimed. |
| I04 | PARTIAL | Scoped mock/contract and APK02 Adevice1 −33/78 observed; final independentB same-consentcapture,3cameras anddevice2 wire acceptance incomplete. Preparation errors recipientproposal/coreSid retained and repaired in QA harness. |
| I05 | NOT RUN FINAL | FinalAPK Bpartition/pendingUNKNOWN/rejoin0rights and pilotforegroundloss/APfailsafe not executed. Earlier component evidence is not substituted. |
| I06 | PARTIAL | Full HDR/PBR/shadow/SSAO licensed visual model and source/run/plan/age binding implemented. ActualAPK02 ground source sample3000frames at120Hz retained as bounded~25s sample, not full30s gate. Corrected8192/coverage/overflow/visibility gate independently mocked; finalairborne30s measurement and estimatedaudio observation pending. No calibrated physics/acoustics/GPU present-time claim. |
| I07 | NOT RUN FINAL | Exactselectedrun+receiver/nonce predeclaration and independent strictSAF receiver prepared. Finalactual Android export/provider/readback/receiver and corruption/context rejection not completed. |
| I08 | NOT RUN FINAL | Processrestart/coldboot plus finalclosedjournals/noauthority/oldprivateafter checks pending. Legacyprivatebefore576files including51CREW02exact; no finalafter substitute. |
| I09 | PARTIAL | Glass cockpit and QGCsummary inspected in actualAndroid; no observedP0/P1 in that scopedUI review. LongHomecaption clipping and technicalrawdensity remainP2. Complete finalflight/fault/review/popups and companionjourney visual acceptance pending. |
| I10 | PARTIAL | 71158protectedhostpaths SHApass before and atresource-stop; APK/source pins; owned runtime closure. Finalnewprivate/SAF integrity and completionfingerprint remain dependent. No continuouspathpresence claim. |

No aggregate percentage conceals mandatory missing gates. Only I02 is accepted at its declared scoped evidence coverage; this is not1/10commercialproduct maturity.

## Cause-oriented repairs and verification

- Native stage trace snapshots release the hot monitor before serialization/fsync, with native and JS clocks kept separate. Presentation redundant work removed; comparative timing is bounded evidence, not matched causalA/B or DJI/Ragas superiority.
- First actual APK02 run failed RX_ADAPTER EVENT_BOUND after20000classified frames while telemetry was fresh and aircraft disarmed. EXPLICIT_SOCKET_CLOSE was downstream cleanup. An earlier harness-only attribution was wrong and preserved in causal-decision05; causal-decision06 corrects it.
- Final repair keeps generic/unbacked20000 guard. Only owned native direct transport uses immutable fsynced RX-prefix proof and one-use chunk token, first32+last256diagnostic retention and exact lifetimecounts. Full authoritative raw remains, ACK stays afterallconsumers, same1500ms delivery limit rechecked after synchronous proof lookup. This is a trusted pinned native/WebView contract, not cryptographic/hardware attestation.
- Independent repair corpus:24317frames, labels16353accepted/6948foreign/561duplicate/455reordered; all frames returned/classified. Two new explicit cohorts afterpressure READY. Wrongtype/config/boot/CRC/stale/cohort/request/backing faults failclosed. Postproof1499/1500ms accepted;1501ms/clockregression refuse beforeconsumer/ack. Sourcegate05 is CLEAR for runtime, not DONE.

## Resource stop and preservation

Second actual window with finalAPK03 stopped during read-only health warmup: measuredfree24553467904bytes beforephase, later21626880000bytes in a read-only observation. Emulator guard20.5GiB closed HEADROOM_STOP; AP guard closed RESOURCE_OR_DEADLINE, everArmed=false, landed. B admission refused before process launch. Afterclosure free rebounded to~24.62GB decimal (~22.93GiB). The specific allocation/drain source is UNKNOWN; temporal coexistence/rebound does not identify the allocator. A breach below user20GiB floor was not proved. No automatic retry, generation reuse, unknowndispatch retry or history deletion.

The final partial native raw remains on the owned AVD; it was not extracted/seal-verified after emulator closure. Do not call it complete/CLOSED. All host evidence and earlier failures retained. No source/candidate/ENDURE bytes changed. No Builder staging remained to remove. Docker dangling-image prune reclaimed0B, no containers/volumes pruned.

## Value evidence and limits

Measured evidence is scoped source/mock, realAndroid intake and three earlier typed preflight cohorts. Final integrated user outcome remains unproved. This deterministic flight/transport work has no meaningful direct-LLM baseline; superiority to Ragas/DJI is UNMEASURED. Full manual/assisted training, externalphysics1×, calibratedHera/load/battery/collision/sensorloss/acoustics, actualPhaseOne/HeraHub, production PKI/signing and realaircraft are separate gates.

## Next controlled acceptance

Wait for measured≥28GiB host free and a new explicit resource admission covering observed coexistence transient, future raw/private/SAF copies and shutdown margin. Reassess the exhausted4window budget before creating a fresh run; preserve both unarmed failures, never reuse their run directories. Keep finalsource05/observer04 fixed unless a new cause requires scoped QA. Then actual>20k/3cohorts, nominal+payload/observer, corridor/Bpartition, pilotloss, correctSAF, independentreceivers, process/coldboot and finalprotected/privatechecks. **No DONE until all mandatory AC pass.**

Report timestamp: 2026-10-20T09:01:05.248386+07:00

APK SHA256: `bd91ac2eef7cb8c977bf613a91eb210185318c39c1baf22e40d2c9f0f5b63554`

Native source: `1d7901adbc07e39a68bac86a51be1ae7d0cd1dd3e7a62ce94f7f5988c241b7dd`

Observer source: `3894481d2de04f8be796343896bee451fdf829b85e1aecf3f5149ece808e2d1c`
