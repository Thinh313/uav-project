"""Read-only exclusive generation03 source/preservation gate. No runtime."""
from pathlib import Path
import sys,json,hashlib,datetime
E=Path('evidence/field02/clockvideo05');sh=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rd=lambda p:json.loads(Path(p).read_text());rows=[]
def test(name,fn):
 try:r=fn();rows.append({'name':name,'status':'PASS',**(r or {})})
 except Exception as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
p=E/'flight-pins03.json';m=rd(p);b=rd(E/'qa-preservation-before01.json');a=rd(E/'generation02-source-archive01.json');f=rd(E/'builder-source-freeze02.json')
def manifest():
 assert sh(p)==sys.argv[1];assert sh(E/'builder-source-freeze03.json')==sys.argv[2];assert p.read_bytes()==(json.dumps(m,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode();assert m['format']=='aeris-clockvideo05-flight-pins';assert m['budget']=={'priorCumulativeSITLRequests':10,'maxCumulativeSITLRequests':12,'newRequestsAllowed':2,'refuseRequestOrdinal':13,'noAutomaticRetry':True}
 for n,h in m['files'].items():assert sh(n)==h,n
 return {'files':len(m['files']),'bytes':p.stat().st_size,'sha256':sh(p),'freezeSHA256':sh(E/'builder-source-freeze03.json')}
test('exclusive_canonical_manifest_all_pins_and_unchanged_cap12',manifest)
def archive():
 assert sh(E/'flight-pins02.json')=='c650ed878ff1247fea86ed54fd2e801898176edd7495b359ce5b409238e516da';assert sh(E/'builder-source-freeze02.json')=='b3012b7b951289adffac3ab2fe7b41de12e0dcb64426a7ac8977175dee90db06';assert sh(E/'flight-pins.json')=='96416c1bf0d45a239387c324bdc8a06eeaff5e062d96683566c3bea707f4540a';assert sh(E/'builder-source-freeze01.json')=='d92994fa86a72124cafef77470c3979945a033d3393d24782df946486aa594ea'
 assert len(a['rows'])==37;old={x['path']:x['sha256']for x in f['files']};changed=[]
 for q in a['rows']:
  assert sh(q['archivePath'])==q['sha256']==old[q['originalPath']];assert m['files'][q['archivePath']]==q['sha256']
  if sh(q['originalPath'])!=q['sha256']:changed.append(q['originalPath'])
 assert sorted(changed)==sorted(['pilot/clockvideo05/ui.css','pilot/clockvideo05/flight/flight04.mjs','pilot/clockvideo05/flight/runtime04.py'])
 for n in changed:
  before=(E/'generation02-source'/n).read_text();now=Path(n).read_text()
  if n.endswith('ui.css'):
   assert now.startswith(before);extra=now[len(before):];assert extra.count('{')==5 and '#field-console>header{height:44px' in extra and '#field-flight-context{min-height:80px}'in extra
  else:assert now.replace('flight-pins03.json','flight-pins02.json')==before
 return {'archived':37,'authorizedCurrentChanges':changed,'scope':'CSS appended five declarations; exact loader filename-only reversal. UI JS/clock/control/profile unchanged.'}
test('exact37_gen02_archive_and_three_authorized_current_changes',archive)
def preservation():
 counts={}
 for k,g in b['groups'].items():
  for n,h in g.items():assert sh(n)==h,n
  counts[k]=len(g)
 return {'counts':counts,'differences':0,'semantics':b['historicalBaselineSemantics'],'preexistingGitDeleted':b['preexistingGitDeletedCount']}
test('historical_protected_native_evidence_source_431_baselines_unchanged',preservation)
def requests():
 prior={r['run']:r['sha256']for r in b['priorSITLRequests']};assert {r['run']:r['requestSha256']for r in m['priorSITLRequests']}==prior
 actual={}
 for q in Path('evidence/field02/flight/runs').glob('*/request.json'):
  if rd(q).get('mode')=='sitl':actual[q.parent.name]=sh(q)
 assert actual==prior
 return {'permanentPriorRequests':len(prior),'newAPRequests':0}
test('ten_permanent_requests_and_zero_new_AP_before_ground_gate',requests)
def helper():
 r=rd(E/'qa-receipt-poll03.json');assert r['status']=='PASS_INDEPENDENT_RECEIPT_WAIT';assert sh(r['source'])==r['sourceSha256'];assert len(r['rows'])==8 and all(x['status']=='PASS'for x in r['rows']);src=Path('planning/clockvideo05/qa-ap-admission.py').read_text();assert "expectedPins=R/'evidence/field02/clockvideo05/flight-pins03.json'"in src
 return {'independentReceiptGroups':8,'helperSHA256':sh('planning/clockvideo05/qa-ui.py'),'admissionSHA256':sh('planning/clockvideo05/qa-ap-admission.py'),'reportSHA256':sh(E/'qa-receipt-poll03.json')}
test('bounded_receipt_deadline_identity_and_pin03_admission_helper',helper)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_GEN03_SOURCE_MOCK_ONLY_ACTUAL_GROUND_GATE_PENDING'if all(x['status']=='PASS'for x in rows)else'FAIL','rows':rows,'scope':'Root alone may start replacement host03 on existing emulator02 before original05:55Z deadline. No added boot/AP/time budget. Actual all-critical-target full/hittest and fresh benign matched receipt required before AP. Gen01/gen02 failures and late ACK evidence remain immutable. No overall READY or flight/video acceptance.'};out=E/'qa-generation03-pre-runtime-gate01.json';out.open('x').write(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));assert r['status'].startswith('PASS')
