"""Pure failed-recording boundary tests; mock closure, no AP/Android/services."""
from pathlib import Path
from importlib import import_module
import copy,json,hashlib,shutil
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-ioadmit13.flight';F=import_module(H+'.closed_failure');C=import_module(H+'.contract');E=C.E/'host';S=E/'failure-scratch01'
def main():
 S.mkdir(exist_ok=False);cases=[]
 def check(name,fn,ok=True):
  err=None
  try:fn();accepted=True
  except Exception as e:accepted=False;err=type(e).__name__+':'+str(e)
  cases.append(dict(case=name,expected=ok,accepted=accepted,error=err));assert accepted is ok,(name,err)
 try:
  tar=S/'native-private.tar';tar.write_bytes(b'SYNTHETIC_TAR_STUB_ONLY_BOUNDARY_TEST_NOT_NATIVE_INTEGRITY')
  b={k:k for k in F.CONTEXT};b['run']=C.CASES['short']['run'];o={k:b[k]for k in('run','epoch','boot','generation')};o.update(closed=True,authorityRestorable=False,firstFailure='MOCK_STALE_ADMISSION',journal=dict(closed=True,commitAnchor='a'*64),input=dict(consent=False,leaseId=None));closure=dict(failure='MOCK_STALE_ADMISSION');location=dict(path=str(tar),sha256=hashlib.sha256(tar.read_bytes()).hexdigest())
  def invoke(bb=b,oo=o,cc=closure,ll=location,case='actual-short01'):return F.validate_closed_failure(bb,oo,cc,ll,S,case)
  check('failed_before_home_without_TX_REFUSED_valid_boundary',invoke)
  assert not(S/'confirm-home-bracket.json').exists()and not(S/'native-confirmation-descriptor.json').exists()
  for label,group,key,value in [('wrong_run','b','run','cockpit05-release12-short-01'),('closed_false','o','closed',False),('authority_restored','o','authorityRestorable',True),('invalid_native_failure_type','o','firstFailure',123),('successful_closure','c','failure',None),('wrong_tar_sha','l','sha256','0'*64),('foreign_tar_path','l','path',str(S/'foreign.tar'))]:
   a,d,f,g=map(copy.deepcopy,(b,o,closure,location));{'b':a,'o':d,'c':f,'l':g}[group][key]=value;check(label,lambda a=a,d=d,f=f,g=g:invoke(a,d,f,g),False)
  a=copy.deepcopy(o);a['input']['consent']=True;check('consent_not_revoked',lambda:invoke(oo=a),False)
  a=copy.deepcopy(o);a['journal']['closed']=False;check('raw_unclosed',lambda:invoke(oo=a),False)
  check('foreign_case',lambda:invoke(case='actual-old01'),False)
  before=set(S.iterdir());invoke();assert set(S.iterdir())==before;check('boundary_pure_no_descriptor_or_other_write',lambda:None)
  result=dict(status='PASS_FAILED_RECORDING_BOUNDARIES_ONLY',cases=cases,provenance='SYNTHETIC_METADATA_AND_TAR_STUB_NO_NATIVE_INTEGRITY_ACCEPTANCE',deviceCommands=False,APOrServices=False,guardPrime=False,rawOrOldSourceWrites=False,scope='Actual selectedreceiver/strictchain must be exercised separately afterAPKbuild and nativeprotocoltests',scratchRemoved=True)
  (E/'failure-helper-unit02.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=len(cases))))
 finally:shutil.rmtree(S)
if __name__=='__main__':main()
