# FIELD02 host Builder handoff

Implemented isolated control8872/media8873 and fixed cached ArduPilot container `aeris-field02`, guest TCP5760 mapped to127.0.0.1:5972. Own source/assets/evidence only. Curated stage derives frozen PHONE07 read-only; independent own media server fork is required because FIELD01's output guard intentionally forbids FIELD02 paths. Media wire/capture schema identities remain FIELD01-compatible; source and evidence namespace are FIELD02. Android is a WebView client of this explicit host companion, never standalone native-direct transport.

## Verification already run

- `host-tests03.json`:11 deterministic policy/flight guard checks, including false fault confirmation with zero fault effects, stale3s, exact client epoch, no automatic authority restore and no simulator abort on background. Includes rejected concurrent request unable to replace the accepted in-flight operation context.
- `qa-client-session02.json`: separate Contractor-authored actual policy tests run by Builder,10PASS. This is not a new independent human review.
- `host-http01/results.json`:10 actual localhostHTTP checks. Polygon and corridor both run full protocol MOCK preflight/grant/upload/readback/arm/Home/AUTO/ground/closed review. Immutable exported raw TAR SHA checked from GET bytes. Anonymous and oldepoch control rejected. No SITL/Android evidence inferred.
- `host-source-check01.json`: syntax and source hashes before final SAF absoluteURL repair; final freeze manifest is issued after QA. No SDK download or dependencies installed.

SITL budget remains4 new attempts; mock runs use no SITL slots. Root coordinates actual Android/SITL and media acceptance. Those required ACs remain NOT_CHECKED until real evidence exists.

## API and lifecycle

`POST /api/client-session` accepts `activate|heartbeat|background|stop`. Activation `{instance,platform}` issues volatile id+epoch. Every flight/payload command uses `{clientId,clientEpoch,clientInstance}`. Heartbeat is750ms; server expiry is3000ms, independently watched every1s, not dependent on GET polling. Background/stop accepts exact instance and origin/CSRF without the volatile token to support the native fallback. It only revokes authority and discovery, never commands/aborts AP. New foreground creates a new epoch and requires explicit mission/payload grants. Client lifecycle operations bypass only the mutating operation mutex so native pause and heartbeat cannot be blocked by a long preflight. Lifecycle is serialized in the client; a queued background dominates a late activate response. Flight operation context is captured only after the busy gate and fenced at each MAVLink command write; rejected concurrent requests cannot replace it.

`POST /api/native82 {action:load|save,expected,body}` retains exact idle/CAS and canonical replay. Android SAF wrapper can export/import this mission workspace, but is not a backup of host raw/media files. Journals normalize object-key order; raw KML, mission/planSHA and media bytes retain identity.

`POST /api/export-artifact {kind:flight,run}|{kind:capture,captureId}` requires closed flight and returns `{url,sha256,bytes,name}`. URL `/artifact/UUID.tar` is immutable and bounded32MiB. The Android native custom URI receives this URL plus expected SHA and performs its own bounded download and SAF readback. Combined delivery-set exposes `/delivery/UUID/index.json|flight.tar|capture-NN.tar`, consistent field02 sender/receiver IDs. Native SAF success is not established by a host HTTP test.

## Fault semantics and provenance

- `cut` actually destroys the owned TCP socket, never reconnects, closes run aborted/incomplete and preserves raw. In mock it is a mocksocket; in SITL it is actualTCP.
- `reboot` with realSITL writes one run-bound fault request to the owned runtime, which checks exact container ownership and performs Docker restart of the AP process. Before/after actual guest hostPID and StartedAt are retained. No new MAVLink connection is made, so post-reboot MAVLink boot identity is explicitly NOT_OBSERVED. This is a real owned guestAP process restart, not proof of a physical FC power cycle. Mock reboot remains mock-only.
- Every fault confirmation and run/session/binding check precedes any cut/restart effect. Aborted/fault runs cannot be accepted even if an earlier AUTO or ground observation existed.
- Camera/gimbal remain mock; encoded network video and JPEG are synthetic. Thermal-look is not radiometric. Positions are nearest host-received telemetry references with unknown sensor/exposure synchronization; no survey quality claim.

## Display and persistence

All current metrics/map markers share clientactive, transportconnected, heartbeatage≤1500ms, positionage≤1500ms and exactrun/boot. Old speed/position disappears when stale. Main Fly shows compiled WGS84 route and fresh marker, with an explicitly schematic flat background. Capture review uses exact WGS84 coordinate text; its small schematic is not a geographic basemap or survey footprint and does not borrow Home from a different mission. Raw and image review survive server restarts through the store; authority and active client do not.

## Run and limits

Stage once: `python3 -B pilot/field02/stage.py` (refuses existing own stage). Pin own flight: `node pilot/field02/flight/pin.mjs` before launch. Root may start `node pilot/field02/app.mjs evidence/field02/host-appNN --allow-sitl --workspace=evidence/field02/<ownedworkspace>` only after TIP/QA readiness. Fixed admitted min29GiB for31 samples; runtimeguard21GiB; floor20GiB. Four SITL attempts maximum,600s total attempt bound each,540s runtime, no retries. Archive sessionquota4, workspace quota bounded, no evidence deletion. Stop only owned app/container; keep failed attempts. Remove own `.stage`/cache at final delivery.

## Actual-runtime repairs, 22/10/2026

Contractor decision DECISION-02-ANDROID-RUNTIME.md permits at most5 total SITL attempts, including failed run1. This supersedes the original4 maximum above; per-attempt600s and all freshness/disk floors remain unchanged. Previous current source-pin files are retained in host-source-pins-before-five-attempts01.json, host-source-pins-before-prefix-repair01.json and host-source-pins-before-auto-gate01.json. Each run retains its own original pin manifest.

Actual WebView101 lacked AbortSignal.timeout. The own media client now uses AbortController with a finally-cleared timer and bounded full response body;5compatibility mock checks passed. Configuration controls use an independently scrollable glass sheet with sticky summary; an open sheet invalidates video visual acceptance. Publisher/panel postMessage names are FIELD02 consistent. Actual VP8 publisher was proven to deliver TCP chunks, but zero displayed frames plus repeated viewer resync remain under diagnosis. Decoder-pressure repair retains queuecap2/pendingcap8 and waits at most150ms for asynchronous output before a counted drop/resync;5deterministic wait tests passed. Queue/pending/wait/timeout/error/output/timestamp-miss counters are displayed and source counters update1Hz. These checks do not prove Android video performance.

Independent raw diagnosis found an unintended numeric replacement introduced during the initial namespace fork: ASCII lower bound32 had become42 in3 copied verifiers. The owned prefix is148bytes and legitimately contains spaces/parentheses; those exact3 predicates were restored to32. Prefix limit1024, pinned banner, frame checks and all raw bytes are unchanged. Seven prefix counterexamples passed. A namespace-normalized comparison of13 copied flight files is retained in host-flight-normalized-diff01.json; the earlier admission duration40000→30000 repair was also recorded. This was a Builder defect, not grounds for weakening acceptance or rewriting the failed run.

Independent AUTO diagnosis of first run found Home age9.367s was still fresh, while extra parameter ages11.785–11.960s were stale. The own read-only AUTO gate now displays the earlier effective expiry of Home and extra parameter freshness, disables AUTO when any original prerequisite is false, and records gates immediately before invoking the unchanged authoritative AUTO routine. It never refreshes parameters or extends the10s windows. Five gate tests include fresh Home with stale parameters, which must refuse AUTO. New source pins include this helper,56files. First run remains accepted:false; raw/oldreview are never rewritten.

## Measured performance cycle and safe ground exit

Actual Android report host-app04/media/report-01.json is retained as FAIL:7.832fps,P95upper1012.048ms. The measured decoder itself was not the sustained bottleneck; most delay preceded decode. The approved performance cycle adds bounded source encoder/publish timestamps, HTTP send/header/body timing and per-packet host relay→decode timestamps. Discovery state polling is at most1Hz during normal operation. Every binary packet independently checks run/boot/config/feed/profile, strictly increasing frame/time and valid source-clock metadata before decode. Mismatches immediately clear preview/decoder/pending and invalidate a measurement. Probe JSON is now a collapsed summary after primary source/viewer controls.

Actual report02 after explicit viewer restart is also retained as FAIL:22.526fps,P95upper345.955ms. Its measured window has zero decoder errors/drops/resync/queue waits; old cold-start failures remain in cumulative counters and are excluded through the recorded baseline. Source→relay P95upper307.416ms, relay→decode P95upper56.294ms, decodeP95 20ms. Latest64 source stage samples point to encoder-output delay and publisher backlog; their limited coverage is explicit. No profile, queue cap or performance target was weakened. A producer admission-credit repair is proposed from these measurements but is not implemented without Contractor disposition.

Cold-start failure is now bounded: a single1500ms startup grace per source configuration ends with a visible stopped viewer if no output arrives. It never silently repeats steady150ms resets forever. Restart is an explicit user action, with no claimed success from a local codec probe. Actual-viewer mocked-HTTP/stalled-codec test host-cold-start-tests01.json proves this bounded disposition.

DECISION-03-UI-HOME-QA.md supersedes the total SITL attempt maximum to6, retaining all prior incomplete runs and all freshness/resource/per-attempt floors. The new explicit recover-ground action does not reset mission execution or loosen raw verification. It requires exact session/boot, explicit simulation+ground/disarm review, fresh connected and unambiguous source, no AUTO ever, observed ground/disarm within0.5m relativeHome and a second fresh telemetry cohort. It then closes the current run as aborted/incomplete, revokes permissions, retains raw and requires manual connection of a new run. No automatic reconnect, upload, arm or AUTO occurs. Nine guard checks and six actual-HTTP/mock-AP recovery checks passed; real SITL UI recovery remains a Contractor acceptance gate. Current flight pins include the recovery helper,57files; prior pins are retained before the six-attempt change.

The measured producer-credit repair was approved and implemented after report02: raw frames are admitted before encode only when pending+encodedQueue+publishInFlight has fewer than3 credits. Original encoderqueue2/pending8/encodedqueue2 bounds remain. Raw skips are counted; already encoded dependencies are retained. Any impossible queue overflow explicitly stops the publisher rather than silently discarding a burst and continuing. Six deterministic admission/drain/fault/identity checks passed in host-producer-credit-tests01.json. This is not a performance PASS until a new real Android measurement meets the unchanged24fps/300ms targets. No host/UI restart was performed by Builder. host-source-check02.json freezes all own source hashes and confirms57flight pins, with no claim of runtime acceptance.


## Large-journal state repair22/10

ActualAndroid SAF initiation hit GET/api/state409 JSON_SIZE after delivery export crossed aggregate journal128KiB. Read-only journal observation:36records131397bytes,largest22355bytes. Cause: oldrecords() cloned entire array with per-document128KiB canonicalizer, also breakinghostrestart. FIELD02ownstorefork changes only records projection torecords.map(copy), preserving bounds and existingbytes. host-store02 eightmockchecksPASS includingoldfailure,restart,deepcopy,oversizedsingle record andHTTP200. host-store01 sandboxEPERM retained. Host-source-check03 validates syntax and57flightpins. LiveAndroid SAF requiresparentmanagedapprestart; noNativeSAFacceptance claimed frommock.


## Final bounded network bootstrap and admission correction

DECISION05 permits at most7 total requests, preserving the earlier below29GiB prelaunch refusal and at most6 actual AP starts. Only flight01 length>=6→>=7 andruntime <=6→<=7 changed; prior57pins archived inhost-source-pins-before-seven-attempts01 andcurrent57pins refreshed. No resource/freshness/time/profile change.

Productionnetworkbootstrap flushes first validated actualnetworkkey once, at most1500ms, demands exacttimestampoutput, retainsconfigureddecoder acrossoneexplicitresyncrecoveryId andskipsdelta untilitsfreshkey. Callbackidentity+epoch+configguards closeinvalidlateframes beforecounter/canvas/pendingeffects. Preview/measurementavailableonlyafterpostflushwarmkeyactuallyoutputs. No localdummyframes/no nativecodechange. Productionhelper8mockchecks,actualviewer8mockchecks andindependentQA5checksPASS; actualAndroidcoldstart/performance stillrootgate. Sourcecheck04 syntax and57pinsPASS. No more Builderproductioneditsinthiscycle;root owns restartapp08/UI.


## Actual cold network FAIL and startup-position presentation repair

Parent4-coreAndroidfirstnetworkflush1500mstimedout: bootstrap1/0/0,error1,elapsed1509ms,output0. RetainFAIL; no furthermediaalgorithmrepair. Read-only codec log doesnotidentifyVP8cause. Localprobeencoderwasflushedbutnotclosedbeforedecoderflush; quiescentvscontinuousproducer remainsuntested. FutureboundedtestmustretainactualnetworkkeybytesandSHA before comparingproduceractive/stopped; do notinfercausefromlocalprobe.

Actualraw n89GPSnull,followingfix0/sats0at0/0 revealedUIpositionusabilitygap. Newposition-validity.mjs UI-onlyfilter rejectsnotusableGNSS andwrongtarget/staleinvalidgeography; allsharedmetrics/markers useit.20mockchecksPASS includinglegitimate0/0withgoodGPS. staticapproute added; noflightpins/coreauthoritychange. Sourcecheck05 verifies57pinsunchanged. Parentmustrestart/reloadonlyafteractiveAPcloses; noNativeUIacceptanceclaimed.


## Final UI closure for managedapp09

Localpayloadtoken nowclearsbeforeheaderpaint whenrunabsent, clientinactiveorpositionunknown; a newrun/foregroundneverrecreatesit. Serverauthorityunchanged. Sevenunit/CSSdeclarationchecksPASS. DAYenabledprimarybuttons use#51420b; declaredwhitecontrast9.84:1 butactualglasspixelcontrastneedsAndroidQA. HeaderusescompactFIELD02 · Android / host,12px/16pxsessionline and11px/14pxownersline within48pxtarget. NoUIoverhaul. IndependentQAidentifiedundefinedidentityequality; helpernowrequiresnonemptyboundedcontextfieldsbeforecomparison. Positionunit22/22PASS; original20checkevidenceretained. Finalsourcecheck05 replacedonlyafterpreservingexactpreviousbytesinhost-source-check05-before-ui-closure.json;57flightpinsunchanged. No furthermediapatch/retry/SITL/APKlaunchbyBuilder.
