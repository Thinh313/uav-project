"""Integrity-valid assistant-authored native tar mutations, never old raw edits."""
from pathlib import Path
import base64,copy,datetime,hashlib,io,json,sys,tarfile
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control04 import confirmation as current,confirmation_v01 as previous
O=R/'evidence/betaintegrated01-m1control02/qa/confirmation01';O.mkdir()
source_paths=list((R/'pilot/betaintegrated01/control04').glob('*.py'));before={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths}
D=json.loads((R/'evidence/betaintegrated01-m1control02/host/old-regression01/derived-loss05-confirmation-descriptor.json').read_bytes());B=D['hostBracket'];CTX=[B[k]for k in('run','epoch','boot')]
def encode(v):return json.dumps(v,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
with tarfile.open(D['nativeTarPath'])as t:original={m.name[len(D['prefix']):]:t.extractfile(m).read()for m in t.getmembers()if m.isfile()and m.name.startswith(D['prefix'])}
def data(row):return json.loads(base64.b64decode(row['base64']))
def make(label,mutate):
 table=dict(original);terminal=json.loads(table['session.json']);previous_head='';previous_seal='';confirmation_sha=None
 for segment in range(terminal['segments']):
  name=f'segment-{segment:06}.jsonl';rows=[json.loads(line)for line in table[name].splitlines()];lines=[]
  for row in rows:
   if row['kind']=='HEADER':v=data(row);v['previousSeal']=previous_seal;row['base64']=base64.b64encode(encode(v)).decode()
   mutate(row)
   row['previous']=previous_head;row.pop('sha256');previous_head=sha(encode(row));row['sha256']=previous_head;lines.append(encode(row)+b'\n')
   if row['kind']=='POST_ARM_HOME_EXPLICITLY_CONFIRMED':confirmation_sha=previous_head
  raw=b''.join(lines);table[name]=raw;sealname=f'seal-{segment:06}.json';seal=json.loads(table[sealname]);seal.update(bytes=len(raw),sha256=sha(raw),head=previous_head,previousSeal=previous_seal);table[sealname]=encode(seal);previous_seal=sha(table[sealname])
 terminal.update(head=previous_head,lastSeal=previous_seal);table['session.json']=encode(terminal);path=O/(label+'.tar')
 with tarfile.open(path,'w')as t:
  for name,body in table.items():m=tarfile.TarInfo(D['prefix']+name);m.size=len(body);m.mode=0o600;t.addfile(m,io.BytesIO(body))
 desc=copy.deepcopy(D);desc.update(nativeTarPath=str(path.resolve()),nativeExternalAnchor=sha(table['session.json']),confirmationRecordSHA256=confirmation_sha)
 return desc
def update_action(row,change):
 if row['kind']=='OPERATOR_TOUCH_ACTION'and data(row).get('action')=='CONFIRM_HOME':
  v=data(row);change(v,row);row['base64']=base64.b64encode(encode(v)).decode()
def probe(module,desc):
 try:module.verify_confirmation(desc,module.descriptor_sha256(desc),*CTX);return {'accepted':True}
 except Exception as e:return {'accepted':False,'error':repr(e)}
cases=[]
baseline=probe(current,D);assert baseline['accepted']
mutators={
 'missing_prior_touch':lambda row:update_action(row,lambda v,r:r.update(kind='QA_REMOVED_ACTION')),
 'wrong_touch_action':lambda row:update_action(row,lambda v,r:v.update(action='STATUS')),
 'wrong_action_id':lambda row:update_action(row,lambda v,r:v.update(actionId='qa-foreign-action')),
 'wrong_displayed_hash':lambda row:update_action(row,lambda v,r:v.update(displayedHomeHash='0'*64)),
 'stale_producer':lambda row:update_action(row,lambda v,r:v.update(producerElapsedNs=v['receiptElapsedNs']-1_000_000_001)),
 'producer_after_receipt':lambda row:update_action(row,lambda v,r:v.update(producerElapsedNs=v['receiptElapsedNs']+1)),
 'wrong_touch_source':lambda row:update_action(row,lambda v,r:v.update(source='NETWORK_RETIMESTAMPED')),
}
for label,mutate in mutators.items():
 desc=make(label,mutate);old,new=probe(previous,desc),probe(current,desc);cases.append({'id':label,'priorFrozenSource':old,'currentSource':new,'pass':old['accepted']and not new['accepted'],'fixtureTarSHA256':sha(Path(desc['nativeTarPath']).read_bytes()),'descriptor':desc})
after={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths};old_record=json.loads((R/'evidence/betaintegrated01-m1control02/qa/geo02/results.json').read_bytes())['sourceAfter']['pilot/betaintegrated01/control04/confirmation.py'];assert sha((R/'pilot/betaintegrated01/control04/confirmation_v01.py').read_bytes())==old_record
r={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if all(x['pass']for x in cases)and before==after else'FAIL','baselineActualClosedNative':baseline,'cases':cases,'sourceBefore':before,'sourceAfter':after,'sourceChanged':before!=after,'scope':'Assistant-authored integrity-valid re-chained closedjournalfixtures; mockrootanchorsdeclaredfortest, no newliveattestation or editsoldraw','APAndroidServicesStarts':0,'priorFailureSourceSnapshotMatchesIndependentEarlierHash':True};(O/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'cases':len(cases),'failed':[x['id']for x in cases if not x['pass']]}))
