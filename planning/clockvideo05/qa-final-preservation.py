"""Read-only final preservation vs exact selected baseline, not whole-repository completeness."""
import json,hashlib,datetime,sys
from pathlib import Path
E=Path('evidence/field02/clockvideo05');rd=lambda p:json.loads(Path(p).read_text());sh=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();b=rd(E/'qa-preservation-before01.json');rows=[];errors=[]
for key,g in b['groups'].items():
 diff=[]
 for n,h in g.items():
  try:
   if sh(n)!=h:diff.append({'path':n,'status':'HASH_MISMATCH'})
  except OSError as e:diff.append({'path':n,'status':'READ_ERROR','reason':str(e)})
 rows.append({'group':key,'files':len(g),'differences':diff});errors+=diff
for gen in ['01','02']:
 a=rd(E/f'generation{gen}-source-archive01.json');q=a.get('rows',a.get('files'));diff=[]
 for r in q:
  p=r.get('archivePath')or str(E/f'generation{gen}-source'/r['path'])
  try:
   if sh(p)!=r['sha256']:diff.append({'path':p,'status':'HASH_MISMATCH'})
  except OSError as e:diff.append({'path':p,'status':'READ_ERROR','reason':str(e)})
 rows.append({'group':f'generation{gen}Archive','files':len(q),'differences':diff});errors+=diff
p=E/'flight-pins03.json';m=rd(p);diff=[]
for n,h in m['files'].items():
 try:
  if sh(n)!=h:diff.append({'path':n,'status':'HASH_MISMATCH'})
 except OSError as e:diff.append({'path':n,'status':'READ_ERROR','reason':str(e)})
assert sh(p)=='02b532462598893f384a3af7fe83771c2d30daae612ad7cff26bb4387b1adb26';rows.append({'group':'current226Pins','files':len(m['files']),'differences':diff});errors+=diff
prior={x['run']:x for x in b['priorSITLRequests']};actual={}
for p in Path('evidence/field02/flight/runs').glob('*/request.json'):
 if rd(p).get('mode')=='sitl':actual[p.parent.name]={'requestSHA256':sh(p),'path':str(p)}
for run,q in prior.items():
 if actual.get(run,{}).get('requestSHA256')!=q['sha256']:errors.append({'priorRequest':run,'status':'MISSING_OR_CHANGED'})
new={k:v for k,v in actual.items()if k not in prior}
if len(new)>2:errors.append({'status':'NEW_AP_BUDGET_EXCEEDED','new':len(new)})
for run,q in new.items():
 base=Path(q['path']).parent;q['sourcePinsSHA256']=sh(base/'source-pins.json');q['exactPins03']=q['sourcePinsSHA256']=='02b532462598893f384a3af7fe83771c2d30daae612ad7cff26bb4387b1adb26'
 if not q['exactPins03']:errors.append({'run':run,'status':'WRONG_SOURCE_PINS'})
 q['closurePresent']=(base/'closure.json').exists();q['reviewPresent']=(base/'review.json').exists()
 if q['reviewPresent']:
  z=rd(base/'review.json');q['review']={k:z.get(k)for k in ['accepted','aborted','rawRecords','rawHead']}
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_SELECTED_BASELINES_AND_AUTHORIZED_NEW_AP_INVENTORY'if not errors else'FAIL_PRESERVATION','baselineSHA256':sh(E/'qa-preservation-before01.json'),'groups':rows,'priorRequests':len(prior),'totalCurrentSITLRequests':len(actual),'newRequests':new,'errors':errors,'limitations':['Historical SHA semantics dereference seven retained negative-test symlinks, not literal symlink identity.','The 95 preexisting deleted Git paths are not repaired; no whole-repository completeness claim.','New AP request presence and matching source pins do not prove accepted flight, live lease, payload exposure or video acceptance.','Live closure/process/resource assertions require separate actual root evidence.']};out=Path(sys.argv[1]);assert str(out).startswith(str(E/'qa-')) and not out.exists();out.open('x').write(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':r['status'],'groups':[{k:x[k]for k in ['group','files']}for x in rows],'errors':len(errors),'newRequests':new}));assert not errors
