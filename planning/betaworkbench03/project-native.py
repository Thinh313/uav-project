from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[2];assert shutil.disk_usage(R).free>=20*2**30+256*2**20
pins=json.loads((R/'evidence/workbench02/handoff-java01.json').read_text())['inventory'];rows={}
def load(n):
 b=(R/n).read_bytes();assert hashlib.sha256(b).hexdigest()==pins[n]['sha256'];return b.decode()
def replace(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
out=R/'native/betaworkbench03/src/vn/rtr/aeris/betaworkbench03';out.mkdir(parents=True,exist_ok=False)
for name in ['WorkspaceStore.java','ShellActivity.java']:
 path='native/workbench02/src/vn/rtr/aeris/workbench02/'+name;original=load(path);s=original;changes=[]
 def edit(a,b):
  global s
  s=replace(s,a,b);changes.append([a,b])
 edit('package vn.rtr.aeris.workbench02;','package vn.rtr.aeris.betaworkbench03;')
 if name=='ShellActivity.java':
  edit('http://127.0.0.1:8892','http://127.0.0.1:8894')
  edit('private boolean busy=false,pickerOwned=false;','private boolean pickerOwned=false;private final OperationGate gate=new OperationGate();')
  edit('if(busy)throw new IOException("NATIVE_BUSY_NO_QUEUE");','if(gate.busy())throw new IOException("NATIVE_BUSY_NO_QUEUE");')
  edit('busy=true;lastSequence=seq;','gate.begin(q.getString("session")+":"+requestId);lastSequence=seq;')
  edit('if(release)busy=false;','if(release&&q!=null)gate.finish(q.optString("session")+":"+q.optString("id"));')
  mark='@Override protected void onActivityResult';prefix,tail=s.split(mark);assert tail.count('catch(Exception e){deliver(q,null,e,false);}')==1
  oldtail=tail;tail=tail.replace('catch(Exception e){deliver(q,null,e,false);}','catch(Exception e){reply(q,null,e);}')
  edit(mark+oldtail,mark+tail)
  edit('if(origin(r.getUrl().toString()))return null;','if(origin(r.getUrl().toString())||mediaOrigin(r.getUrl().toString()))return null;')
  edit('private void directorySync(File dir)', 'private static boolean mediaOrigin(String url){try{URI u=new URI(url);return "http".equals(u.getScheme())&&"127.0.0.1".equals(u.getHost())&&u.getPort()==8893&&u.getUserInfo()==null;}catch(Exception e){return false;}}\n private void directorySync(File dir)')
 inverse=s
 for a,b in reversed(changes):inverse=replace(inverse,b,a)
 assert inverse==original
 p=out/name;p.open('x').write(s);rows[path]={'originalSha256':hashlib.sha256(original.encode()).hexdigest(),'projectedPath':str(p.relative_to(R)),'projectedSha256':hashlib.sha256(s.encode()).hexdigest(),'exactReplacements':len(changes),'inverseExact':True}
m=load('native/workbench02/AndroidManifest.xml');m=replace(m,'vn.rtr.aeris.workbench02','vn.rtr.aeris.betaworkbench03');(R/'native/betaworkbench03/AndroidManifest.xml').open('x').write(m)
(R/'evidence/betaworkbench03/native-projection01.json').open('x').write(json.dumps({'status':'PROJECTED_SOURCE_NOT_APK','rows':rows,'safErrorCompletionReleasesOnlyOwner':True,'navigationOrigin':'http://127.0.0.1:8894','mediaSubresourceOrigin':'http://127.0.0.1:8893'},indent=2)+'\n');print(json.dumps(rows))
