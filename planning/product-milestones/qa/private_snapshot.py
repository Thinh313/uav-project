from android_qa import *
import sys
owned();tag=sys.argv[1];assert tag in ['before','after'];assert b'uid=0'in adb('shell','id');snap={}
for v in range(90,99):
 pkg='vn.rtr.aeris.native'+str(v);b=adb('exec-out','tar','-C','/data/user/0/'+pkg+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(b))as t:snap[pkg]={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest()for m in t.getmembers()if m.isfile()}
out={'packages':snap,'files':sum(len(x)for x in snap.values()),'status':'SNAPSHOT'}
if tag=='after':assert snap==json.loads((E/'old-private-before.json').read_text())['packages'],'OLD_PRIVATE_DRIFT';out['status']='PASS'
(E/('old-private-'+tag+'.json')).open('x').write(json.dumps(out,indent=2));print(json.dumps({'status':out['status'],'files':out['files']}))
