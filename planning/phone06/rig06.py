"""Asserted PHONE06 adaptation of the pinned lifecycle05 controller, never edits it."""
from pathlib import Path
import sys,json,hashlib,re,types,os
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];P=Path(__file__).parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):
 pins=json.loads((P/'runtime-dependencies.json').read_text())['files'];b=(R/p).read_bytes()
 if pins.get(p)!=sha(b):raise RuntimeError('PHONE_RIG_FROZEN_DEPENDENCY_DRIFT:'+p)
 return b.decode()
def replace(s,a,b,count=None):
 n=s.count(a)
 if not n or count is not None and n!=count:raise RuntimeError('PHONE_RIG_DERIVATION_CONTEXT:'+a)
 return s.replace(a,b)
def derived():
 helper=read('planning/integration03/runtime/bootstrap04.py');helper=replace(helper,'/aeris-integration03','/aeris-phone06',1);helper=replace(helper,'!= "integration03"','!= "phone06"',1);helper=replace(helper,'5941','5965',1)
 runtime=read('planning/integration03/runtime/runtime05.py');runtime=replace(runtime,'parents[3]','parents[2]',1);runtime=replace(runtime,'evidence/integration03-runtime','evidence/phone06/runtime');runtime=replace(runtime,'aeris-integration03','aeris-phone06',1);runtime=replace(runtime,'aeris.task=integration03','aeris.task=phone06',1);runtime=replace(runtime,'INTEGRATION03_ADMISSION','PHONE06_ADMISSION',1);runtime=replace(runtime,'planning/integration03/runtime','planning/phone06');runtime=replace(runtime,"'controllerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),","'controllerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'derivedControllerSha256':DERIVED_SOURCE_SHA06,'hostStartedMonoNs':str(time.monotonic_ns()),",1)
 counts={}
 for old,new in [(5937,5960),(5938,5962),(5939,5963),(5940,5964),(5941,5965)]:
  counts[str(old)]=len(re.findall(r'\b'+str(old)+r'\b',runtime));assert counts[str(old)]>0;runtime=re.sub(r'\b'+str(old)+r'\b',str(new),runtime)
 return helper,runtime,{'helperSha256':sha(helper.encode()),'controllerSha256':sha(runtime.encode()),'explicitPortOccurrenceCounts':counts,'sameLifecycleBranches':True,'hostGCSCommandBytes':0,'nativeSoleGCS':True}
def main():
 helper,runtime,receipt=derived()
 if sys.argv[1:]==['--dry-run']:print(json.dumps(receipt,indent=2));return
 if len(sys.argv)!=3:raise RuntimeError('PHONE_RIG_EXPLICIT_RUN_CASE')
 from phase06 import validate_phase
 phase=validate_phase(Path(os.environ['PHONE06_ADMISSION']),require_resource=True)
 if sys.argv[1]not in phase['allowedRuns']:raise RuntimeError('PHONE_RIG_RUN_NOT_ADMITTED')
 module=types.ModuleType('bootstrap04');module.__file__=str(P/'rig06.py');exec(compile(helper,module.__file__,'exec'),module.__dict__);sys.modules['bootstrap04']=module
 # Actual unchanged lifecycle branches execute, including first-cause, pre-stop and process seal.
 exec(compile(runtime,str(P/'runtime.py'),'exec'),{'__name__':'__main__','__file__':str(P/'runtime.py'),'DERIVED_SOURCE_SHA06':receipt['controllerSha256']})
if __name__=='__main__':main()
