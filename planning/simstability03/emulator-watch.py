"""Only task-owned cached emulator5582; bounded process and retained closure."""
from pathlib import Path
import os,json,time,signal,subprocess,shutil,socket,datetime,sys,re
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03'
TAG=sys.argv[1]if len(sys.argv)>1 else'01';assert re.fullmatch('[0-9]{2}',TAG)
assert shutil.disk_usage(R).free>=20*2**30,'ADMISSION20GIB'
for port in [5582,5583]:
 with socket.socket()as s:s.bind(('127.0.0.1',port))
def stamp(pid):
 q=subprocess.run(['ps','-p',str(pid),'-o','lstart='],capture_output=True,text=True)
 return q.stdout.strip()if q.returncode==0 else None

def owned(pid,start):
 if stamp(pid)!=start:return False
 q=subprocess.run(['ps','-p',str(pid),'-o','args='],capture_output=True,text=True)
 allowed=[str(R/'.local/native86-android/sdk/emulator/emulator'),str(R/'.local/native86-android/sdk/emulator/qemu/darwin-aarch64/qemu-system-aarch64-headless')]
 return os.getpgid(pid)==pid and any(q.stdout.strip()==a+' '+' '.join(argv[1:])for a in allowed)
env={**os.environ,'ANDROID_AVD_HOME':str(R/'.local/field02/avd'),'ANDROID_HOME':str(R/'.local/native86-android/sdk')}
argv=[str(R/'.local/native86-android/sdk/emulator/emulator'),'-avd','aeris-field02','-port','5582','-no-window','-accel','on','-gpu','host','-no-snapshot','-no-boot-anim','-camera-back','none','-camera-front','none','-memory','2048','-cores','4','-no-metrics']
stop=False
def halt(*_):
 global stop
 stop=True
for sig in [signal.SIGINT,signal.SIGTERM]:signal.signal(sig,halt)
log=(E/('emulator-console'+TAG+'.txt')).open('xb');p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);identity=stamp(p.pid);start=time.monotonic();reason=None
owner={'watcherPid':os.getpid(),'watcherStamp':stamp(os.getpid()),'pid':p.pid,'startTimeIdentity':identity,'argv':argv,'serial':'emulator-5582','physicalDevice':False,'maxSeconds':5400}
(E/('emulator-owner'+TAG+'.json')).open('x').write(json.dumps(owner,indent=2));print(json.dumps(owner),flush=True)
try:
 while not stop and p.poll()is None:
  if time.monotonic()-start>=5400:reason='OWNED90MIN_LIMIT';break
  if shutil.disk_usage(R).free<10*2**30+256*2**20:reason='FLOOR10_WITH_RESERVE';break
  if (E/('emulator-console'+TAG+'.txt')).stat().st_size>4*2**20:reason='CONSOLE4MIB';break
  time.sleep(.5)
finally:
 if p.poll()is None:
  if owned(p.pid,identity):p.terminate()
  else:reason='OWNED_IDENTITY_CHANGED_STOP_REFUSED'
 try:p.wait(timeout=25)
 except subprocess.TimeoutExpired:reason='OWNED_EXIT_UNCONFIRMED'
 log.flush();os.fsync(log.fileno());log.close()
 (E/('emulator-closure'+TAG+'.json')).open('x').write(json.dumps({'pid':p.pid,'exit':p.returncode,'reason':reason or'EXPLICIT_STOP_OR_CHILD_EXIT','execTransitionAware':True,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidenceRetained':True},indent=2))
