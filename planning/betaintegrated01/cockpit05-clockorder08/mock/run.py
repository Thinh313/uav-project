from pathlib import Path
import json,subprocess,shutil,hashlib,sys,datetime
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];Q=Path(__file__).parent;E=R/'evidence/betaintegrated01-cockpit05-clockorder08/mock';W=R/'native/betaintegrated01/nativeio08-core/.build';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');C=R/'native/betaintegrated01/nativeio07-core/src/vn/rtr/aeris/control01';B=R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/beta01runtime';F=R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01'
shared=[R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/native98/Json.java',C/'ControlAuthority.java',B/'Values.java',F/'RunLifecycle.java',F/'ProviderDescriptor.java',Q/'ClockBoundaryMock.java'];old=C/'InputScheduler.java';new=R/'native/betaintegrated01/nativeio08-core/src/vn/rtr/aeris/control01/InputScheduler.java';pin={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [old,new,*shared]};W.mkdir();out=[];logs=[]
try:
 for variant,path in [('baseline',old),('candidate',new)]:
  d=W/variant;d.mkdir();args=[str(J/'javac'),'--release','8','-d',str(d),*map(str,[path,*shared])];p=subprocess.run(args,capture_output=True,text=True,timeout=30);logs.append(dict(argv=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr
  args=[str(J/'java'),'-cp',str(d),'ClockBoundaryMock',variant];p=subprocess.run(args,capture_output=True,text=True,timeout=10);logs.append(dict(argv=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr;out.append(json.loads(p.stdout))
finally:
 scratch=sum(p.stat().st_size for p in W.rglob('*')if p.is_file());shutil.rmtree(W)
assert new.read_text().replace('long u=clock.uptimeNs(),n=clock.elapsedNs();','long n=clock.elapsedNs(),u=clock.uptimeNs();')==old.read_text()
result=dict(status='PASS',results=out,groups=2,sourceSHA256=pin,onlyClockReadOrderChanged=True,scratchBytes=scratch,scratchRemoved=not W.exists(),AndroidStarts=0,APKBuildOrSign=False,commands=logs,atUTC=datetime.datetime.now(datetime.timezone.utc).isoformat());(E/'clock-boundary02.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'results':out}))
