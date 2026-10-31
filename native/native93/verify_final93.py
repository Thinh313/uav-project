"""VERIFY phase: read retained artifacts only, no flight or Android actions."""
from pathlib import Path
import json,hashlib,tarfile,base64,zipfile
from receiver91 import trace
R=Path(__file__).resolve().parents[2];E=R/'evidence/native93';read=lambda n:json.loads((E/n).read_text());sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(name,v):
 assert v,name;checks.append(name)
b=read('build02.json');ck('Final source matches APK02 build',all(sha((R/n).read_bytes())==h for n,h in b['sourceFiles'].items()))
with zipfile.ZipFile(R/b['apk'])as z:ck('Every packaged asset matches build source',all(sha(z.read('assets/cockpit/'+n.removeprefix('assets/')))==h for n,h in b['sourceAssets'].items()))
ck('Installed APK readback after reboot is delivered signed02',read('installed02.json')['exactDelivered']and read('installed02.json')['sha256']==b['sha256']==sha((R/b['apk']).read_bytes()))
ck('Shared model92 and fixture retained exact bytes from92',all((R/'native/native93/assets'/n).read_bytes()==(R/'native/native92/assets'/n).read_bytes()for n in ['mission92.mjs','mission-fixtures92.mjs']))
ck('Protocol mock before SITL: polygon/corridor plus revoke/restart',read('mock92.json')['checks']==34 and read('mock93.json')['checks']==11 and read('mock92.json')['status']==read('mock93.json')['status']=='PASS')
ck('False completion mutations rejected after successful integrity rehash',read('receiver-false-completion93.json')['status']=='PASS'and read('receiver-false-completion93.json')['checks']==2 and all(v['integrityPassed']and v['semanticRejected']for v in read('receiver-false-completion93.json')['results']))
model=set();mission=set();plans=set();boots=set();containers=set();runs=[]
for label in ['nominal','link','restart']:
 q=read(label+'-qualification.json');s=read(label+'-closed.json');r=s['review'];run=q['run'];out='runs/'+run+'/';raw=read(out+'raw-verification-final.json');rec=json.loads((R/q['rawReceipt']).read_text());launch=read(out+'launch.json');session=read(out+'session.json');expected=label=='nominal';model.add(q['modelSha256']);mission.add(q['missionSha256']);plans.add(q['planSha256']);boots.add(session['boot']);containers.add(launch['containerId']);runs.append({'label':label,'run':run,'accepted':r['accepted'],'failure':r['failure'],'rawRecords':raw['rawRecords'],'rxFrames':raw['incoming'],'txFrames':raw['outgoing'],'missionItems':raw['missionItems'],'cameraCommands':rec['semantic']['cameraCommands'],'readbackCycles':raw['readbackCycles']})
 ck(label+' committed corridor matches independent receipt and raw witness',q['status']=='PASS'and q['missionAccepted']==expected and r['accepted']==expected and r['aborted']==(not expected)and raw['missionItems']==12 and raw['readbackCycles']==2 and rec['semantic']['cameraCommands']==4 and rec['semantic']['missionAccepted']==expected and rec['semantic']['failureVerified']==(not expected)and raw['parameterWrites']==0 and r['actualImages']==0 and not r['authorityRestorable'])
 ck(label+' context pinned source and owned AP closure',launch['speedup']==1 and launch['binarySha256']=='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'and read(out+'closure.json')['stopped']and not read(out+'closure.json')['error'])
 if not expected:
  ack=read(label+'-recovery-ack.json');ck(label+' requires explicit safe-terminal ack without restoring grant',ack['recovery88']['safeTerminal']and ack['recovery88']['acknowledged']and not ack['grant']and r['failure88']['recoveryAcknowledged'])
ck('Three separate AP boots/runtimes use exactly one committed model/plan/mission',len(boots)==len(containers)==3 and len(model)==len(mission)==len(plans)==1)
ck('Disconnect actually cuts duplex and grant',read('link-cut.json')['recovery88']['cutReason']=='EXPLICIT_DUPLEX_CUT'and not read('link-cut.json')['grant'])
ck('APK force-stop triggers foreground lease expiry and no automatic grant',read('restart-lost-foreground.json')['recovery88']['cutReason']=='NATIVE_FOREGROUND_LEASE_EXPIRED'and not read('restart-lost-foreground.json')['grant']and not read('restart-reopened.json')['grant'])
for a,c,label in [('restart-before-kill.json','restart-after-reopen.json','Airborne app restart'),('android93-before-reboot.json','android93-after-reboot.json','Closed Android reboot')]:
 x,y=read(a),read(c);ck(label+' preserves every workspace byte and CURRENT',x['files']==y['files']and x['selected']==y['selected'])
ck('SAF ledger unchanged after Android reboot',read('diag-ops-before-reboot.json')['files']==read('diag-ops-after-reboot.json')['files']and len(read('diag-ops-after-reboot.json')['operations'])==1 and read('diag-ops-after-reboot.json')['operations'][0]['phase']=='COMPLETED')
cold=read('android93-cold-host.json');ck('Cold host restores no plan/binding/session/grant',cold['run']is None and cold['binding92']is None and cold['plan']is None and not cold['grant']and not cold['authorityRestored'])
r=read('receiver93-final.json');ck('SAF receiver recompile keeps interrupted last review and current trace HEAD',r['status']=='PASS_LOCAL_INTEGRITY_AND_SEMANTICS'and r['currentHeadReferencesVerified']>=1 and not r['workspaceSemantic'][1]['accepted']and r['workspaceSemantic'][0]['modelSha256']in model)
ck('Pinned backend/compiler/source dependencies unchanged',all(sha((R/n).read_bytes())==h for n,h in read('flight-pins.json')['files'].items()))
ck('62059 protected earlier paths unchanged',read('preservation-after.json')['status']=='PASS'and read('preservation-after.json')['count']==62059)
for n in ['90','91','92']:ck('Prior Android'+n+' private workspace/trace unchanged',read('native'+n+'-private-final.json')['status']=='PASS')
allowed={read(p.name)['sourceId']for p in E.glob('build[0-9][0-9].json')};traces={};art=[];history=[]
with tarfile.open(E/'android93-closed-files.tar')as t:
 for m in t.getmembers():
  if not m.isfile():continue
  data=t.extractfile(m).read()
  if m.name.startswith('./diagnostics90/')and m.name.endswith('.jsonl'):
   v=trace(data,Path(m.name).stem,allowed);traces[Path(m.name).stem]=v
   for line in data.splitlines():
    p=json.loads(base64.b64decode(json.loads(line)['payloadBase64']))
    if p['kind']=='ART_SELF_TEST':art.append({'sourceId':v['sourceId'],**p['data']})
  if m.name.startswith('./workspaces/initial/sitl/')and m.name.endswith('.bin'):
   v=json.loads(data.split(b'\n',6)[6]);history.append({'run':v['run'],'accepted':v['accepted'],'aborted':v['aborted']});expected=json.loads((E/'runs'/v['run']/'review.json').read_text());ck('Android persisted exact host review '+v['run'],v==expected)
ck('Three distinct review records retained; no failure promoted',len(history)==3 and len({x['run']for x in history})==3 and sorted(x['accepted']for x in history)==[False,False,True])
ck('Final APK guard33 actually executed on Android ART',any(x['sourceId']==b['sourceId']and x['status']=='PASS'and x['runtime']=='ANDROID_ART'and x['checks']==33 for x in art))
ck('125 foreground/busy/file gate host checks pass',read('filegate-tests02.json')['status']=='PASS'and read('filegate-tests02.json')['checks']==125)
ck('Owned runtime/PID/ports closed cleanly',read('runtime-closure.json')['status']=='PASS')
ck('20GiB storage floor preserved without emulator errors',read('android-closure.json')['minFreeBytes']>=20*2**30 and read('android-closure.json')['error']is None)
result={'status':'PASS_ENGINEERING_CORRIDOR_ANDROID_SITL_FAULT_RESTART','checkCount':len(checks),'checks':checks,'requirementCoverage':{'implemented':6,'total':6,'percent':100,'scope':'REQ93-01..06 only; not whole product readiness'},'scenarioResults':runs,'technicalHealth':{'build':'PASS02','mockCases':45,'fileGateCases':125,'ARTGuardCases':33,'falseCompletionCases':2},'overallStatus':'READY_FOR_SCOPED_ENGINEERING_DELIVERY','apkSha256':b['sha256'],'sourceId':b['sourceId'],'diagnosticTraces':len(traces),'diagnosticEvents':sum(x['records']for x in traces.values()),'history':history,'limits':['One synthetic corridor fixture, not customer-wide KML corpus','ArduPilot internal quad, not physical Hera/payload/video/physics qualification','Force-stop APK while airborne; Android reboot/cold bridge after closure, not autopilot reboot airborne','64KiB KML;10..30m;0.5..2m/s;synthetic Home/camera/flat terrain','Host compiler bridge still required; no standalone HeraHub release','No production signing/candidate promotion/ENDURE24h/pacing acceptance']};(E/'final-verification.json').open('x').write(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in ['checks','history','scenarioResults']}))
