from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
R=Path(__file__).resolve().parents[4];out=R/'evidence/betaintegrated01-m1control02/qa/nominal01';out.mkdir();classes=R/'native/betaintegrated01/.build/qa-control02';classes.mkdir()
core=R/'native/betaintegrated01/control01/src/vn/rtr/aeris/control01';base=R/'native/betaintegrated01/runtime/src/vn/rtr/aeris';oldqa=R/'planning/betaintegrated01/m1control01/qa';foundation=R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01'
src=[core/n for n in ('ControlAuthority.java','ControlSession.java','RcWire.java')]+[R/'native/betaintegrated01/control02/src/vn/rtr/aeris/control01/ControlFlight.java']+[base/'beta01runtime'/n for n in ('Values.java','Mavlink.java','NativeSegments.java')]+[base/'native98'/n for n in ('Dialect95.java','Json.java')]+[foundation/n for n in ('RunLifecycle.java','ProviderDescriptor.java')]+[oldqa/n for n in ('ProfileFixture.java','SessionQA.java')]+[Path(__file__).with_name('NominalReleaseQA.java')]
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in src};before=pins();jdk=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');logs=[];results=[]
try:
 c=subprocess.run([str(jdk/'javac'),'--release','8','-d',str(classes),*map(str,src)],capture_output=True,text=True,timeout=60);logs.append({'kind':'javac','exit':c.returncode,'stdout':c.stdout,'stderr':c.stderr})
 if c.returncode==0:
  c=subprocess.run([str(jdk/'java'),'-cp',str(classes),'NominalReleaseQA',str(out/'fixtures')],capture_output=True,text=True,timeout=60);logs.append({'kind':'java','exit':c.returncode,'stdout':c.stdout,'stderr':c.stderr});results=json.loads(c.stdout)['results']if c.returncode==0 else[]
finally:shutil.rmtree(classes)
r={'status':'PASS'if results and all(x['pass']for x in results)and before==pins()else'FAIL','sourceBefore':before,'sourceAfter':pins(),'results':results,'commands':logs,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'APAndroidServicesStarts':0,'classScratchRemoved':not classes.exists(),'scope':'ActualcurrentAPK02core+realjournalfsync, syntheticAP/mockedSocket; noAndroidUI/flightattestation'}
(out/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'failed':[x for x in results if not x['pass']]}))
