"""Check native artifact/source/tool fingerprints without installing or rebuilding."""
from pathlib import Path
import json,hashlib,subprocess,os,zipfile,datetime
R=Path(__file__).resolve().parents[1];E=R/'evidence/hera03';b=json.loads((E/'native-build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in b['source_files'].items():assert sha(R/name)==h,name+' changed after compilation'
for name,h in b['tool_hashes'].items():assert sha(Path(name))==h,name+' tool changed'
apk=R/b['apk'];assert sha(apk)==b['apk_sha256'];source_id=hashlib.sha256(json.dumps(b['source_files'],sort_keys=True,separators=(',',':')).encode()).hexdigest();assert source_id==b['sourceId']
sdk=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0');env={**os.environ,'JAVA_HOME':'/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'}
sig=subprocess.run([sdk/'apksigner','verify','--verbose','--print-certs',apk],env=env,text=True,capture_output=True);assert sig.returncode==0;assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in sig.stdout
permissions=subprocess.run([sdk/'aapt2','dump','permissions',apk],text=True,capture_output=True);assert permissions.returncode==0 and 'uses-permission:' not in permissions.stdout
with zipfile.ZipFile(apk) as z:
 dex=z.read('classes.dex');assert dex.startswith(b'dex\n');assert b'vn/rtr/aeris/diagnostic/DiagnosticActivity' in dex and source_id.encode() in dex
assert not (R/'native/diagnostic/.build').exists()
report={'status':'PASS_STATIC_NATIVE_ARTIFACT','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'apk_sha256':b['apk_sha256'],'source_files_checked':len(b['source_files']),'tool_files_checked':len(b['tool_hashes']),'signature_v2':True,'permissions':0,'sourceId':source_id,'scope':'Native bytes/dex/signature/source consistency; installation/runtime/HIL NOT_CHECKED'};O=R/os.environ.get('AERIS_EVIDENCE_DIR','evidence/hera03');O.mkdir(parents=True,exist_ok=True);(O/'native-integrity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
