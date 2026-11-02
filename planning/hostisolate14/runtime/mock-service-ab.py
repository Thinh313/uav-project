"""Controlled QA process experiment, not ArduPilot/Android or pmset evidence.

Inject the same 250ms CPython-GIL-holding native call in serving process versus
its owned child. A separate process sends one read-only socket request per trial.
No production flag, altered guard, SDK, package build or flight command exists.
"""
import ctypes,json,os,socket,subprocess,sys,threading,time
DEADLINE=.1;BLOCK_US=250000

def blocking():
 # PyDLL deliberately retains the CPython GIL. This is a synthetic scheduler
 # adversary, not a claim that the measured original pmset used this exact path.
 libc=ctypes.PyDLL(None);fn=libc.usleep;fn.argtypes=[ctypes.c_uint];fn.restype=ctypes.c_int
 n=time.monotonic_ns();print(json.dumps({'event':'BLOCK_START','pid':os.getpid(),'hostNs':n}),flush=True);fn(BLOCK_US)
 print(json.dumps({'event':'BLOCK_END','pid':os.getpid(),'hostNs':time.monotonic_ns()}),flush=True)
def server(mode):
 listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(1);stop=threading.Event();rows=[]
 def serve():
  try:
   connection,_=listener.accept()
   with connection:
    connection.settimeout(.1);request=connection.recv(32);n=time.monotonic_ns();connection.sendall(b'STATUS_ONLY\n');rows.append({'serverPID':os.getpid(),'serverReceivedNs':n,'requestHex':request.hex(),'serverSentNs':time.monotonic_ns()})
  except BaseException as e:rows.append({'serverError':type(e).__name__+':'+str(e)})
  finally:stop.set()
 t=threading.Thread(target=serve);t.start();print(json.dumps({'event':'READY','port':listener.getsockname()[1],'pid':os.getpid()}),flush=True);helper=None
 try:
  if mode=='inline':blocking()
  else:
   helper=subprocess.Popen([sys.executable,'-B',__file__,'--block'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   start=helper.stdout.readline();print(start.strip(),flush=True);end,err=helper.communicate(timeout=2)
   if helper.returncode or err:raise RuntimeError('MOCK_HELPER_FAILURE:'+err[:256])
   print(end.strip(),flush=True)
  t.join(2)
  if t.is_alive():raise RuntimeError('MOCK_SERVER_THREAD_DID_NOT_CLOSE')
  print(json.dumps({'event':'CLOSED','pid':os.getpid(),'helperPID':None if helper is None else helper.pid,'helperExit':None if helper is None else helper.returncode,'rows':rows}),flush=True)
 finally:
  listener.close()
  if helper is not None and helper.poll()is None:helper.kill();helper.wait(timeout=2)
def run():
 rows=[]
 for mode in('inline','isolated'):
  for trial in range(3):
   p=subprocess.Popen([sys.executable,'-B',__file__,'--server',mode],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);prefix=[]
   try:
    ready=p.stdout.readline();prefix.append(ready);q=json.loads(ready);start=p.stdout.readline();prefix.append(start);block=json.loads(start)
    begun=time.monotonic_ns();reply=b'';error=None
    try:
     with socket.socket()as s:
      s.settimeout(DEADLINE);s.connect(('127.0.0.1',q['port']));s.sendall(b'STATUS_ONLY\n');reply=s.recv(64)
    except BaseException as e:error=type(e).__name__+':'+str(e)
    ended=time.monotonic_ns();out,err=p.communicate(timeout=3);raw=''.join(prefix)+out
    if p.returncode or err or len(raw)>4096:raise RuntimeError('MOCK_PROCESS_OR_CAPTURE_FAILED:'+err[:256])
    samples=[json.loads(v)for v in raw.splitlines()];closed=samples[-1]
    if closed['event']!='CLOSED':raise RuntimeError('MOCK_CLOSE_NOT_OBSERVED')
    ok=error is None and reply==b'STATUS_ONLY\n'and ended-begun<=100000000
    rows.append({'mode':mode,'trial':trial+1,'clientPID':os.getpid(),'serverPID':q['pid'],'blockerPID':block['pid'],'requestStartNs':begun,'finishedNs':ended,'elapsedNs':ended-begun,'error':error,'responseHex':reply.hex(),'guard100msAccepted':ok,'originalProcessRows':samples,'stdoutCaptureComplete':True,'stderrHex':err.encode().hex(),'exit':p.returncode})
   finally:
    if p.poll()is None:p.kill();p.wait(timeout=2)
    p.stdout.close();p.stderr.close()
 result={'format':'aeris-controlled-power-isolation-mock-ab','version':1,'scope':'SYNTHETIC_GIL_BLOCKING_INJECTION_NOT_PMSET_OR_ANDROID_SITL_ROOT_CAUSE_PROOF','input':'one STATUS_ONLY request per trial;250ms native GIL hold','sameBlockingDurationUs':BLOCK_US,'unchangedGuardNs':100000000,'rows':rows,'inlineAccepted':sum(r['guard100msAccepted']for r in rows if r['mode']=='inline'),'isolatedAccepted':sum(r['guard100msAccepted']for r in rows if r['mode']=='isolated'),'realPMSetCauseProven':False,'runtimePerformanceClaim':False}
 print(json.dumps(result,separators=(',',':')))
 if result['inlineAccepted']!=0 or result['isolatedAccepted']!=3:raise SystemExit(1)
if __name__=='__main__':
 if len(sys.argv)==2 and sys.argv[1]=='--block':blocking()
 elif len(sys.argv)==3 and sys.argv[1]=='--server':server(sys.argv[2])
 elif len(sys.argv)==1:run()
 else:raise SystemExit(2)
