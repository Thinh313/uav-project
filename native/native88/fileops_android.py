from android_qa import *
import base64

def fileops(name,root="fileops87"):
 assert root in ["fileops87","bundleops88"]
 owned();assert b'uid=0'in adb('shell','id');raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-',root);(E/(name+'.tar')).open('xb').write(raw)
 with tarfile.open(fileobj=io.BytesIO(raw))as t:files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
 out={'files':{n:hashlib.sha256(b).hexdigest()for n,b in files.items()},'operations':[]}
 for path,b in files.items():
  if not path.endswith('/HEAD'):continue
  parent=path[:-5];head=b.decode().strip();rows={}
  for n,body in files.items():
   if str(Path(n).parent)!=parent or not n.endswith('.bin'):continue
   h=body.split(b'\n',6);token=hashlib.sha256(body).hexdigest();assert n.endswith(token+'.bin')and h[0]==b'AERISWORKSPACE33'and len(h[6])==int(h[4])and hashlib.sha256(h[6]).hexdigest()==h[3].decode();v=h[6].decode().splitlines();assert v[0]=='AERISFILEOP87'and len(v)==10;fields=[base64.b64decode(x).decode()for x in v[1:]];rows[token]={'revision':int(h[1]),'previous':h[2].decode(),'op':dict(zip(['id','kind','workspace','head','phase','sha','staged','artifactHead','reason'],fields))}
  at=head;seen=set()
  while at!='ROOT':assert at in rows and at not in seen;seen.add(at);at=rows[at]['previous']
  out['operations'].append({**rows[head]['op'],'journalHead':head,'records':len(rows),'chainCount':len(seen)})
 (E/(name+'.json')).open('x').write(json.dumps(out,indent=2));print(json.dumps({'operations':[{k:o[k]for k in['id','kind','phase','records']}for o in out['operations']]}));return out
