from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
R=Path(__file__).resolve().parents[4];Q=Path(__file__).parent;attempt=sys.argv[1];O=R/('evidence/betaintegrated01-m1cockpit03/qa/store'+attempt);O.mkdir();W=R/'native/betaintegrated01/.build/qa-cockpit03';W.mkdir();base=R/'native/betaintegrated01/runtime/src/vn/rtr/aeris';target=Q/'pre01/vn/rtr/aeris/cockpit03/WorkspaceStore.java'if len(sys.argv)>2 and sys.argv[2]=='pre'else R/'native/betaintegrated01/cockpit03/src/vn/rtr/aeris/cockpit03/WorkspaceStore.java'
src=[target,base/'beta01runtime/NativeSegments.java',base/'beta01runtime/Values.java',base/'native98/Json.java',Q/'StoreQA.java'];pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in src};before=pins();jdk=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');logs=[];results=[]
try:
 c=subprocess.run([str(jdk/'javac'),'--release','8','-d',str(W),*map(str,src)],capture_output=True,text=True,timeout=60);logs.append({'kind':'javac','exit':c.returncode,'stdout':c.stdout,'stderr':c.stderr})
 if c.returncode==0:
  c=subprocess.run([str(jdk/'java'),'-cp',str(W),'StoreQA',str(O/'fixtures')],capture_output=True,text=True,timeout=60);logs.append({'kind':'java','exit':c.returncode,'stdout':c.stdout,'stderr':c.stderr});results=json.loads(c.stdout)['results']if c.returncode==0 else[]
finally:shutil.rmtree(W)
r={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if results and all(x['pass']for x in results)and before==pins()else'FAIL','results':results,'sourceBefore':before,'sourceAfter':pins(),'commands':logs,'sourceStage':'preservedinitialsource'if 'pre01'in str(target)else'currentwork-in-progress','scope':'RealJavaStore/realFSsync/faultfixtures, noAPK/ADB/AP/services','scratchRemoved':not W.exists()};(O/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'failed':[x['id']for x in results if not x['pass']]}))
