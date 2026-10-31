from pathlib import Path
import sys,hashlib,json,subprocess,shutil,datetime,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];N=R/'native/phone06';E=R/'evidence/phone06-qa';W=R/'.local/phone06-qa-stage01';OUT=E/'native-heldout01.json'
assert not OUT.exists() and not W.exists()
assert shutil.disk_usage(R).free>=20*2**30+32*2**20
freeze=R/'evidence/phone06/builder/native-source-ready01.json';pins=json.loads(freeze.read_text())['files'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 for p,s in pins.items():assert sha(R/p)==s,p
verify();logs=[];results=[];error=None;outputs={};W.mkdir(parents=True)
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');SDK=Path('/opt/homebrew/share/android-commandlinetools');A=SDK/'platforms/android-37.0/android.jar';B=SDK/'build-tools/36.0.0'
def run(a):
 try:
  p=subprocess.run(list(map(str,a)),cwd=R,text=True,capture_output=True,timeout=45)
  logs.append({'command':list(map(str,a)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 except subprocess.TimeoutExpired as x:
  logs.append({'command':list(map(str,a)),'exit':'TIMEOUT','stdout':str(x.stdout or ''),'stderr':str(x.stderr or '')});raise
 assert p.returncode==0,p.stderr
 return p.stdout
try:
 sys.path.insert(0,str(N));from overlay import stage
 stage(W);(W/'src/BuildInfo90.java').write_text('package vn.rtr.aeris.phone06;public final class BuildInfo90{public static final String SOURCE_ID="OFFLINE_QA_NATIVE_SUBSET01";}')
 outputs['generatedSources']={p.name:sha(p) for p in (W/'src').glob('*.java')}
 run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+':'+str(A),'-d',W/'classes',*sorted((W/'src').glob('*.java'))])
 run([J/'bin/javac','-cp',W/'classes','-d',W/'classes',N/'tests/NativeFixture06.java',R/'planning/phone06/qa/QA06.java'])
 s=run([J/'bin/java','-cp',W/'classes','vn.rtr.aeris.phone06.QA06',W/'cases'])
 results=[json.loads(x) for x in s.splitlines() if x.startswith('{')]
 assert len(results)==19
 # Independent pinned upstream CRC/fields, distinct from product encoder.
 sys.path.insert(0,str(R/'planning/phone06/qa'));from manual_oracle06 import decode_manual06
 for q in results:
  if 'frames' in q:
   decoded=[]
   for h in q['frames']:
    b=bytes.fromhex(h);mid=int.from_bytes(b[7:10],'little')
    if mid==69:decoded.append(decode_manual06(h))
   q['independentManualDecode']=decoded
   if q['id']=='PQ02':assert len(decoded)==2 and {k:decoded[1][k] for k in ['x','y','z','r']}=={'x':430,'y':580,'z':810,'r':-370}
   if q['id']=='PQ03':assert len(decoded)==3 and {k:decoded[-1][k] for k in ['x','y','z','r']}=={'x':0,'y':0,'z':500,'r':0}
   if q['id']=='PQ05':assert len(decoded)==1
   if q['id'] in ['PQ07','PQ08']:assert len(decoded)==0 and 'TX_INTENT' in q['raw'] and 'TX_WRITTEN' not in q['raw']
 verify()
except BaseException as x:error=traceback.format_exc()
finally:
 # Retain causal actual fixture WALs bounded; no host/private identity data.
 causal={str(p.relative_to(W)):p.read_text() for p in W.rglob('raw.jsonl') if p.stat().st_size<131072}
 OUT.open('x').write(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'status':'EXECUTED_WITH_FINDINGS'if not error else'QA_HARNESS_FAILURE_RETAINED','sourceFreeze':str(freeze.relative_to(R)),'sourceFreezeSha256':sha(freeze),'sourcePins':pins,'qaJavaSha256':sha(R/'planning/phone06/qa/QA06.java'),'scope':'ACTUAL_ASSEMBLED_NATIVE_CLASSES_WITH_SYNTHETIC_OBSERVATIONS_IN_MEMORY_WIRE_NO_NETWORK_AP_DEVICE_OR_APK','plannedInputs':19,'executedInputs':sum(q['status']!='NOT_CHECKED'for q in results),'results':results,'error':error,'logs':logs,'causalRaw':causal,'outputs':outputs,'scratchRemoved':str(W.relative_to(R))},indent=2)+'\n')
 shutil.rmtree(W)
print(OUT, error or [(q['id'],q['status']) for q in results])
