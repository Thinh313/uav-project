# FIELD02 repair01 current handoff (22/10/2026 ~09:36 local)

User current task: fix FIELD02 cold-start/FPS, DAY contrast, active payload rights at actual AP reboot. Mock then Android–SITL, frozen old source/candidate/ENDURE and20GiB floor. User confirmed will keep>=29GiB; actual now~30.6. User supplied replacement AGENTS adds Word/PDF orphan-word rule, unrelated here. Use personalVibecode6.3 Contractor/Builder/QA separation.

## Live / budgets

- Emulator repair launch02 PID92539, controller session39789, serialemulator-5582, AVDaeris-field02, Android13/WebView101,2048MiB/4CPU verifiedCPUonline0-3. Starts02:14:54Z, hard1h ends10:14:54local. Root has explicit prior user ADB/UIAutomator+adbroot permission only emulator5582. APK unchanged vn.rtr.aeris.field02. Reverse8872/8873 established. No physicaldevice.
- Emulator repairlaunch01 closed clean. Root discovered copiedcontroller used2CPU despiteplanned4; correction+oldrunner retained qa-runtime-cpu-correction.json. All exact-key diagnostic proof at2CPU; never claim4CPU.
- Latest companion app06 PID from repair01/host-app06/app-launch.json is CLOSED clean, as app01..05. Next new output app07 should use `--workspace=evidence/field02/repair01/workspace --allow-sitl`. `allow-sitl` permits laterfixedlocaltarget; doesnotstartAP. Loopback8872 control/8873media.20min companiondeadline.
- ZERO new AP requests/starts in repair01 so far. Existing old7 request dirs unchanged. Authorized exactly2 new requests/starts, cumulativecap9. No retry uncertainPOST. Root uses actual Android UI for flight actions, readonlyGETstate observes. No extra emulatorlaunch/nativebuild/sign.
- Sourcephase07 is pending Builder/QA at time note. No AP until finalmock/sourcefreeze +31stable29GiB samples (flight.connect internally samples31). Runtimeguard21 floor20, speedup1/noPARAMwrites.
- Protected1486oldbaseline/native7 unchanged; all1081oldFIELD02evidencefile hashes preserved in repair01/preservation-before.json. Newworkspace is smallverified14file datafork700KiB of oldworkspace; don'tappendoldworkspace. Oldflight/runs may appendnewrun dirs, NEVERrewrite oldsource-pins.json.

## Source / agents

Existing agents /root/field02_host videoBuilder, /root/field02_android authorityBuilder(done), /root/field02_qa independentQA. Use followup_task to wake idle, send_message doesn'twakeidle.
Host owns media/*/media-panel.mjs; approved sole ui.mjs noopcallback removal. AuthorityBuilder owns gateway/app/ui/css/fault helper; source native untouched.
Latest completed freeze06 `media-presentation-source-freeze06.json`27files source/mock/QA passed. Changes: firstvalidatedkey configures decoder ONCE, optionalobserver skips hugeunusedclone; routineUI/readout<=10Hz, decoder/canvas/sample/identity+criticalevents immediate. All target/profile/queue/clocks unchanged. Publisher still freeze04 instrumentation before phase07.
Phase fix explicit approval planning/field02/repair01/DECISION-SOURCE-CADENCE.md: exactlyONE source scheduler repair based actualmedian35.7ms/27.43Hz quantization. Absolute30Hzphase; atmostONEactualrawcapture/callback, countmissedscheduledslots, no burst/fakeclock/profilechange. Separatecreditdrops. Await freeze07+QA then rootone30s window; no endlessFPSloop.
Flightcaps prepared by AndroidBuilder and independentQA: ownflight01>=9/runtime<=9. `pins()` reads fixednew `evidence/field02/repair01/flight-source-pins.json`,57files SHA46e2266eef05c2ad85dacf7e425ca696b0a16a088c895d43075968005c51f43b. Oldmanifest unchanged. pin.mjs --repair01 exclusivewx. No moreflightcodeedit expected.

## Evidence so far (all retained, no READY)

- Exactnetworkkey diag app02: network-key-dba49c21-03d1-4c3f-b922-9662186be9cd-report.json/.bin, packet14332B key13883B, ACTIVEflush36ms/STOPPED13.1ms, samekeySHA113e225...; QAverified. No normalviewer started beforeprobe. Refutes blanketcodec/keyincapability, not streamacceptance. ActiveACK37.6ms no encodedcounterdelta, don'tinfercontinuousencodecausality.
- app02 attemptedbaseline neverstarted (disabledmeasure); later sourceCLOCK_CALIBRATION_UNKNOWN. baseline-unstarted01.json; noFPSclaim. Actual2CPU.
- app03 freshboot4CPU/no probe/firstviewer: configure1/reset0, bootstrap413.5ms only. Actualreport01 595frames19.8314fpsFAIL24, p95upper222.575PASS300, firstoutput1504.3, initialReady2009.5FAIL1500, relay500 recovered615.4PASS2s. QAqa-cold-media03.json exact. Earlier commentpositivebootstrap is notwholecoldreadyPASS.
- app04 instrumentationonly report01 207frames6.8977fpsFAIL, p95660.039FAIL, ready1239.9PASS processcold/samewarmemulator; nofault. Sourcephase timings showedcheapdraw/VF butencodecall/backlog+fullcredits. Hostloaduncontrolled, no intrinsiccauseclaim.
- app06 cycle2 report01 686frames22.8659FAIL24, p95171.976PASS, ready490.9PASS, relay500 recovery555.9PASS. QAqa-media06.json. Sourceeligible snapshotdelta823/~30s=27.43Hz; latest64eligiblegapmedian35.7ms, creditdrops123/823; motivatesonephasefix. Counterfactual~25fpsnotpromise.
- Actual DAY contrast: error Viewer:Failedtofetch5.67:1, freshage7.12:1. QAqa-day-pixels01.json. SelectedROI only, noteveryUI/devicecert.
- Authority ownwrapper persists exact pre/post+station/client/run/boot/model/plan+time+seq/hash, synchronouslyclear thenawaitWALbeforefault. FailclosedonanyWALfailure. Upfrontknownaction/scope/confirm validatebeforeinvalidate. Wrongcontext/oldresponse/lategrant mock+realWAL tests pass; lastreceipt persists acrossrestart, rightsneverrestore. Needs actualAPactiveleaseproof.
- Hostresource actual disk fell35→27 while ownnewdata~11MiB. Swap20GiB used but memory_pressure-Q70%free; do notclaimswapcausedFPS/space. Userconfirmed29stable; actuallater30.6. OwnSwiftmodulecache245.85MiB removed early recordedcleanup-cache-early.json, keepOCRbinary. Otherprocesses untouched.

## Root QA helpers

- planning/field02/qa-android-repair01.py savesonly repair01, ownershiplatestrepairlaunch. Commands xy/swipe/capture, eachADBlogged. `owned()`checksAVDserial/qemu/PID. Nativecold: adb shell am start -S -W --user0 -f0x10008000 -n vn.rtr.aeris.field02/.ShellActivity. Doesnotcleardata.
- OCR binary .local/field02/qa-ocr stillpresent, Swiftmodulecachealreadyremoved. Source planning/field02/qa-ocr.swift. OCRreadsPNG only; UIAutomator canstallheartbeat so avoidduringAPtimecriticalactions.
- planning/field02/qa-ui-sequence-repair01.py LABEL [cut|reboot] usesactualADB+freshOCR, readonlyhostGET, exactHomefixture10.854/106.807/MSL10, autoexpiry>1800ms. Preflightreadywait90sec, freshprearmcohort, arm/Home/AUTO. Itdoesnotconnect/selectpayload. RootcanrunthenhandlefaultUI separately orscriptreboot; faultairborneadmission>5m.
- planning/field02/qa-observe-repair01.py LABEL SECONDS readsGETstate1Hz<=600sec, bounded2MiB, selectspayloadAuthority+flight etc. NoPOST.
- QA prepared planning/field02/repair01/qa-postfault-payload.mjs: afterclosedSITLrun +sameactiveclient sendsONEpayload-only gimbalnegative oldflightcontext, fixedinvalidplaceholdertoken (notrealoldtoken), expectsPAYLOAD_REQUEST_IDENTITY beforetokenread, noWALcommandintent/datachanges. Input11keys gatewaySession/stationId/clientId/clientEpoch/clientInstance/flightRun/flightBoot/modelSha256/planSha256/generation/deviceId fromrealprelease/receipt. NOPOSTflight/retry. Correctoldtoken policy separatelymocktested. Useactualdurablepre/post toprove livelease revoke, notthisnegativealone.

## UI1280x800 / next live plan

InitialAPKviewPLAN; Fly52,145; preflight52,279 opensrightconsole; review52,348. Header theme1051,56; consoleclose1123,190. Console tabsflight830247/payload960247/review1090247. Leftmedia controls stable: setup420539 then codec565300/VP8option565404/source275358/viewer275414/setupclose420224. Measurement194453/relay345453/save495453. BEFOREwait30sec VERIFYscreenshot saysĐangđo30giây; earlierdisabledtap createsNOmeasurement. Bothsourceiframe+viewercanvas visible. Setupopeninvalidatesvisualcoverage. Normalrightconsole doesn'tcoverleftmedia.
Fieldmode dropdown~875495 thenSITLoption~565? actualinspectpopup, connect1080486/503. Rootmustverifyexactdf>=29beforetap toavoidwastingrequest; internal31samplesstillrequired. NewSITLrun under evidence/field02/flight/runs/s... appendonly.
Afterconnecttransportready, scrollconsoleup2x(x1157,550→300) topreflight/grant/upload/armcontrols, useqa-ui-sequence. Forpayloadgrant beforeauto: afterpreflightREADY (EKFwarmed), payloadtab/discover, scrolltopselectRGB→select→grant60s→gimbalmockpositive. Thenflighttab+scrollcontrols, sequencepreflight/grant/upload/preflight/arm/Home/AUTO. Grantimmediatelybeforesequence so60snotexpiredatfault.
TwoAPscenarios planned: nominalAUTO withmedia30s+relay500ms concurrent (keepFly/sourcevisible), then actualAPreboot at>5m withlivepayloadlease. Forreboot run, durableFLIGHT_REBOOTpre mustshowleaseCount>=1 andhostMonoMs<until; post0 BEFORErawfault sideeffect, actualDockerPID/StartedAtrestart; noautoauthority/run afterclose. GETstate.payloadAuthority exposesreceiptafterclosedrun. Runpayloadnegativeoldcontextbeforebackground/SAF soactiveclientepochstillmatches.
Actual UIflightduration21s corridor +RTL canbequick; savedKMLcorridor modelrev6/12items. Couldchoosepolygonfixturebeforeconnectifnecessary, butdon'tchangeHome/datum orPARAMs. Allphotos/gimbalsynthetic, internalquadnotHera.

## Finish

Need finalactualphasevideo+AP2(ifresource), affectedAndroidrestart/SAFregression, independentQA, old1486/native7/1081oldevidencehashes, allfinalsources/pins. Stopownedcompanion/emulatorcontrollerstoprequest02, fixedcontaineronly; nootherprocesses/volume/containerprune. docker imageprune-f. Cleanupownstage/OCRbinary/remainingQAbytecode, keepAVDuserdata/APK/evidence. Newdelivery COMPLETION-FIELD02-REPAIR01.md/html, originalcompletionunchanged. OverallNOT_READY ifanymandatoryFAIL/NOT_CHECKED; don'tissueDONEbecausebudgetends. NoXiaomi/HeraSDK/production/ENDURErelaunch/commitpush.
