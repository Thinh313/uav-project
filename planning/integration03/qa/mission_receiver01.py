"""INTEGRATION03 offline mission layer reusing pinned, independently authored raw oracle.
Compiler parity is separate from held-out independent geometry/semantic QA.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'evidence/crew02-qa/tools/mission-raw03.py'
BASE_SHA='0b021de1732b7950091896d03160868156cc8a4927bc237f7bae5aafbd9b0fbe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--pins',required=True,type=Path);p.add_argument('--case',choices=['nominal','partition','pilot-loss'],required=True);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 if a.output.exists():raise RuntimeError('immutable output exists')
 try:
  if sha(BASE)!=BASE_SHA:raise ValueError('frozen mission receiver changed')
  sp=importlib.util.spec_from_file_location('i03_frozen_mission_raw',BASE);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  r=m.verify(a.run,m.load(a.pins),'pilot-loss' if a.case=='pilot-loss' else 'nominal',a.case!='pilot-loss')
  r.update(integration03Case=a.case,acceptedReviewMandatory=a.case!='pilot-loss',independentI02Geometry='SEPARATE_HELDOUT_CHECKER_REQUIRED',claim='RAW_MISSION_LAYER_ONLY_NOT_WHOLE_MILESTONE')
  code=0
 except Exception as e:r={'status':'FAIL_OR_SCHEMA_UNSUPPORTED','errorType':type(e).__name__,'error':str(e),'run':str(a.run)};code=2
 r.update(receiverSha256=sha(Path(__file__)),frozenMissionReceiverSha256=BASE_SHA,actualImages=0,physicalExecutionProven=False)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x') as f:json.dump(r,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
 print(json.dumps({'status':r['status'],'output':str(a.output),'error':r.get('error')}));return code
if __name__=='__main__':raise SystemExit(main())
