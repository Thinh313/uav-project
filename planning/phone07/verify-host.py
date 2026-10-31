"""Reproduce bounded host checks. No build, emulator, SITL, network or protected writes."""
from pathlib import Path
import os,sys,json,subprocess,shutil,hashlib,datetime,tarfile
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];N=R/'native/phone07';E=R/'evidence/phone07';W=N/'.check';attempt=sys.argv[1]
assert attempt in ['01','02','03'] and not W.exists(),'Fresh owned stage / finite attempt required'
assert shutil.disk_usage(R).free>=20*2**30+128*2**20,'20 GiB floor + small host budget'
sys.path.insert(0,str(N));from assemble import stage,source
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');logs=[]
def run(args,**env):
 assert shutil.disk_usage(R).free>=20*2**30+64*2**20,'Floor during host checks'
 p=subprocess.run(list(map(str,args)),cwd=R,env={**os.environ,**env},text=True,capture_output=True,timeout=90)
 logs.append({'command':list(map(str,args)),'exit':p.returncode,'stdout':p.stdout[-60000:],'stderr':p.stderr[-20000:]})
 assert p.returncode==0,logs[-1]
 return p.stdout
try:
 W.mkdir();files=stage(W);freeze=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
 rows=['DraftStore.java','Json.java','Data97.java','PayloadFiles07.java']
 run([J/'javac','-d',W/'jvm',*[W/'src'/x for x in rows],N/'qa/Fixture07.java',N/'qa/Files07Test.java'])
 run([J/'java','-cp',W/'jvm','vn.rtr.aeris.phone07.Files07Test',E/('files-final'+attempt)])
 # Port the existing 22 grouped policy cases, keep its original host Store as a
 # policy test double. Native persistence is tested separately above/below.
 s=(R/'planning/payload-gateway01/test.mjs').read_text()
 s=s.replace("'../../payload/gateway01/core.mjs'","'./assets/gateway/core.mjs'").replace("'../../payload/gateway01/store.mjs'","'../../../payload/gateway01/store.mjs'").replace("'../../media/big02/geotag-fixtures.mjs'","'../../../media/big02/geotag-fixtures.mjs'").replace("'/evidence/payload-gateway01/mock'","'/evidence/phone07/gateway-final'")
 s=s.replace('const results=[];','Store.prototype.guard=function(){if(this.readOnly)throw Error("JOURNAL_READ_ONLY");};const results=[];')
 (W/'gateway-regression.mjs').write_text(s);run(['node',W/'gateway-regression.mjs',E/('gateway-final'+attempt)])
 # Each file bridge operation is a new JVM process: host persistence/process
 # reopen, not an Android app restart or native JavascriptInterface execution.
 run(['node',N/'qa/journey-test.mjs'],PHONE07_ATTEMPT=attempt,PHONE07_RECEIPT='journey-final'+attempt+'.json',PHONE07_FIXTURE_ROOT='journey-final-workspace'+attempt)
 wire=E/('receiver-final'+attempt);wire.mkdir()
 with tarfile.open(E/('synthetic-package'+attempt+'.tar'))as tar:
  assert sorted(tar.getnames())==['manifest.json','original.jpg','sidecar.json']
  for item in tar.getmembers():
   assert item.isfile()and item.size<=524288
   (wire/item.name).open('xb').write(tar.extractfile(item).read())
 run(['python3','-B',R/'planning/big02/qa-receiver.py','--package-dir',wire,'--receiver-id','rtr-host01-evaluator','--sender-id','aeris-gateway01-mock','--state',E/('receiver-final-state'+attempt+'.json')])
 assert source()==files,'Source changed during verification'
 result={'at':datetime.datetime.now().astimezone().isoformat(),'status':'PASS_HOST_ONLY','sourceId':freeze,'scope':'24 JVM assertions +22 policy groups +13 JS/JVM journey groups + independent receiver; no Android ART/SAF/SITL/hardware','logs':logs}
except Exception as error:
 result={'status':'FAIL_OR_UNKNOWN','error':str(error),'logs':logs};raise
finally:
 (E/('host-verification'+attempt+'.json')).open('x').write(json.dumps(result,indent=2)+'\n')
 shutil.rmtree(W)
print(json.dumps({'status':result['status'],'sourceId':result['sourceId']}))
