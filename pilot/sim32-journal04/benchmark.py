"""Offline matched row work only; no runtime or RTF claims."""
from pathlib import Path
import sys,json,gzip,time,statistics,hashlib,shutil
from wal_journal import Journal,encode
R=Path(__file__).resolve().parents[2];E=R/'evidence/sim32-journal04';old=R/'evidence/sim32-pipe03/runs/ui1791948167891';root=E/'benchmark-final';root.mkdir();rows=[]
with gzip.open(old/'physics-raw.jsonl.gz','rb')as f:
 for line in f:
  row=json.loads(line);rows.append(row)
  if len(rows)==2048:break
assert shutil.disk_usage(R).free>20*2**30+768*2**20
def stats(v):
 b=sorted(v);return {'samples':len(b),'meanUs':statistics.fmean(b)/1000,'p50Us':b[int((len(b)-1)*.5)]/1000,'p95Us':b[int((len(b)-1)*.95)]/1000,'p99Us':b[int((len(b)-1)*.99)]/1000,'maxUs':b[-1]/1000}
serialization=[]
for rep in range(4):
 for name in ['worker-json-encode','preencoded-payload-reference'][::1 if rep%2==0 else-1]:
  prepared=[encode(row)+b'\n'for row in rows];samples=[];digest=hashlib.sha256()
  for row,data in zip(rows,prepared):
   start=time.perf_counter_ns();actual=encode(row)+b'\n'if name=='worker-json-encode'else data;samples.append(time.perf_counter_ns()-start);assert actual==data;digest.update(actual)
  serialization.append({'rep':rep,'mode':name,'duration':stats(samples),'sameRowBytesSha256':digest.hexdigest(),'preencodingProducerCostExcludedForReferencePath':name=='preencoded-payload-reference'})
walruns=[]
for rep in range(3):
 for policy in ['fsync-before-publish','process-crash-only'][::1 if rep%2==0 else-1]:
  out=root/f'walr{rep}{policy}';out.mkdir();state=out/'state';state.mkdir();j=Journal(out,state,{'run':out.name,'epoch':'benchmark','source':'OFFLINE_IMPORTED_ROWS_NO_SEND'},policy=policy,wal_limit=8*2**20);samples=[];prepared_cost=[];start=time.perf_counter_ns()
  for frame,row in enumerate(rows[:512]):
   mock={**row,'frame':frame,'epoch':'benchmark','source':'OFFLINE_IMPORTED_ROWS_NO_SEND'};mock.pop('sensorSent',None)
   a=time.perf_counter_ns();j.reserve(frame);p=j.prepare(mock,None);prepared_cost.append(time.perf_counter_ns()-a)
   # Marker is a declared mock send result for archive benchmark only. No socket exists.
   a=time.perf_counter_ns();j.transmitted(p,len(mock['sensorUtf8'].encode()),len(mock['sensorUtf8'].encode()));samples.append(time.perf_counter_ns()-a)
   while j.pending>=128:time.sleep(.0001);j.check()
  result=j.seal();assert result['status']=='COMPLETE_ACCEPTED_MOCK_CAPTURE'
  wall=(time.perf_counter_ns()-start)/1e9
  actual=[json.loads(x)for x in gzip.open(out/'physics-raw.jsonl.gz','rb')];assert len(actual)==512
  for i,row in enumerate(actual):
   expected={**rows[i],'frame':i,'epoch':'benchmark','source':'OFFLINE_IMPORTED_ROWS_NO_SEND','sensorSent':True,'sendObservation':'UDP_SEND_RETURNED_LENGTH'};assert row==expected
  walruns.append({'rep':rep,'policy':policy,'rows':512,'wallSeconds':wall,'wholeOfflineRowsPerSecond':512/wall,'prepareAndDurability':stats(prepared_cost),'commitAndEnqueue':stats(samples),'walAppend':stats(j.wal.append_cost),'walFsync':stats(j.wal.flush_cost)if j.wal.flush_cost else None,'archiveWrite':stats(j.costs),'queueHighwater':j.highwater,'archiveExactRowSemantics':True,'actualSensorsPublished':0})
with(E/'offline-benchmark-final.json').open('x')as f:json.dump({'status':'PASS_OFFLINE_SAME_ROW_BYTES','importedRun':'ui1791948167891','rowCount':len(rows),'serialization':serialization,'walRuns':walruns,'limits':['Moving JSON encoding to producer removes worker serialization but moves cost; no total-speed claim','process-crash-only policy is benchmark-only, no physical power-loss guarantee or implicit selection','fsync-before-publish default mock; costs included and need future SITL gate','Offline IO throughput has no renderer/AP/network/guest load and is not RTF']},f,indent=2);f.write('\n')
print('OFFLINE_BENCHMARK_COMPLETE',len(walruns),flush=True)
