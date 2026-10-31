"""Adversarial read-only recovery and snapshot ownership tests; small fixtures."""
from pathlib import Path
import sys,shutil,json,hashlib,struct,gzip,zlib,threading,time
from wal_journal import Journal,read_wal,HEADER,MAGIC,KINDS,unpack_intent,encode
from recovery import recover,public
R=Path(__file__).resolve().parents[2];E=R/'evidence/sim32-journal04';root=E/'negative-fixtures-final';root.mkdir();source=E/'cases/healthy08';checks=[]
def fixture(name):
 p=root/name;p.mkdir()
 for file in ['frames.wal','physics-raw.jsonl.gz']:shutil.copyfile(source/file,p/file)
 return p
def test(name,p):
 before={f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in p.iterdir()if f.is_file()};r=recover(p);after={f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in p.iterdir()if f.is_file()};assert before==after and not r['completeAcceptedCapture'];checks.append({'name':name,'pass':True,'recovery':public(r),'readOnlyHashesUnchanged':True})
p=fixture('torn-final');p.joinpath('frames.wal').write_bytes(p.joinpath('frames.wal').read_bytes()[:-13]);test('torn-close-never-complete',p)
p=fixture('corrupt-intent');b=bytearray((p/'frames.wal').read_bytes());records=read_wal(p/'frames.wal')['records'];offset=8
for r in records:
 if r['kind']=='INTENT':b[offset+HEADER.size+20]^=1;break
 offset+=HEADER.size+len(r['payload'])+36
(p/'frames.wal').write_bytes(b);test('CRC-or-chain-break-never-complete',p)
p=fixture('semantic-forged-sent');chain=bytes(32);buf=bytearray(MAGIC)
for r in records:
 payload=r['payload']
 if r['kind']=='SENT'and r['frame']==3:
  d=json.loads(payload);d['returnedBytes']+=1;payload=encode(d)
 head=HEADER.pack(KINDS[r['kind']],0,0,r['frame'],len(payload),r['seq'],r['ns']);chain=hashlib.sha256(chain+head+payload).digest();buf+=head+payload+struct.pack('<I',zlib.crc32(head+payload))+chain
(p/'frames.wal').write_bytes(buf);test('valid-chain-does-not-bypass-send-semantic-check',p)
p=fixture('archive-truncated');(p/'physics-raw.jsonl.gz').write_bytes((p/'physics-raw.jsonl.gz').read_bytes()[:-15]);test('truncated-gzip-trailer-never-complete',p)
p=fixture('archive-false-row');rows=[json.loads(x)for x in gzip.open(p/'physics-raw.jsonl.gz','rb')];rows[3]['sensorUtf8']='\n{}\n'
with gzip.open(p/'physics-raw.jsonl.gz','wb')as f:
 for row in rows:f.write(encode(row)+b'\n')
test('well-formed-gzip-different-sensor-never-complete',p)
p=fixture('duplicate-archive');raw=gzip.open(p/'physics-raw.jsonl.gz','rb').read();first=raw.splitlines(keepends=True)[0]
with gzip.open(p/'physics-raw.jsonl.gz','wb')as f:f.write(raw+first)
test('duplicate-archive-frame-never-complete',p)
# Prove caller mutation cannot change queued row/snapshot after intent binding.
p=root/'immutable-owner';p.mkdir();state=p/'state';state.mkdir();blocked=threading.Event();release=threading.Event()
def hook(stage,*args):
 if stage=='archive-before-write':blocked.set();assert release.wait(2)
j=Journal(p,state,{'run':'unit','epoch':'unit'},policy='process-crash-only',hook=hook)
j.receive(0,struct.pack('<HHI16H',18458,1200,0,*([1000]*16)),['127.0.0.1',1]);j.reserve(0)
row={'frame':0,'rate':1200,'servoHex':struct.pack('<HHI16H',18458,1200,0,*([1000]*16)).hex(),'epoch':'unit','source':'MOCK_REFERENCE_PHYSICS_NOT_SITL','clockDomain':'mock-backend-python-monotonic','rxSeq':1,'sensorUtf8':'\n{"timestamp":0.0}\n'};snapshot={'epoch':'unit','frame':0,'marker':'original'}
prepared=j.prepare(row,snapshot);j.transmitted(prepared,len(row['sensorUtf8']),len(row['sensorUtf8']));assert blocked.wait(1);row['sensorUtf8']='MUTATED';snapshot['marker']='MUTATED';release.set();result=j.seal();assert result['status']=='COMPLETE_ACCEPTED_MOCK_CAPTURE';stored=json.loads(gzip.open(p/'physics-raw.jsonl.gz','rb').read());assert stored['sensorUtf8']=='\n{"timestamp":0.0}\n'and json.loads((state/'physics.json').read_bytes())['marker']=='original';checks.append({'name':'prepared-row-and-snapshot-immutable-under-caller-mutation','pass':True})
# Worker failure can race recv; retain RX in available WAL before rejecting admission.
p=root/'worker-failed-rx';p.mkdir();state=p/'state';state.mkdir();j=Journal(p,state,{'run':'unit','epoch':'unit'},policy='process-crash-only');j.fail('Injected worker failure while waiting for RX');packet=struct.pack('<HHI16H',18458,1200,0,*([1000]*16));seq=j.receive(0,packet,['127.0.0.1',1]);refused=False
try:j.reserve(0)
except RuntimeError:refused=True
result=j.seal();parsed=read_wal(p/'frames.wal');assert refused and result['status']=='INCOMPLETE_CAPTURE'and any(r['kind']=='RX'and json.loads(r['payload'])['rawHex']==packet.hex()for r in parsed['records']);checks.append({'name':'worker-failed-during-recv-retains-input-before-admission-refusal','pass':True})
with(E/'negative-tests-final.json').open('x')as f:json.dump({'status':'PASS','checks':checks,'fixtureCopies':'Small individual test files only; no project copy','scope':'Mock/offline, not power loss'},f,indent=2);f.write('\n')
print('RECOVERY_NEGATIVE_PASS',len(checks))
