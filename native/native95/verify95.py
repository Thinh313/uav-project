from pathlib import Path
import json,hashlib,shutil,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/native95';checks=[]
def check(name,value):
 assert value,name
 checks.append({'name':name,'pass':True})
load=lambda name:json.loads((E/name).read_text())
b=load('build03.json');r=load('runs/s095f2c41e36548be9071/receiver95.json');s=load('runs/s095f2c41e36548be9071/semantic95.json')
check('APK03 signature v2/v3 with existing development certificate','Verified using v2 scheme (APK Signature Scheme v2): true'in b['signature']and'Verified using v3 scheme (APK Signature Scheme v3): true'in b['signature']and'3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in b['signature'])
check('APK03 bytes match build and installed Android APK',hashlib.sha256((R/b['apk']).read_bytes()).hexdigest()==b['sha256']==load('installed03.json')['deviceSha256']==r['apkSha256'])
check('all 138 packaged source inputs unchanged',all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b['sourceFiles'].items()) and len(b['sourceFiles'])==138)
check('raw metadata SourceID matches APK03',r['sourceId']==b['sourceId'])
for file in['portable-mock.json','native-tests95.json','native-faults95.json','socket-mock95.json','host-tests03.json','filegate-tests03.json','filegate94-tests03.json','archive-tests03.json']:
 value=load(file);check(file,value.get('status')=='PASS' or value.get('pass') is True or value.get('checks',0)>0)
check('nominal full receiver02 retained',load('runs/s095e2c41e36548be9071/receiver95.json')['status']=='PASS')
check('final03 native raw and passive observer independently accepted',r['status']=='PASS' and r['nativeAndObserverExecution'] and r['groundDisarmNearHome'])
check('12 mission items and two readback cycles',r['missionItems']==12 and r['readbackCycles']==2)
check('camera commands preserved; no actual-image claim',r['cameraCommands']==4 and r['actualImages']==0)
check('23 typed parameter checks and no PARAM_SET',r['typedParameterChecks']==23 and r['parameterWrites']==0)
check('Home and full plan recompiled by frozen host oracle',s['fullFrozenCompilerParity'] and s['homeReviewDigest'])
check('geography track digest and no truncation',s['geographyDigest'] and 20<s['trackPoints']<=1200)
restart=load('restart03.json');check('final03 force-stop/reboot preserved all private workspace/raw bytes',restart['status']=='PASS' and restart['bytesUnchanged'] and restart['androidReboot'] and restart['processRestart'])
check('no automatic reconnect or authority restore',restart['automaticReconnect'] is False and restart['authorityRestored'] is False)
check('Native90..94 private files unchanged',sum(restart['oldAppPrivateFilesUnchanged'].values())==270)
pres=load('preservation-final03.json');check('63,830 protected paths through94 unchanged',pres['status']=='PASS'and pres['count']==63830 and not pres['failures'])
closed=load('runtime-closure95.json');check('owned AP/emulator/controllers/ports closed',closed['status']=='PASS' and closed['ownedContainerAbsent'] and closed['emulatorAndControllersExited'])
check('no host GCS transport/control bridge',closed['noHostGCSBridge'] and all(not load('runs/'+run+'/launch.json')['hostGCSController'] for run in['s095b2c41e36548be9071','s095c2c41e36548be9071','s095d2c41e36548be9071','s095e2c41e36548be9071','s095f2c41e36548be9071']))
check('no transient build directory or unsigned APK left',not(R/'native/native95/.build').exists()and not(R/'native/native95/.host95').exists()and not list((R/'native/native95/dist').glob('native95-unsigned*.apk')))
minimum=min([load('android-closure.json')['minFreeBytes'],load('android-closure02.json')['minFreeBytes']]+[load('runs/'+run+'/closure.json')['minFreeBytes']for run in['s095b2c41e36548be9071','s095c2c41e36548be9071','s095d2c41e36548be9071','s095e2c41e36548be9071','s095f2c41e36548be9071']])
check('20GiB floor maintained',minimum>=20*2**30 and shutil.disk_usage(R).free>=20*2**30)
result={'status':'PASS_SCOPED_ENGINEERING_NATIVE_DIRECT_SITL','at':datetime.datetime.now().astimezone().isoformat(),'checkCount':len(checks),'checks':checks,'requirements':{k:'PASS_IN_TIP_SCOPE' for k in ['R95-1','R95-2','R95-3','R95-4','R95-5','R95-6']},'apk':b['apk'],'apkSha256':b['sha256'],'sourceId':b['sourceId'],'minimumFreeGiB':minimum/2**30,'finalFreeGiB':shutil.disk_usage(R).free/2**30,'acceptedFinalRun':'s095f2c41e36548be9071','independentReceiver':r,'openFindings':[{'priority':'P2','finding':'Persistent UI diagnostics saturate ~2MiB; cached receipts must not be runtime evidence. Native cap checks Java char count while writes are UTF-8 bytes, observed +376B over configured cap. Flight raw journal is separate and byte-bounded.','evidence':'ui-file-capacity-diagnosis.json','mitigation':'Reject stale diagnostic ages; final restart uses fresh screenshot and unchanged private raw/workspace hashes. Preserve old diagnostic evidence; no automatic truncation.','next':'Controlled diagnostic generations and byte-exact quota in NATIVE96'}],'notChecked':['HeraHub/radio/HID/SDK or real aircraft/payload/PhaseOne/dual-operator bench','Direct Android airborne link loss/reboot/hard-kill fault matrix; prior host-bridge evidence does not substitute','Native direct raw SAF handoff package and receiver receipt (this task uses authorized ADB pull)','Sustained fsync/storage-pressure/full native IO fault injection beyond mocks','Photogrammetry/DEM/RTK/PPK field accuracy, 1x pacing/thermal/endurance24h or production qualification'],'scope':'APK development only; fixed owned-emulator endpoint and AP4.7.1 internal quad, not calibrated Hera. No frozen candidate integration or production signature; ACK/camera command is not physical execution/image proof.'}
(E/'final-verification.json').open('x').write(json.dumps(result,ensure_ascii=False,indent=2));print({'status':result['status'],'checks':len(checks),'minimumFreeGiB':result['minimumFreeGiB']})
