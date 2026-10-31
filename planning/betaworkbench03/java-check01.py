from pathlib import Path
import subprocess,shutil,hashlib,json,datetime,time
R=Path(__file__).resolve().parents[2];E=R/'evidence/betaworkbench03';N=R/'native/betaworkbench03';W=N/'.check';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');SDK=Path('/opt/homebrew/share/android-commandlinetools');A=SDK/'platforms/android-37.0/android.jar';S=SDK/'build-tools/36.0.0/core-lambda-stubs.jar';logs=[];created=False;error=None
def floor():assert shutil.disk_usage(R).free>=20*2**30+256*2**20,'PHYSICAL_FLOOR'
def run(args):
 floor();p=subprocess.run([str(x)for x in args],text=True,capture_output=True,timeout=45,cwd=R);logs.append({'args':[str(x)for x in args],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,logs[-1];return p.stdout
try:
 floor();assert not W.exists();assert not(E/'java-check01.json').exists();W.mkdir();created=True;(W/'host').mkdir();(W/'android').mkdir()
 src=N/'src/vn/rtr/aeris/betaworkbench03';gate=N/'OperationGate.java';test=R/'planning/betaworkbench03/OperationGateTest.java'
 old=(R/'planning/workbench02/StoreTest.java').read_text();assert old.count('package vn.rtr.aeris.workbench02;')==1;adapted=old.replace('package vn.rtr.aeris.workbench02;','package vn.rtr.aeris.betaworkbench03;');floor();(W/'StoreTest.java').write_text(adapted)
 run([J/'javac','-d',W/'host',src/'WorkspaceStore.java',gate,test,W/'StoreTest.java'])
 assert 'PASS owner correlation'in run([J/'java','-cp',W/'host','vn.rtr.aeris.betaworkbench03.OperationGateTest'])
 assert 'SUMMARY 19 HOST_JAVA_NOT_ART'in run([J/'java','-cp',W/'host','vn.rtr.aeris.betaworkbench03.StoreTest',E/'native-store-fixtures01'])
 run([J/'javac','-source','8','-target','8','-bootclasspath',str(S)+':'+str(A),'-d',W/'android',src/'WorkspaceStore.java',src/'ShellActivity.java',gate])
 text=(src/'ShellActivity.java').read_text();head,tail=text.split('@Override protected void onActivityResult');assert 'catch(Exception e){reply(q,null,e);}'in tail;assert 'deliver(q,null,e,false)'not in tail;assert 'deliver(q,null,e,false)'in head;assert 'gate.finish(q.optString("session")+":"+q.optString("id"))'in text
except BaseException as e:error=repr(e)
finally:
 if created:shutil.rmtree(W)
 report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FAIL'if error else'PASS','error':error,'hostStoreCases':19 if not error else'NOT_ALL_CHECKED','operationGate':'HOST_CLASS_EXECUTED_NOT_ANDROID_SAF','safTail':'STATIC_PATH_ASSERTION_PLUS_OWNER_GATE_MODEL_NOT_ANDROID_IO','androidTypecheck':'ANDROID37_STUBS_NOT_ART','logs':logs,'apkBuilt':False,'cleanup':['native/betaworkbench03/.check']if created else[],'freeBytes':shutil.disk_usage(R).free}
 print(json.dumps(report,indent=2));floor();(E/'java-check01.json').open('x').write(json.dumps(report,indent=2)+'\n')
if error:raise RuntimeError(error)
