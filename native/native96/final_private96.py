from android_qa import *
import base64
owned();b=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.');(E/'final-private96.tar').open('xb').write(b)
with tarfile.open(fileobj=io.BytesIO(b))as t:files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
sha=lambda b:hashlib.sha256(b).hexdigest();chains={};ops=[]
for n,raw in files.items():
 if not n.endswith('/HEAD'):continue
 parent=n[:-5];head=raw.decode().strip();records={}
 for k,v in files.items():
  if str(Path(k).parent)!=str(Path(parent))or not k.endswith('.bin'):continue
  h=v.split(b'\n',6);token=sha(v);assert k.endswith(token+'.bin')and h[0]==b'AERISWORKSPACE33'and h[5]==b'1'and len(h[6])==int(h[4])and sha(h[6])==h[3].decode();records[token]={'revision':int(h[1]),'previous':h[2].decode(),'body':h[6]}
 at=head;seen=set()
 while at!='ROOT':assert at in records and at not in seen;seen.add(at);at=records[at]['previous']
 chains[parent]={'head':head,'records':len(records),'chain':len(seen)}
 if parent.startswith('./raw-fileops96/'):
  history=sorted(records.values(),key=lambda v:v['revision']);values=[[base64.b64decode(l).decode()for l in r['body'].splitlines()[1:]]for r in history];ops.append({'id':values[-1][0],'phase':values[-1][4],'sha256':values[-1][5],'phases':[v[4]for v in values],'reasons':[v[-1]for v in values]})
assert not any(n.endswith('.pending')for n in files)
raws={}
for n,raw in files.items():
 if n.startswith('./direct95/')and n.endswith('/raw.jsonl'):
  run=n.split('/')[2];rows=[json.loads(l)for l in raw.splitlines()];head=''
  for i,r in enumerate(rows):
   body={k:v for k,v in r.items()if k!='sha256'};assert r['n']==i+1 and r['previous']==head and sha(json.dumps(body,separators=(',',':')).encode())==r['sha256'];head=r['sha256']
  prior=E/'runs'/run/'android-raw.jsonl'
  if prior.exists():assert prior.read_bytes()==raw
  assert rows[-1]['kind']=='CLOSED';raws[run]={'sha256':sha(raw),'records':len(rows),'head':head,'bytes':len(raw)}
with tarfile.open(E/'rawsaf-loss05-pending-before-reboot.tar')as oldui:
 olduiFiles={m.name:oldui.extractfile(m).read()for m in oldui.getmembers()if m.isfile()and m.name.startswith('./ui96/')and m.name.endswith('.jsonl')}
assert all(files.get(n)==v for n,v in olduiFiles.items()),'OLD_UI_GENERATION_CHANGED'
ui={n:len(v)for n,v in files.items()if n.startswith('./ui96/')and n.endswith('.jsonl')};assert len(ui)<=16 and all(v<=2**21 for v in ui.values())and sum(ui.values())<=16*2**20
old=json.loads((E/'old-private-before.json').read_text());oldsummary={}
for package,expected in old.items():
 raw=adb('exec-out','tar','-C','/data/user/0/'+package+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(raw))as t:actual={m.name:sha(t.extractfile(m).read())for m in t.getmembers()if m.isfile()}
 assert expected==actual,'OLD_PRIVATE_CHANGED:'+package;oldsummary[package]=len(actual)
assert any(o['phase']=='CANCELLED'for o in ops);assert any('UNKNOWN'in o['phases']and o['phase']=='COMPLETED'for o in ops)
(E/'final-private-verification.json').open('x').write(json.dumps({'status':'PASS','rawGenerations':raws,'workspaceAndOpsChains':chains,'rawSafOperations':ops,'uiGenerationByteSizes':ui,'uiTotalBytes':sum(ui.values()),'oldUiGenerationsUnchanged':len(olduiFiles),'oldPrivateFilesUnchanged':oldsummary,'noPendingStoreHead':True,'noAutomaticDeletion':True},indent=2));print(json.dumps({'raws':len(raws),'chains':len(chains),'ops':len(ops),'oldPrivate':oldsummary,'uiTotalBytes':sum(ui.values())}))
