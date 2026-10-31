"""Independent pure tar/schema/path tests; no Export/Guard/device/process instance."""
from pathlib import Path
from importlib import util
from unittest.mock import patch
import sys,subprocess,tarfile,hashlib,json,io
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];P=R/'planning/betaintegrated01/cockpit05-closure01/export02.py';calls=[]
def denied(*a,**k):calls.append(1);raise AssertionError('NO_PROCESS')
with patch.object(subprocess,'run',denied),patch.object(subprocess,'Popen',denied),patch.object(subprocess,'check_output',denied):
 spec=util.spec_from_file_location('exportpure',P);m=util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.R==R
O=R/'evidence/betaintegrated01-cockpit05-closure01/qa/pure02';O.mkdir();run='test';name='files/control-runs/test/session.json';raw=b'MOCK notactualnative';expected={name:hashlib.sha256(raw).hexdigest()};tests=[]
def make(path,names):
 with tarfile.open(path,'w')as t:
  for label,data in names:
   i=tarfile.TarInfo(label);i.size=len(data);t.addfile(i,io.BytesIO(data))
def run_case(label,path,accept):
 try:m.tar_check(path,expected,run);ok=accept
 except(RuntimeError,tarfile.TarError,EOFError):ok=not accept
 tests.append({'id':label,'pass':ok})
a=O/'valid.tar';make(a,[(name,raw)]);run_case('validSyntheticSHAandZeros',a,True)
b=O/'noeof.tar';b.write_bytes(a.read_bytes()[:1024]);run_case('missingZeroEOF',b,False)
b=O/'trailingnonzero.tar';b.write_bytes(a.read_bytes()+b'X'+b'\0'*1023);run_case('paddedTrailingNonzero',b,False)
b=O/'duplicate.tar';make(b,[(name,raw),(name,raw)]);run_case('duplicateMember',b,False)
b=O/'foreign.tar';make(b,[(name,raw),('files/foreign/x',b'x')]);run_case('foreignMember',b,False)
b=O/'badsha.tar';make(b,[(name,b'wrong')]);run_case('changedMemberSHA',b,False)
b=O/'traversal.tar';make(b,[('../x',raw)]);run_case('unsafePath',b,False)
assert all(t['pass']for t in tests);assert not calls
s=P.read_text();assert 'prime.get(\'elapsedRealMonotonicNs\''in s or "['elapsedRealMonotonicNs']"in s
r={'status':'PASS_BOUNDED_PRESERVATION_EXPORT_SOURCE_AND_TAR_MOCK','tests':tests,'repositoryPathExact':str(m.R),'sourceSHA256':hashlib.sha256(P.read_bytes()).hexdigest(),'scope':'NoGuard/Exportinstance, noADB/PID/process/actualtar/export; tinySYNTHETICmemberfixtures only. Actualnativebytes externalanchors/contextstillneedslatercoldreader.','externalCommands':len(calls),'flightAccepted':False};(O/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(r['status'],len(tests),r['sourceSHA256'])
