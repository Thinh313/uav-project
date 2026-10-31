"""Independent private-record preservation checker02 with exact predeclared old-unsealed exception. No extraction or device access.
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
def unsealed_prefix(b,entry):
 need(sha(b)==entry['sha256'] and len(b)==entry['bytes'],'preexisting unsealed exact bytes/size')
 pieces=b.splitlines(keepends=True);complete=[];tail=b''
 for i,line in enumerate(pieces):
  if line.endswith(b'\n'):complete.append(line[:-1])
  else:need(i==len(pieces)-1,'only terminal unsealed tail permitted');tail=line
 head='';n=0;first=None;last=None
 for line in complete:
  r=strict(line);h=r.pop('sha256');need(r['n']==n+1 and r['previous']==head and sha(json.dumps(r,separators=(',',':'),ensure_ascii=False).encode())==h,'preexisting complete prefix SHA/sequence');base64.b64decode(r['dataBase64'],validate=True);first=first or r['kind'];last=r['kind'];n+=1;head=h
 need(n>0 and first=='META' and last!='CLOSED','allowlist only preexisting unsealed META prefix')
 return {'status':'EXACT_PREEXISTING_UNSEALED_NOT_ACCEPTED','sha256':sha(b),'bytes':len(b),'verifiedCompletePrefixRecords':n,'verifiedCompletePrefixHead':head,'lastCompleteKind':last,'unterminatedTailBytes':len(tail),'unterminatedTailSha256':sha(tail) if tail else None,'closed':False,'authorityRestorable':False,'qualification':'Exact bytes preserved; tail not parsed/committed and no synthesized CLOSED or mission acceptance.'}
def allowed(q):
 d=strict(q.read_bytes());need(d.get('format')=='aeris-integration03-preexisting-unsealed-allowlist' and d.get('version')==1,'explicit allowlist schema');entries=d.get('entries');need(isinstance(entries,list) and len(entries)==1,'only exact known resource-stop exception');e=entries[0];need(e.get('run')=='s22a26a892379a044e6a5' and e.get('path')=='direct95/s22a26a892379a044e6a5/raw.jsonl' and e.get('reason')=='RESOURCE_STOP_UNSEALED_NOT_ACCEPTED','no wildcard/new accepted run exception');need(type(e.get('bytes')) is int and e['bytes']>0 and isinstance(e.get('sha256'),str) and len(e['sha256'])==64 and all(x in '0123456789abcdef' for x in e['sha256']),'predeclared exact SHA/size');return {e['path']:e}
def archive(p,allow):
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
   if body is not None:closed[name]=unsealed_prefix(b''.join(body),allow[name]) if name in allow else raw_closed(b''.join(body))
 need(set(allow)<=set(files),'preexisting exception missing from archive')
 return files,closed
# Only presentation-generation/diagnostic files may change on launch, never workspace/crew/raw/export.
OPTIONAL_PREFIXES=('ui96/','diagnostics90/','stage03/')
def main():
 a=argparse.ArgumentParser();a.add_argument('--before',required=True,type=Path);a.add_argument('--after',required=True,type=Path);a.add_argument('--after-kind',choices=['archive','collector-manifest'],required=True);a.add_argument('--kind',choices=['process','coldboot'],required=True);a.add_argument('--runtime-receipt',required=True,type=Path);a.add_argument('--kernel-receipt',required=True,type=Path);a.add_argument('--old-before',required=True,type=Path);a.add_argument('--old-after',required=True,type=Path);a.add_argument('--unsealed-allowlist',required=True,type=Path);a.add_argument('--unsealed-allowlist-sha256',required=True);a.add_argument('--required-closed-run',action='append',required=True);a.add_argument('--output',required=True,type=Path);q=a.parse_args();need(not q.output.exists(),'immutable output exists')
 try:
  need(sha(q.unsealed_allowlist.read_bytes())==q.unsealed_allowlist_sha256,'predeclared allowlist SHA changed');allow=allowed(q.unsealed_allowlist);need(len(set(q.required_closed_run))>=3 and all(r!='s22a26a892379a044e6a5' and len(r)==21 and r.startswith('s') and all(x in '0123456789abcdef' for x in r[1:])for r in q.required_closed_run),'all3 accepted new runs declared, no exception');before,closed=archive(q.before,allow)
  for run in q.required_closed_run:need('direct95/'+run+'/raw.jsonl' in closed and closed['direct95/'+run+'/raw.jsonl'].get('closed',True) is not False,'accepted new run must exist and be CLOSED')
  if q.after_kind=='archive':after,afterClosed=archive(q.after,allow);provenance='QA independently hashes both actual private archives'
  else:after=strict(q.after.read_bytes())['files'];afterClosed=None;provenance='QA hashes before archived bytes and compares Root-collected after-device manifest; after bytes not re-extracted by QA'
  missing=[p for p in before if p not in after];changed=[p for p in before if p in after and before[p]!=after[p]];new=[p for p in after if p not in before];need(not missing,'private files missing');need(all(p.startswith(OPTIONAL_PREFIXES) for p in changed+new),'core/private mutation or automatic new connection generation')
  if afterClosed is not None:need(closed==afterClosed,'closed/unsealed raw heads/counts changed')
  for name,e in allow.items():need(before[name]==after.get(name)==e['sha256'],'preexisting unsealed must remain byte exact')
  oldBefore=strict(q.old_before.read_bytes())['files'];oldAfter=strict(q.old_after.read_bytes())['files'];need(oldBefore and oldBefore==oldAfter,'older protected private baseline changed/missing')
  rt=strict(q.runtime_receipt.read_bytes());kernel=strict(q.kernel_receipt.read_bytes());need(rt.get('pass') is True and rt.get('automaticReconnect') is False and rt.get('automaticAuthority') is False,'actual runtime no-restore receipt required');need(kernel.get('pass') is True and kernel.get('activeFlightOrCrewSockets')==[],'actual kernel no-flight/crew-socket observation required')
  r={'status':'PASS_SCOPED_PRIVATE_RECORD_AND_RESTART_WITH_EXACT_PREEXISTING_UNSEALED_EXCEPTION','kind':q.kind,'beforeFiles':len(before),'afterFiles':len(after),'coreStableFiles':sum(not p.startswith(OPTIONAL_PREFIXES) for p in before),'missing':missing,'expectedPresentationChanges':changed,'expectedNewPresentationFiles':new,'rawClassification':closed,'preexistingUnsealedException':list(allow),'acceptedNewRunsRequiredClosed':q.required_closed_run,'olderPrivateFiles':len(oldBefore),'provenance':provenance,'noRestoreEvidence':'Actual Root device/UI/kernel receipts, separately pinned; never inferred solely from saved hashes','limits':'Not hardware power-loss/authority attestation or whole-mission acceptance','humanReview':False};code=0
 except Exception as e:r={'status':'FAIL_OR_SCHEMA_UNSUPPORTED','errorType':type(e).__name__,'error':str(e),'kind':q.kind};code=2
 r['toolSha256']=sha(Path(__file__).read_bytes());r['inputs']={str(p):sha(p.read_bytes()) for p in [q.before,q.after,q.runtime_receipt,q.kernel_receipt,q.old_before,q.old_after,q.unsealed_allowlist]}
 with q.output.open('x')as f:json.dump(r,f,indent=2,ensure_ascii=False);f.write('\n')
 print(json.dumps({'status':r['status'],'error':r.get('error')}));return code
if __name__=='__main__':raise SystemExit(main())
