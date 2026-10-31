from pathlib import Path
import sys,hashlib,json,subprocess,shutil,datetime
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];Q=Path(__file__).parent;W=R/'native/betaintegrated01/iocommit09-core/.build';E=R/'evidence/betaintegrated01-cockpit05-iocommit09/mock';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');C=R/'native/betaintegrated01/nativeio07-core/src/vn/rtr/aeris';B=R/'native/betaintegrated01/runtime/src/vn/rtr/aeris';F=R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01';O=R/'planning/betaintegrated01/cockpit05-nativeio06/mock'
NEW=R/'native/betaintegrated01/iocommit09-core/src/vn/rtr/aeris'
sources=[NEW/'control01'/n for n in ['ControlAuthority.java','ControlSession.java']]+[C/'control01'/n for n in ['ControlOwner.java','ControlFlight.java']]+[R/'native/betaintegrated01/nativeio08-core/src/vn/rtr/aeris/control01/InputScheduler.java',NEW/'beta01runtime/NativeSegments.java',C/'beta01runtime/IoTiming.java']+[B/'beta01runtime'/n for n in ['Values.java','Mavlink.java']]+[B/'native98'/n for n in ['Dialect95.java','Json.java']]+[F/n for n in ['RunLifecycle.java','ProviderDescriptor.java']]+[R/'native/betaintegrated01/control01/src/vn/rtr/aeris/control01/RcWire.java',O/'ControlConfig.java',Q/'CommitMock.java',Q/'OwnerOrderMock.java',R/'planning/betaintegrated01/m1control02/qa/OwnerCloseQA.java',R/'planning/betaintegrated01/cockpit05-nativeio07/mock/SessionMock.java',R/'planning/betaintegrated01/m1control01/qa/ProfileFixture.java']

def pins():return{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources}
import argparse
p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);args=p.parse_args();D=E/('builder'+args.attempt);D.mkdir();W.mkdir();before=pins();logs=[];results=[];error=None
try:
 argv=[str(J/'javac'),'--release','8','-d',str(W),*map(str,sources)];p=subprocess.run(argv,capture_output=True,text=True,timeout=60);logs.append(dict(argv=argv,code=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr
 for cls in ['CommitMock','SessionMock','OwnerOrderMock','OwnerCloseQA']:
  argv=[str(J/'java'),'-cp',str(W),cls,str(D/(cls+'-fixtures'))];p=subprocess.run(argv,capture_output=True,text=True,timeout=40);logs.append(dict(argv=argv,code=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr;results.append({'class':cls,**json.loads(p.stdout)})
except BaseException as e:error=str(e)
finally:
 scratchBytes=sum(p.stat().st_size for p in W.rglob('*')if p.is_file());shutil.rmtree(W)
out=dict(status='PASS'if not error and all(x['pass']for b in results for x in b['results'])and before==pins()else'FAIL',error=error,groups=sum(len(b['results'])for b in results),results=results,commands=logs,sourceBefore=before,sourceAfter=pins(),scratchRemoved=not W.exists(),scratchBytes=scratchBytes,AndroidOrAPStarts=0,APKBuildOrSign=False,atUTC=datetime.datetime.now(datetime.timezone.utc).isoformat());(D/'results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k]for k in ['status','groups','error']}));sys.exit(0 if out['status']=='PASS'else 1)
