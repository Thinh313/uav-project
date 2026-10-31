"""Independent command-only correction check. Fake sockets only; no kernel capture."""
import ast,hashlib,importlib.util,json,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;E=R/'evidence/beta06-port14fix'
H=lambda b:hashlib.sha256(b).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
oldp=R/'planning/beta06g14/qa-port-guard.py';newp=P/'qa-port-guard.py';oldb=oldp.read_bytes();newb=newp.read_bytes()
assert oldb.count(b"'-an'")==2 and newb==oldb.replace(b"'-an'",b"'-anl'")
assert ast.dump(ast.parse(newb.replace(b"'-anl'",b"'-an'")))==ast.dump(ast.parse(oldb))
old=load('qa_port14_original',oldp);new=load('qa_port14_candidate',newp)
header=b'Active Internet connections (including servers)\nProto Recv-Q Send-Q Local Address Foreign Address (state)\n';ports=(8872,8873);results=[]
def table(rows):return header+rows.encode()
full=table('tcp6 0 0 2001:db8:1234:5678:9abc:def0:1234:5678.4455 2001:db8::9.443 ESTABLISHED\n')
trunc=table('tcp6 0 0 2001:db8:1234:56.4455 2001:db8::9.443 ESTABLISHED\n')
def parse(label,b,reason=None,module=new,err=b'',code=0):
 try:
  v=module.parse_kernel_table(b,err,code,ports);module.checked_kernel_snapshot(v,ports);assert reason is None,(label,'unexpected accept');results.append({'case':label,'status':'PASS_ACCEPTED','rows':v['rowCount'],'targetListeners':len(v['listeners'])});return v
 except module.KernelObservationError as ex:
  assert str(ex)==reason,(label,str(ex),reason);results.append({'case':label,'status':'PASS_REFUSED','reason':str(ex)})
for m,label in [(old,'original'),(new,'candidate')]:
 parse(label+'_full_ipv6',full,module=m);parse(label+'_truncated_ipv6',trunc,'KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED',module=m)
assert parse('reported_command',full)['command']==['/usr/sbin/netstat','-anl','-p','tcp']
for label,b,reason,err,code in [
 ('empty',b'','KERNEL_OBSERVER_KNOWN_COMPLETE_HEADER_REQUIRED',b'',0),
 ('missing_second_header',header.splitlines()[0]+b'\n','KERNEL_OBSERVER_KNOWN_COMPLETE_HEADER_REQUIRED',b'',0),
 ('unknown_family',table('udp6 0 0 ::1.8872 *.* LISTEN\n'),'KERNEL_OBSERVER_COMPLETE_TCP_ROW_GRAMMAR_REQUIRED',b'',0),
 ('unknown_state',table('tcp6 0 0 ::1.8872 *.* MYSTERY\n'),'KERNEL_OBSERVER_COMPLETE_TCP_ROW_GRAMMAR_REQUIRED',b'',0),
 ('truncated_unrelated_row',full+trunc[len(header):],'KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED',b'',0),
 ('ambiguous_listen',table('tcp6 0 0 *.* *.* LISTEN\n'),'KERNEL_OBSERVER_AMBIGUOUS_LISTEN_PORT',b'',0),
 ('wildcard_specific_host_port',table('tcp4 0 0 127.0.0.1.* *.* LISTEN\n'),'KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED',b'',0),
 ('non_ascii',header+b'\xff','KERNEL_OBSERVER_ASCII_GRAMMAR_REQUIRED',b'',0),
 ('stderr',full,'KERNEL_OBSERVER_EXIT_OR_STDERR_AMBIGUITY',b'permission denied',0),
 ('exit_nonzero',full,'KERNEL_OBSERVER_EXIT_OR_STDERR_AMBIGUITY',b'',1),
 ('oversize',b'x'*(2**20+1),'KERNEL_OBSERVER_STDOUT1MIB_BOUND',b'',0),
 ('target_overflow',table('tcp6 0 0 ::1.8872 *.* LISTEN\n'*33),'KERNEL_OBSERVER_TARGET_ROW32_BOUND',b'',0)]:parse(label,b,reason,err=err,code=code)
before=new.parse_kernel_table(header,b'',0,ports)
heldraw=table('tcp4 0 0 127.0.0.1.8872 *.* LISTEN\ntcp4 0 0 127.0.0.1.8873 *.* LISTEN\n')
held=new.parse_kernel_table(heldraw,b'',0,ports)
class FakeSocket:
 def __init__(self,items,fail=False):self.closed=False;self.fail=fail;items.append(self)
 def setsockopt(self,*args):assert args==(new.socket.SOL_SOCKET,new.socket.SO_REUSEADDR,1)
 def bind(self,address):
  assert address[0]=='127.0.0.1'
  if self.fail:raise OSError(48,'synthetic bind failure')
 def listen(self,n):assert n==1
 def close(self):self.closed=True
def probe(label,snaps,refuse=False,fail_second=False):
 items=[];it=iter(snaps)
 def fake(*args):assert args==(new.socket.AF_INET,new.socket.SOCK_STREAM);return FakeSocket(items,fail_second and len(items)==1)
 try:
  v=new.probe_host_ports(ports,socket_factory=fake,clock=lambda:1.0,kernel_observer=lambda _:next(it));assert not refuse;assert v['heldTogetherUntilCleanup'] and len(items)==2
 except new.PortProbeError:
  assert refuse
 assert all(x.closed for x in items)
 results.append({'case':label,'status':'PASS_REFUSED'if refuse else'PASS_FAKE_HELD_TWO','fakeHandles':len(items),'allFakeHandlesClosed':True})
probe('fake_exact_two', [before,held])
for label,row in [('wildcard','tcp46 0 0 *.8872 *.* LISTEN\n'),('ipv6','tcp6 0 0 ::1.8873 *.* LISTEN\n')]:probe('foreign_'+label+'_before',[new.parse_kernel_table(table(row),b'',0,ports)],True)
probe('fake_held_missing_one',[before,new.parse_kernel_table(table('tcp4 0 0 127.0.0.1.8872 *.* LISTEN\n'),b'',0,ports)],True)
probe('fake_held_foreign_race',[before,new.parse_kernel_table(heldraw+table('tcp6 0 0 ::1.8872 *.* LISTEN\n')[len(header):],b'',0,ports)],True)
probe('fake_partial_bind_cleanup',[before],True,True)
report={'status':'PASS_SOURCE_AND_SYNTHETIC_FAKE_ONLY','scope':'No socket allocated, no portprobe, no listener, no kernel subprocess, no Android/AP/runtime. probe_host_ports invoked with fake socket/observer only.','original':{'path':str(oldp.relative_to(R)),'sha256':H(oldb)},'candidate':{'path':str(newp.relative_to(R)),'sha256':H(newb)},'recipe':{'path':str(Path(__file__).relative_to(R)),'sha256':H(Path(__file__).read_bytes())},'sourceDelta':'Exactly two command literals -an to -anl; reverse bytes and AST exact; parser, numeric bounds, cleanup and guards unchanged.','cases':results,'historicalG14OffendingRow':'UNKNOWN; original raw table absent. Current truncation reproduction is distinct evidence, not exact historical attribution.','actualG14':'NOT_READY; zero hosts/emulators/AP; no retry or new actual campaign authorized here.','independentLiveCapture':'NOT_RUN; Builder passive capture remains separately labelled.','scratchCreated':False}
data=(json.dumps(report,indent=2)+'\n').encode();assert len(data)<=128*1024
assert sum(p.stat().st_size for root in [P,E,R/'pilot/port14fix'] if root.exists() for p in root.rglob('*') if p.is_file())+len(data)<2*2**20
out=E/'qa-independent01.json'
with out.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(data),'bytes':len(data),'cases':len(results),'status':report['status']}))
