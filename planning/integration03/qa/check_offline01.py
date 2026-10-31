"""Independent held-out contract checker. Reads normalized observations from a pinned QA adapter.
PASS is offline-only and never substitutes actual Android/SITL/SAF/coldboot evidence.
"""
from pathlib import Path
import argparse,json,hashlib,math,datetime,copy
ROOT=Path(__file__).resolve().parents[3]
CORPUS=ROOT/'evidence/integration03-qa/heldout-corpus01.json'
CORPUS_SHA='c6aa625a315d210084bd7f33265976a52c6e7d06142e3c24b9b755d91710a493'
class Refusal(Exception):pass
def require(x,m):
 if not x:raise Refusal(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def strict(p):
 def pairs(a):
  d={}
  for k,v in a:
   require(k not in d,'duplicate key:'+k);d[k]=v
  return d
 return json.loads(p.read_text(),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(Refusal('nonfinite JSON')))
def verify(c,obs):
 require(type(obs) is dict,'observations must be map')
 expected={x['id'] for x in c['checks']}
 require(set(obs)==expected,'missing/unexpected executed check IDs')
 out=[]
 for case in c['checks']:
  cid=case['id'];got=obs[cid];require(type(got) is dict,cid+': map required')
  required=case.get('required',case.get('metrics'))
  for k,v in required.items():
   require(k in got,cid+': missing '+k);actual=got[k]
   if case['kind']=='numeric':
    require(type(actual) in (int,float) and math.isfinite(actual),cid+': finite number required '+k)
    require(abs(actual-v)<=case['absoluteTolerances'][k],cid+': numeric oracle mismatch '+k)
   else:require(type(actual) is type(v) and actual==v,cid+': exact typed mismatch '+k)
  out.append({'id':cid,'status':'PASS'})
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--observations',type=Path);ap.add_argument('--source-freeze',type=Path);ap.add_argument('--adapter',type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--selftest',action='store_true');a=ap.parse_args()
 require(not a.output.exists(),'immutable output exists')
 require(sha(CORPUS)==CORPUS_SHA,'frozen corpus SHA changed');c=strict(CORPUS)
 result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'NOT_RUN','corpusSha256':CORPUS_SHA,'TIP_SHA256':c['TIP_SHA256'],'provenance':'SEPARATE_AI_QA_NOT_HUMAN_REVIEW','actualRuntimeAcceptance':False,'sourceFreeze':None}
 try:
  if a.selftest:
   obs={x['id']:copy.deepcopy(x.get('required',x.get('metrics'))) for x in c['checks']};verify(c,obs)
   bites=[]
   for name,mutate in [('missing-case',lambda o:o.pop(next(iter(o)))),('null-is-not-zero',lambda o:o['H03.homeMutation'].update(impliedAmslDeltaM=None)),('camera-placeholder',lambda o:o['H03.source'].update(cameraCommandPreserved=False)),('unknown-upload',lambda o:o['H04.terrain'].update(operationalUploadAllowed=True)),('old-owner-wire',lambda o:o['H07.crew'].update(oldOwnerPostWalWrites=1)),('stale-pose',lambda o:o['H06.expiry'].update(staleAtAge1001=False)),('wrong-SAF-context',lambda o:o['H08.export'].update(wrongRunAccepted=True))]:
    m=copy.deepcopy(obs);mutate(m)
    try:verify(c,m)
    except Refusal as e:bites.append({'name':name,'rejected':True,'reason':str(e)})
    else:raise Refusal('checker failed negative control:'+name)
   result.update(status='PASS_CHECKER_SELFTEST_ONLY_NOT_PRODUCT',negativeControls=bites,checks=len(c['checks']))
  else:
   require(a.observations and a.source_freeze and a.adapter,'observations,source-freeze,adapter required')
   f=strict(a.source_freeze);require(type(f.get('files')) is dict and f['files'],'source freeze files required')
   failures=[p for p,h in f['files'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
   require(not failures,'frozen source mismatches:'+str(failures))
   inp=strict(a.observations)
   require(inp.get('sourceId')==f.get('sourceId') and f.get('sourceId'),'observations sourceId mismatch')
   require(inp.get('corpusSha256')==CORPUS_SHA,'observations corpus mismatch')
   require(inp.get('adapterSha256')==sha(a.adapter),'adapter hash mismatch')
   require(inp.get('mode')=='OFFLINE_ACTUAL_PRODUCTION_API','synthetic observations are not product execution')
   checks=verify(c,inp.get('observations'))
   result.update(status='PASS_OFFLINE_HELDOUT_ONLY_NOT_RUNTIME',checks=checks,sourceFreeze={'path':str(a.source_freeze),'sha256':sha(a.source_freeze),'sourceId':f['sourceId'],'files':len(f['files'])},observationsSha256=sha(a.observations),adapterSha256=sha(a.adapter))
 except Exception as e:result.update(status='FAIL',errorType=type(e).__name__,error=str(e))
 result['toolSha256']=sha(Path(__file__))
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['status'])
 return 0 if result['status'].startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
