from pathlib import Path
import sys,subprocess,shutil,json,datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from overlay import *
E=R/'evidence/integration03';E.mkdir(parents=True,exist_ok=True);suffix=sys.argv[1];W=N/'.mock';assert not W.exists();assert shutil.disk_usage(R).free>=20*2**30+160*2**20;W.mkdir();logs=[]
def run(args):
 r=subprocess.run(list(map(str,args)),cwd=R,capture_output=True,text=True,timeout=120);logs.append({'command':list(map(str,args)),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});assert r.returncode==0,r.stdout+r.stderr
try:
 stage(W)
 for p in(W/'assets').rglob('*.mjs'):run(['node','--check',p])
 run(['node',N/'tests/intake.mjs',W/'assets']);run(['node',N/'tests/presentation.mjs',R/'native/crew02/assets','old']);run(['node',N/'tests/presentation.mjs',W/'assets','new'])
 J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0');A=Path('/opt/homebrew/share/android-commandlinetools/platforms/android-37.0/android.jar');(W/'src/BuildInfo90.java').write_text('package vn.rtr.aeris.integration03;public final class BuildInfo90{public static final String SOURCE_ID="MOCK";}');run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+':'+str(A),'-d',W/'classes',*sorted((W/'src').glob('*.java')),N/'tests/Stage03Test.java',N/'tests/CommittedRx03Test.java',N/'tests/UiPumpDelivery03Test.java']);run([J/'bin/java','-cp',W/'classes','vn.rtr.aeris.integration03.Stage03Test',E/('stage-fixture'+suffix)]);run([J/'bin/java','-cp',W/'classes','vn.rtr.aeris.integration03.CommittedRx03Test',E/('committed-fixture'+suffix)]);run(['node',N/'tests/retention03.mjs',W/'assets']);run(['node',N/'tests/delivery06.mjs',W/'assets']);run(['node',N/'tests/socket-proof-age.mjs',W/'assets']);run(['node',N/'tests/socket-diagnostics06.mjs',W/'assets']);run([J/'bin/java','-cp',W/'classes','vn.rtr.aeris.integration03.UiPumpDelivery03Test']);print('PASS')
finally:
 (E/('source-mock'+suffix+'.json')).open('x').write(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'scope':'OFFLINE_COMPILE_AND_ACTUAL_JS_NO_ANDROID_RUNTIME','logs':logs},indent=2)+'\n');shutil.rmtree(W)
