"""Standalone loopback servo mock only. Cannot launch or send to ArduPilot."""
from pathlib import Path
import sys,json,os,signal,socket,struct,time,hashlib,shutil,errno
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'pilot/sim32'),str(R/'pilot/sim32-pipe03'),str(R/'runtime/sim32-pipe03-build/host-native')]
from fast_physics import Model,profile
from epoch import Epoch
from wal_journal import Journal,encode

class Fault:
 def __init__(self,out,config):self.out,self.c=out,config;self.once=set();self.events=(out/'phase-events.jsonl').open('x')
 def point(self,name,frame):
  self.events.write(json.dumps({'phase':name,'frame':frame,'ns':time.monotonic_ns(),'domain':'mock-backend-python-monotonic'})+'\n');self.events.flush()
  if self.c.get('pausePhase')==name and frame==self.c.get('pauseFrame',3)and name not in self.once:
   self.once.add(name);(self.out/'paused.json').write_bytes(encode({'pid':os.getpid(),'phase':name,'frame':frame,'domain':'mock-backend-python-monotonic'}));os.kill(os.getpid(),signal.SIGSTOP)
 def io(self,stage,kind,frame,fd,data):
  name=self.c.get('fault');target=self.c.get('faultFrame',3)
  if stage=='archive-before-write'and name in ['archive-stall','queue-full']and frame==0:
   (self.out/'writer-blocked.json').write_bytes(encode({'frame':frame,'fault':name}));time.sleep(30)
  if stage=='compressed-write'and name in ['compressed-short','compressed-partial']and frame>=target and len(data)>10 and 'compressed-fault'not in self.once:
   self.once.add('compressed-fault');n=os.write(fd,data[:max(1,len(data)//2)])
   if name=='compressed-partial':raise OSError(errno.EIO,'Injected compressed stream partial write')
   return n
  if frame!=target and stage!='archive-close'and stage!='archive-flush':return None
  if name=='wal-short'and stage=='wal-write'and kind=='INTENT'and 'short'not in self.once:
   self.once.add('short');return os.write(fd,data[:max(1,len(data)//2)])
  if name=='wal-enospc'and stage=='wal-write'and kind=='INTENT':
   if 'partial'not in self.once:self.once.add('partial');return os.write(fd,data[:max(1,len(data)//2)])
   raise OSError(errno.ENOSPC,'Injected primary WAL ENOSPC after partial write')
  if name=='wal-zero'and stage=='wal-write'and kind=='INTENT':return 0
  if name=='wal-flush'and stage=='wal-flush'and kind=='INTENT':raise OSError(errno.EIO,'Injected intent flush failure')
  if name=='wal-commit'and stage=='wal-write'and kind=='SENT':raise OSError(errno.EIO,'Injected send-marker write failure')
  if name=='archive-write'and stage=='archive-write':raise OSError(errno.ENOSPC,'Injected archive ENOSPC')
  if name=='snapshot'and stage=='snapshot-write':raise OSError(errno.EIO,'Injected snapshot failure')
  if name=='archive-close'and stage=='archive-close':raise OSError(errno.EIO,'Injected archive close failure')
  if name=='archive-flush'and stage=='archive-flush':raise OSError(errno.EIO,'Injected archive fsync failure')
  return None

def main():
 out=Path(sys.argv[1]).resolve();assert out.parent==R/'evidence/sim32-journal04/cases'
 c=json.loads((out/'config.json').read_text());assert c['scope']=='MOCK_ONLY_NO_SITL'
 assert shutil.disk_usage(R).free>20*2**30+768*2**20
 state=out/'state';state.mkdir();p=profile('offset','gust');(out/'profile.json').write_bytes(encode(p));m=Model(p);epoch=Epoch(state,out,out.name);fault=Fault(out,c);stop=False;signals=0;error=None;phase='waiting';raw=None;frame=None;previous=None;rx_seq=None;prepared=None;reserved=False;wire_started=False;wire_marked=False;computed=0;wire_returns=0;step_ns=[];encode_ns=[]
 def request_stop(*args):
  nonlocal stop,signals;stop=True;signals+=1
 signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGINT,request_stop)
 j=Journal(out,state,{'run':out.name,'epoch':epoch.id,'source':'MOCK_REFERENCE_PHYSICS_NOT_SITL','counterDomain':'mock-backend-python-monotonic','profile':p},policy=c.get('policy','fsync-before-publish'),raw_limit=c.get('rawLimit',4*2**20),compressed_limit=c.get('compressedLimit',4*2**20),wal_limit=c.get('walLimit',16*2**20),seal_seconds=.2,hook=fault.io)
 sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.bind(('127.0.0.1',0));sock.settimeout(.1);peer=None
 (out/'ready.json').write_bytes(encode({'pid':os.getpid(),'port':sock.getsockname()[1],'run':out.name,'source':'MOCK_ONLY_NO_SITL'}))
 def checkpoint(name,number):
  nonlocal phase
  phase=name;fault.point(name,number)
  if stop and not epoch.draining and not epoch.terminal:epoch.drain()
  epoch.check()
 try:
  while not stop:
   raw=None;prepared=None;reserved=False;wire_started=False;wire_marked=False;phase='waiting';j.check();epoch.check()
   try:raw,ancillary,flags,address=sock.recvmsg(8192)
   except socket.timeout:continue
   frame=struct.unpack_from('<I',raw,4)[0]if len(raw)>=8 else 0xffffffff
   received=time.monotonic_ns();rx_seq=j.receive(frame,raw,address);checkpoint('received',frame)
   if stop:
    j.wal.append('ERROR',frame,encode({'rxSeq':rx_seq,'reason':'UNADMITTED_AT_MANAGED_STOP','modelAdmitted':False}));break
   if flags&socket.MSG_TRUNC or len(raw)!=40:raise RuntimeError('Malformed/truncated mock input')
   magic,rate,count,*pwm=struct.unpack('<HHI16H',raw)
   if magic!=18458 or rate!=1200:raise RuntimeError('Mock servo format/rate')
   if peer is None:peer=address
   if peer!=address:raise RuntimeError('Foreign mock peer')
   if previous is None and count!=0:epoch.invalidate('FRAME_START_NOT_ZERO',frame=count)
   if previous is not None and count!=previous+1:epoch.invalidate('FRAME_DUPLICATE_GAP_OR_REGRESSION',frame=count,previous=previous)
   checkpoint('validated',count)
   mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGTERM,signal.SIGINT})
   try:
    if stop:
     j.wal.append('ERROR',count,encode({'rxSeq':rx_seq,'reason':'UNADMITTED_AT_MANAGED_STOP','modelAdmitted':False}));break
    j.reserve(count);reserved=True;phase='admitted'
   finally:signal.pthread_sigmask(signal.SIG_SETMASK,mask)
   checkpoint('admitted',count);a=time.perf_counter_ns();sensors=m.step(pwm,1/rate);step_ns.append(time.perf_counter_ns()-a);computed+=1;checkpoint('computed',count)
   a=time.perf_counter_ns();sensor=('\n'+json.dumps(sensors,separators=(',',':'),allow_nan=False)+'\n').encode();encode_ns.append(time.perf_counter_ns()-a)
   row={'frame':count,'rate':rate,'rxSeq':rx_seq,'epoch':epoch.id,'source':'MOCK_REFERENCE_PHYSICS_NOT_SITL','clockDomain':'mock-backend-python-monotonic','hostReceiveNs':received,'servoHex':raw.hex(),'sensorUtf8':sensor.decode(),'modelAux':{k:m.snapshot()[k]for k in ['rpmEstimated','energyWhEstimated','ground']}}
   snapshot={**m.snapshot(),'frame':count,'epoch':epoch.id,'source':'MOCK_REFERENCE_PHYSICS_NOT_SITL'}
   prepared=j.prepare(row,snapshot);checkpoint('intent',count);j.check();epoch.check();wire_started=True
   if c.get('fault')=='send-error'and count==c.get('faultFrame',3):raise OSError(errno.ENOBUFS,'Injected send call exception; no real send executed')
   if c.get('fault')=='send-short'and count==c.get('faultFrame',3):returned=len(sensor)-1
   else:returned=sock.sendto(sensor,peer)
   wire_returns+=1;checkpoint('wire',count);j.transmitted(prepared,returned,len(sensor));wire_marked=True;checkpoint('committed',count);previous=count;epoch.progress()
   if shutil.disk_usage(R).free<20*2**30+768*2**20:raise RuntimeError('Resource reserve lost')
 except Exception as e:
  error=str(e);j.fail(error)
  if reserved and not wire_started:j.aborted(frame,error)
  elif reserved and wire_started and not wire_marked and not j.wal.failed:
   try:j.wal.append('OUTCOME',frame,encode({'intentSeq':prepared.intent_seq if prepared else None,'outcome':'SEND_RESULT_UNCERTAIN','reason':error}));j.release(frame)
   except Exception as tail:j.fail(tail)
  if raw is not None and not reserved and not j.wal.failed:
   try:j.wal.append('ERROR',frame,encode({'rxSeq':rx_seq,'reason':error,'modelAdmitted':False}))
   except Exception as tail:j.fail(tail)
  if not epoch.terminal:
   try:epoch.invalidate('MOCK_BACKEND_FAILURE',error=error)
   except RuntimeError:pass
 finally:
  sock.close()
  try:fault.point('seal',0);result=j.seal()
  except Exception as e:result={'status':'INCOMPLETE_CAPTURE','error':str(e),'workerAlive':j.worker.is_alive()}
  epoch.close();fault.events.close()
  (out/'summary.json').write_bytes(encode({'source':'MOCK_ONLY_NO_SITL','status':result['status']if not error else'INCOMPLETE_CAPTURE','error':error,'journalResult':result,'phase':phase,'signals':signals,'computed':computed,'localSendReturns':wire_returns,'sentMarkers':len(j.sent),'archiveRows':j.rows,'queueHighwater':j.highwater,'queueCapacity':j.capacity,'epochTerminal':epoch.terminal,'epochReason':epoch.reason,'rowEncodingNs':encode_ns,'modelStepNs':step_ns,'walAppendNs':j.wal.append_cost,'walFlushNs':j.wal.flush_cost,'minimumResourceAdmissionFreeBytes':shutil.disk_usage(R).free}))
 if error or result['status']!='COMPLETE_ACCEPTED_MOCK_CAPTURE':return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
