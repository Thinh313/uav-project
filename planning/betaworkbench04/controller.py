from pathlib import Path
import subprocess,os,time,json,shutil,signal,socket,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/betaworkbench04';SDK=R/'.local/native86-android/sdk';W=R/'.local/field02';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
P=json.loads((R/'pilot/betaworkbench04/resource-policy.json').read_text());started=time.monotonic();children=[];handles=[];stopped=False
def put(n,d):
 with(E/n).open('x')as f:json.dump(d,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def stop(*_):
 global stopped
 stopped=True
def run():
 global stopped
 assert not(E/'controller-launch06.json').exists(),'NO_AUTOMATIC_RUNTIME_RETRY'
 samples=[]
 for i in range(31):
  t=time.monotonic();free=shutil.disk_usage(R).free;samples.append({'mono':t,'freeBytes':free});assert free>=P['admissionBytes'],'ADMISSION20';assert max(x['freeBytes']for x in samples)-free<=P['maxDeclineBytes'],'DISK_TREND'
  if i<30:time.sleep(1)
 put('controller-admission06.json',{'samples':samples,'policy':P,'durationS':samples[-1]['mono']-samples[0]['mono']})
 for port in[8895,8896,5582,5583,5984]:
  with socket.socket()as s:s.bind(('127.0.0.1',port))
 env={**os.environ,'ANDROID_AVD_HOME':str(W/'avd'),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
 commands=[['node','pilot/betaworkbench04/server.mjs','evidence/betaworkbench04/android06','--workspace','evidence/betaworkbench04/android04/session/workspace'],[str(SDK/'emulator/emulator'),'-avd','aeris-field02','-port','5582','-no-window','-accel','on','-gpu','host','-no-snapshot','-no-boot-anim','-no-audio','-camera-back','none','-camera-front','none','-memory','2048','-cores','4','-no-metrics']]
 for i,a in enumerate(commands):
  f=(E/('runtime06-'+str(i)+'-console.txt')).open('xb');handles.append(f);children.append(subprocess.Popen(a,cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True))
 put('controller-launch06.json',{'pid':os.getpid(),'children':[{'pid':p.pid,'argv':a}for p,a in zip(children,commands)],'policy':P,'startMono':started,'deadlineMono':started+2700});print('BETA04_LAUNCHED',flush=True)
 with(E/'controller-guard06.jsonl').open('x')as log:
  trail=[];logged=-1
  while not stopped and not(E/'stop-controller06.json').exists():
   t=time.monotonic();free=shutil.disk_usage(R).free;trail.append((t,free));trail=[x for x in trail if t-x[0]<=2];rate=max(0,(trail[0][1]-free)/max(.001,t-trail[0][0]));forecast=free-rate*15
   assert free>=P['hardFloorBytes']+P['writeReserveBytes'] and forecast>=P['hardFloorBytes']+P['writeReserveBytes'],'DISK10_OR_FORECAST_WITH_RESERVE'
   assert all(p.poll()is None for p in children),'OWNED_CHILD_EXIT';assert t<started+2700,'FINITE45MIN';assert all(f.tell()<4*2**20 for f in handles),'CONSOLE4MIB'
   files=[p for p in E.rglob('*')if p.is_file()];assert len(files)<5000 and sum(p.stat().st_size for p in files)<P['evidenceBudgetBytes'],'TASK1GIB'
   if t-logged>=1:log.write(json.dumps({'mono':t,'freeBytes':free,'forecastBytes':forecast,'children':[p.pid for p in children]})+'\n');log.flush();logged=t
   time.sleep(.25)
error=None
for sig in[signal.SIGTERM,signal.SIGINT]:signal.signal(sig,stop)
try:run()
except BaseException as e:error=str(e);print('CONTROLLER_ERROR '+repr(e),flush=True)
finally:
 for p in children:
  if p.poll()is None:p.send_signal(signal.SIGTERM)
 for p in children:
  try:p.wait(timeout=25)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=10)
 for f in handles:f.flush();os.fsync(f.fileno());f.close()
 if children:put('controller-closure06.json',{'error':error,'children':[{'pid':p.pid,'exit':p.returncode}for p in children],'freeBytes':shutil.disk_usage(R).free,'evidenceRetained':True,'noProductionSignature':True})
sys.exit(1 if error else 0)
