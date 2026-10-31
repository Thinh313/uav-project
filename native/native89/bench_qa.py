from android_qa import *
import base64

def decode(raw):
 assert raw.endswith(b'\n'),'TORN_TRACE';previous='';last=-1;out=[]
 for i,line in enumerate(raw.splitlines(),1):
  v=json.loads(line);assert set(v)=={'n','elapsedMs','previous','payloadBase64','sha256'};body={k:v[k]for k in ['n','elapsedMs','previous','payloadBase64']};assert type(v['n'])is int and v['n']==i and type(v['elapsedMs'])is int and v['elapsedMs']>=last and v['previous']==previous
  h=hashlib.sha256(json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();assert h==v['sha256'],'SHA_CHAIN';payload=json.loads(base64.b64decode(v['payloadBase64'],validate=True));out.append({'n':i,'elapsedMs':v['elapsedMs'],'data':payload});previous=h;last=v['elapsedMs']
 return out

def traces(name):
 owned();assert b'uid=0'in adb('shell','id');raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','bench89');(E/(name+'.tar')).open('xb').write(raw)
 with tarfile.open(fileobj=io.BytesIO(raw))as t:
  files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()};assert all(not m.issym()for m in t.getmembers())
 result={'files':{n:hashlib.sha256(b).hexdigest()for n,b in files.items()},'traces':{n:decode(b)for n,b in files.items()if n.endswith('.jsonl')}}
 (E/(name+'.json')).open('x').write(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'traces':{n:len(a)for n,a in result['traces'].items()}}));return result
