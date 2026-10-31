"""Read retained snapshots only; no Android/flight control or source mutation."""
from pathlib import Path
import json,hashlib,tarfile,base64,zipfile
from receiver91 import trace
R=Path(__file__).resolve().parents[2];E=R/'evidence/native91';read=lambda n:json.loads((E/n).read_text());sha=lambda b:hashlib.sha256(b).hexdigest();allowed={read(p.name)['sourceId']for p in E.glob('build[0-9][0-9].json')};build=read('build05.json');checks=[]
def check(n,v):
 assert v,n;checks.append(n)
check('All final source bytes match development05 build',all(sha((R/n).read_bytes())==h for n,h in build['sourceFiles'].items()))
with zipfile.ZipFile(R/build['apk'])as z:check('Every packaged asset matches source05',all(sha(z.read('assets/cockpit/'+n.removeprefix('assets/')))==h for n,h in build['sourceAssets'].items()))
check('Installed APK after reboot is exact delivered signed bytes',read('installed05.json')['sha256']==build['sha256']==sha((R/build['apk']).read_bytes()))
for a,b,label in [('android91-before-update05.json','android91-after-update05.json','APK update'),('android91-before-reboot05.json','android91-after-reboot05.json','Android reboot')]:
 before,after=read(a),read(b);check(label+' preserves every workspace byte',before['files']==after['files'] and before['selected']==after['selected'])
check('SAF ledger preserves every byte across Android reboot',read('diag-ops05-before-reboot.json')['files']==read('diag-ops05-after-reboot.json')['files'])
ops=read('diag-ops05-after-reboot.json')['operations'];check('Six operations retain expected outcomes',sorted(o['phase']for o in ops)==sorted(['COMPLETED']*4+['CANCELLED','UNKNOWN']))
check('Old Native90 private trace/workspace unchanged',read('native90-sandbox-preservation.json')['status']=='PASS')
check('All 59229 protected paths unchanged',read('preservation-after.json')['status']=='PASS' and read('preservation-after.json')['count']==59229)
check('Original frozen flight pins current',all(sha((R/n).read_bytes())==h for n,h in read('flight-pins.json')['files'].items()))
traces={};counts={};art=[];heads=[]
with tarfile.open(E/'android91-closed-files.tar')as t:
 for m in t.getmembers():
  if not m.isfile():continue
  if m.name.startswith('./diagnostics90/')and m.name.endswith('.jsonl'):
   b=t.extractfile(m).read();session=Path(m.name).stem;v=trace(b,session,allowed);traces[session]=v
   for line in b.splitlines():
    row=json.loads(line);p=json.loads(base64.b64decode(row['payloadBase64']));k=p['kind'];counts[k]=counts.get(k,0)+1
    if k=='ART_SELF_TEST':
     d=p['data'];check('ART runtime guard suite '+session,d['status']=='PASS'and d['runtime']=='ANDROID_ART'and d['checks']==read('host-tests05.json')['model']['checks']and d['names']==read('host-tests05.json')['model']['names']);art.append({'session':session,'checks':d['checks'],'sourceId':v['sourceId']})
  if m.name.startswith('./workspaces/initial/sitl/')and m.name.endswith('.bin'):
   b=t.extractfile(m).read().split(b'\n',6)[6];v=json.loads(b)
   if v.get('format')=='aeris-native84-sitl-review':heads.append({'run':v['run'],'accepted':v['accepted'],'aborted':v['aborted']})
check('Both distinct SITL reviews retained',len(heads)==2 and sorted(v['accepted']for v in heads)==[False,True])
check('Delivered05 ART guards actually executed',any(x['sourceId']==build['sourceId']for x in art))
check('SITL decode callbacks and lifecycle events actually recorded',counts.get('FRAME_CALLBACK',0)>0 and counts.get('ACTIVITY_PAUSED',0)>0 and counts.get('WORKSPACE_REVIEW_LINK',0)>=2)
check('Both raw semantic receipts distinguish failure and completion',sorted(read(p.relative_to(E).as_posix())['missionAccepted']for p in(E/'independent-raw-receiver').glob('*.receipt.json'))==[False,True])
check('20 receiver attacks refused',read('receiver-negative-final.json')['checks']+read('receiver-extra-negative.json')['checks']==20)
r={'status':'PASS','checks':checks,'checkCount':len(checks),'diagnosticTraces':len(traces),'diagnosticEvents':sum(v['records']for v in traces.values()),'traceReports':traces,'eventCounts':counts,'artGuardExecutions':art,'sitlReviewHistory':heads,'sourceId':build['sourceId'],'apkSha256':build['sha256'],'limits':['Committed prefixes are not whole-session or flight execution evidence','Independent raw receiver supplies execution/failure qualification; trace ZIP alone does not','No Hera/HeraHub/physical input/video/production/ENDURE or pacing acceptance']};(E/'final-verification.json').open('x').write(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k not in ['traceReports','checks','eventCounts']}))
