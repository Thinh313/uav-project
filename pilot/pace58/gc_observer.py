"""Diagnostic only: retain GC wall/CPU times, never disable or force collections."""
import gc,time,threading
class GCObserver:
 def __init__(self):self.frame=None;self.phase='runtime';self.open={};self.rows=[];self.overflow=False;gc.callbacks.append(self.callback)
 def callback(self,phase,info):
  t=threading.get_ident()
  if phase=='start':self.open[t]=(time.monotonic_ns(),time.thread_time_ns(),self.frame,self.phase,info['generation'])
  elif t in self.open:
   start=self.open.pop(t)
   if len(self.rows)<10000:self.rows.append({'thread':t,'frameAtStart':start[2],'phase':start[3],'generation':start[4],'startNs':start[0],'endNs':time.monotonic_ns(),'wallNs':time.monotonic_ns()-start[0],'cpuNs':time.thread_time_ns()-start[1],'collected':info.get('collected'),'uncollectable':info.get('uncollectable')})
   else:self.overflow=True
 def seal(self):gc.callbacks.remove(self.callback);return{'events':self.rows,'overflow':self.overflow,'forcedCollections':0,'disabledGC':False}
