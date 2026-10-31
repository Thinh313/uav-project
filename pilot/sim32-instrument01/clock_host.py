import socket,struct,time,json,threading,os
class ClockObserver:
 def __init__(self,out):
  self.out=out;self.stop=threading.Event();self.error=None;self.rows=0
  self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def run(self):
  try:
   with (self.out/'clock-pairs.jsonl').open('x') as f,socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
    s.settimeout(.3);i=0
    while not self.stop.is_set():
     # Three independent exchanges/second, retain all including timeout; no flight retry.
     for _ in range(3):
      i+=1;a=time.monotonic_ns();s.sendto(struct.pack('<Q',i),('127.0.0.1',9004))
      try:
       data,addr=s.recvfrom(64);b=time.monotonic_ns();rid,g1,g2,usage,periods,throttles,throttled=struct.unpack('<7Q',data)
       if rid!=i or addr!=('127.0.0.1',9004):raise RuntimeError('Clock probe identity')
       row={'id':i,'hostSendNs':a,'hostReceiveNs':b,'guestReceiveNs':g1,'guestSendNs':g2,'offsetLowNs':a-g1,'offsetHighNs':b-g2,'cgroupUsageUs':usage,'cgroupPeriods':periods,'cgroupThrottles':throttles,'cgroupThrottledUs':throttled}
      except socket.timeout:row={'id':i,'hostSendNs':a,'status':'TIMEOUT'}
      f.write(json.dumps(row,separators=(',',':'))+'\n');self.rows+=1
     f.flush();self.stop.wait(1)
    f.flush();os.fsync(f.fileno())
  except Exception as e:self.error=str(e)
 def seal(self):
  self.stop.set();self.thread.join(3)
  if self.thread.is_alive()or self.error:raise RuntimeError('Clock observer failed '+str(self.error))
