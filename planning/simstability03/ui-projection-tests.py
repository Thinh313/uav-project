from pathlib import Path
import sys,types,json,ast,hashlib,importlib.util,struct
R=Path(__file__).resolve().parents[2];P=R/'.local/simstability03/receiver01/pilot/simhand01';out=R/'evidence/simstability03';out.mkdir(exist_ok=True)
b={'apSeconds':300,'runtimeStopUTC':'2099-01-01T00:00:00+00:00'}
sys.modules['guard']=types.SimpleNamespace(budget=lambda:b)
ns={'__file__':str(P/'projection.py')};exec(compile((P/'projection.py').read_text(),str(P/'projection.py'),'exec'),ns)
backend=ns['backend_source']()[1];runtime=ns['runtime_source']()[1]
ast.parse(backend);ast.parse(runtime)
assert 'frames < 360000' in backend and 'deadline=min(time.monotonic()+300,' in runtime
assert "'apSeconds':300,'closureReserveSeconds':5" in runtime
assert "--speedup','1'" in runtime and "'negativeDebtCapUs':500000" in runtime
assert runtime.index('admit_ap(rid)')<runtime.index('check_cancel()')<runtime.index('proc = subprocess.Popen')
assert runtime.index('check_cancel()',runtime.index('assert (out/'))<runtime.index("args = ['docker'")
assert runtime.index('check_cancel()',runtime.index("args = ['docker'"))<runtime.index('cid = command(args)')
assert "wal.append('INTENT', frame, struct.pack('<II', len(body), 0)+body, flush=True)" in backend
assert backend.index("wal.append('INTENT'")<backend.index('returned = s.sendto')
assert "if not stopped: raise RuntimeError('UNREQUESTED_FRAME_BOUND')" in backend
assert "'successCloseWritten':False" in backend
# Compare emitted bytes under the same deterministic recorded metadata clock.
wp=P.parents[0]/'sim32-journal04/wal_journal.py';spec=importlib.util.spec_from_file_location('test_wal',wp);m=importlib.util.module_from_spec(spec);sys.modules['test_wal']=m;spec.loader.exec_module(m)
klass=next(n for n in ast.walk(ast.parse(backend)) if isinstance(n,ast.ClassDef)and n.name=='Wal')
import os,time
ctx={'BaseWal':m.Wal,'os':os,'time':time};exec(compile(ast.Module(body=[klass],type_ignores=[]),'projected-wal','exec'),ctx)
# Only the header's monotonic timestamp is normalized. No runtime code is patched.
original=time.monotonic_ns;time.monotonic_ns=lambda:123456789
try:
 for suffix,cls in [('baseline',m.Wal),('instrumented',ctx['Wal'])]:
  folder=out/('wal-equivalence02-'+suffix);folder.mkdir(exist_ok=False);w=cls(folder,{'source':'DETERMINISTIC_MOCK'},limit=2**20)
  for frame in range(64):
   w.append('RX',frame,m.encode({'frame':frame,'rawHex':'aa'*40}))
   payload=m.encode({'frame':frame,'sensorUtf8':'{mock}'});w.append('INTENT',frame,struct.pack('<II',len(payload),0)+payload,flush=True)
   w.append('SENT',frame,m.encode({'frame':frame,'returnedBytes':8}))
  w.append('CLOSE',0,m.encode({'mock':True}),flush=True);w.close()
finally:time.monotonic_ns=original
one=(out/'wal-equivalence02-baseline/frames.wal').read_bytes();two=(out/'wal-equivalence02-instrumented/frames.wal').read_bytes();assert one==two
for bad in [None,True,0,1,299,301,300.0]:
 b['apSeconds']=bad
 try:exec(compile((P/'projection.py').read_text(),'bad-policy','exec'),{'__file__':str(P/'projection.py')});raise AssertionError(bad)
 except RuntimeError as e:assert str(e)=='AP_SECONDS_POLICY_REQUIRED'
result={'status':'PASS','scope':'MOCK_STATIC_AND_EXACT_WAL_OUTPUT_EQUIVALENCE_NOT_RUNTIME_PERFORMANCE','checks':14,'walFrames':64,'walBytes':len(one),'walSHA256':hashlib.sha256(one).hexdigest(),'apWallUpperSeconds':300,'closureReserveSeconds':5,'sourceSensorModelUnchanged':True,'additionalStageColumns':['intentWriteNs','intentFsyncWithHookSpanNs','intentAppendNs','intentWriteCalls'],'unknowns':['No AP or emulator started by this test','No pacing improvement measured','AP trace capacity remains bounded at 2097088 events; 300 seconds is a wall upper bound, not accepted trace duration']}
(out/'ui-projection-mock02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
