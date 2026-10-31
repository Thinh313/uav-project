"""Owned loopback JSON backend. Strict frame clock; renderer is never a physics source."""
from pathlib import Path
import socket,struct,json,time,gzip,hashlib,os,sys,shutil,signal,datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'pilot/sim32'))
if sys.platform=='linux':sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'runtime/sim32-pipe03-build/native'))
from physics import Model,profile
from guarded_journal import Journal
from stage_trace import StageTrace
from clock_host import ClockObserver
from epoch import Epoch
import importlib.util
R=Path(__file__).resolve().parents[2]
def main():
 run,load,wind=sys.argv[1:4]
 if not run.isalnum()or len(run)>32:raise ValueError('Run ID')
 engine=os.environ.get('SIM32_ENGINE','optimized')
 if engine not in ['baseline','optimized','fused']:raise ValueError('Engine allowlist')
 model_class=Model
 if engine=='baseline':
  spec=importlib.util.spec_from_file_location('sim32_perf_reference',R/'evidence/sim32/source-final/pilot/sim32/physics.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref);model_class=ref.Model
 if engine=='fused':
  sys.path.insert(0,str(R/'runtime/sim32-pipe03-build/host-native'));from fast_physics import Model as FusedModel;model_class=FusedModel
 state=R/'.local/sim32-pipe03'/run;out=R/'evidence/sim32-pipe03/runs'/run
 if out.exists():raise ValueError('Evidence ID exists')
 assert shutil.disk_usage(R).free>20*1024**3+640*1024**2
 out.mkdir(parents=True);state.mkdir(parents=True,exist_ok=True);p=profile(load,wind);(out/'profile.json').write_text(json.dumps(p,indent=2)+'\n');model=model_class(p);sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.bind(('127.0.0.1',9002));sock.settimeout(.5)
 if engine!='baseline':
  sock.setblocking(True);sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVTIMEO,struct.pack('@ll',0,500000))
 data=None;peer=None;frame=None;last=None;total=0;dups=0;rawbytes=0;started=time.monotonic();last_at=started;stop=False;minimum=shutil.disk_usage(R).free;times=[];digest=hashlib.sha256();status='RUNNING_NOT_FINAL';error=None;written=0;packet_times=[];first_ns=None;last_ns=None;first_rate=None
 shutdown=None;epoch=None;phase='startup';row=None
 def terminate(*a):
  nonlocal stop,shutdown;stop=True
  if shutdown is None:
   shutdown={'signal':a[0]if a else None,'atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':phase,'frameCounterAtSignal':frame,'modelFrameCounterAtSignal':total,'finishAlreadyAdmittedFrame':phase in ['admitted','computing','committing']}
   if epoch is not None and not epoch.terminal:
    try:epoch.drain()
    except Exception:pass
 signal.signal(signal.SIGTERM,terminate);signal.signal(signal.SIGINT,terminate)
 (out/'backend-identity.json').write_text(json.dumps({'pid':os.getpid(),'run':run,'bind':'127.0.0.1:9002','platform':sys.platform,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n');print('BACKEND_READY',run,flush=True)
 epoch=Epoch(state,out,run);domain='guest-python-monotonic' if sys.platform=='linux' else 'host-python-monotonic'
 journal=None;stage=None;clock=None;instrument=os.environ.get("AERIS_INSTRUMENT","0")=="1"
 try:
  journal=Journal(out,state,engine!='baseline');clock=ClockObserver(out,run,epoch.id)
  if instrument:stage=StageTrace(out/'backend-stages.bin')
  pause_at=int(os.environ['SIM32_TEST_PAUSE_AT_FRAME']) if 'SIM32_TEST_PAUSE_AT_FRAME'in os.environ else None
  while not stop:
   phase='waiting';row=None
   epoch.check()
   journal.check()
   if clock.error:epoch.invalidate('CLOCK_OBSERVER_FAILED',clockError=clock.error)
   if time.monotonic()-started>300:raise RuntimeError('Owned maximum lifetime300s reached')
   try:
    rx_begin=time.monotonic_ns();data,address=sock.recvfrom(1024)
   except (socket.timeout,BlockingIOError):
    epoch.check()
    continue
   epoch.check()
   if stop:
    (out/'shutdown-pending-servo.json').write_text(json.dumps({'run':run,'epoch':epoch.id,'rawHex':data.hex(),'peer':address,'reason':'UNADMITTED_DATAGRAM_AT_OWNED_SHUTDOWN','noModelStep':True})+'\n');break
   now=time.monotonic_ns();packet_started=time.perf_counter_ns()
   if len(data)!=40 or struct.unpack_from('<H',data)[0]!=18458:raise RuntimeError('Unsupported JSON servo packet')
   magic,rate,count,*pwm=struct.unpack('<HHI16H',data)
   if not 400<=rate<=2000:
    (out/'rejected-servo.json').write_text(json.dumps({'hex':data.hex(),'rate':rate,'frame':count,'peer':address},indent=2)+'\n');raise RuntimeError('Frame rate outside supported400..2000Hz')
   if peer is None:peer=address;first_rate=rate
   if rate!=first_rate:raise RuntimeError('Frame rate changed within run')
   if address!=peer:raise RuntimeError('Foreign UDP endpoint')
   if frame is not None and count==frame:
    dups+=1;(out/'rejected-servo.json').write_text(json.dumps({'hex':data.hex(),'rate':rate,'frame':count,'peer':address,'reason':'DUPLICATE_NO_SENSOR_ECHO'})+'\n');epoch.invalidate('DUPLICATE_FRAME_NO_REPLAY',frame=count)
   if frame is not None and count!=frame+1:epoch.invalidate('FRAME_GAP_OR_REGRESSION',frame=count,previous=frame)
   phase='admitted'
   if pause_at is not None and count==pause_at:
    (out/'pause-ready.json').write_text(json.dumps({'run':run,'pid':os.getpid(),'framePending':count,'committedFrames':total,'epoch':epoch.id})+'\n');pause_at=None;os.kill(os.getpid(),signal.SIGSTOP)
   if first_ns is None:first_ns=now
   last_ns=now
   epoch.check()
   phase='computing'
   step_begin=time.monotonic_ns();a=time.perf_counter_ns();sensors=model.step(pwm,1/rate);cost=(time.perf_counter_ns()-a)/1e6;step_end=time.monotonic_ns();last=('\n'+json.dumps(sensors,separators=(',',':'),allow_nan=False)+'\n').encode();serialized=time.monotonic_ns()
   try:
    epoch.check()
    if clock.error:epoch.invalidate('CLOCK_OBSERVER_FAILED',clockError=clock.error)
   except Exception:
    (out/'aborted-step.json').write_text(json.dumps({'frame':count,'rate':rate,'servoHex':data.hex(),'sensorUtf8':last.decode(),'epoch':epoch.id,'modelStepComputed':True,'sensorSent':False,'reason':epoch.reason})+'\n');raise
   phase='committing'
   times.append(cost);frame=count;total+=1;sock.sendto(last,peer);sent=time.monotonic_ns();last_at=time.monotonic()
   row={'frame':count,'rate':rate,'hostMonotonicNs':now,'clockDomain':domain,'epoch':epoch.id,'sensorSent':True,'stepCostMs':cost,'servoHex':data.hex(),'sensorUtf8':last.decode(),'modelAux':{'rpmEstimated':[v*model.p['rotorMaximumRpm']*(model.voltage/25.2)for v in model.u],'energyWhEstimated':model.energyWh,'ground':model.ground}}
   snapshot=None
   if total%20==0:
    snapshot={**model.snapshot(),'frame':frame,'rateHz':rate,'receivedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostMonotonicNs':now,'clockDomain':domain,'epoch':epoch.id,'run':run,'source':'ACTUAL_SITL_SERVO_TO_PROVISIONAL_PHYSICS','duplicatePackets':dups}
   enqueue_begin=time.monotonic_ns();journal.submit(row,snapshot);enqueued=time.monotonic_ns()
   if total%400==0:
    free=shutil.disk_usage(R).free;minimum=min(minimum,free)
    if free<20*1024**3+768*1024**2:raise RuntimeError('Resource headroom lost; stopping owned physics')
   packet_end=time.monotonic_ns();packet_times.append((time.perf_counter_ns()-packet_started)/1e6)
   if stage:stage.record((count,rx_begin,now,step_begin,step_end,serialized,sent,enqueue_begin,enqueued,packet_end))
   epoch.progress()
  status='STOPPED_EXPLICITLY_NOT_FLIGHT_ACCEPTANCE'
  if shutdown:(out/'shutdown.json').write_text(json.dumps({**shutdown,'finalCommittedFrame':frame,'finalFrames':total,'noNewFrameAdmittedAfterStop':True},indent=2)+'\n')
 except Exception as e:
  status='FAILED';error=str(e)
  if row is not None and journal is not None:journal.rescue_unsubmitted(row)
  if data is not None and epoch.terminal and not (out/'rejected-servo.json').exists():
   (out/'rejected-servo.json').write_text(json.dumps({'hex':data.hex(),'reason':epoch.reason,'modelCommittedFrames':total,'sensorReplay':False})+'\n')
  if not epoch.terminal:
   try:epoch.invalidate('BACKEND_FAILURE',error=error)
   except RuntimeError:pass
  print(error,file=sys.stderr,flush=True)
 finally:
  sock.close();epoch.close()
  try:
   if stage:stage.seal()
   if clock:clock.seal()
  except Exception as e:status="FAILED";error="Observer: "+str(e)
  try:
   if journal is None:raise RuntimeError('Journal never started')
   journal.seal()
   if journal.rows!=total:raise RuntimeError('Journal count mismatch: incomplete evidence')
  except Exception as e:status='FAILED';error=str(e)
  if journal is not None:rawbytes=journal.bytes;written=journal.snapshots;digest=journal.digest
  s=sorted(times);percent=lambda q:s[min(len(s)-1,int((len(s)-1)*q))]if s else None
  import resource
  packet_sorted=sorted(packet_times);quantile=lambda q:packet_sorted[min(len(packet_sorted)-1,int((len(packet_sorted)-1)*q))]if packet_sorted else None
  active_wall=(last_ns-first_ns)/1e9 if first_ns is not None and last_ns!=first_ns else None
  report={'epoch':epoch.id,'epochTerminal':epoch.terminal,'epochReason':epoch.reason,'clockDomain':domain,'platform':sys.platform,'instrumented':instrument,'backendStageRows':stage.n if stage else None,'clockRows':clock.rows if clock else None,'engine':engine,'modelKernel':'strict-fused-RK4-host' if engine=='fused' else 'native-float64-cpython314' if engine=='optimized' else 'python-reference','receiveMode':'blocking-native-timeout' if engine!='baseline' else 'python-select-timeout','journal':({'mode':'bounded-worker' if journal.threaded else 'inline-reference','rows':journal.rows,'queueCapacity':256,'queueHighwater':journal.highwater,'quotaUncompressedBytes':journal.raw_limit,'quotaCompressedBytes':journal.compressed_limit,'salvagedRows':len(journal.rescue),'queueRemaining':journal.queue.qsize(),'error':journal.error,'sealed':error is None,'writeCostMs':{'samples':len(journal.costs),'p50':sorted(journal.costs)[int((len(journal.costs)-1)*.5)] if journal.costs else None,'p95':sorted(journal.costs)[int((len(journal.costs)-1)*.95)] if journal.costs else None,'p99':sorted(journal.costs)[int((len(journal.costs)-1)*.99)] if journal.costs else None,'max':max(journal.costs) if journal.costs else None}} if journal else {'error':'never started','sealed':False}),'packetProcessingMs':{'p50':quantile(.5),'p95':quantile(.95),'p99':quantile(.99),'max':max(packet_times)if packet_times else None,'samples':len(packet_times),'overFramePeriod':sum(v>1000/first_rate for v in packet_times)if first_rate else 0},'activeWireWallSeconds':active_wall,'activeRealTimeFactor':((total-1)/first_rate)/active_wall if active_wall else None,'hostBackendPeakRssBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform=='linux' else 1),'status':status,'error':error,'frames':total,'duplicates':dups,'rawUncompressedBytes':rawbytes,'rawSha256':digest.hexdigest(),'modelSeconds':model.t,'wallSeconds':time.monotonic()-started,'stepCostMs':{'p50':percent(.5),'p95':percent(.95),'p99':percent(.99),'max':max(s)if s else None},'minimumFreeBytes':minimum,'snapshotWrites':written,'scope':'Provisional physics driven by actual pinned AP servo packets; not physical calibration'};(out/'backend-summary.json').write_text(json.dumps(report,indent=2)+'\n')
 if error:raise SystemExit(1)
if __name__=='__main__':main()
