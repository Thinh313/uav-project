"""One owned loopback host. No automatic AP start, ARM, retries or lock recovery."""
import argparse,datetime,json,os,signal,socket,subprocess,sys,time,uuid
from pathlib import Path
from support import ROOT,E,CONTROL,LOCK,now,stamp,put,disk,usage,budget,doctor,UTC

def owned(p,ident):return p.poll()is None and stamp(p.pid)==ident and os.getpgid(p.pid)==p.pid

def run(ack):
 if not ack:raise RuntimeError('EXPLICIT_ACK_SIMULATION_REQUIRED')
 if LOCK.exists():raise RuntimeError('OWNER_LOCK_EXISTS_NO_AUTOMATIC_DELETE')
 bp,b,recipient=budget(True)
 info=doctor()
 if info['status']!='PASS':print(json.dumps(info,indent=2));return 2
 wallStop=datetime.datetime.fromisoformat(b['runtimeStopUTC']);remaining=(wallStop-now()).total_seconds();monoStop=time.monotonic()+remaining
 E.mkdir(parents=True,exist_ok=True)
 if len(list(E.glob('host-*/launch.json')))>=6:raise RuntimeError('MAX6_HOST_STARTS')
 for port in [8896,5984]:
  with socket.socket()as s:s.bind(('127.0.0.1',port))
 CONTROL.mkdir(parents=True,exist_ok=True);LOCK.mkdir();out=E/('host-'+now().strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);out.mkdir();owner={'pid':os.getpid(),'processStamp':stamp(os.getpid()),'out':str(out),'budget':str(bp),'recipient':recipient};put(LOCK/'owner.json',owner);put(out/'owner.json',owner);put(out/'doctor.json',info)
 child=None;childStamp=None;stop=False;reason=None;error=None;log=None
 def halt(*_):
  nonlocal stop
  stop=True
 for sig in[signal.SIGINT,signal.SIGTERM]:signal.signal(sig,halt)
 try:
  samples=[]
  for i in range(31):
   if stop:raise RuntimeError('OPERATOR_STOP_DURING_ADMISSION')
   free=disk(True);samples.append({'mono':time.monotonic(),'freeBytes':free})
   if max(s['freeBytes']for s in samples)-free>256*2**20:raise RuntimeError('DISK_DECLINE256MIB')
   if now()>=wallStop-datetime.timedelta(seconds=60)or time.monotonic()>=monoStop-60:raise RuntimeError('DEADLINE_BEFORE_LAUNCH')
   if i<30:time.sleep(1)
  put(out/'admission.json',{'samples':samples,'budget':b,'policy':'20_10_RESERVE256_TREND256_FORECAST15'})
  argv=['node','pilot/simhand01/server.mjs','--out',str(out/'gateway')];log=(out/'host-console.txt').open('xb');env={**os.environ,'AERIS_SIMHAND_BUDGET_PATH':str(bp),'AERIS_SIMHAND_RECIPIENT':'1'if recipient else'0','PYTHONDONTWRITEBYTECODE':'1'}
  child=subprocess.Popen(argv,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);childStamp=stamp(child.pid);put(out/'launch.json',{'argv':argv,'pid':child.pid,'processStamp':childStamp,'budget':str(bp),'wallRuntimeStop':wallStop.isoformat(),'monoRuntimeStop':monoStop,'closureReserveSeconds':30,'recipient':recipient,'automaticAPStart':False})
  print('AERIS SIM started: phone http://127.0.0.1:8896/phone | observer http://127.0.0.1:8896/observer',flush=True);trail=[];nextUsage=0
  while not stop:
   t=time.monotonic();free=disk();trail.append((t,free));trail=[v for v in trail if t-v[0]<=2];rate=max(0,(trail[0][1]-free)/max(.001,t-trail[0][0]));
   if free-rate*15<10*2**30+256*2**20:raise RuntimeError('DISK_FORECAST15_FLOOR10_RESERVE256')
   if child.poll()is not None:raise RuntimeError('OWNED_HOST_EXIT:'+str(child.returncode))
   if (out/'host-console.txt').stat().st_size>4*2**20:raise RuntimeError('HOST_CONSOLE4MIB')
   if t>=nextUsage:usage();nextUsage=t+15
   if now()>=wallStop-datetime.timedelta(seconds=30)or t>=monoStop-30:reason='HARD_STOP_WITH30S_CLOSURE_RESERVE';break
   time.sleep(.1)
  reason=reason or'EXPLICIT_OPERATOR_STOP'
 except BaseException as e:error=repr(e);reason=reason or'GUARD_FAILURE'
 finally:
  if child is not None and owned(child,childStamp):child.send_signal(signal.SIGTERM)
  if child is not None:
   try:child.wait(timeout=max(.1,min(25,(wallStop-now()).total_seconds())))
   except subprocess.TimeoutExpired:
    error=error or'OWNED_HOST_CLOSURE_UNKNOWN'
    if owned(child,childStamp):os.killpg(child.pid,signal.SIGTERM)
   if child.poll()is None:error=error or'RUNTIME_STOP_UNCONFIRMED_AT_HARD_DEADLINE'
  if log:log.flush();os.fsync(log.fileno());log.close()
  put(out/'launcher-closure.json',{'reason':reason,'error':error,'hostPid':child.pid if child else None,'hostExit':child.returncode if child else None,'deadline':wallStop.isoformat(),'atUTC':now().isoformat(),'authorityRestored':False,'evidenceRetained':True,'productAcceptance':'NOT_INFERRED_FROM_EXIT_CODE'})
  if(child is None or child.returncode is not None)and json.loads((LOCK/'owner.json').read_text())==owner:(LOCK/'owner.json').unlink();LOCK.rmdir()
 if error:raise RuntimeError(error)
 return 0

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['doctor','start','status','stop']);p.add_argument('--ack-simulation',action='store_true');a=p.parse_args()
 if a.action=='doctor':q=doctor();print(json.dumps(q,indent=2));return 0 if q['status']=='PASS'else 2
 if a.action=='start':return run(a.ack_simulation)
 if not LOCK.exists():print(json.dumps({'state':'STOPPED','automaticResume':False}));return 0
 q=json.loads((LOCK/'owner.json').read_text());q['liveIdentityMatches']=stamp(q['pid'])==q['processStamp'];print(json.dumps(q,indent=2))
 if a.action=='stop':
  if not q['liveIdentityMatches']:raise RuntimeError('STALE_OWNER_REFUSED_NO_LOCK_DELETE')
  os.kill(q['pid'],signal.SIGTERM)
 return 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print('AERIS SIM:',str(e),file=sys.stderr);sys.exit(2)
