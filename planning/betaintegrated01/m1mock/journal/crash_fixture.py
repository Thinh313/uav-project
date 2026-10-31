"""Task-owned pure-Python crash fixture. No network, simulator or old evidence."""
from pathlib import Path
import sys,os,json
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from pilot.betaintegrated01.journal import SegmentedJournal,Policy,FileIO
root=Path(sys.argv[1]);point=sys.argv[2]
assert root.is_relative_to(R/'evidence/betaintegrated01-m1mock/journal')
class CrashIO(FileIO):
 def __init__(self):super().__init__();self.kind=None;self.path=None
 def open_exclusive(self,p):
  if point=='before-next'and p.name=='segment-000001.jsonl':os._exit(75)
  if point=='before-session'and p.name=='session.json':os._exit(75)
  self.path=p.name;return super().open_exclusive(p)
 def write(self,fd,b):
  try:self.kind=json.loads(bytes(b)).get('body',{}).get('kind')
  except Exception:self.kind=None
  return super().write(fd,b)
 def fsync(self,fd):
  super().fsync(fd)
  if(point=='after-intent'and self.kind=='INTENT')or(point=='after-sent'and self.kind=='SENT')or(point=='after-close'and self.kind=='CLOSE'):os._exit(75)
 def dirsync(self,p):
  super().dirsync(p)
  if point=='committed'and self.path=='session.json':os._exit(75)
j=SegmentedJournal(root,'run01','epoch01',Policy(segment_bytes=12288,max_record_bytes=2048,quota_bytes=262144,max_segments=32),CrashIO())
for i in range(20):j.record_frame(i,b'rx',b'sensor',len)
j.close();raise AssertionError('CRASH_POINT_NOT_REACHED')
