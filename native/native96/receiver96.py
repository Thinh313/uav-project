"""Independent receiver: ZIP/chain/wire/receipt, never sends aircraft commands. Integrity is not flight acceptance."""
from pathlib import Path
import json,hashlib,base64,zipfile,io,sys,os,importlib.util,struct,math,subprocess
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];MAX=40*2**20
def digest(b):return hashlib.sha256(b).hexdigest()
def pairs(xs):
 d={}
 for k,v in xs:
  if k in d:raise ValueError('DUPLICATE_JSON_KEY')
  d[k]=v
 return d
def obj(b):return json.loads(b,object_pairs_hook=pairs)
def verify(data,receiver,nonce):
 assert 0<len(data)<=MAX,'PACKAGE_BOUND'
 with zipfile.ZipFile(io.BytesIO(data))as z:
  infos=z.infolist();names=[i.filename for i in infos];assert len(names)==len(set(names))and set(names) in [set(['manifest.json','raw.jsonl','source-meta.json']),set(['manifest.json','raw.jsonl','source-meta.json','review.json'])],'MEMBERS'
  assert all(i.compress_type==zipfile.ZIP_STORED and not i.flag_bits&1 and i.file_size<=32*2**20 and not i.is_dir() for i in infos)and sum(i.file_size for i in infos)<=MAX,'ZIP_BOUNDS'
  assert z.getinfo('manifest.json').file_size<=16384
  files={n:z.read(n) for n in names};manifest=obj(files['manifest.json']);context=manifest['context']
 assert manifest['format']=='aeris-native96-raw'and manifest['version']==1 and manifest['missionAcceptance']=='NOT_ASSERTED_BY_PACKAGE' and manifest['authorityRestorable']is False and manifest['sourceAuthenticated']is False and manifest['actualImages']==0,'SCOPE'
 assert context['receiver']==receiver and context['nonce']==nonce,'RECEIVER_NONCE_MISMATCH'
 entries={f['name']:f for f in manifest['files']};assert len(entries)==len(manifest['files'])and set(entries)==set(names)-{'manifest.json'},'MANIFEST_MEMBERS'
 for n,e in entries.items():assert type(e['bytes'])is int and len(files[n])==e['bytes']and digest(files[n])==e['sha256'],'MEMBER_SHA'
 raw=files['raw.jsonl'];end=raw.rfind(b'\n')+1;tail=raw[end:];assert len(tail)<=180000
 rows=[];head='';clock=-1;decoded=[]
 for line in raw[:end].splitlines():
  row=obj(line);assert list(row)==['n','previous','elapsedMs','kind','dataBase64','sha256'],'RAW_KEYS'
  body=line.rsplit(b',"sha256":',1)[0]+b'}';assert row['n']==len(rows)+1 and row['previous']==head and digest(body)==row['sha256'],'RAW_CHAIN'
  assert type(row['elapsedMs'])is int and row['elapsedMs']>=clock,'RAW_CLOCK';clock=row['elapsedMs'];head=row['sha256'];payload=base64.b64decode(row['dataBase64'],validate=True);assert len(payload)<=131072 and base64.b64encode(payload).decode()==row['dataBase64'],'RAW_BASE64';rows.append(row);decoded.append((row,payload))
 assert rows and rows[0]['kind']=='META'and decoded[0][1]==files['source-meta.json'],'META_BINDING'
 meta=obj(files['source-meta.json']);run=context['run'];assert meta['ownedLaunchAssertion']['run']==run and meta['sourceId']==context['rawSourceId'],'RUN_SOURCE_BINDING'
 semantic=subprocess.run(['node',str(R/'native/native96/receiver_semantic96.mjs')],input=json.dumps(meta['document']).encode(),capture_output=True,timeout=20);assert semantic.returncode==0,'MODEL_PLAN_COMPILER_MISMATCH'
 closed=rows[-1]['kind']=='CLOSED' and not tail;extent='CLOSED_RAW'if closed else'TORN_TAIL_RETAINED'if tail else'UNTERMINATED_PREFIX'
 assert manifest['raw']=={'extent':extent,'records':len(rows),'head':head,'committedBytes':end,'tailBytes':len(tail)},'PREFIX_DESCRIPTOR'
 oracle=R/'pilot/apstream40/oracle-v2.py';assert digest(oracle.read_bytes())=='0b4dda7c7655fe896bf6f69920465b226bf38d5b46e21aa9f6d87d4daaff698e'
 spec=importlib.util.spec_from_file_location('receiver96_wire',oracle);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 rx=m.MAVLink(None);tx=m.MAVLink(None);rx.robust_parsing=True;tx.robust_parsing=True;incoming=[];outgoing=[];noise=bytearray();intents=[];written=[];events={}
 for row,payload in decoded:
  kind=row['kind']
  if kind in ['TX_INTENT','TX_WRITTEN']:(intents if kind=='TX_INTENT'else written).append((row['n'],payload))
  if kind not in ['RX','TX_INTENT','TX_WRITTEN']:events.setdefault(kind,[]).append((row,obj(payload)))
  if kind not in ['RX','TX_INTENT']:continue
  parser=rx if kind=='RX'else tx
  for f in parser.parse_buffer(payload)or[]:
   if f.get_type()=='BAD_DATA':
    assert kind=='RX';noise.extend(bytes(f.data));continue
   (incoming if kind=='RX'else outgoing).append((row,f))
 assert len(noise)<=1088 and all(v in[9,10,13]or 32<=v<=126 for v in noise),'WIRE_CORRUPTION'
 assert not noise or b'Init ArduCopter V4.7.1 (dbe79216)'in noise,'BANNER'
 assert len(written)<=len(intents) and all(a[0]<b[0]and a[1]==b[1] for a,b in zip(intents,written)),'TX_RECEIPT_PAIR'
 assert all(f.get_srcSystem()==255 and f.get_srcComponent()==190 and f.get_msgId()!=23 and(f.get_msgId()==0 or f.target_system==42 and f.target_component==1)for r,f in outgoing),'TX_TARGET_OR_PARAM_WRITE'
 grant=events.get('EXPLICIT_GRANT',[])
 for row,f in outgoing:
  if f.get_msgId()in[44,73,43,51,47]or f.get_msgId()==76 and f.command in[176,400]:assert any(g['n']<row['n']and 0<=row['elapsedMs']-g['elapsedMs']<=30000 for g,_ in grant),'UNGRANTED_WRITE'
 expected=meta['document']['compiled']['plan']['compiled']['items'];sent=[f for r,f in outgoing if f.get_msgId()==73];f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
 for f in sent:
  assert 0<=f.seq<len(expected);e=expected[f.seq]
  for key in['seq','command','frame','x','y','autocontinue','mission_type']:assert getattr(f,key)==e[key],'COMPILED_ITEM'
  for key in['param1','param2','param3','param4','z']:assert getattr(f,key)==f32(e[key]),'COMPILED_FLOAT'
 selected=[(r,f)for r,f in incoming if f.get_srcSystem()==42 and f.get_srcComponent()==1];reads=[f for r,f in selected if f.get_msgId()==73 and f.target_system==255 and f.target_component==190]
 outcome='UNKNOWN_PREFIX';review=obj(files['review.json'])if'review.json'in files else None
 if review:
  assert review['run']==run and review['rawHead']==head and review['rawRecords']==len(rows) and review['planSha256']==meta['document']['compiled']['plan']['sha256']and review['authorityRestorable']is False and review['actualImages']==0,'REVIEW_BINDING'
  if review['accepted']:
   assert closed and not tail and len(intents)==len(written)and not rx.buf_len()and not tx.buf_len(),'COMPLETE_RAW_REQUIRED'
   assert events['CLOSED'][-1][1]['safeComplete']is True and review['execution']['complete']is True and not review['aborted'],'RAW_CLOSED_COMPLETION'
   assert len(sent)==len(expected)and len(reads)==2*len(expected)and len(events.get('POST_ARM_READBACK',[]))==1,'READBACK_CYCLES'
   for cycle in[reads[:len(expected)],reads[len(expected):]]:
    for f,e in zip(cycle,expected):
     assert f.seq==e['seq']and f.command==e['command'],'READBACK_COMMAND'
     if f.seq>0:
      assert f.x==e['x']and f.y==e['y'],'READBACK_POSITION'
      for key in['param1','param2','param3','param4','z']:assert abs(getattr(f,key)-f32(e[key]))<1e-5,'READBACK_VALUES'
   auto=next(r for r,f in outgoing if f.get_msgId()==76 and f.command==176 and f.param2==3);after=[(r,f)for r,f in selected if r['n']>auto['n']];reached={f.seq for r,f in after if f.get_msgId()==46};assert all(e['seq']in reached for e in expected if e['seq']>0 and e['command']==16),'NAV_INCOMPLETE'
   assert any(f.get_msgId()in[42,46]and f.seq==len(expected)-1 for r,f in after)and expected[-1]['command']==20,'TERMINAL_RTL'
   hb=next((r,f)for r,f in reversed(after)if f.get_msgId()==0);land=next((r,f)for r,f in reversed(after)if f.get_msgId()==245);pos=next((r,f)for r,f in reversed(after)if f.get_msgId()==33)
   assert not hb[1].base_mode&128 and land[1].landed_state==1 and abs(pos[1].relative_alt)<1000 and abs(hb[0]['elapsedMs']-land[0]['elapsedMs'])<1800,'GROUND_DISARM'
   hr=events['POST_ARM_HOME_REVIEW_REQUIRED'][-1][1];home=hr['postArmHome'];near=lambda p:math.hypot((p.lat/1e7-home['lat'])*111319,(p.lon/1e7-home['lon'])*111319*math.cos(home['lat']*math.pi/180));assert near(pos[1])<5
   witness=events['TAKEOFF_GEOMETRY_OBSERVED'][-1][1];assert witness==review['execution']['takeoffWitness'];boots={f.time_boot_ms:f for r,f in after if f.get_msgId()==33}
   for name in['first','last']:
    p=boots[witness[name]['bootMs']];assert near(p)<=3 and abs(p.relative_alt/1000-next(e['z']for e in expected if e['command']==22))<=1
   assert witness['last']['at']-witness['first']['at']>=300,'TAKEOFF_WITNESS'
   outcome='SIM_COMPLETED_RAW_REPLAY_NOT_HARDWARE'
  else:
   assert review['aborted']is True and review['execution']['complete']is False,'INTERRUPTED_NOT_COMPLETE'
   outcome='INTERRUPTED_UNKNOWN_AIRCRAFT_STATE'
 return {'format':'aeris-native96-receiver-receipt','version':1,'integrity':'PASS','packageSha256':digest(data),'manifestSha256':digest(files['manifest.json']),'receiver':receiver,'nonce':nonce,'run':run,'extent':extent,'rawRecords':len(rows),'rawHead':head,'tailBytes':len(tail),'txIntentCount':len(intents),'txWrittenCount':len(written),'missionOutcome':outcome,'missionItemsSent':len(sent),'readbackItems':len(reads),'sourceAuthenticated':False,'authorityRestorable':False,'actualImages':0,'partialWireRXBytes':rx.buf_len(),'partialWireTXBytes':tx.buf_len(),'clock':'ANDROID_ELAPSED_REALTIME_MS_ONLY'}
def receive(path,root,receiver,nonce):
 source=Path(path);assert source.is_file()and not source.is_symlink()and 0<source.stat().st_size<=MAX,'INPUT_FILE_BOUND';data=source.read_bytes();receipt=verify(data,receiver,nonce);root=Path(root);root.mkdir(parents=True,exist_ok=True);assert not root.is_symlink();identifier=receipt['packageSha256'];target=root/(identifier+'.json');pending=root/(identifier+'.pending');assert not target.exists()and not pending.exists(),'REPLAY_OR_PENDING_RECEIPT'
 # Nonce must not be reused with a different package for this receiver.
 assert len(list(root.iterdir()))<64,'RECEIVER_LEDGER_QUOTA_NO_DELETE'
 for p in root.iterdir():
  assert p.is_file()and not p.is_symlink()and p.suffix in['.json','.pending'],'RECEIVER_FOREIGN_ENTRY'
  prior=obj(p.read_bytes());assert (prior['receiver'],prior['nonce'])!=(receiver,nonce),'NONCE_REPLAY'
 encoded=(json.dumps(receipt,sort_keys=True,separators=(',',':'))+'\n').encode()
 with pending.open('xb')as f:f.write(encoded);f.flush();os.fsync(f.fileno())
 # Link publishes exclusively; a crash retaining both names is fail-closed on restart.
 os.link(pending,target);pending.unlink();fd=os.open(root,os.O_RDONLY);os.fsync(fd);os.close(fd);return receipt
if __name__=='__main__':
 try:print(json.dumps(receive(*sys.argv[1:5])))
 except Exception as e:print(json.dumps({'status':'REJECTED','reason':str(e)}));sys.exit(1)
