from android_qa import *
owned();adb('root');time.sleep(.6);assert b'uid=0'in adb('shell','id');before={}
for v in range(90,98):
 pkg='vn.rtr.aeris.native'+str(v);b=adb('exec-out','tar','-C','/data/user/0/'+pkg+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(b))as t:before[pkg]={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest()for m in t.getmembers()if m.isfile()}
(E/'old-private-before.json').open('x').write(json.dumps(before,indent=2));print({p:len(f)for p,f in before.items()},flush=True)
