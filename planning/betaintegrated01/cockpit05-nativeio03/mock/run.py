"""Cached JVM source-order tests only. No APK or Android/OS network."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];Q=Path(__file__).parent;E=R/'evidence/betaintegrated01-cockpit05-nativeio03/native';W=R/'native/betaintegrated01/cockpit05-nativeio03/.build'
core=R/'native/betaintegrated01/control01/src/vn/rtr/aeris/control01';base=R/'native/betaintegrated01/runtime/src/vn/rtr/aeris';foundation=R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01'
old=R/'native/betaintegrated01/cockpit04/src/vn/rtr/aeris/control01/ControlOwner.java';new=R/'native/betaintegrated01/cockpit05-nativeio03/src/vn/rtr/aeris/control01/ControlOwner.java'
shared=[R/'native/betaintegrated01/control02/src/vn/rtr/aeris/control01/ControlFlight.java']+[core/n for n in('ControlAuthority.java','ControlSession.java','RcWire.java')]+[base/'beta01runtime'/n for n in('Values.java','Mavlink.java','NativeSegments.java')]+[base/'native98'/n for n in('Dialect95.java','Json.java')]+[foundation/n for n in('RunLifecycle.java','ProviderDescriptor.java')]+[Q/'ControlConfig.java',Q/'OwnerOrderMock.java',R/'planning/betaintegrated01/m1control01/qa/ProfileFixture.java',R/'planning/betaintegrated01/m1control02/qa/OwnerCloseQA.java']
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[old,new,*shared]}
before=pins();logs=[];results=[];jdk=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');E.mkdir(exist_ok=True);O=E/'mock03';O.mkdir();W.mkdir()
try:
 for variant,owner in [('baseline',old),('candidate',new)]:
  classes=W/variant;classes.mkdir();args=[str(jdk/'javac'),'--release','8','-d',str(classes),*map(str,[owner,*shared])];p=subprocess.run(args,capture_output=True,text=True,timeout=60);logs.append(dict(argv=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr
  args=[str(jdk/'java'),'-cp',str(classes),'OwnerOrderMock',str(O/(variant+'-fixtures')),*(['baseline']if variant=='baseline'else[])];p=subprocess.run(args,capture_output=True,text=True,timeout=30);logs.append(dict(argv=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr;v=json.loads(p.stdout);results.append({'variant':variant,**v})
  if variant=='candidate':
   args=[str(jdk/'java'),'-cp',str(classes),'OwnerCloseQA',str(O/'closure-fixtures')];p=subprocess.run(args,capture_output=True,text=True,timeout=30);logs.append(dict(argv=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr;results.append({'variant':'candidate-close-regression',**json.loads(p.stdout)})
finally:shutil.rmtree(W)
passed=all(t['pass']for batch in results for t in batch['results']);out={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if passed and before==pins()else'FAIL','groups':sum(len(batch['results'])for batch in results),'results':results,'commands':logs,'sourceBefore':before,'sourceAfter':pins(),'scratchRemoved':not W.exists(),'APKBuildOrSign':False,'AndroidOrAPStarts':0,'scope':'ActualOwner source with actualSession/Authority/segmentedjournal; fakeclock+connection; testonlyneutral authorityfixture seed, NOTpreflight/UI/flight proof.'}
with(O/'results.json').open('x')as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'groups':out['groups'],'failed':[t for b in results for t in b['results']if not t['pass']]}))
