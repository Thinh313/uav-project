"""Tiny genuine FileIO/fsync chains with SYNTHETIC priming metadata, no live clock/AP."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
import json,struct,time,hashlib,shutil
from pilot.betaintegrated01.clock.correlation import Context,BoundedCorrelator
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-clockowner02'
O=import_module(H+'.runtime.owner');V=import_module(H+'.runtime.receiver');P=import_module(H+'.policy');J=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal');W=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal.writer')
E=R/'evidence/betaintegrated01-cockpit05-clockowner02/host/cold-mock01'
class SyntheticGuard:
 def __init__(self,*a):self.prime_receipt={'elapsedRealMonotonicNs':15000000000,'historySpanNs':15000000000,'primed':True,'source':'ACTUAL_HOST_15S_PRIME_NO_SYNTHETIC_SEED','sampleCount':151}
 def prime(self):pass
 def check(self,*a):return 20*2**30
 def rebind(self,*a):pass
class Alive:
 def is_alive(self):return True

def main():
 E.mkdir(parents=True,exist_ok=False);s=E/'scratch';s.mkdir();checks=[]
 def test(name,fn):
  try:checks.append({'case':name,'pass':True,'detail':fn()})
  except BaseException as error:checks.append({'case':name,'pass':False,'error':repr(error)})
 def fixture(name,offset_fault=False):
  d=s/name;d.mkdir();now=time.monotonic_ns();o=O.ClockOwner(d,'mockrun','epoch','boot',180,'a'*64,origin_ns=now-1000000);o.thread=Alive()
  with patch.object(W,'DiskGuard',SyntheticGuard):o.journal=J.SegmentedJournal(d/'clock-journal','mockrun','epoch',P.clock_policy(180),io=o.diagnostic_io)
  o._append('CLOCK_OWNER_BINDING',{'run':'mockrun','epoch':'epoch','boot':'boot','sourceAmendmentSHA256':'a'*64,'originHostNs':o.origin_ns,'maximumEvents':P.clock_events(180),'maximumRecordBytes':2048})
  c=BoundedCorrelator(Context('mockrun','epoch','boot'),('127.0.0.1',9014),o.sink,max_pending=8,recent_limit=64)
  c.tick(now,c.context);c.register(1,now,c.context);c.receive(struct.pack('<7Q',1,now-100000000,now-100000000,0,0,0,0),('127.0.0.1',9014),now+10000,c.context);o.publish(c.calibration(now+10000,c.context))
  if offset_fault:
   c.register(2,now+100000000,c.context)
   # Integrity-valid but semantically false producer claim, never real calibration.
   prior=dict(o.last_response[0]);raw=struct.pack('<7Q',2,now+100000000,now+100000000,0,0,0,0)
   prior.update(sequence=prior['sequence']+2,id=2,hostSendNs=now+100000000,hostReceiveNs=now+100010000,hostNs=now+100010000,guestReceiveNs=now+100000000,guestSendNs=now+100000000,offsetLowNs=0,offsetHighNs=10000,uncertaintyNs=10000,rawHex=raw.hex(),rawSHA256=hashlib.sha256(raw).hexdigest())
   o.sink(prior)
  closed=o.journal.close();return d,closed['commitAnchor'],o
 good,anchor,owner=fixture('good');bad,badanchor,_=fixture('offset-fault',True)
 def verify(path=good,a=anchor):return V.verify_clock(path,'mockrun','epoch','boot',expected_anchor=a,source_amendment='a'*64,maximum_seconds=180)
 test('full V2 framed clock chain with synthetic guard metadata and genuine local fsync',lambda:{'events':verify()['events'],'ioOperations':owner.diagnostic_io.operations})
 def reject(fn):
  try:fn()
  except Exception as e:return type(e).__name__+':'+str(e)
  raise AssertionError('counterfeitaccepted')
 test('integrity-valid MATCHED 100ms offset discontinuity rejects frozen correlator replay',lambda:reject(lambda:verify(bad,badanchor)))
 test('external clock anchor required',lambda:reject(lambda:verify(good,None)))
 def corruption():
  p=sorted((good/'clock-journal').glob('segment-*.jsonl'))[0];b=p.read_bytes();p.write_bytes(b[:-2]+b'X\n')
  try:return reject(verify)
  finally:p.write_bytes(b)
 test('deep framed stream corruption rejects and fixture restored',corruption)
 def refs():
  v=verify();pub=owner.publication;origin=owner.origin_ns;checked=time.monotonic_ns();f={}
  for suffix,checkkey,agekey,idkey in [('Receive','clockCheckAtReceiveSinceOriginNs','clockAgeAtReceiveNs','clockIDAtReceive'),('Send','clockCheckBeforeSendSinceOriginNs','clockAgeBeforeSendNs','clockIDBeforeSend')]:
   f.update({'clockPublicationAt'+suffix:pub.clockPublicationSequence,'clockPublicationCompleteAt'+suffix+'SinceOriginNs':pub.publicationCompleteHostNs-origin,checkkey:checked-origin,agekey:checked-pub.hostReceiveNs,idkey:pub.id})
  f.update(clockAtomicPermitSinceOriginNs=checked-origin,clockAtomicPermitAgeNs=checked-pub.hostReceiveNs,sendBeginSinceOriginNs=checked-origin)
  V.verify_frame_reference(f,origin,v['publications']);f['clockPublicationAtSend']+=1
  return reject(lambda:V.verify_frame_reference(f,origin,v['publications']))
 test('separate receive/send durable references good and unknown publication rejected',refs)
 removed=sum(p.stat().st_size for p in s.rglob('*')if p.is_file());shutil.rmtree(s)
 value={'status':'PASS'if all(x['pass']for x in checks)else'FAIL','cases':checks,'guardPrimeWasSynthetic_TEST_ONLY':True,'actual15sPrime':False,'genuineLocalFileIOFsync':True,'APorNetworkServices':False,'scratchRemoved':True,'removedBytes':removed};(E/'results.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2));assert value['status']=='PASS'
if __name__=='__main__':main()
