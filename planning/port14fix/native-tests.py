"""Focused additive full-IPv6 display proof; never calls a socket/probe."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;E=R/'evidence/beta06-port14fix';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
oldpath=R/'planning/beta06g14/qa-port-guard.py';newpath=P/'qa-port-guard.py';raw=oldpath.read_bytes();assert raw.count(b"'-an'")==2 and newpath.read_bytes()==raw.replace(b"'-an'",b"'-anl'")
old=load('port14_old',oldpath);new=load('port14_candidate',newpath);header=b'Active Internet connections (including servers)\nProto Recv-Q Send-Q Local Address Foreign Address (state)\n';ports=(8872,8873);cases=[]
def check(label,data,reason=None,stderr=b'',code=0,module=new):
 try:
  value=module.parse_kernel_table(data,stderr,code,ports)
  assert reason is None,('ACCEPTED',label,reason)
  module.checked_kernel_snapshot(value,ports);cases.append({'case':label,'status':'PASS_COMPLETE','rows':value['rowCount'],'targetListeners':len(value['listeners'])});return value
 except module.KernelObservationError as exc:
  assert str(exc)==reason,(label,str(exc),reason);cases.append({'case':label,'status':'PASS_REFUSED','reason':str(exc),'rawSha256':exc.evidence['stdoutSha256']})
full=header+b'tcp6 0 0 2001:db8:1234:5678:abcd:ef01:2345:6789.12345 2001:db8::2.443 ESTABLISHED\n'
trunc=header+b'tcp6 0 0 2001:db8:1234:56.12345 2001:db8::2.443 ESTABLISHED\n'
check('old_truncated_ipv6_refusal',trunc,'KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED',module=old)
check('candidate_truncated_ipv6_still_refuses',trunc,'KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED')
value=check('candidate_complete_ipv6',full);assert not value['listeners'];assert value['command']==['/usr/sbin/netstat','-anl','-p','tcp']
check('old_parser_also_accepts_full_ipv6',full,module=old)
listen=header+b'tcp4 0 0 127.0.0.1.8872 *.* LISTEN\ntcp4 0 0 127.0.0.1.8873 *.* LISTEN\n'
v=check('synthetic_two_owned_rows_parser_only',listen);assert [(x['address'],x['port'])for x in v['listeners']]==[('127.0.0.1',8872),('127.0.0.1',8873)]
check('ipv6_scoped',header+b'tcp6 0 0 fe80::1%en0.8872 *.* LISTEN\n')
check('tcp46_wildcard',header+b'tcp46 0 0 *.8872 *.* LISTEN\n')
for name,data,reason,err,code in [
 ('missing_header',b'', 'KERNEL_OBSERVER_KNOWN_COMPLETE_HEADER_REQUIRED',b'',0),
 ('malformed_row',header+b'tcp6 broken\n','KERNEL_OBSERVER_COMPLETE_TCP_ROW_GRAMMAR_REQUIRED',b'',0),
 ('bad_port',header+b'tcp4 0 0 127.0.0.1.70000 *.* LISTEN\n','KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED',b'',0),
 ('ambiguous_listen',header+b'tcp46 0 0 *.* *.* LISTEN\n','KERNEL_OBSERVER_AMBIGUOUS_LISTEN_PORT',b'',0),
 ('specific_wildcard_port_refuses',header+b'tcp4 0 0 127.0.0.1.* *.* LISTEN\n','KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED',b'',0),
 ('stderr',full,'KERNEL_OBSERVER_EXIT_OR_STDERR_AMBIGUITY',b'permission denied',0),
 ('nonzero',full,'KERNEL_OBSERVER_EXIT_OR_STDERR_AMBIGUITY',b'',1),
 ('oversized',b'x'*(1024*1024+1),'KERNEL_OBSERVER_STDOUT1MIB_BOUND',b'',0),
 ('nonascii',header+b'\xff\n','KERNEL_OBSERVER_ASCII_GRAMMAR_REQUIRED',b'',0)]:check(name,data,reason,err,code)
# Exactly the original functions/guards after reversing only both argv literals.
assert ast.dump(ast.parse(newpath.read_text().replace("'-anl'","'-an'")))==ast.dump(ast.parse(oldpath.read_text()))
# Real bounded read-only collector only; no probe_host_ports/socket call.
live=new.observe_kernel_listeners(ports);new.checked_kernel_snapshot(live,ports);assert live['command']==['/usr/sbin/netstat','-anl','-p','tcp']
report={'status':'PASS_MOCK_AND_ONE_READONLY_KERNEL_CAPTURE','originalSource':{'path':str(oldpath.relative_to(R)),'sha256':H(oldpath)},'candidateSource':{'path':str(newpath.relative_to(R)),'sha256':H(newpath)},'testSha256':H(Path(__file__)),'sourceDelta':'Exactly two -an→-anl command literals; reverse transform byteexact and ASTexact, all numeric/grammar/guard functions identical.','syntheticCases':cases,'liveReadOnly':live,'historicalG14OffendingRow':'UNKNOWN_NO_RETAINED_RAW_ACTUAL_TABLE','diagnosis':'Current default table truncation reproduced separately; no claim of exact historical cause.','socketOrProbePerformed':False,'productRuntimePerformed':False,'scope':'No listeners/portprobe/socket allocation/ADB/AP/Android/runtime/build/install/sign; one directApple bounded passive kernel table capture, no unrelated addresses retained.','scratchCreated':False}
out=E/'native-candidate-proof01.json';data=(json.dumps(report,indent=2)+'\n').encode();assert len(data)<128*1024
with out.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(out),'bytes':len(data),'syntheticCases':len(cases),'candidateSha256':H(newpath)}))
