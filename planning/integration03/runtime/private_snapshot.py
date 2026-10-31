from android_qa import *
import sys
owned();tag=sys.argv[1];assert tag in ['before','after'];assert b'uid=0'in adb('shell','id');snap={}
for pkg in ['vn.rtr.aeris.native'+str(v) for v in range(90,99)]+['vn.rtr.aeris.operator01','vn.rtr.aeris.crew02']:
 b=adb('exec-out','tar','-C','/data/user/0/'+pkg+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(b))as t:snap[pkg]={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest()for m in t.getmembers()if m.isfile()}
legacy=json.loads((R/'evidence/operator01-runtime/old-private-after.json').read_text())['packages'];assert all(snap[k]==v for k,v in legacy.items()),'PREEXISTING_NATIVE90_98_PRIVATE_DRIFT'
p1=json.loads((R/'evidence/operator01-runtime/restart-coldboot/verification.json').read_text())['keptSHA256'];assert all(snap['vn.rtr.aeris.operator01'].get(k)==v for k,v in p1.items()),'PREEXISTING_P1_RAW_WORKSPACE_DRIFT'
out={'packages':snap,'files':sum(len(x)for x in snap.values()),'status':'SNAPSHOT'}
if tag=='after':assert snap==json.loads((E/'old-private-before.json').read_text())['packages'],'OLD_PRIVATE_DRIFT';out['status']='PASS'
(E/('old-private-'+tag+'.json')).open('x').write(json.dumps(out,indent=2));print(json.dumps({'status':out['status'],'files':out['files']}))
