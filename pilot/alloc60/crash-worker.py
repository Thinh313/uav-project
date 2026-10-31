from pathlib import Path
import sys,time,socket
from instrument import TimedWal,IOTrace
out=Path(sys.argv[1]);phase=sys.argv[2];port=int(sys.argv[3])
def await_release():
 while not(out/'release').exists():time.sleep(.01)
def hook(stage,kind,*_):
 if stage=='wal-flush' and kind=='INTENT' and phase=='before':
  (out/'barrier-pending').write_text('INTENT written; fsync not called');await_release()
w=TimedWal(out,{'scope':'PROCESS_CRASH_MOCK'},trace=IOTrace(100),preallocate=True,limit=2*2**20,hook=hook)
w.append('RX',0,b'input');w.append('INTENT',0,b'sensor',flush=True)
(out/'barrier-durable').write_text('fsync returned; sensor not sent');await_release()
with socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as s:s.sendto(b'sensor',('127.0.0.1',port))
w.append('SENT',0,b'sensor');w.append('CLOSE',0,b'{}',flush=True);w.close()
