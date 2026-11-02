"""Bounded parent-owned metadata stdout/stderr, independent of AP authority."""
import os,selectors,threading
from .metadata_budget import BoundedCapture
class OwnedOutput:
 def __init__(self,budget,owner,process,paths,*,maximum_each=500*1024,lease=None):
  self.lease=lease;self.released=False;self.budget=budget;self.owner=owner;self.process=process;self.paths=paths;self.maximum=maximum_each;self.failure=None;self.eof=set();self.done=threading.Event();self.captures={}
  if lease is None:raise ValueError('OWNED_OUTPUT_PREDISPATCH_LEASE_REQUIRED')
  with budget.use_lease(lease):self.captures={name:BoundedCapture(budget,owner,path,maximum_each)for name,path in paths.items()}
  self.thread=threading.Thread(target=self._pump,name='aeris-owned-output',daemon=True);self.thread.start()
 def _pump(self):
  with self.budget.use_lease(self.lease):return self._pump_reserved()
 def _pump_reserved(self):
  selector=None
  try:
   selector=selectors.DefaultSelector()
   for name in self.paths:
    stream=getattr(self.process,name)
    if stream is None:raise ValueError('OWNED_OUTPUT_PIPE_REQUIRED')
    os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,name)
   while selector.get_map():
    for key,_ in selector.select(.05):
     raw=os.read(key.fileobj.fileno(),65536)
     if not raw:self.eof.add(key.data);selector.unregister(key.fileobj);continue
     self.captures[key.data].feed(raw)
  except BaseException as e:
   self.failure=type(e).__name__+':'+str(e)
   try:self.budget.failure(e,detail={'owner':self.owner,'captureIncomplete':True,'childOwnershipRetained':True})
   except BaseException:pass
  finally:
   operations=([('selector',selector.close)]if selector is not None else[])+[(name,getattr(self.process,name).close)for name in self.paths]
   for name,operation in operations:
    try:operation()
    except BaseException as close_error:
     secondary='CLOSE_SECONDARY:'+name+':'+type(close_error).__name__+':'+str(close_error)[:256]
     self.failure=secondary if self.failure is None else self.failure+';'+secondary
   self.done.set()
 def check(self):
  if self.failure:raise RuntimeError('OWNED_OUTPUT_FAILED:'+self.failure)
 def close(self,timeout=2):
  self.thread.join(timeout)
  result={name:capture.finish(name in self.eof)for name,capture in self.captures.items()}
  if self.thread.is_alive():raise RuntimeError('OWNED_OUTPUT_EOF_JOIN_DEADLINE')
  if not self.released:self.budget.release_lease(self.lease);self.released=True
  self.check()
  if not all(row['captureComplete']for row in result.values()):raise RuntimeError('OWNED_OUTPUT_INCOMPLETE')
  return result
