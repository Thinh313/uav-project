"""Independent follow-up of finalcommit, cold anchoring and receiver schema."""
from pathlib import Path
import sys,json,os,hashlib,zlib,copy,shutil,datetime
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.journal import SegmentedJournal,Policy,FileIO,verify_journal
tag=sys.argv[1]if len(sys.argv)>1 else'01';E=R/'evidence/betaintegrated01-m1mock/qa'/('journal-followup'+tag);E.mkdir(exist_ok=False)
assert shutil.disk_usage(E).free>=10*2**30+256*2**20
sources=[R/'pilot/betaintegrated01/journal'/p for p in ['writer.py','receiver.py']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p.relative_to(R)):sha(p)for p in sources};results=[]
P=Policy(segment_bytes=20480,quota_bytes=524288,max_record_bytes=2048,max_segments=128,termination_reserve_bytes=16384)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def case(name,fn):
 try:results.append({'id':name,'status':'PASS','detail':fn()})
 except Exception as e:results.append({'id':name,'status':'FAIL','error':type(e).__name__+':'+str(e)})
def fail(fn):
 try:fn()
 except Exception as e:return str(e)
 raise AssertionError('expected refusal')
def create(name,io=None):
 p=E/name;j=SegmentedJournal(p,'run','epoch',P,io=io);j.record_frame(0,b'raw',b'sensor',lambda b:len(b));j.append_event('CLOCK',{'id':1});return p,j
base,j=create('normal');closed=j.close();anchor=closed['commitAnchor'];(E/'trusted-close-anchor.json').write_bytes(canonical(anchor))
def normal():
 v=verify_journal(base,'run','epoch');assert v['state']=='COMPLETE_BYTES_UNATTESTED'and v['byteSequenceComplete']and not v['writerCommitAttested']and not v['publicationAllowed']
 z=verify_journal(base,'run','epoch',expected_commit=anchor);assert z['state']=='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'and z['writerCommitAttested']and not z['publicationAllowed'];return {'default':v,'externalAnchor':z}
case('JF01_default_unattested_external_anchor_not_publication',normal)
def finalfault():
 class Fault(FileIO):
  def dirsync(self,p):
   if (Path(p)/'session.json').exists():raise OSError('QA_FINAL_DIRSYNC')
   return super().dirsync(p)
  def open_exclusive(self,p):
   if Path(p).name=='failure.json':raise OSError('QA_FAILURE_MARKER')
   return super().open_exclusive(p)
 p,j=create('finalfault',Fault());err=fail(j.close);v=verify_journal(p,'run','epoch');assert v['state']=='COMPLETE_BYTES_UNATTESTED'and not v['writerCommitAttested']and not v['publicationAllowed'];return {'closeError':err,'cold':v}
case('JF02_J13_final_double_fault_cannot_attest_commit',finalfault)
def reseal(p,mutate):
 f=p/'segment-000000.jsonl';rows=[json.loads(x)for x in f.read_bytes().splitlines()];mutate(rows);head='0'*64;out=[]
 for row in rows:
  row['body']['previous']=head;raw=canonical(row['body']);row['crc32']=format(zlib.crc32(raw),'08x');row['sha256']=hashlib.sha256(bytes.fromhex(head)+raw).hexdigest();head=row['sha256'];out.append(canonical(row)+b'\n')
 data=b''.join(out);f.write_bytes(data);sp=p/'segment-000000.seal.json'
 if sp.exists():
  seal=json.loads(sp.read_bytes());seal.update(fileBytes=len(data),fileSHA256=sha(f),head=head);sp.write_bytes(canonical(seal)+b'\n')
 if (p/'session.json').exists():
  session=json.loads((p/'session.json').read_bytes());session.update(head=head,lastSegmentSHA256=sha(f));(p/'session.json').write_bytes(canonical(session)+b'\n')
def clone(n):p=E/n;shutil.copytree(base,p);return p
def altered():
 p=clone('resealed-data');reseal(p,lambda rows:rows[1]['body']['payload'].update(base64='bmV3'))
 v=verify_journal(p,'run','epoch');assert v['state']=='COMPLETE_BYTES_UNATTESTED'and not v['publicationAllowed'];err=fail(lambda:verify_journal(p,'run','epoch',expected_commit=anchor));return {'resealedDefault':v['state'],'externalAnchorRefusal':err,'scope':'Unkeyed coherent bytes are not authentic source; original trusted external anchor detects modification'}
case('JF03_resealed_payload_rejected_by_original_external_anchor',altered)
def policy():
 p=clone('badpolicy');m=json.loads((p/'manifest.json').read_bytes());m['policy']['termination_reserve_bytes']=1;(p/'manifest.json').write_bytes(canonical(m));return fail(lambda:verify_journal(p,'run','epoch'))
case('JF04_receiver_policy_parity',policy)
def eventkind():
 p=clone('badeventkind');reseal(p,lambda rows:rows[-2]['body']['payload'].update(eventKind=False));return fail(lambda:verify_journal(p,'run','epoch'))
case('JF05_resealed_nonstring_event_kind',eventkind)
def closefault():
 class Fault(FileIO):
  def __init__(self):super().__init__();self.paths={};self.armed=False
  def open_exclusive(self,p):fd=super().open_exclusive(p);self.paths[fd]=str(p);return fd
  def close(self,fd):
   super().close(fd)
   if self.armed and self.paths.get(fd,'').endswith('.jsonl'):self.armed=False;raise OSError('QA_CLOSE_AFTER_REAL_CLOSE')
 io=Fault();p,j=create('closefault',io);io.armed=True;err=fail(j.close);v=verify_journal(p,'run','epoch');assert v['state']=='INCOMPLETE_RECORDING'and not v['writerCommitAttested'];return {'closeError':err,'coldState':v['state']}
case('JF06_segment_close_failure_no_commit_anchor',closefault)
def composed():
 from pilot.betaintegrated01.clock.correlation import Context,BoundedCorrelator
 import struct
 p=E/'clockcomposed';j=SegmentedJournal(p,'run','epoch',P);c=Context('run','epoch','boot');peer=('127.0.0.1',18000);b=BoundedCorrelator(c,peer,lambda r:j.append_event('CLOCK',r),recent_limit=3)
 for rid in range(24):
  t=rid*1000+100;b.register(rid,t,c);b.receive(struct.pack('<7Q',rid,t,t+1,0,0,0,0),peer,t+2,c)
 close=j.close();v=verify_journal(p,'run','epoch',expected_commit=close['commitAnchor']);assert v['events']==48 and v['writerCommitAttested']and not v['publicationAllowed'];return {'events':v['events'],'segments':v['segments'],'state':v['state']}
case('JF07_new_source_clock_sink_composition',composed)
def boolheader():
 p=clone('boolheader');reseal(p,lambda rows:rows[0]['body']['payload'].update(ordinal=False));return fail(lambda:verify_journal(p,'run','epoch'))
case('JF08_header_ordinal_bool_not_int',boolheader)
def boolclose():
 p=clone('boolclose');reseal(p,lambda rows:rows[-1]['body']['payload'].update(completedFrames=True));return fail(lambda:verify_journal(p,'run','epoch'))
case('JF09_close_count_bool_not_int',boolclose)
def boolunknown():
 p,j=create('boolunknown');fail(lambda:j.record_frame(1,b'r',b's',lambda b:0));reseal(p,lambda rows:rows[-1]['body'].update(frame=True));return fail(lambda:verify_journal(p,'run','epoch'))
case('JF10_unknown_frame_bool_not_int',boolunknown)
after={str(p.relative_to(R)):sha(p)for p in sources};q={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':after,'sourceChanged':before!=after,'status':'PASS_SCOPED'if all(x['status']=='PASS'for x in results)and before==after else'FINDINGS_OR_DRIFT','results':results,'scope':'Mock bounded recording only; no flight, device, signature, AP-stage or source-authenticity claim'}
(E/'results.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2));sys.exit(0 if q['status']=='PASS_SCOPED'else 2)
