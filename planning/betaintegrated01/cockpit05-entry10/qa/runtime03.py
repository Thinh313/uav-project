"""Independent tiny mock journal closure and direct source wiring. No real guard prime."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
import hashlib,json,sys,ast
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));H='planning.betaintegrated01.cockpit05-entry10';w=import_module(H+'.runtime.journal.writer');rr=import_module(H+'.runtime.journal.receiver');ow=import_module('pilot.betaintegrated01.runtime02.journal.writer');orr=import_module('pilot.betaintegrated01.runtime02.journal.receiver');newfa=import_module(H+'.runtime.frame_adapter');oldfa=import_module('pilot.betaintegrated01.runtime02.frame_adapter');O=R/'evidence/betaintegrated01-cockpit05-entry10/qa/runtime03';O.mkdir();tests=[]
def ok(n,v):assert v,n;tests.append({'id':n,'pass':True})
class MockGuard:
 def __init__(self,*a):self.prime_receipt={'elapsedRealMonotonicNs':15000000000,'historySpanNs':15000000000,'primed':True,'source':'ACTUAL_HOST_15S_PRIME_NO_SYNTHETIC_SEED','sampleCount':151}
 def prime(self):return self.prime_receipt
 def check(self,*a):return None
 def rebind(self,*a):pass
# Metadata labels intentionallysyntheticcontractfixtures; not realprime evidence.
with patch.object(w,'DiskGuard',MockGuard):
 journal=w.SegmentedJournal(O/'new10','r','e');trace=[];journal.record_frame(0,b'rx',b'sensor',lambda b:trace.append(bytes(b))or len(b));anchor=journal.close()['commitAnchor'];result=rr.verify_journal(O/'new10','r','e',expected_commit=anchor)
ok('new10writerCold10Anchored',result['state']=='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'and trace==[b'sensor'])
try:orr.verify_journal(O/'new10','r','e',expected_commit=anchor);reject=False
except orr.VerificationError as exc:reject='DISK_GUARD_POLICY'in str(exc)
ok('old20receiverRejectsNew10',reject)
with patch.object(ow,'DiskGuard',MockGuard):
 journal=ow.SegmentedJournal(O/'old20','r','e');journal.record_frame(0,b'rx',b'sensor',lambda b:len(b));oldanchor=journal.close()['commitAnchor']
try:rr.verify_journal(O/'old20','r','e',expected_commit=oldanchor);reject=False
except rr.VerificationError as exc:reject='DISK_GUARD_POLICY'in str(exc)
ok('new10receiverRejectsOld20',reject)
with patch.object(w,'DiskGuard',MockGuard):
 journal=w.SegmentedJournal(O/'fault10','r','e');calls=[]
 def fail(kind,*args):
  if kind=='fsync':raise OSError('QA_INTENT_FSYNC_FAULT')
 journal.io.hook=fail
 try:journal.record_frame(0,b'rx',b'sensor',lambda b:calls.append(b)or len(b));rejected=False
 except OSError:rejected=True
 ok('intentFsyncFaultBeforeSendNoCallback',rejected and not calls and journal.send_called is False)
methods=[n for n,v in oldfa.FrameAdapter.__dict__.items()if callable(v)and n!='__init__'];ok('everyInheritedAdapterMethodExactObject',all(getattr(newfa.FrameAdapter,n)is getattr(oldfa.FrameAdapter,n)for n in methods))
for n in ['record_frame','append_event','append_stage','close','_write_all','_record']:
 ok('journalAlgorithmExactAST_'+n,ast.dump(ast.parse(__import__('inspect').getsource(getattr(w.SegmentedJournal,n)).lstrip()))==ast.dump(ast.parse(__import__('inspect').getsource(getattr(ow.SegmentedJournal,n)).lstrip())))
backend=(R/'planning/betaintegrated01/cockpit05-entry10/runtime/backend.py').read_text();transport=(R/'planning/betaintegrated01/cockpit05-entry10/runtime/transport.py').read_text();ok('backendSelectsNewAdapterAndTransport','from .frame_adapter import FrameAdapter'in backend and 'from .transport import TransportHub'in backend and 'validate_recording_policy(config)'in backend);ok('transportSelectsNewJournal','from .journal import'in transport)
from pilot.betaintegrated01.runtime02.journal import admission as aold
anew=import_module(H+'.host.admission');ok('onlyEntryPolicyChanges',{k:v for k,v in anew.DISK_POLICY.items()if k!='entryBytes'}=={k:v for k,v in aold.DISK_POLICY.items()if k!='entryBytes'})
files=list((R/'planning/betaintegrated01/cockpit05-entry10/runtime').rglob('*.py'))+[R/'planning/betaintegrated01/cockpit05-entry10/host/policy02.py'];pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files};report={'status':'PASS_NEW_RUNTIME_MOCK_SOURCE_NOT_ACTUAL_PRIME_OR_AP','tests':tests,'inheritedAdapterMethods':methods,'sourcePins':pins,'physicalPolicy':'AP03/model/kernel/speedup1/cap500/fsync algorithm retained, sourceidentity pins external prior manifest gate','mockGuardExplicit':'Test-onlypatchedDiskGuard, 15spr iming metadata synthetic solely readercontract fixture; NEVER actualdurability/admission proof. RealFileIO/fsync executed tinyfiles.','actualGuardPrime':False,'APEmulatorServices':0,'full30minAccepted':False};(O/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(report['status'],len(tests))
