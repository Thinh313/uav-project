"""Derive/sign N30 development APK only; never write N30, ENDURE or release keys."""
from pathlib import Path
import subprocess,os,json,hashlib,shutil,zipfile,datetime
R=Path(__file__).resolve().parents[2]; N=R/'native/shell30'; M=R/'native/runtime31'; E=R/'evidence/native31'
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'); S=Path('/opt/homebrew/share/android-commandlinetools'); B=S/'build-tools/36.0.0'; A=S/'platforms/android-37.0/android.jar'
W=M/'.build'; D=M/'dist'; K=R/'.local/native31'; h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert shutil.disk_usage(R).free>20*1024**3+64*1024**2
assert not W.exists(); W.mkdir(); D.mkdir(exist_ok=True); K.mkdir(exist_ok=True); os.chmod(K,0o700)
attempt=1
while (E/f'build{attempt:02d}.txt').exists():attempt+=1
env={**os.environ,'JAVA_HOME':str(J)}; logs=[]
def run(args):
 p=subprocess.run([str(x) for x in args],cwd=R,env=env,text=True,capture_output=True); logs.append(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
try:
 sources=list((N/'src').rglob('*.java'))+list((N/'tests').rglob('*.java')); transformed=[]; compile_sources=[]
 for p in sources:
  dst=W/'src'/p.name; text=p.read_text()
  if p.name=='ShellActivity.java':
   text=text.replace('web=new WebView(this);','WebView.setWebContentsDebuggingEnabled(true);web=new WebView(this);')
   text=text.replace('if(web!=null)web.onResume();','if(web!=null){web.onResume();web.evaluateJavascript("window.dispatchEvent(new Event(\'focus\'))",null);}')
  dst.parent.mkdir(parents=True,exist_ok=True); dst.write_text(text); compile_sources.append(dst)
  transformed.append({'source':str(p.relative_to(R)),'sourceSha256':h(p),'compiledSha256':h(dst),'changed':p.read_bytes()!=dst.read_bytes()})
 manifest=(N/'AndroidManifest.xml').read_text().replace('0.3.0-native30-unsigned','0.3.1-native30-development').replace('android:versionCode="30"','android:versionCode="31"').replace('android:debuggable="false"','android:debuggable="true"').replace('AERIS Editable Preparation','AERIS N30 Development')
 (W/'AndroidManifest.xml').write_text(manifest); assets=W/'assets/editor'; assets.mkdir(parents=True); asset_sources={}
 for p in [N/'index.html',N/'shell.css',N/'shell.mjs',N/'editor.mjs',N/'pins.mjs',*list((N/'vendor').glob('*.mjs'))]:
  dst=assets/p.relative_to(N); dst.parent.mkdir(parents=True,exist_ok=True); text=p.read_text().replace('unsigned build scope','development build · offline mock').replace('unsigned engineering shell','development engineering shell'); dst.write_text(text)
  asset_sources[str(p.relative_to(N))]={'originalSha256':h(p),'packagedSha256':h(dst)}
 classes=W/'classes'; classes.mkdir(); run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*compile_sources])
 run([B/'aapt2','link','-I',A,'--manifest',W/'AndroidManifest.xml','-A',W/'assets','-o',W/'raw.apk']); dex=W/'dex'; dex.mkdir(); run([B/'d8','--min-api','26','--lib',A,'--output',dex,*classes.rglob('*.class')])
 with zipfile.ZipFile(W/'raw.apk','a') as z:z.write(dex/'classes.dex','classes.dex')
 run([B/'zipalign','-f','4',W/'raw.apk',W/'aligned.apk'])
 pw=K/'password'; key=K/'development.p12'
 if not key.exists():
  assert not pw.exists(); pw.write_text(os.urandom(24).hex()); os.chmod(pw,0o600)
  run([J/'bin/keytool','-genkeypair','-keystore',key,'-storetype','PKCS12','-storepass:file',pw,'-keypass:file',pw,'-alias','native31-development','-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=AERIS NATIVE31 Development, OU=Engineering Emulator Only, O=RtR']); os.chmod(key,0o600)
 apk=D/f'aeris-native30-development-{attempt:02d}.apk'
 run([B/'apksigner','sign','--ks',key,'--ks-key-alias','native31-development','--ks-pass','file:'+str(pw),'--out',apk,W/'aligned.apk'])
 verification=run([B/'apksigner','verify','--verbose','--print-certs',apk]); (E/f'signature{attempt:02d}.txt').write_text(verification)
 permissions=run([B/'aapt2','dump','permissions',apk]); assert 'uses-permission:' not in permissions; (E/f'permissions{attempt:02d}.txt').write_text(permissions)
 cert=D/'development-certificate.der'; run([J/'bin/keytool','-exportcert','-keystore',key,'-storepass:file',pw,'-alias','native31-development','-file',cert])
 with zipfile.ZipFile(apk) as z,zipfile.ZipFile(W/'aligned.apk') as u:
  assert all(z.read(n)==u.read(n) for n in u.namelist()),'signing changed payload'
 report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':attempt,'apk':str(apk.relative_to(R)),'sha256':h(apk),'bytes':apk.stat().st_size,'certificateSha256':h(cert),'scope':'Development/emulator only; not software release/Hera acceptance','sourceOverlays':transformed,'assets':asset_sources,'signaturePayloadExact':True,'zeroPermissions':True,'debuggable':True,'privateKey':'Dedicated .local/native31 only; never release keys'}
 (E/f'build{attempt:02d}.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report|{'sourceOverlays':'see receipt','assets':'see receipt'}))
finally:
 (E/f'build{attempt:02d}.txt').write_text('\n'.join(logs)); shutil.rmtree(W)
