from pathlib import Path
import sys,json,time,io,tarfile,hashlib
sys.path.insert(0,str(Path(__file__).parent));from android_qa import *
def files(package):
 raw=adb('exec-out','tar','-C','/data/user/0/'+package+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(raw))as t:return{m.name.removeprefix('./'):hashlib.sha256(t.extractfile(m).read()).hexdigest()for m in t.getmembers()if m.isfile()}
def old_private(name):
 baseline={}
 for v in[90,91,92,93]:baseline[str(v)]=files('vn.rtr.aeris.native'+str(v))
 (E/(name+'.json')).open('x').write(json.dumps(baseline,indent=2));return baseline
def before():
 end=time.monotonic()+90
 while time.monotonic()<end:
  try:
   if adb('shell','getprop','sys.boot_completed',allow_failure=True).strip()==b'1':break
  except Exception:pass
  time.sleep(1)
 owned();adb('root');time.sleep(1);assert b'uid=0'in adb('shell','id');old_private('old-private-before');adb('install','-r',R/'native/native94/dist/aeris-native94-development01.apk',timeout=60);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(3);capture('offline-start');journal('offline-initial');print(json.dumps(compact(),ensure_ascii=False))
if __name__=='__main__':
 if sys.argv[1]=='before':before()
 elif sys.argv[1]=='private':old_private(sys.argv[2])
