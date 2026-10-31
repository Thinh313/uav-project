"""Rechain bounded synthetic copies of shared real-Java unit raw, not actual flight."""
from pathlib import Path
import base64,copy,hashlib,json,tarfile,io
from .native_stream import closed_native
R=Path(__file__).resolve().parents[4];BASE=R/'evidence/betaintegrated01-cockpit05-iocommit09/qa/owner-fixture01';PREFIX='files/control-runs/periodic-carrier/'
def enc(v):return json.dumps(v,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def h(raw):return hashlib.sha256(raw).hexdigest()
def fixture():
 with tarfile.open(BASE/'native-synthetic-owner.tar')as t:
  return [json.loads(x)for x in t.extractfile(PREFIX+'segment-000000.jsonl').read().splitlines()]
def values(rows):
 return [(r,json.loads(base64.b64decode(r['base64'])))for r in rows if r['kind'].startswith('CONTROL_')]
def mutate(rows,mode):
 tx=next((r,v)for r,v in values(rows)if r['kind']=='CONTROL_INPUT_TX')
 carrier=next((r,v)for r,v in values(rows)if v.get('commitReceipt')is not None)
 r,v=tx;cr,cv=carrier
 if mode=='candidate-string-version':v['version']='1'
 if mode=='receipt-string-version':cv['commitReceipt']['version']='1'
 if mode=='receipt-string-clock':cv['commitReceipt']['decisionNs']=str(cv['commitReceipt']['decisionNs'])
 if mode=='candidate-extra':v['extra']=1
 if mode=='context-extra':v['context']['extra']='bad'
 if mode=='unknown-carrier':cr['kind']='CONTROL_UNKNOWN_CARRIER'
 if mode=='mismatch-release-kind':v['input']['release']=True
 if mode=='consent-input-retimestamp':
  rr,vv=next((rr,vv)for rr,vv in values(rows)if rr['kind']=='CONTROL_CONSENT_TX');vv['neutralInput']['elapsedNs']+=1;vv['neutralInput']['uptimeNs']+=1;vv['proposal']['proposedExpiryNs']+=1;rr['base64']=base64.b64encode(enc(vv)).decode()
 if mode=='receipt-after-refused-noFailure':
  cv['commitReceipt']['disposition']='REFUSED';cv['commitReceipt']['reason']='expiry';cr['kind']='CONTROL_COMMIT_REFUSED'
  index=rows.index(cr);tail=[next(x for x in rows[index+1:]if x['kind']=='TX_WRITTEN')];rows[:]=rows[:index+1]+tail+[next(x for x in rows if x['kind']=='SESSION_CLOSE')]
 if mode=='refused-then-new-candidate':cv['commitReceipt']['disposition']='REFUSED';cv['commitReceipt']['reason']='expiry';cr['kind']='CONTROL_COMMIT_REFUSED'
 r['base64']=base64.b64encode(enc(v)).decode();cr['base64']=base64.b64encode(enc(cv)).decode()
def frame(rows,path):
 previous='';parts=[];payload_hash={};candidateValues={};run=rows[0]['run'];epoch=rows[0]['epoch']
 for n,r in enumerate(rows,1):
  raw=base64.b64decode(r['base64'])
  if r['kind'].startswith('CONTROL_'):
   v=json.loads(raw);receipt=v.get('priorCommitReceipt')or v.get('commitReceipt')
   if receipt is not None:
    receipt['txPayloadSHA256']=payload_hash[receipt['txRecordN']];receipt['proposal']=copy.deepcopy(candidateValues[receipt['txRecordN']]['proposal'])
   raw=enc(v)
  if r['kind']in('CONTROL_INPUT_TX','CONTROL_CONSENT_TX'):payload_hash[n]=h(raw);candidateValues[n]=json.loads(raw)
  v=dict(format='aeris-native-record',version=1,run=run,epoch=epoch,segment=0,n=n,previous=previous,monotonicNs=r['monotonicNs'],kind=r['kind'],base64=base64.b64encode(raw).decode());plain=enc(v);previous=h(plain);parts.append(plain[:-1]+b',"sha256":"'+previous.encode()+b'"}\n')
 body=b''.join(parts);seal=enc(dict(format='aeris-native-seal',version=1,run=run,epoch=epoch,segment=0,file='segment-000000.jsonl',bytes=len(body),sha256=h(body),first=1,last=len(rows),head=previous,previousSeal=''))
 terminal=enc(dict(format='aeris-native-session',version=1,run=run,epoch=epoch,segments=1,records=len(rows),head=previous,lastSeal=h(seal),authorityRestorable=False,publicationAllowed=False))
 with tarfile.open(path,'w')as t:
  for name,data in [('segment-000000.jsonl',body),('seal-000000.json',seal),('session.json',terminal)]:
   i=tarfile.TarInfo(PREFIX+name);i.size=len(data);t.addfile(i,io.BytesIO(data))
 return h(terminal)
def main():
 E=R/'evidence/betaintegrated01-cockpit05-iocommit09/host/framed-mock03';E.mkdir(parents=True,exist_ok=False);results=[]
 modes=['baseline','candidate-string-version','receipt-string-version','receipt-string-clock','candidate-extra','context-extra','unknown-carrier','consent-input-retimestamp','mismatch-release-kind','receipt-after-refused-noFailure','refused-then-new-candidate']
 for mode in modes:
  rows=fixture();mutate(rows,mode);p=E/(mode+'.tar');anchor=frame(rows,p)
  try:proof,_=closed_native(p,PREFIX,anchor);accepted=True;error=None
  except Exception as e:accepted=False;error=repr(e)
  results.append(dict(case=mode,accepted=accepted,expectedAccepted=mode=='baseline',pass_=accepted==(mode=='baseline'),error=error,tarSHA256=h(p.read_bytes()),unitOutsideAnchor=anchor))
 v=dict(status='PASS'if all(x['pass_']for x in results)else'FAIL',cases=results,sourceRealJavaUnitTarSHA256=h((BASE/'native-synthetic-owner.tar').read_bytes()),mutations='SYNTHETIC_RECHAINED_UNIT_RAW_NOT_ACTUAL_RECORDINGS',rawOldModified=False,AndroidAP=False)
 (E/'results.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v));assert v['status']=='PASS'
if __name__=='__main__':main()
