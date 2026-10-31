"""Contractor findings, bound to existing evidence; never modifies product or old receipts."""
from pathlib import Path
import json,hashlib,datetime,subprocess,socket,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03';REC=R/'.local/simstability03/receiver03'
def get(n):return json.loads((E/n).read_text())
def put(n,v): (E/n).open('x').write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
pres=get('preservation-final01.json');raw=get('manual-flight-raw-audit01.json');oracle=get('original-model-replay01.json');saf=get('receiver-saf04.json');freeze=get('media05-freeze-comparison.json');cold=get('cold-host04-before-start.json');ground=get('media05-ground-disarm.json');native=get('saf-import04-physical-target/state.json')
assert pres['status']=='PASS'and oracle['status']=='EXACT_ORIGINAL_MODEL_BYTES_PASS'and raw['inputsUnchanged']and raw['review']['success']and saf['tamperedBodyRejected']
assert not cold['controllerActive']and cold['session']is None and cold['boot']is None and not cold['input']['active']
assert native['lifecycle']['closed']and not native['input']['active']and native['review']['run']==raw['run']
closures=[]
for tag in ['01','02','03']:
 src=R/('.local/simstability03/receiver'+tag)
 assert not(src/'evidence/simhand01/control/.host.lock').exists()
 for p in (src/'evidence/simhand01').glob('host-*/launcher-closure.json'):
  q=json.loads(p.read_text());assert q['hostExit']is not None;closures.append({'path':str(p.relative_to(R)),**q})
active=subprocess.check_output(['docker','ps','--filter','label=aeris.task=simhand01','--format','{{.ID}}'],timeout=5).decode().strip();assert not active
ports={}
for port in [8896,5582,5583]:
 with socket.socket()as s:ports[str(port)]=s.connect_ex(('127.0.0.1',port))!=0
assert all(ports.values())
emulator=get('emulator-closure02.json');assert emulator['exit']==0
sizes={tag:sum(p.stat().st_size for p in (R/('.local/simstability03/receiver'+tag)/'evidence').rglob('*')if p.is_file())for tag in ['01','02','03']};assert sum(sizes.values())<3*2**30
runtime={'atUTC':now,'status':'OWNED_RUNTIMES_CLOSED','hostClosures':closures,'ownedAPContainersRunning':False,'portsRefusingConnections':ports,'emulator':emulator,'runtimeEvidenceBytes':sizes,'cumulativeRuntimeEvidenceGiB':sum(sizes.values())/2**30,'taskBudgetGiB':3,'userAdmissionGiB':20,'userRuntimeFloorGiB':10,'reserveMiB':256,'forecastSeconds':15,'freeBytes':shutil.disk_usage(R).free,'dockerImagePrune':'Completed; reclaimed0B; no containers or volumes removed','scratchProjectCopiesCreated':0,'cleanupRemovedFiles':[]}
put('runtime-final01.json',runtime)
media={'atUTC':now,'run':ground['run'],'status':'PARTIAL_NOT_FULL_MEDIA_ACCEPTANCE','actualPBRRender':'Observed in task-owned Android WebView screenshots; GLB/HDR/PBR visible','audioGesture':'Trusted native tap changed mute icon to audio icon','audioTrack':'AudioFlinger reports an active48kHz track; no PCM recording, per-track UID proof or calibrated audible output established','faultInjection':'ADB reverse mapping removed then restored; established socket kept live updates, so this is NOT a demonstrated link outage','sceneROIEquality':freeze,'staleFreezeVerdict':'NOT_CHECKED_FAULT_NOT_ESTABLISHED','landObserved':ground['vehicle']['mode']=='LAND'and not ground['vehicle']['armed']and ground['physics']['ground'],'reviewDriver':'After LAND, next navigation pixel template mismatch stopped driver with no navigation action. Operator did not close before immutable trace recorder exhausted. No automatic flight retry.','finalRunVerdict':'FAILED_INTERRUPTED; retained and excluded from successful manual capture','fpsOrPhotonLatency':'NOT_MEASURED','projectorAndLaptopBrowser':'NOT_CHECKED','physicalHeraCalibration':'NOT_CHECKED'}
put('media05-contractor-audit01.json',media)
rows=[
 ('AC01','failed lifecycle cleanup and explicit restart','PASS_SCOPED','gateway-fault-tests05.json; actual AP01/AP03/AP05 failed closures; allOwnedClosed; no successful-flight inference'),
 ('AC02','native preflight/Home/takeoff/manual pitch+yaw/LAND/disarm/review','PASS_SCOPED','AP04 actual ADB touch actions and independently checked raw ACK/HB/RC/WAL'),
 ('AC03','neutral claim/release/session and boot fences','PASS_SCOPED','AP04 observed two neutral/manual handoffs and GUIDED releases; independent-handoff03.json; fixed TTL200ms/HB1500ms'),
 ('AC04','background revokes input without restoring authority','PASS_OBSERVATION_ONLY','AP03 background03-revoked.json; held GUIDED reference altitude. AP03 final run failed and is not promoted'),
 ('AC05','cold host history/restart never restores lease','PASS_SCOPED','cold-host04-before-start.json has null run/session/boot, no input; prior failed history retained'),
 ('AC06','durable review plus native SAF export/import and receiver','PASS_SCOPED','SAF-manual04 exact SHA; actual Android import; receiver-saf04 tamper rejection; external raw not embedded'),
 ('AC07','pacing >=1x with complete captured frame/WAL/AP correlation','PASS_ONE_RUN','AP04 RTF1.000696;116815 admitted contiguous frames; no AP required-stage gaps; fsync-before-sensor retained'),
 ('AC08','optimized sensor/model output matches immutable original','PASS_EXACT_OFFLINE','Original pure-Python replay116815 frames;0 sensor UTF8 or modelAux byte mismatches; not Hera calibration'),
 ('AC09','consistent bounded300s lifecycle and capture duration','FAIL','AP recorder exhausted on AP03/AP05 before full300s; life() activeAPSeconds keeps advancing after closed. Manual04 remained within short verified capture'),
 ('AC10','3D/audio/stale freeze and visual performance','PARTIAL','Actual PBR view and audio gesture observed; no PCM/FPS/photon measurement; reverse removal did not interrupt established socket'),
 ('AC11','explicit AP reboot fault and recovery in final native build','NOT_CHECKED','Host restart and background tested; AP reboot is not equivalent and was not exercised in final runtime')
]
ac=[dict(zip(['id','requirement','status','evidence'],r))for r in rows]
q={'format':'aeris-simstability03-contractor-qualification','version':1,'atUTC':now,'assemblyAuthorized':True,'sourceManifestSHA256':'df3eb4ec961e2fc83116440ec017796593b36847f2e1a601e7dd0a8b11ec5c8f','status':'NOT READY','runtimeAcceptance':'MANUAL_ANDROID_SITL_SLICE_PASS_FULL_MILESTONE_NOT_READY','scope':'Engineering diagnostic handoff only; no production/physical aircraft/market-readiness claim','userOutcome':'One complete actual native-touch manual reference-quad flight, durable review and SAF export/import, with raw/model byte evidence. Full simulator stability milestone remains blocked.','requirementCoverage':{'requirements':11,'scopedPassOrObservation':8,'failed':1,'partial':1,'notChecked':1,'percentageClaim':None},'acceptance':ac,'verifiedOutcomes':[
 'Actual engineering APK on owned emulator5582 completed typed preflight/Home, GUIDED takeoff, neutral LOITER claim, bounded pitch and yaw, GUIDED release, LAND/ground/disarm, durable review and native SAF export/import in AP04.',
 'AP04 captured116815 contiguous frames over97.2773 receive wall seconds, RTF1.000696. WAL CRC/SHA chain and AP required frame stages checked with0 missing/duplicate required records. fsync-before-sensor, speedup1 and500ms cap retained.',
 'Independent replay of the same116815 captured PWM frames through the immutable original pure-Python model matched all sensor UTF8 and modelAux bytes exactly.',
 'Failed runs retained FAILED_INTERRUPTED with no successful-flight inference. Cold host restart restored history only, never session/boot/input lease. Native background revocation observed separately in AP03.',
 'Actual public SAF manual04 package SHA b34b341260663d84c1a0b40f1d8981d7807b64de3f98f35559f177ce81126394 verified and tampering rejected. External raw remains on original host and is not embedded.',
 '17117 protected legacy identities and650 predecessor entries unchanged relative to retained baselines.165 previously missing paths remain recorded. ENDURE history not rewritten; no ENDURE acceptance inferred.'
 ],'remainingGates':[
 'NOT READY overall. Immutable AP recorder capacity did not support full300s captures in AP03/AP05; a separate bounded capture-capacity solution and actual recheck are required without dropping frames or changing firmware silently.',
 'Closed-session activeAPSeconds still advances in public state; freeze elapsed time at exact closure and regression-check late callbacks in a new isolated revision.',
 'Native UI harness must select the actual current page before review navigation; AP05 LAND succeeded, next template mismatch halted driver, then the unclosed session exhausted trace capacity.',
 'Actual scene-loss/audio mute/freeze, final AP reboot and measured visual FPS/photon latency remain unverified. Removing ADB reverse did not prove an established socket outage. Active AudioFlinger track is not measured audible or calibrated Hera sound.',
 'Physical Xiaomi/Hera/HeraHub, real gimbal/camera/payload, projector display, Hera mass/aerodynamics/acoustics/environment calibration, AUTO, SDK and production release are outside this slice or NOT_CHECKED.',
 'Client HTTP input sequence/clock/axes are validated by code/mocks but not directly embedded in raw; wire sequence is a different evidence layer. Generic DJI superiority or training certification is not claimed.'
 ],'technicalHealth':{'rawManualAudit':'PASS_SCOPED','originalModelReplay':'EXACT_BYTES_PASS','preservation':'PASS_BASELINE_COMPARISON','mockReports':['gateway-fault-tests05.json','manual-handoff-tests04.json','independent-handoff03.json','pending-client03-mock01.json','closed-capture-rejection01.json','ui-projection-mock02.json'],'aggregateTestCount':None,'allOldFailuresRetained':True},'valueEvidence':{'status':'MEASURED_NARROW_OUTCOME','before':'AP01 RTF0.6166, frequent default-HB gaps; AP02 premature LOITER descent before input','after':'AP04 RTF1.000696, explicit GUIDED hold until neutral manual claim, complete actual manual flight','notControlledBenchmark':True,'directLLMBaseline':'NOT_APPLICABLE_TO_DETERMINISTIC_FLIGHT_TRANSPORT_REPAIR','modelOrAcousticCalibration':'NOT_MEASURED'},'unchangedPolicy':{'speedup':1,'pacingCapMs':500,'journal':'fsync-before-publish','admissionGiB':20,'runtimeFloorGiB':10,'reserveMiB':256,'forecastSeconds':15},'newAPKBuild':False,'newSignature':False,'productionSignature':False,'authorityRestorable':False,'runtimeStopped':True,'endureAcceptanceClaim':False,'disposition':'Retain verified manual capture and diagnostic package; do not call full milestone done. Next bounded repair is recorder/time accounting + actual socket outage and AP reboot, then media performance.'}
put('qualification-final01.json',q)
print(json.dumps({'status':q['status'],'coverage':q['requirementCoverage'],'runtimeGiB':runtime['cumulativeRuntimeEvidenceGiB'],'qualifiedSourceManifest':q['sourceManifestSHA256']},indent=2))
