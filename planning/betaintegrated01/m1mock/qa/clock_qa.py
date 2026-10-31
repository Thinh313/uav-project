"""Independent bounded clock and composed durable sink probes. No sockets."""
from pathlib import Path
import sys,json,hashlib,struct,os,datetime,shutil
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.clock.correlation import Context,BoundedCorrelator,ClockError
from pilot.betaintegrated01.journal import SegmentedJournal,Policy,verify_journal
tag=sys.argv[1]if len(sys.argv)>1 else'01';assert tag.isdigit()
E=R/'evidence/betaintegrated01-m1mock/qa'/('clock-qa'+tag);E.mkdir(exist_ok=False)
assert shutil.disk_usage(E).free>=10*2**30+256*2**20
source=R/'pilot/betaintegrated01/clock/correlation.py';before=hashlib.sha256(source.read_bytes()).hexdigest()
C=Context('run','epoch','boot');P=('127.0.0.1',18000);results=[]
def fail(fn):
 try:fn()
 except Exception as e:return str(e)
 raise AssertionError('expected rejection')
def packet(rid,g1,g2):return struct.pack('<7Q',rid,g1,g2,1,2,3,4)
def case(name,fn):
 try:results.append({'id':name,'status':'PASS','detail':fn()})
 except Exception as e:results.append({'id':name,'status':'FAIL','error':type(e).__name__+':'+str(e)})
def longrun():
 path=E/'events.jsonl';f=path.open('xb');count=0
 def sink(row):
  nonlocal count
  f.write(json.dumps(row,sort_keys=True).encode()+b'\n');f.flush();os.fsync(f.fileno());count+=1
 b=BoundedCorrelator(C,P,sink,max_pending=4,recent_limit=7)
 for rid in range(2051):
  t=rid*1000000+1000;b.register(rid,t,C);z=b.receive(packet(rid,t-100,t),P,t+100,C)
  assert z['freshCalibration']and z['offsetLowNs']==100 and z['offsetHighNs']==100
 f.flush();s=b.snapshot();assert s['pending']==0 and s['recent']==7 and s['recentPeak']==7
 assert s['journalEvents']==count==4102 and sum(1 for _ in path.open('rb'))==4102
 assert b.receive(packet(0,0,1),P,2051002000,C)['freshCalibration']is False
 fail(lambda:b.register(0,2051003000,C));f.close();s['journalSourceRecords']=count;return s
case('C01_2051_exchanges_bounded_with_complete_durable_history',longrun)
def pending_timeout():
 rows=[];b=BoundedCorrelator(C,P,rows.append,max_pending=2,recent_limit=2,timeout_ns=100,fresh_ns=100,max_step_ns=1000)
 b.register(1,100,C);b.register(2,101,C);assert 'PENDING_BOUND'in fail(lambda:b.register(3,102,C))
 b.tick(202,C);assert b.snapshot()['pending']==0
 z=b.receive(packet(1,90,91),P,203,C);assert z['status']=='LATE_MATCHED'and not z['freshCalibration']
 assert b.calibration(204,C)is None
 assert b.snapshot()['pendingPeak']==2;return [r['kind']for r in rows]
case('C02_pending_timeout_late_never_calibration',pending_timeout)
def reordered():
 rows=[];b=BoundedCorrelator(C,P,rows.append);b.register(1,100,C);b.register(2,101,C)
 assert b.receive(packet(2,101,102),P,103,C)['freshCalibration']
 x=b.receive(packet(1,100,101),P,104,C);assert x['status']=='REORDERED_MATCHED'and not x['freshCalibration']
 assert b.calibration(105,C)['id']==2;assert not b.receive(packet(2,101,102),P,106,C)['freshCalibration'];return x
case('C03_reorder_duplicate_not_fresh',reordered)
def packet_context():
 rows=[];b=BoundedCorrelator(C,P,rows.append);b.register(1,100,C)
 for raw,peer in [(b'x',P),(packet(1,1,2),('127.0.0.2',18000))]:fail(lambda:b.receive(raw,peer,101,C))
 fail(lambda:b.receive(packet(1,1,2),P,102,Context('run','epoch','foreign')))
 assert b.snapshot()['pending']==1;assert [r['kind']for r in rows][-1]=='REJECTED_CONTEXT';return len(rows)
case('C04_malformed_peer_foreign_boot',packet_context)
def poisoned_sink():
 rows=[];armed=[False]
 def sink(row):
  if armed[0]:raise OSError('QA_SINK_FAILURE')
  rows.append(row)
 b=BoundedCorrelator(C,P,sink);b.register(1,100,C);armed[0]=True
 fail(lambda:b.receive(packet(1,100,101),P,102,C));s=b.snapshot();assert s['pending']==1 and s['journalEvents']==1 and s['failed']
 fail(lambda:b.calibration(103,C));return s
case('C05_sink_failure_before_publish_poisons',poisoned_sink)
def discontinuity():
 out=[]
 for mode in ('regress','suspend','guest'):
  b=BoundedCorrelator(C,P,out.append,max_step_ns=1000,timeout_ns=500,max_offset_step_ns=10)
  b.register(1,100,C);b.receive(packet(1,100,101),P,102,C)
  if mode=='regress':fail(lambda:b.tick(101,C))
  elif mode=='suspend':fail(lambda:b.tick(1103,C))
  else:b.register(2,103,C);fail(lambda:b.receive(packet(2,50,51),P,104,C))
  assert b.snapshot()['failed'];fail(lambda:b.register(3,1104,C))
 return [r['kind']for r in out if r['kind']in ['CLOCK_REGRESSION','SUSPEND_OR_STALE_GAP','GUEST_CLOCK_DISCONTINUITY']]
case('C06_host_suspend_regression_guest_restart',discontinuity)
def numeric():
 for rid in [True,-1,2**64,float('nan')]:
  b=BoundedCorrelator(C,P,lambda r:None);fail(lambda:b.register(rid,100,C));assert b.snapshot()['pending']==0
 for n in [True,-1,2**64,float('inf')]:
  b=BoundedCorrelator(C,P,lambda r:None);fail(lambda:b.tick(n,C))
 return '8 uint64 boundary refusals'
case('C07_numeric_schema',numeric)
def reentry():
 box={};caught=[]
 def sink(row):
  caught.append(fail(lambda:box['b'].register(99,100,C)))
 b=BoundedCorrelator(C,P,sink);box['b']=b;b.register(1,100,C)
 assert b.snapshot()['pending']==1 and b.snapshot()['journalEvents']==1 and caught==['REENTRANT_CLOCK_OPERATION'];return caught
case('C08_sink_reentry_cannot_mutate',reentry)
def composed():
 p=E/'composed';j=SegmentedJournal(p,'run','epoch',Policy(segment_bytes=32768,quota_bytes=2097152,max_record_bytes=2048,max_segments=128,termination_reserve_bytes=16384))
 b=BoundedCorrelator(C,P,lambda row:j.append_event('CLOCK',row),recent_limit=3)
 for rid in range(1100):
  t=rid*1000+100;b.register(rid,t,C);b.receive(packet(rid,t,t+1),P,t+2,C)
 j.close();v=verify_journal(p,'run','epoch');assert v['events']==2200 and v['state']=='COMPLETE_RECORDING'and b.snapshot()['recent']==3
 seq=[]
 for segment in sorted(p.glob('*.jsonl')):
  for line in segment.open('rb'):
   row=json.loads(line)['body']
   if row['kind']=='EVENT':seq.append(row['payload']['data']['sequence'])
 assert seq==list(range(1,2201));return {'clockEvents':2200,'segments':v['segments'],'state':v['state'],'scope':v['scope']}
if '--skip-composed' not in sys.argv:case('C09_actual_clock_sink_to_segmented_journal',composed)
after=hashlib.sha256(source.read_bytes()).hexdigest()
q={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':after,'sourceChanged':before!=after,'status':'PASS_SCOPED'if all(x['status']=='PASS'for x in results)and before==after else'FINDINGS_OR_DRIFT','results':results,'scope':'Mock correlation and retained bytes, not authenticated clocks/transport/flight','runtimeLaunches':0}
(E/'results.json').open('x').write(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
sys.exit(0 if q['status']=='PASS_SCOPED'else 2)
