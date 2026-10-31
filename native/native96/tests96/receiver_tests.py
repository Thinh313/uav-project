from pathlib import Path
import json,sys,zipfile,io,hashlib,base64,subprocess,importlib.util,struct
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];E=R/'evidence/native96';spec=importlib.util.spec_from_file_location('receiver96',R/'native/native96/receiver96.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
D=E/'receiver-mock';D.mkdir();fixture=E/'mock96-02/closed.zip'
with zipfile.ZipFile(fixture)as z:files={n:z.read(n)for n in z.namelist()}
manifest=json.loads(files['manifest.json']);meta=json.loads(files['source-meta.json']);manifest['context']['rawSourceId']=meta['sourceId'];manifest['context']['exporterSourceId']='MOCK_HOST_NO_ANDROID_EXPORT';manifest['context']['nonce']='mock96-unique-nonce';files['review.json']=(R/'evidence/native95/runs/s095f2c41e36548be9071/review.json').read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
def build(fs,man):
 man=json.loads(json.dumps(man));man['files']=[{'name':n,'bytes':len(b),'sha256':sha(b)}for n,b in fs.items()if n!='manifest.json'];out=io.BytesIO()
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_STORED)as z:
  z.writestr('manifest.json',json.dumps(man,separators=(',',':')))
  for n,b in fs.items():
   if n!='manifest.json':z.writestr(n,b)
 return out.getvalue()
data=build(files,manifest);(D/'nominal.zip').write_bytes(data);r=m.receive(D/'nominal.zip',D/'ledger','rtr-evaluator','mock96-unique-nonce');assert r['missionOutcome']=='SIM_COMPLETED_RAW_REPLAY_NOT_HARDWARE';checks=['nominal independent full semantic raw replay'];bad=[]
def reject(name,fn):
 try:fn();raise RuntimeError('NO_REJECTION:'+name)
 except Exception as e:
  assert not str(e).startswith('NO_REJECTION'),str(e);bad.append({'name':name,'reason':str(e),'pass':True})
reject('replay after receiver process restart',lambda:subprocess.run([sys.executable,str(R/'native/native96/receiver96.py'),str(D/'nominal.zip'),str(D/'ledger'),'rtr-evaluator','mock96-unique-nonce'],capture_output=True,check=True))
reject('wrong receiver',lambda:m.verify(data,'wrong-receiver','mock96-unique-nonce'))
reject('wrong nonce',lambda:m.verify(data,'rtr-evaluator','wrong96-unique-nonce'))
changed=data[:len(data)//2]+bytes([data[len(data)//2]^1])+data[len(data)//2+1:];reject('ZIP corruption',lambda:m.verify(changed,'rtr-evaluator','mock96-unique-nonce'))
f=dict(files);f['raw.jsonl']=f['raw.jsonl'].replace(b'"n":2,',b'"n":7,',1);reject('rehashed package cannot hide raw-chain corruption',lambda:m.verify(build(f,manifest),'rtr-evaluator','mock96-unique-nonce'))
f=dict(files);f['../escape']=b'no';reject('path traversal member',lambda:m.verify(build(f,manifest),'rtr-evaluator','mock96-unique-nonce'))
rows=[json.loads(l)for l in files['raw.jsonl'].splitlines()];camera=None
for row in rows:
 if row['kind']=='TX_INTENT':
  b=base64.b64decode(row['dataBase64'])
  if b[0]==253 and int.from_bytes(b[7:10],'little')==73 and int.from_bytes(b[40:42],'little')==206 and struct.unpack('<f',b[10:14])[0]>0:camera=b;break
assert camera
# Change a camera trigger distance and correctly recompute MAV CRC, both native TX records and full journal chain.
wire_spec=importlib.util.spec_from_file_location('wire96',R/'pilot/apstream40/oracle-v2.py');w=importlib.util.module_from_spec(wire_spec);wire_spec.loader.exec_module(w);parser=w.MAVLink(None);frame=parser.parse_char(camera);changed=bytearray(camera);struct.pack_into('<f',changed,10,0.0);c=w.x25crc(changed[1:-2]);c.accumulate(bytes([frame.crc_extra]));changed[-2:]=struct.pack('<H',c.crc);head='';encoded=[]
for row in rows:
 if row['kind']in['TX_INTENT','TX_WRITTEN']and base64.b64decode(row['dataBase64'])==camera:row['dataBase64']=base64.b64encode(changed).decode()
 row['previous']=head;row.pop('sha256');body=json.dumps(row,separators=(',',':'));head=sha(body.encode());row['sha256']=head;encoded.append((body[:-1]+',"sha256":"'+head+'"}\n').encode())
f=dict(files);f['raw.jsonl']=b''.join(encoded);rr=json.loads(f['review.json']);rr['rawHead']=head;f['review.json']=json.dumps(rr).encode();man=json.loads(json.dumps(manifest));man['raw']['head']=head;man['raw']['committedBytes']=len(f['raw.jsonl']);reject('CRC-valid rehashed camera corruption',lambda:m.verify(build(f,man),'rtr-evaluator','mock96-unique-nonce'))
# A source torn tail is retained and receipted as UNKNOWN, never as completion.
f={k:v for k,v in files.items()if k!='review.json'};f['raw.jsonl']=f['raw.jsonl']+b'{"n":';man=json.loads(json.dumps(manifest));man['raw']['extent']='TORN_TAIL_RETAINED';man['raw']['tailBytes']=5;r=m.verify(build(f,man),'rtr-evaluator','mock96-unique-nonce');assert r['tailBytes']==5 and r['missionOutcome']=='UNKNOWN_PREFIX';checks.append('torn source bytes retained as unknown')
f=dict(files);raw=f['raw.jsonl'];last=raw.rfind(b'\n',0,-1)+1;f['raw.jsonl']=raw[:last];endrow=json.loads(f['raw.jsonl'].splitlines()[-1]);rr=json.loads(f['review.json']);rr['rawHead']=endrow['sha256'];rr['rawRecords']-=1;f['review.json']=json.dumps(rr).encode();man=json.loads(json.dumps(manifest));man['raw'].update(extent='UNTERMINATED_PREFIX',records=rr['rawRecords'],head=rr['rawHead'],committedBytes=len(f['raw.jsonl']));reject('prefix cannot claim completed mission',lambda:m.verify(build(f,man),'rtr-evaluator','mock96-unique-nonce'))
result={'status':'PASS','positive':checks,'negative':bad,'checks':len(checks)+len(bad),'scope':'HOST_RECEIVER_WITH_FROZEN95_FIXTURE_NOT_NEW_ANDROID_SAF_EVIDENCE'};(E/'receiver-tests96.json').open('x').write(json.dumps(result,indent=2));print(result['checks'])
