"""INTEGRATION03 SAF strict outer validation with separately pinned crew provenance.
Offline/read-only. Never relabel a wrong selected run as the expected target.
"""
from pathlib import Path
import argparse,hashlib,json,importlib.util,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'evidence/operator01-qa/tools/saf-package04.py'
BASE_SHA='2062e6bd7e890c53983603d365136340631378cc10506b8fcd6f40ab6eb39acb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def resolve(p):
 p=Path(p);return p if p.is_absolute() else ROOT/p
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser()
 for k in ('package','staged','descriptor','expect','pins','run','private','external-receipt','output'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--expect-sha256',required=True,help='Pre-export declaration SHA; never obtained by rewriting expectation after SAVE')
 a=p.parse_args();need(not a.output.exists(),'immutable output exists')
 try:
  need(sha(BASE)==BASE_SHA,'frozen strict ZIP verifier changed')
  spec=importlib.util.spec_from_file_location('i03_frozen_p1_saf',BASE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  need(sha(a.expect)==a.expect_sha256,'predeclared expectation hash changed')
  expect=m.obj(a.expect.read_bytes());need(expect['receiver']=='rtr-evaluator','receiver policy');need(expect['run']==a.run.name,'declared selected-run mismatch')
  need(type(expect['nonce']) is str and 12<=len(expect['nonce'])<=128 and expect['nonce'].isascii(),'declared nonce bound')
  r=m.verify(a);pins=m.obj(a.pins.read_bytes());apk=resolve(pins['apkPath']);need(sha(apk)==pins['apkSha256'],'exact exporter APK bytes')
  ext=m.obj(a.external_receipt.read_bytes());need(ext['run']==a.run.name and ext['sourceId']==pins['sourceId'] and ext['apkSha256']==pins['apkSha256'],'external evidence context')
  verified=[]
  for item in ext['files']:
   path=resolve(item['path']);need(path.is_file() and sha(path)==item['sha256'],'external evidence SHA:'+str(path));verified.append(item)
  kinds={x['kind'] for x in verified}
  need({'native-public','admin-policy','crew-audit','b-peer','crew-receiver','mission-receiver','source-freeze','tls-auth-receipt'}<=kinds,'missing external evidence classes')
  bykind={k:[resolve(x['path']) for x in verified if x['kind']==k] for k in kinds}
  for kind,prefix in [('crew-receiver','PASS_CREW_LAYER_ONLY'),('mission-receiver','PASS_MISSION_ROUTE_OBSERVER_LAYER')]:
   q=load(bykind[kind][0]);need(q['status']==prefix and q['run']==a.run.name and q['sourceId']==pins['sourceId'],'independent receiver context/result:'+kind)
  r.update(status='PASS_SAF_OUTER_AND_EXTERNAL_BINDINGS_ONLY',exporterApkSha256=pins['apkSha256'],declaredExpectationSha256=a.expect_sha256,externalCompanion={'path':str(a.external_receipt),'sha256':sha(a.external_receipt),'files':verified},externalEvidenceInZIP=False,actualMissionAcceptance='SEPARATE_ACCEPTED_REVIEW_GATE_REQUIRED',authenticationClaim='Separate actual TLS/source/negative trials; never inferred from ZIP/SHA/ACK',physicalExecutionProven=False)
  code=0
 except Exception as e:r={'status':'FAIL_SAF_INTENDED_TARGET_OR_BINDING','errorType':type(e).__name__,'error':str(e)};code=2
 r.update(toolSha256=sha(Path(__file__)),frozenVerifierSha256=BASE_SHA,scope='OFFLINE_SAF_INTEGRITY_AND_PINNED_COMPANIONS_NOT_FULL_MILESTONE')
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x') as f:json.dump(r,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
 print(json.dumps({'status':r['status'],'output':str(a.output),'error':r.get('error')}));return code
if __name__=='__main__':raise SystemExit(main())
