"""Read-only qualification of retained Android/SITL/receiver snapshots. No runtime actions."""
from pathlib import Path
import json,hashlib,zipfile,tarfile,base64
from receiver91 import trace
R=Path(__file__).resolve().parents[2];E=R/'evidence/native92';read=lambda n:json.loads((E/n).read_text());sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def check(n,v):
 assert v,n;checks.append(n)
build=read('build08.json');allowed={read(p.name)['sourceId']for p in E.glob('build[0-9][0-9].json')}
check('Final source bytes match packaged development08',all(sha((R/n).read_bytes())==h for n,h in build['sourceFiles'].items()))
with zipfile.ZipFile(R/build['apk'])as z:check('Packaged assets byte-identical to build source',all(sha(z.read('assets/cockpit/'+n.removeprefix('assets/')))==h for n,h in build['sourceAssets'].items()))
check('Installed APK after reboot matches exact development08 signature-verified artifact',read('installed08.json')['exactDelivered']and read('installed08.json')['sha256']==sha((R/build['apk']).read_bytes())==build['sha256'])
for a,b,label in [('android92-before-app-restart07.json','android92-after-app-restart07.json','App restart'),('android92-before-update08.json','android92-after-update08.json','APK update'),('android92-before-reboot08.json','android92-after-reboot08.json','Android reboot')]:
 x,y=read(a),read(b);check(label+' preserves every workspace byte and CURRENT',x['files']==y['files']and x['selected']==y['selected'])
check('SAF operation journals byte-identical after reboot',read('diag-ops-before-reboot08.json')['files']==read('diag-ops-after-reboot08.json')['files'])
check('Both diagnostic SAF exports completed with provider readback',len(read('diag-ops-after-reboot08.json')['operations'])==2 and all(o['phase']=='COMPLETED'for o in read('diag-ops-after-reboot08.json')['operations']))
cold=read('android92-cold-host08.json');check('Cold host does not restore plan/model binding/session/authority',cold['run']is None and cold['binding92']is None and cold['plan']is None and not cold['grant']and not cold['authorityRestored'])
for v in ['90','91']:check('Prior Android'+v+' sandbox unchanged',read('native'+v+'-private-preservation-final.json')['status']=='PASS')
check('60507 protected prior paths unchanged',read('preservation-after.json')['status']=='PASS'and read('preservation-after.json')['count']==60507)
check('Pinned backend/AP/compiler/model bytes unchanged',all(sha((R/n).read_bytes())==h for n,h in read('flight-pins.json')['files'].items()))
check('Protocol mock first: polygon and corridor 34 cases pass',read('mock92.json')['status']=='PASS'and read('mock92.json')['checks']==34)
check('Independent receiver refuses 20 adverse cases',read('receiver-negative.json')['checks']+read('semantic-negative92.json')['checks']==20)
for run,suffix in [('sdd2b59b0672441a29b94','07'),('sd9ad41fb943340d28f38','08')]:
 r=read('runs/'+run+'/review.json');raw=read('runs/'+run+'/raw-verification-final.json');oracle=read('upstream-raw-oracle-'+('final07'if suffix=='07'else'closed08')+'.json')
 check('AUTO completed with independent raw witnesses '+suffix,r['accepted']and not r['aborted']and not r['failure']and raw['executionVerified']and raw['missionItems']==16 and raw['readbackCycles']==2 and raw['transfer']['cameraCommands']==6 and raw['partialRXBytes']==raw['partialTXBytes']==0 and oracle['status']=='PASS'and oracle['parameterWrites']==0)
 check('Review retains complete original model '+suffix,r['model92']['sha256']==read('receiver92-final'+suffix+'.json')['workspaceSemantic'][0]['modelSha256']and r['actualImages']==0 and r['authorityRestorable']is False)
for suffix in ['07','08']:
 r=read('receiver92-final'+suffix+'.json');check('SAF receiver independently recompiles KML/model and review '+suffix,r['status']=='PASS_LOCAL_INTEGRITY_AND_SEMANTICS'and r['workspaceSemantic'][0]['phase']=='COMPILED_MODEL92'and r['workspaceSemantic'][1]['accepted']and r['workspaceSemantic'][0]['missionSha256']==r['workspaceSemantic'][1]['missionSha256'])
check('Final trace links captured current review HEAD',read('receiver92-final08.json')['currentHeadReferencesVerified']>=1)
receipts=[read(str(p.relative_to(E)))for p in(E/'independent-raw-receiver').glob('*.receipt.json')];check('Both portable raw receivers qualify execution',len(receipts)==2 and all(r['missionAccepted']and r['semantic']['status']=='PASS'and not r['authorityRestored']for r in receipts))
a,b=read('android92-journal-closed08.json'),read('android92-after-mutant08.json');selected='workspaces/'+a['selected'];check('Rehashed camera mutant never activated or changes selected model/review',a['selected']==b['selected']and a['journals'][selected]==b['journals'][selected]and a['journals'][selected+'/sitl']==b['journals'][selected+'/sitl'])
traces={};art=[];counts={}
with tarfile.open(E/'android92-closed-files08.tar')as t:
 for m in t.getmembers():
  if not m.isfile()or not m.name.startswith('./diagnostics90/')or not m.name.endswith('.jsonl'):continue
  raw=t.extractfile(m).read();v=trace(raw,Path(m.name).stem,allowed);traces[Path(m.name).stem]=v
  for line in raw.splitlines():
   event=json.loads(base64.b64decode(json.loads(line)['payloadBase64']));kind=event['kind'];counts[kind]=counts.get(kind,0)+1
   if kind=='ART_SELF_TEST':
    d=event['data'];check('ART guard runtime '+Path(m.name).stem,d['status']=='PASS'and d['runtime']=='ANDROID_ART'and d['checks']==33);art.append({'sourceId':v['sourceId'],'checks':d['checks']})
check('Final APK08 guard actually ran on ART',any(v['sourceId']==build['sourceId']for v in art))
check('New file gate suite passes125cases',read('filegate-tests08.json')['status']=='PASS'and read('filegate-tests08.json')['checks']==125)
closure=read('runtime-closure.json');check('All owned runtimes and ports closed',closure['status']=='PASS')
check('Storage stayed above20GiB floor',read('android-closure.json')['minFreeBytes']>=20*2**30 and not read('android-closure.json')['error'])
r={'status':'PASS_ENGINEERING_ANDROID_SITL_MODEL92','checkCount':len(checks),'checks':checks,'sourceId':build['sourceId'],'apkSha256':build['sha256'],'diagnosticTraces':len(traces),'diagnosticEvents':sum(v['records']for v in traces.values()),'artGuardExecutions':art,'eventCounts':counts,'scope':'ISOLATED_INTERNAL_QUAD_ENGINEERING_NOT_HERA_NOT_PRODUCTION','limits':['Actual SITL only polygon default; corridor protocol mock qualified','Camera/Home/terrain synthetic pinned fixtures; no physical calibration or real photos','64KiB KML and bounded simulator envelope10..30m/0.5..2m/s','Imported models require host compiler; no self-contained offline parser','Legacy Native44 capsules not silently migrated; prior apps preserved','Rejected import remains isolated staging; no automatic deletion','No HeraHub/HID/video/PhaseOne/ENDURE/pacing/hardware acceptance']};(E/'final-verification.json').open('x').write(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k not in ['checks','eventCounts']}))
