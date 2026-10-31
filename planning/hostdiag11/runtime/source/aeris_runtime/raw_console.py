"""Bounded clockprobe diagnostic pipe in the original registered raw domain."""
from pathlib import Path
import os,selectors,threading
class RawConsole:
 def __init__(self,process,path,maximum=131072):
  if maximum!=131072:raise ValueError('CLOCK_CONSOLE_SOURCE128KiB')
  self.process=process;self.path=Path(path);self.maximum=maximum;self.bytes=0;self.failure=None;self.eof=False;self.thread=threading.Thread(target=self._pump,name='aeris-clockprobe-console',daemon=True);self.file=self.path.open('xb');self.thread.start()
 def _pump(self):
  selector=None
  try:
   selector=selectors.DefaultSelector()
   os.set_blocking(self.process.stdout.fileno(),False);selector.register(self.process.stdout,selectors.EVENT_READ)
   while True:
    for key,_ in selector.select(.05):
     raw=os.read(key.fileobj.fileno(),65536)
     if not raw:self.eof=True;return
     room=self.maximum-self.bytes;prefix=raw[:room]
     if prefix:
      view=memoryview(prefix)
      while view:
       n=self.file.write(view)
       if type(n)is not int or not 0<n<=len(view):raise OSError('CLOCK_CONSOLE_SHORT_WRITE')
       view=view[n:];self.bytes+=n
      self.file.flush();os.fsync(self.file.fileno())
     if len(raw)>room:raise ValueError('CLOCK_CONSOLE_OVERFLOW_FAILED_PREFIX')
  except BaseException as e:self.failure=type(e).__name__+':'+str(e)
  finally:
   operations=([('selector',selector.close)]if selector is not None else[])+[('stdout',self.process.stdout.close),('file',self.file.close)]
   for name,operation in operations:
    try:operation()
    except BaseException as close_error:
     secondary='CLOSE_SECONDARY:'+name+':'+type(close_error).__name__+':'+str(close_error)[:256]
     self.failure=secondary if self.failure is None else self.failure+';'+secondary
 def check(self):
  if self.failure:raise RuntimeError(self.failure)
 def close(self,timeout=2):
  self.thread.join(timeout);receipt={'path':str(self.path),'bytes':self.bytes,'maximumBytes':self.maximum,'eof':self.eof,'captureComplete':self.eof and self.failure is None and not self.thread.is_alive(),'failure':self.failure,'originalRawDomain':True}
  if self.thread.is_alive():raise RuntimeError('CLOCK_CONSOLE_EOF_JOIN_DEADLINE')
  self.check()
  if not receipt['captureComplete']:raise RuntimeError('CLOCK_CONSOLE_INCOMPLETE')
  return receipt
