from pathlib import Path
import subprocess,json,time,hashlib
R=Path(__file__).resolve().parents[2];E=R/'evidence/native79';A='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';P='vn.rtr.aeris.native79';remote='/data/local/tmp/aeris-native79.apk';root='/data/user/0/'+P+'/files/qa79';checks=[];log=[]
def call(args,data=None,allow=False):
 p=subprocess.run([A,'-s',S,*args],input=data,capture_output=True,timeout=90);log.append({'args':args,'code':p.returncode,'stdout':p.stdout.decode(errors='replace')[:16000],'stderr':p.stderr.decode(errors='replace')[:2000]});assert p.returncode==0 or allow,log[-1];return p
def sh(command,**kw):return call(['shell',command],**kw)
def check(name,x):assert x,name;checks.append({'name':name,'pass':True});print(name,flush=True)
def invoke(mode,path,token=None,body=None):
 c='run-as '+P+' env CLASSPATH='+remote+' app_process /system/bin '+P+'.JournalMain '+mode+' '+path
 if token:c+=' '+token
 return json.loads(sh(c,data=body).stdout)
try:
 check('owned AOSP emulator',sh('getprop ro.boot.qemu').stdout.strip()==b'1' and sh('getprop ro.build.version.sdk').stdout.strip()==b'33')
 call(['push',str(R/'native/runtime79/dist/aeris-native79-development.apk'),remote]);check('exact APK transfer',sh('sha256sum '+remote).stdout.decode().split()[0]==hashlib.sha256((R/'native/runtime79/dist/aeris-native79-development.apk').read_bytes()).hexdigest())
 t=sh('run-as '+P+' env CLASSPATH='+remote+' app_process /system/bin '+P+'.AndroidProbe test '+root+'/tests');(E/'art-journal.txt').write_bytes(t.stdout+t.stderr);check('31 actual ART app-private journal checks',t.stdout.count(b'PASS ')==31 and b'API=33 ABI=arm64-v8a'in t.stdout)
 x=invoke('save',root+'/restart','ROOT',b'old');y=invoke('load',root+'/restart');check('actual Android process restart committed byte/token',x==y and not y['authorityRestorable'])
 for phase in ['RECORD_PUBLISHED','HEAD_PENDING','HEAD_COMMITTED']:
  path=root+'/kill-'+phase;old=invoke('save',path,'ROOT',b'old');marker=path+'/marker';cmd='run-as '+P+' env CLASSPATH='+remote+' app_process /system/bin '+P+'.AndroidProbe crash '+path+' '+old['token']+' '+phase+' '+marker
  process=subprocess.Popen([A,'-s',S,'shell',cmd],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);process.stdin.write(b'new');process.stdin.close();pid=None
  for _ in range(100):
   p=sh('run-as '+P+' cat '+marker,allow=True)
   if p.returncode==0:pid=int(p.stdout.splitlines()[0]);break
   time.sleep(.1)
  assert pid and pid>100;identity=sh('run-as '+P+' cat /proc/'+str(pid)+'/cmdline').stdout;check('owned ART crash PID '+phase,(P+'.AndroidProbe').encode()in identity)
  sh('run-as '+P+' kill -9 '+str(pid));process.wait(timeout=10);(E/('art-sigkill-'+phase+'.txt')).write_bytes(process.stdout.read()+process.stderr.read());got=invoke('load',path)
  check('exact recovered commit '+phase,got['bodyBase64']==('bmV3'if phase=='HEAD_COMMITTED'else'b2xk'))
  check('pending disclosure '+phase,got['pending']==(phase=='HEAD_PENDING'))
  check('both revisions retained '+phase,sh('run-as '+P+' ls '+path).stdout.count(b'.bin')==2)
except Exception as ex:
 checks.append({'name':'ART failure','pass':False,'error':str(ex)});raise
finally:
 with(E/'art-commands.json').open('x')as f:json.dump(log,f,indent=2)
 with(E/'art-verification.json').open('x')as f:json.dump({'status':'PASS'if checks and all(x['pass']for x in checks)else'FAIL','checks':checks,'scope':'Actual ART Android13 and run-as app-private UID, not physical power loss/Hera'},f,indent=2)
