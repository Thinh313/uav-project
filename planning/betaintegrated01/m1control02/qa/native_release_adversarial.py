from pathlib import Path
import base64,copy,hashlib,importlib.util,io,json,struct,sys,tarfile,datetime
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));O=R/'evidence/betaintegrated01-m1control02/qa/release01';O.mkdir()
from pilot.betaintegrated01.control04.confirmation import create_confirmation_descriptor
from pilot.betaintegrated01.control01.mavlink import DEFINITIONS
s=importlib.util.spec_from_file_location('old_release',Path(__file__).with_name('native_release_pre01.py'));old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
BASE=R/'evidence/betaintegrated01-m1control02/qa/nominal01/fixtures/nominal';table={p.name:p.read_bytes()for p in BASE.iterdir()if p.is_file()};prefix='files/control-runs/nominal/';context=dict(run='nominal',epoch='epoch01',boot='boot01',generation='generation01',operator='operator01',profileId='qa-profile',binarySHA256='1'*64,configSHA256='3'*64)
def enc(v):return json.dumps(v,separators=(',',':'),ensure_ascii=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def body(r):return base64.b64decode(r['base64'])
def msg(w):return int.from_bytes(w[7:10],'little')
def packet_mode(w):return int(struct.unpack_from('<f',w,14)[0])if msg(w)==76 else None
flat=[json.loads(x)for p in sorted(BASE.glob('*.jsonl'))for x in p.read_bytes().splitlines()]
confirmation=next(json.loads(body(r))for r in flat if r['kind']=='POST_ARM_HOME_EXPLICITLY_CONFIRMED')
bracket=dict(beforeActionHostNs=1_100_000_000,afterObservedConfirmedHostNs=1_300_000_000,run='nominal',epoch='epoch01',boot='boot01',generation='generation01',displayedHomeHash=confirmation['displayedHomeHash'])
written=[body(r)for r in flat if r['kind']=='TX_WRITTEN'];brake=next(w for w in written if packet_mode(w)==17);land=next(w for w in written if packet_mode(w)==9);rc=[w for w in written if msg(w)==70];forward=next(w for w in rc if struct.unpack_from('<H',w,12)[0]<1480);neutral=next(w for w in rc if struct.unpack_from('<4H',w,10)==(1500,)*4);release=next(w for w in rc if struct.unpack_from('<8H',w,10)==(0,)*8)
def row(t,k,w,**kw):return dict(hostNs=int(t*1e9),kind=k,wireSHA256=sha(w),**kw)
wire={'nativeForwardedTimeline':[row(4.9,'RC_OVERRIDE',forward,channels=[1500,1450,1500,1500]+[65535]*14,forwardPitchHeld=True),row(5,'COMMAND_LONG',brake,command=176,params=[1,17,0,0,0,0,0]),row(5.101,'RC_OVERRIDE',neutral,channels=[1500]*4+[65535]*14,forwardPitchHeld=False),row(5.111,'RC_OVERRIDE',release,channels=[0]*8+[65534]*10,forwardPitchHeld=False),row(5.6,'COMMAND_LONG',land,command=176,params=[1,9,0,0,0,0,0])],'passiveTimeline':[dict(hostNs=5_400_000_000,kind='heartbeat',armed=True,mode=17)]}
def is17(r):
 w=body(r);return r['kind']=='RX'and w[0]==253 and msg(w)==0 and struct.unpack_from('<I',w,10)[0]==17
def make(label):
 t=dict(table);terminal=json.loads(t['session.json']);rows=[json.loads(x)for p in sorted(BASE.glob('*.jsonl'))for x in p.read_bytes().splitlines()];rx_index=next(i for i,r in enumerate(rows)if is17(r))
 if label=='intent_before_mode17':
  ni=next(i for i,r in enumerate(rows)if r['kind']=='TX_INTENT'and body(r)==neutral);rows[rx_index],rows[ni]=rows[ni],rows[rx_index]
 if label=='newer_mode9_before_cleanup':
  r=rows[rx_index];w=bytearray(body(r));w[4]=(w[4]+1)&255;struct.pack_into('<I',w,10,9);crc=65535
  for b in bytes(w[1:-2])+bytes([DEFINITIONS[0][2]]):
   crc^=b
   for _ in range(8):crc=(crc>>1)^0x8408 if crc&1 else crc>>1
  struct.pack_into('<H',w,len(w)-2,crc);raw=body(r)+bytes(w);r['base64']=base64.b64encode(raw).decode()
  receipt=rows[rx_index+1];assert receipt['kind']=='AP_RX_RECEIPT';v=json.loads(body(receipt));v['wireSHA256']=sha(raw);receipt['base64']=base64.b64encode(enc(v)).decode()
 previous='';previous_seal='';ordinal=0;cursor=0;confsha=None
 for seg in range(terminal['segments']):
  name=f'segment-{seg:06}.jsonl';size=len(table[name].splitlines());group=rows[cursor:cursor+size];cursor+=size;first=ordinal+1;lines=[]
  for r in group:
   ordinal+=1;r['n']=ordinal;r['segment']=seg;r['previous']=previous
   if r['kind']=='HEADER':v=json.loads(body(r));v.update(segment=seg,previousSeal=previous_seal);r['base64']=base64.b64encode(enc(v)).decode()
   r.pop('sha256');previous=sha(enc(r));r['sha256']=previous;lines.append(enc(r)+b'\n')
   if r['kind']=='POST_ARM_HOME_EXPLICITLY_CONFIRMED':confsha=previous
  raw=b''.join(lines);t[name]=raw;sn=f'seal-{seg:06}.json';seal=json.loads(t[sn]);seal.update(bytes=len(raw),sha256=sha(raw),first=first,last=ordinal,head=previous,previousSeal=previous_seal);t[sn]=enc(seal);previous_seal=sha(t[sn])
 terminal.update(head=previous,lastSeal=previous_seal);t['session.json']=enc(terminal);path=O/(label+'.tar')
 with tarfile.open(path,'w')as archive:
  for name,raw in t.items():info=tarfile.TarInfo(prefix+name);info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
 d,anchor=create_confirmation_descriptor(str(path.resolve()),prefix,sha(t['session.json']),bracket,context);assert d['confirmationRecordSHA256']==confsha
 return d,anchor
cases=[]
for label in ('baseline','intent_before_mode17','newer_mode9_before_cleanup'):
 try:
  d,a=make(label);out=old.release_witness(d,a,'nominal','epoch01','boot01',wire);cases.append({'id':label,'result':out,'descriptor':d,'descriptorAnchor':a})
 except Exception as e:cases.append({'id':label,'error':repr(e)})
r={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'OLD_PROOF_GAPS_REPRODUCED'if all(c.get('result',{}).get('status')=='HOST_NATIVE_RELEASE_WITNESS_PASS'for c in cases)else'REVIEW_FIXTURE','cases':cases,'wire':wire,'scope':'Integrity-valid assistantauthorednominalnativejournals; exactoldhelper snapshot. No oldrawedits/services. Invalidfixtures mustreject in repaired witness.'};(O/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'cases':[{k:v for k,v in c.items()if k in('id','error')}for c in cases]}))
