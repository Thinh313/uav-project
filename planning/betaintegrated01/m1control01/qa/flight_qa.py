from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
R=Path(__file__).resolve().parents[4];out=R/('evidence/betaintegrated01-m1control01/qa/flight'+sys.argv[1]);out.mkdir();classes=R/'native/betaintegrated01/.build/qa-control';classes.mkdir()
profile=R/'runtime/betaintegrated01/control01/nominal/typed-profile.json';d=json.loads(profile.read_text());generated=Path(__file__).with_name('ProfileFixture.java')
body='import java.util.*; public final class ProfileFixture { public static Map<String,int[]> specs(){Map<String,int[]>p=new LinkedHashMap<>();'
for name,item in d['parameters'].items():body+='p.put('+json.dumps(name)+',new int[]{'+str(item['mavType'])+','+str(int.from_bytes(bytes.fromhex(item['float32Hex']),'little',signed=True))+'});'
body+='return p;}}\n'
if not generated.exists():generated.write_text(body)
assert generated.read_text()==body,'profile fixture drift'
flight_version='control02'if len(sys.argv)>2 and sys.argv[2]=='control02'else'control01'
src=[R/('native/betaintegrated01/'+flight_version+'/src/vn/rtr/aeris/control01/ControlFlight.java'),R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/beta01runtime/Values.java',R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/beta01runtime/Mavlink.java',R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/native98/Dialect95.java',R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/native98/Json.java',Path(__file__).with_name('ControlFlightQA.java'),generated]
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in src+[profile]};before=pins();jdk=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');logs=[];results=[]
try:
 c=subprocess.run([str(jdk/'javac'),'--release','8','-d',str(classes),*map(str,src)],capture_output=True,text=True,timeout=60);logs.append({'kind':'javac','exit':c.returncode,'stdout':c.stdout,'stderr':c.stderr})
 if c.returncode==0:
  r=subprocess.run([str(jdk/'java'),'-cp',str(classes),'ControlFlightQA'],capture_output=True,text=True,timeout=60);logs.append({'kind':'java','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});results=json.loads(r.stdout)['results']if r.returncode==0 else[]
finally:count=len(list(classes.rglob('*.class')));shutil.rmtree(classes)
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':pins(),'sourceChanged':before!=pins(),'commands':logs,'results':results,'status':'PASS'if results and all(r['pass']for r in results)and before==pins()else'FAIL','classFilesRemoved':count,'classOutputExistsAfter':classes.exists(),'APAndroidSocketLaunches':0,'scope':'Independent preflight/Home/motion predicates from synthetic padded wire observations. No actual flight or physical sensor attested'}
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(results),'failed':[r['id']for r in results if not r['pass']],'sourceChanged':report['sourceChanged']}))
