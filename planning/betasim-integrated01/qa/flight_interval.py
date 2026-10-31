"""Independent receive-only AUTO/resume causal cases, no files or actors."""
from pathlib import Path
import hashlib,json,struct,sys
P=Path(__file__).resolve();REPO=P.parents[3];R=P.parent.parent/'runtime';sys.path[:0]=[str(R/'source'),str(REPO)]
from aeris_runtime.flight_interval import FlightIntervalTracker
from pilot.betaintegrated01.control01.mavlink import Framer,observe,crc,DEFINITIONS
source=R/'source/aeris_runtime/flight_interval.py';pin=hashlib.sha256(source.read_bytes()).hexdigest();checks=[];C={'run':'qa','epoch':'e','boot':'b','operator':'A','generation':'g','profileId':'WORKBENCH_SIM_V1'}
def wire(i,p,seq,system=42,component=1):
 b=bytes([253,len(p),0,0,seq,system,component])+i.to_bytes(3,'little')+p;return b+crc(b[1:],DEFINITIONS[i][2]).to_bytes(2,'little')
def auto(t,n,seq=1):
 raw=wire(76,struct.pack('<7fHBBB',1.,3.,0.,0.,0.,0.,0.,176,42,1,0),seq,255,190);t.event('NATIVE_RX',{'hostNs':n,'rawHex':raw.hex()},{'sequence':seq,'sha256':str(seq%10)*64})
def hb(t,n,mode,seq,armed=True):
 raw=wire(0,struct.pack('<IBBBBB',mode,2,3,128 if armed else 0,4,3),seq);data={**observe(Framer().feed(raw,n)[0]),'newSequenceObservation':True};t.event('PASSIVE_FRAME',data,{'sequence':seq+20,'sha256':str(seq%10)*64})
def test(name,fn):
 try:fn();checks.append({'id':name,'pass':True})
 except BaseException as e:checks.append({'id':name,'pass':False,'error':str(e)})
def basic():
 t=FlightIntervalTracker(C);auto(t,100);hb(t,200,3,1);hb(t,300,5,2);return t
def resume():
 t=basic();auto(t,400,2);assert t.start==100 and len(t.auto_ingresses)==2

def repeated():
 t=basic();auto(t,400,2)
 try:auto(t,401,3)
 except ValueError:return
 raise AssertionError('second AUTO resume before any observed new AUTO heartbeat accepted as another explicit resume')
def same():
 t=FlightIntervalTracker(C);auto(t,100);hb(t,200,3,1)
 try:auto(t,300,2)
 except ValueError:return
 raise AssertionError('same-mode AUTO retry accepted')
def crc_bad():
 t=FlightIntervalTracker(C);raw=bytearray(wire(76,struct.pack('<7fHBBB',1.,3.,0.,0.,0.,0.,0.,176,42,1,0),1,255,190));raw[-1]^=1
 try:t.event('NATIVE_RX',{'hostNs':100,'rawHex':bytes(raw).hex()},{})
 except ValueError:return
 raise AssertionError('badCRC accepted')
for name,fn in [('AUTO-HOLD-explicit-resume-retains-initial-start',resume),('duplicate-resume-before-observed-mode-transition-refused',repeated),('same-mode-AUTO-retry-refused',same),('corrupt-command-CRC-refused',crc_bad)]:test(name,fn)
report={'format':'aeris-independent-flight-interval-resume-source-contract','version':1,'status':'PASS_RECEIVE_ONLY_NOT_FLIGHT_ACCEPTANCE'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourceSHA256':pin,'checks':checks,'actualAndroidAPOrDurableColdJoin':False};out=REPO/'evidence/betasim-integrated01/qa';n=1
while(out/f'flight-interval-{n:02}.json').exists():n+=1
p=out/f'flight-interval-{n:02}.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'output':str(p)}))
