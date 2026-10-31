"""Original wire CRC + lossless AJZ + WAL interval joins; no AP actors."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,shutil,struct,sys,zlib
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)]
from aeris_runtime.flight_interval import FlightIntervalTracker
from pilot.betaintegrated01.control01.mavlink import Framer,observe,crc,DEFINITIONS
LAB=REPO/'evidence/betasim-integrated01/runtime/.interval';C={'run':'wire','epoch':'a'*32,'boot':'b'*32,'operator':'pilot','generation':'c'*32,'profileId':'WORKBENCH_SIM_V1'}
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def wire(i,p,seq,system=42,component=1):
 b=bytes([253,len(p),0,0,seq,system,component])+i.to_bytes(3,'little')+p;return b+crc(b[1:],DEFINITIONS[i][2]).to_bytes(2,'little')
def passive(t,seq,i,p):
 w=wire(i,p,seq);f=Framer().feed(w,t)[0];return{**observe(f),'newSequenceObservation':True}
def deny(f):
 try:f()
 except ValueError:return
 raise AssertionError('expected rejection')
def main():
 assert not LAB.exists();product=LAB/'sessions/wire/product';(product/'journal').mkdir(parents=True);checks=[]
 try:
  t=FlightIntervalTracker(C);cmd=wire(76,struct.pack('<7fHBBB',1.,3.,0.,0.,0.,0.,0.,176,42,1,0),1,255,190);t.event('NATIVE_RX',{'hostNs':100,'rawHex':cmd[:13].hex()},{'sequence':1,'sha256':'1'*64});t.event('NATIVE_RX',{'hostNs':110,'rawHex':cmd[13:].hex()},{'sequence':2,'sha256':'2'*64});assert t.start==110
  for at,s,i,p in [(200,1,0,struct.pack('<IBBBBB',3,2,3,128,4,3)),(250,2,0,struct.pack('<IBBBBB',5,2,3,128,4,3)),(270,3,0,struct.pack('<IBBBBB',3,2,3,128,4,3)),(300,4,0,struct.pack('<IBBBBB',0,2,3,0,4,3)),(310,5,245,b'\x00\x01'),(320,6,33,struct.pack('<IiiiihhhH',1000,1,1,1,0,0,0,0,0))]:
   t.event('PASSIVE_FRAME',passive(at,s,i,p),{'sequence':s+2,'sha256':str(s)*64})
   if at==250:t.event('NATIVE_RX',{'hostNs':260,'rawHex':cmd.hex()},{'sequence':5,'sha256':'5'*64})
  assert t.end==320 and t.start==110 and len(t.auto_ingresses)==2;checks.append('CRC-original-command-ingress-bounds-start-and-complete-landed-disarmed-group-bounds-end')
  short={k:C[k]for k in('run','epoch','boot','operator','generation')};rows=[];head=''
  for n,(kind,data)in enumerate([('ROOT_WIRE_SESSION',{'context':{'context':short}}),('TX_INTENT',{'id':76,'fields':{'command':176,'param2':3},'rawHex':cmd.hex()}),('AUTO_OBSERVED',{'mode':3}),('TX_INTENT',{'id':76,'fields':{'command':176,'param2':3},'rawHex':cmd.hex()}),('LINK_CLOSE',{'failure':None,'completion':{'complete':True}})],1):
   b={'n':n,'previous':head,'hostClockDomain':'NODE_HRTIME_NS','hostNs':str(n),'kind':kind,'data':data};head=hashlib.sha256(enc(b)).hexdigest();rows.append(enc({**b,'sha256':head})+b'\n')
  plain=b''.join(rows);name='flight-'+'a'*36;header=enc({'format':'aeris-lossless-semantic-journal','version':1,'codec':'AJZ01_DEFLATE_RAW_SYNC','segment':1,'firstSequence':1,'previousRowSHA256':'','name':name});z=zlib.compressobj(wbits=-15);compressed=z.compress(plain)+z.flush(zlib.Z_SYNC_FLUSH);end=z.flush(zlib.Z_FINISH);bh='0'*64
  def block(c,p,first,last):
   nonlocal bh
   b=struct.pack('!IIII',len(c),p,first,last)+bytes.fromhex(bh)+c;h=hashlib.sha256(b).digest();bh=h.hex();return b+h
  ajz=b'AJZ01\n'+struct.pack('!I',len(header))+header+block(compressed,len(plain),1,5)+block(end,0,6,5);file='journal/'+name+'-s01.ajz01';(product/file).write_bytes(ajz);mission='d'*64
  review={'run':'wire','boot':C['boot'],'missionSHA256':mission,'accepted':True,'flightClose':{'journal':{'head':head,'records':5,'segments':[{'file':file,'storedBytes':len(ajz),'closed':True}]}}};b={'seq':1,'previousHash':'0'*64,'kind':'BETA_FLIGHT_REVIEW','data':review};(product/'journal/workspace.jsonl').write_bytes(enc({**b,'hash':hashlib.sha256(enc(b)).hexdigest()})+b'\n');prefix={'sequence':100,'sha256':'f'*64};reader=SimpleNamespace(root=LAB/'sessions/wire/raw/transport-journal',seq=100,head='f'*64,witness=SimpleNamespace(prefix=prefix));proof=t.proof(reader,product,mission);assert proof['rootStartNs']=='110'and proof['rootEndNs']=='320';checks.append('exact-original-workspace-and-closed-AJZ-bound-to-same-run-boot-mission')
  deny(lambda:t.proof(reader,product,'e'*64));deny(lambda:t.event('NATIVE_RX',{'hostNs':400,'rawHex':cmd.hex()},{'sequence':101,'sha256':'a'*64}));checks.append('wrong-mission-and-second-AUTO-retry-refused')
  bad=bytearray(cmd);bad[-1]^=1;deny(lambda:FlightIntervalTracker(C).event('NATIVE_RX',{'hostNs':100,'rawHex':bytes(bad).hex()},{}));checks.append('bad-CRC-not-an-interval')
  changed=bytearray(ajz);changed[-1]^=1;(product/file).write_bytes(changed);deny(lambda:t.proof(reader,product,mission));checks.append('tampered-original-closed-AJZ-refused')
  report={'status':'PASS_ORIGINAL_BYTE_INTERVAL_MOCK_NOT_SITL','groups':checks,'actualAndroidAP':False,'scope':'interval only; no independent wholemission PASS'}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/flight-interval-mock.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks))
if __name__=='__main__':main()
