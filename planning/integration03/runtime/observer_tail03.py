"""Incremental Root QA passive observer decoder; no repeated full-log parse during live flight."""
import importlib.util,json,time
from pathlib import Path
class ObserverTail03:
 def __init__(self,root,run):
  self.path=root/'evidence/integration03-runtime/runs'/run/'observer.jsonl';sp=importlib.util.spec_from_file_location('i03_observer_oracle',root/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);self.parser=m.MAVLink(None);self.parser.robust_parsing=True;self.offset=0;self.pending=b'';self.latest={};self.reached=set();self.everArmed=False;self.rows=0
 def read(self):
  with self.path.open('rb')as f:f.seek(self.offset);chunk=f.read(8*2**20+1);self.offset=f.tell()
  assert len(chunk)<=8*2**20 and self.offset<=8*2**20,'OBSERVER_CAPTURE_BOUND';self.pending+=chunk
  while b'\n'in self.pending:
   line,self.pending=self.pending.split(b'\n',1);r=json.loads(line);self.rows+=1;assert r['n']==self.rows,'OBSERVER_ROW_ORDER'
   for frame in self.parser.parse_buffer(bytes.fromhex(r['hex']))or[]:
    if frame.get_srcSystem()!=42 or frame.get_srcComponent()!=1:continue
    self.latest[frame.get_msgId()]=(int(r['hostMonoNs']),frame)
    if frame.get_msgId()==0:self.everArmed|=bool(frame.base_mode&128)
    if frame.get_msgId()==46:self.reached.add(frame.seq)
  assert len(self.pending)<65536,'OBSERVER_LINE_BOUND';return self.latest
 def freshAirborne(self):
  last=self.read();return all(k in last and time.monotonic_ns()-last[k][0]<2e9 for k in [0,33,245])and bool(last[0][1].base_mode&128)and last[245][1].landed_state==2 and last[33][1].relative_alt>4000
 def proof(self):return {str(k):{'hostMonoNs':str(at),'frame':f.to_dict()}for k,(at,f)in self.latest.items()if k in[0,33,245]}
