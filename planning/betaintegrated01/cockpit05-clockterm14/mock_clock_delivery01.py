"""Actual socket/correlator and owner; fake UDP, no services or device."""
from pathlib import Path
from importlib import import_module
import collections,hashlib,json,struct,time
R=Path(__file__).resolve().parents[3];E=R/'evidence/betaintegrated01-cockpit05-clockterm14/host'
NEW=import_module('planning.betaintegrated01.cockpit05-clockterm14.runtime.clock_socket');OWN=import_module('planning.betaintegrated01.cockpit05-clockterm14.runtime.owner')
class Sock:
 def __init__(self,*a):self.queue=collections.deque();self.sent=[];self.recvCalls=0
 def bind(self,a):pass
 def setblocking(self,v):assert v is False
 def recvmsg(self,n):
  self.recvCalls+=1
  if not self.queue:raise BlockingIOError()
  return self.queue.popleft()
 def sendto(self,b,p):self.sent.append((b,p));return len(b)
 def close(self):pass
class Journal:
 def __init__(self,owner):self.owner=owner;self.seq=-1;self.head='0'*64;self.rows=[];self.before=[]
 def append_event(self,k,v):
  if k=='CLOCK'and v.get('kind')=='REGISTERED':self.before.append(self.owner.publication.id if self.owner.publication else None);time.sleep(.015)
  self.seq+=1;self.rows.append((k,v));self.head=hashlib.sha256(json.dumps(self.rows,sort_keys=True).encode()).hexdigest();return self.seq

def main():
 results=[];now=[1_000_000_000];sock=Sock();owner=OWN.ClockOwner(E,'probe','epoch','boot',180,'a'*64);journal=Journal(owner);owner.journal=journal
 s=NEW.ClockSocket('probe','epoch','boot',owner.sink,maximum_seconds=180,on_matched_response=owner.publish,socket_factory=lambda*a:sock,now_ns=lambda:now[0]);s.poll();assert len(sock.sent)==1
 now[0]+=20_000_000;sock.queue.append((struct.pack('<7Q',1,1_001_000_000,1_002_000_000,0,0,0,0),[],0,s.peer));s.poll()
 assert owner.publication.id==1 and len(sock.sent)==1 and owner.publication.hostReceiveNs==now[0];results.append('BEFORE_DEADLINE_DRAINS_ORIGINAL_RECEIPT')
 callbacks=s.probe.callbacks;sock.queue.extend([(struct.pack('<7Q',1,1_001_000_000,1_002_000_000,0,0,0,0),[],0,s.peer),(struct.pack('<7Q',99,1,2,0,0,0,0),[],0,s.peer)]);s.poll();assert s.probe.callbacks==callbacks;results.append('DUPLICATE_UNKNOWN_NOT_CALLBACK')
 now[0]=1_100_000_000;s.poll();now[0]=1_200_000_000;sock.queue.append((struct.pack('<7Q',2,1_101_000_000,1_102_000_000,0,0,0,0),[],0,s.peer));s.poll();assert journal.before[-1]==2;results.append('PUBLISH_BEFORE_UNRELATED15MS_REGISTER')
 sock.queue.extend([(struct.pack('<7Q',200+i,1,2,0,0,0,0),[],0,s.peer)for i in range(9)]);s.poll();assert len(sock.queue)==1;results.append('DRAIN8')
 assert(s.correlator.max_pending,s.correlator.recent_limit,s.correlator.fresh_ns,s.correlator.timeout_ns)==(8,64,250_000_000,300_000_000);results.append('UNCHANGED_LIMITS')
 assert len(s.probe.snapshot()['lastOperations'])<=64;results.append('BOUNDED_PROBE')
 value=dict(status='PASS_MOCK_CLOCK_DELIVERY',cases=results,count=len(results),actualServices=False,actualUDP=False,deviceCommands=False,sourcePins={str(Path(p).relative_to(R)):hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in(NEW.__file__,OWN.__file__,__file__)},timingProof='DECLARED15MS_REGISTER_SLEEP_CONTROL_FLOW_NOT_END_TO_END_PERFORMANCE',diagnostic=s.probe.snapshot());s.close()
 (E/'clock-delivery01.json').open('x').write(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(status=value['status'],count=len(results))))
if __name__=='__main__':main()
