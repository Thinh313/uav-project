"""Exact old methods, synthetic socket/correlator/journal seams; no globals patched.
This proves control-flow deferral only, not real clock or IO performance.
"""
from pathlib import Path
from importlib import import_module
import json,time,hashlib,collections
R=Path(__file__).resolve().parents[3];E=R/'evidence/betaintegrated01-cockpit05-clockterm14/host'
OLD=import_module('pilot.betaintegrated01.cockpit04.clock_socket');OWN=import_module('planning.betaintegrated01.cockpit05-clockowner02.runtime.owner')
class Sock:
 def __init__(self):self.pending=collections.deque([b'SYNTHETIC_RESPONSE']);self.recvCalls=0;self.sent=[]
 def recvmsg(self,n):
  self.recvCalls+=1
  if not self.pending:raise BlockingIOError()
  return self.pending.popleft(),[],0,('127.0.0.1',9014)
 def sendto(self,raw,peer):self.sent.append((raw,peer));return len(raw)
class Journal:
 def __init__(self):self.seq=-1;self.head='0'*64;self.rows=[];self.owner=None;self.observed=None
 def append_event(self,kind,data):
  if kind=='CLOCK'and data.get('kind')=='REGISTERED':
   self.observed=dict(beforeUnrelatedRegisterIO=time.monotonic_ns(),publicationVisible=self.owner.publication is not None,injectedDelayNs=15_000_000)
   time.sleep(.015)
  self.seq+=1;self.rows.append((kind,data));self.head=hashlib.sha256(json.dumps(self.rows,sort_keys=True).encode()).hexdigest();return self.seq
class Corr:
 def __init__(self,owner):self.owner=owner;self.row=None
 def receive(self,raw,peer,now,context):
  self.row=dict(run='baseline',epoch='epoch',boot='boot',kind='RESPONSE',id=1,hostReceiveNs=now,offsetLowNs=1,offsetHighNs=2,uncertaintyNs=1,freshCalibration=True)
  self.owner.sink(dict(self.row));return dict(self.row)
 def tick(self,now,ctx):self.owner.sink(dict(run='baseline',epoch='epoch',boot='boot',kind='TICK',hostNs=now))
 def register(self,rid,now,ctx):self.owner.sink(dict(run='baseline',epoch='epoch',boot='boot',kind='REGISTERED',id=rid,hostSendNs=now))
 def calibration(self,now,ctx):return {k:v for k,v in self.row.items()if k in('id','hostReceiveNs','offsetLowNs','offsetHighNs','uncertaintyNs')}if self.row else None

def new_old_socket():
 s=OLD.ClockSocket.__new__(OLD.ClockSocket);s.context=object();s.peer=('127.0.0.1',9014);s.sock=Sock();s.closed=False;s.diagnostic=None;s.diagnostic_written=False;s.next_request=0;s.request_id=1;return s

def main():
 early=new_old_socket();early.next_request=time.monotonic_ns()+100_000_000;early.correlator=None;OLD.ClockSocket.poll(early)
 assert early.sock.recvCalls==0 and len(early.sock.pending)==1
 owner=OWN.ClockOwner(E,'baseline','epoch','boot',180,'a'*64);journal=Journal();journal.owner=owner;owner.journal=journal
 s=new_old_socket();s.correlator=Corr(owner)
 OLD.ClockSocket.poll(s);assert owner.publication is None and journal.observed['publicationVisible']is False
 owner.publish(s.calibration());assert owner.publication.id==1
 result=dict(status='REPRODUCED_OLD_EARLY_RETURN_AND_END_OF_WHOLE_POLL_PUBLICATION',oldEarlyReturn=dict(pollWithPendingResponseBeforeRequestDeadline=True,recvmsgCalls=early.sock.recvCalls,pendingResponsesAfter=len(early.sock.pending)),oldWholePoll=dict(actualOldClockSocketPoll=True,actualOldClockOwnerSinkAndPublish=True,unrelatedRegisterObservation=journal.observed,finalPublicationID=owner.publication.id,receiveToVisibleNs=owner.publication.publicationCompleteHostNs-s.correlator.row['hostReceiveNs']),provenance='EXACT_FROZEN_OLD_METHODS_SYNTHETIC_SOCKET_CORRELATOR_JOURNAL_OBJECTS_AND_DECLARED15MS_SLEEP_IN_REGISTER_NOT_REAL_FSYNC_OR_CLOCK_REPLAY',oldModuleGlobalsPatched=False,actualSocketCreated=False,sourceSHA256={str(Path(p).relative_to(R)):hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in(OLD.__file__,OWN.__file__,__file__)},actualServices=False,deviceCommands=False)
 (E/'clock-baseline01.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],recvBeforeDeadline=early.sock.recvCalls,publicationVisibleBeforeUnrelatedIO=journal.observed['publicationVisible'],injectedDelayNs=15_000_000)))
if __name__=='__main__':main()
