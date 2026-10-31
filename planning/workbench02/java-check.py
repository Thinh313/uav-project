from pathlib import Path
import subprocess,os,json,hashlib,datetime,shutil,sys,time

R=Path(__file__).resolve().parents[2];E=R/'evidence/workbench02';W=R/'native/workbench02/.check'
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');SDK=Path('/opt/homebrew/share/android-commandlinetools')
A=SDK/'platforms/android-37.0/android.jar';stub=SDK/'build-tools/36.0.0/core-lambda-stubs.jar'
attempt=sys.argv[1] if len(sys.argv)==2 else '01';assert len(attempt)==2 and attempt.isdigit()
report_path=E/('java-check'+attempt+'.json');log_path=E/('java-command-log'+attempt+'.json')
fixtures=E/('store-fixtures'+attempt);process_root=E/('store-process'+attempt)
logs=[];report=None;created=False;failure=None;cleanup=[]
def floor(extra=8*2**20):
    assert shutil.disk_usage(R).free>=20*2**30+extra,'PHYSICAL_FLOOR_20_GIB_PLUS_RESERVATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd):
    floor();cmd=[str(x)for x in cmd];started=time.monotonic();out=err='';reason=None
    p=subprocess.Popen(cmd,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        while True:
            try:out,err=p.communicate(timeout=.2);break
            except subprocess.TimeoutExpired:
                floor(4*2**20)
                if time.monotonic()-started>45:raise TimeoutError('COMMAND_45_S_BOUND')
        assert len(out.encode())+len(err.encode())<=65536,'COMMAND_LOG_BOUND'
        assert p.returncode==0,'COMMAND_EXIT_'+str(p.returncode)
    except BaseException as e:
        reason=str(e)
        if p.poll()is None:p.terminate()
        try:out,err=p.communicate(timeout=3)
        except subprocess.TimeoutExpired:p.kill();out,err=p.communicate()
        raise
    finally:logs.append({'command':cmd,'exit':p.returncode,'stdout':out,'stderr':err,'failure':reason,'durationS':time.monotonic()-started})
    return out
try:
    floor();assert not any(p.exists()for p in[W,report_path,log_path,fixtures,process_root]),'EXCLUSIVE_NEW_ATTEMPT_REQUIRED'
    assert all(p.is_file()for p in[J/'bin/javac',J/'bin/java',A,stub]),'INSTALLED_TOOLCHAIN_REQUIRED_NO_DOWNLOAD'
    W.mkdir();created=True;host=W/'host';host.mkdir();src=R/'native/workbench02/src/vn/rtr/aeris/workbench02'
    run([J/'bin/javac','-d',host,src/'WorkspaceStore.java',R/'planning/workbench02/StoreTest.java',R/'planning/workbench02/StoreProcessProbe.java'])
    output=run([J/'bin/java','-cp',host,'vn.rtr.aeris.workbench02.StoreTest',fixtures]);assert 'SUMMARY 19 HOST_JAVA_NOT_ART'in output
    wrote=run([J/'bin/java','-cp',host,'vn.rtr.aeris.workbench02.StoreProcessProbe','write',process_root])
    read=run([J/'bin/java','-cp',host,'vn.rtr.aeris.workbench02.StoreProcessProbe','read',process_root])
    assert wrote.removeprefix('WRITE ')==read.removeprefix('READ '),'TWO_PROCESS_RECEIPT_MISMATCH'
    # Execute the exact source predicate with a fake q.opt provider. Not JSONObject/ART/Broker execution.
    shell=(src/'ShellActivity.java').read_text();left='q.length()!=6||';right='||!instance.equals'
    assert shell.count(left)==1
    predicate=shell.split(left,1)[1].split(right,1)[0]
    guard='''public final class VersionGuardProbe {
 static final class Q {Object value;Q(Object v){value=v;}Object opt(String key){return value;}}
 static boolean accepts(Object v){Q q=new Q(v);return !PREDICATE;}
 public static void main(String[] args){Object[] values={1,1L,1.0,"1",1.5,true,null,0,2,Double.NaN,Double.POSITIVE_INFINITY};int pass=0;
 for(int i=0;i<values.length;i++){if(accepts(values[i])!=(i<3))throw new AssertionError("VERSION_CASE_"+i);pass++;}System.out.println("SUMMARY "+pass+" EXTRACTED_GUARD_FAKE_Q_NOT_ANDROID");}}
'''.replace('PREDICATE',predicate)
    floor();probe=W/'VersionGuardProbe.java';probe.write_text(guard)
    run([J/'bin/javac','-d',host,probe]);assert 'SUMMARY 11 EXTRACTED_GUARD_FAKE_Q_NOT_ANDROID'in run([J/'bin/java','-cp',host,'VersionGuardProbe'])
    floor();android=W/'android';android.mkdir()
    run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(stub)+os.pathsep+str(A),'-d',android,src/'WorkspaceStore.java',src/'ShellActivity.java'])
    report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','hostStoreCases':19,'twoHostJvmProcesses':'PASS_NOT_ART','requestVersionCases':11,'requestVersionScope':'EXACT_EXTRACTED_PREDICATE_WITH_FAKE_Q_NOT_JSONOBJECT_OR_BROKER','versionPredicate':predicate,'versionPredicateSha256':hashlib.sha256(predicate.encode()).hexdigest(),'androidJavaTypecheck':'PASS_ANDROID37_STUBS_NOT_ART','sdkJarSha256':sha(A),'lambdaStubsSha256':sha(stub),'javaVersion':run([J/'bin/java','-version']),'sourceSha256':{str(p.relative_to(R)):sha(p)for p in[src/'WorkspaceStore.java',src/'ShellActivity.java',R/'planning/workbench02/StoreTest.java',R/'planning/workbench02/StoreProcessProbe.java',Path(__file__).resolve()]},'apkBuilt':False,'runtime':'NOT_RUN','directorySync':'NOOP_CALLBACK_IN_HOST_CASES_AND_INJECTED_FAILURE_NOT_ANDROID_FSYNC_PROOF','logs':logs}
except BaseException as e:
    failure=e;report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FAIL','error':repr(e),'logs':logs,'runtime':'NOT_RUN','apkBuilt':False}
finally:
    if created:
        shutil.rmtree(W);cleanup.append(str(W.relative_to(R)))
    report=report or {'status':'FAIL','error':'INITIALIZATION_FAILED'}
    report.update(freeBytes=shutil.disk_usage(R).free,cleanup=cleanup,fixturesRetained=True)
    print(json.dumps(report,indent=2),flush=True)
    # If host space falls, stdout remains the log; never write a finally receipt below floor.
    floor()
    log_path.open('x').write(json.dumps(logs,indent=2)+'\n')
    report_path.open('x').write(json.dumps(report,indent=2)+'\n')
if failure is not None:raise failure
