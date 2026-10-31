from pathlib import Path
import sys,subprocess,shutil,json,datetime,hashlib
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parents[1];R=N.parents[1];sys.path.insert(0,str(N));from overlay import stage,source
E=R/'evidence/phone06/builder';suffix=sys.argv[1];assert suffix.isdigit()and len(suffix)==2;out=E/('checks'+suffix+'.json');assert not out.exists();W=N/'.mock';assert not W.exists()and shutil.disk_usage(R).free>=20*2**30+32*2**20;W.mkdir();logs=[];passed=False
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');SDK=Path('/opt/homebrew/share/android-commandlinetools');A=SDK/'platforms/android-37.0/android.jar';B=SDK/'build-tools/36.0.0'
def run(a):
 try:p=subprocess.run(list(map(str,a)),cwd=R,text=True,capture_output=True,timeout=30)
 except subprocess.TimeoutExpired as e:
  logs.append({'command':list(map(str,a)),'exit':'TIMEOUT','output':str(e.stdout or '')+str(e.stderr or '')});raise
 logs.append({'command':list(map(str,a)),'exit':p.returncode,'output':p.stdout+p.stderr});assert p.returncode==0,p.stdout+p.stderr
try:
 pins=stage(W);(W/'src/BuildInfo90.java').write_text('package vn.rtr.aeris.phone06;public final class BuildInfo90{public static final String SOURCE_ID="OFFLINE";}');run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+':'+str(A),'-d',W/'classes',*sorted((W/'src').glob('*.java'))]);run([J/'bin/javac','-cp',W/'classes','-d',W/'classes',N/'tests/NativeFixture06.java',N/'tests/Policy06Test.java']);run([J/'bin/java','-cp',W/'classes','vn.rtr.aeris.phone06.Policy06Test',W/'cases']);run(['node',N/'tests/touch-test.mjs']);
 for p in(W/'assets').rglob('*.mjs'):run(['node','--check',p])
 passed=True
finally:
 out.open('x').write(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'status':'PASS'if passed else'FAIL_RETAINED','sourcePins':source(),'scope':'OFFLINE_HOST_COMPILE_AND_DECLARED_SYNTHETIC_POLICY_INPUTS_NOT_DEVICE_AP_OR_APK','distinctInputPlan':29,'logs':logs,'scratchRemoved':str(W.relative_to(R))},indent=2)+'\n');shutil.rmtree(W)
print('PASS offline29inputs; notdevice/AP acceptance')
