"""Independent private-record preservation checker. No extraction or device access.
Archive bytes and collector-provided manifest comparisons have distinct provenance.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,tarfile,base64
MAX=192*2**20
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def strict(b):
 def pairs(ps):
  d={}
  for k,v in ps:need(k not in d,'duplicate JSON key');d[k]=v
  return d
 return json.loads(b.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def raw_closed(b):
 need(b.endswith(b'\n'),'closed raw newline');head='';n=0;first=None;last=None
 for l in b.splitlines():
  r=strict(l);h=r.pop('sha256');need(r['n']==n+1 and r['previous']==head and sha(json.dumps(r,separators=(',',':'),ensure_ascii=False).encode())==h,'native raw SHA/sequence');base64.b64decode(r['dataBase64'],validate=True);first=first or r['kind'];last=r['kind'];n+=1;head=h
 need(first=='META' and last=='CLOSED','private raw must remain closed');return{'head':head,'records':n}
def archive(p):
 need(p.stat().st_size<=MAX,'private archive bound');files={};closed={};total=0
 with tarfile.open(p)as t:
  for m in t:
   name=m.name.removeprefix('./');parts=PurePosixPath(name).parts;need(not m.issym() and not m.islnk() and not name.startswith('/') and '..'not in parts,'unsafe private tar member')
   if not m.isfile():continue
   need(name not in files and m.size<=48*2**20,'duplicate/oversized private member');total+=m.size;need(total<=MAX,'private expanded bound');f=t.extractfile(m);h=hashlib.sha256();body=[] if name.startswith('direct95/') and name.endswith('/raw.jsonl') else None
   while True:
    b=f.read(256*1024)
    if not b:break
    h.update(b)
    if body is not None:body.append(b)
   files[name]=h.hexdigest()
   if body is not None:closed[name]=raw_closed(b''.join(body))
 return files,closed
# Only presentation-generation/diagnostic files may change on launch, never workspace/crew/raw/export.
OPTIONAL_PREFIXES=('ui96/','diagnostics90/','stage03/')
def main():
 a=argparse.ArgumentParser();a.add_argument('--before',required=True,type=Path);a.add_argument('--after',required=True,type=Path);a.add_argument('--after-kind',choices=['archive','collector-manifest'],required=True);a.add_argument('--kind',choices=['process','coldboot'],required=True);a.add_argument('--runtime-receipt',required=True,type=Path);a.add_argument('--kernel-receipt',required=True,type=Path);a.add_argument('--old-before',required=True,type=Path);a.add_argument('--old-after',required=True,type=Path);a.add_argument('--output',required=True,type=Path);q=a.parse_args();need(not q.output.exists(),'immutable output exists')
 try:
  before,closed=archive(q.before)
  if q.after_kind=='archive':after,afterClosed=archive(q.after);provenance='QA independently hashes both actual private archives'
  else:after=strict(q.after.read_bytes())['files'];afterClosed=None;provenance='QA hashes before archived bytes and compares Root-collected after-device manifest; after bytes not re-extracted by QA'
  missing=[p for p in before if p not in after];changed=[p for p in before if p in after and before[p]!=after[p]];new=[p for p in after if p not in before];need(not missing,'private files missing');need(all(p.startswith(OPTIONAL_PREFIXES) for p in changed+new),'core/private mutation or automatic new connection generation')
  if afterClosed is not None:need(closed==afterClosed,'closed raw heads/counts changed')
  oldBefore=strict(q.old_before.read_bytes())['files'];oldAfter=strict(q.old_after.read_bytes())['files'];need(oldBefore and oldBefore==oldAfter,'older protected private baseline changed/missing')
  rt=strict(q.runtime_receipt.read_bytes());kernel=strict(q.kernel_receipt.read_bytes());need(rt.get('pass') is True and rt.get('automaticReconnect') is False and rt.get('automaticAuthority') is False,'actual runtime no-restore receipt required');need(kernel.get('pass') is True and kernel.get('activeFlightOrCrewSockets')==[],'actual kernel no-flight/crew-socket observation required')
  r={'status':'PASS_SCOPED_PRIVATE_RECORD_AND_RESTART_RECEIPTS','kind':q.kind,'beforeFiles':len(before),'afterFiles':len(after),'coreStableFiles':sum(not p.startswith(OPTIONAL_PREFIXES) for p in before),'missing':missing,'expectedPresentationChanges':changed,'expectedNewPresentationFiles':new,'closedRaw':closed,'olderPrivateFiles':len(oldBefore),'provenance':provenance,'noRestoreEvidence':'Actual Root device/UI/kernel receipts, separately pinned; never inferred solely from saved hashes','limits':'Not hardware power-loss/authority attestation or whole-mission acceptance','humanReview':False};code=0
 except Exception as e:r={'status':'FAIL_OR_SCHEMA_UNSUPPORTED','errorType':type(e).__name__,'error':str(e),'kind':q.kind};code=2
 r['toolSha256']=sha(Path(__file__).read_bytes());r['inputs']={str(p):sha(p.read_bytes()) for p in [q.before,q.after,q.runtime_receipt,q.kernel_receipt,q.old_before,q.old_after]}
 with q.output.open('x')as f:json.dump(r,f,indent=2,ensure_ascii=False);f.write('\n')
 print(json.dumps({'status':r['status'],'error':r.get('error')}));return code
if __name__=='__main__':raise SystemExit(main())
