"""AP drainer independent fragmented-input/fault probes. No producer process."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[4];source=R/'pilot/betaintegrated01/runtime/ap_stage.py'
spec=importlib.util.spec_from_file_location('stage_fault_independent',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=R/('evidence/betaintegrated01-m1runtime/qa/ap-stage-faults'+sys.argv[1]);out.mkdir();before=hashlib.sha256(source.read_bytes()).hexdigest();results=[]
def check(b,s):
 if not b:raise AssertionError(s)
def test(name,f):
 try:results.append({'id':name,'pass':True,'detail':f()})
 except Exception as e:results.append({'id':name,'pass':False,'error':type(e).__name__+':'+str(e)})
def event(n,frame=0,kind=10,tid=42):return m.EVENT.pack(n,frame,kind,tid,n+1,n+1,0,0,0)
def normal():
 d=m.StageDrainer(out/'fragmented','run01','epoch01','boot01',events_per_chunk=3,max_events=40)
 body=b''.join(event(n,n//8,[10,11,12,13,14,20,21,24][n%8]) for n in range(32))
 offsets=[1,63,2,65,7,129];pos=0;i=0
 while pos<len(body):take=offsets[i%len(offsets)];d.feed(body[pos:pos+take]);pos+=take;i+=1
 receipt=d.finish(ap_exit=-15,eof=True);v=m.verify_stage(out/'fragmented','run01','epoch01','boot01',terminal_sha256=receipt['terminalSHA256']);check(v['events']==32 and v['segments']==11,'drain count');return v
test('A_FRAGMENTED_32EVENTS_11SEGMENTS',normal)
def rejected(name,raw):
 d=m.StageDrainer(out/name,'run01','epoch01','boot01',events_per_chunk=2,max_events=8);d.feed(event(0))
 try:d.feed(raw);raise AssertionError('invalid event accepted')
 except ValueError:pass
 check(d.failed and d.total==1,'prefix/fence');failure=json.loads((out/name/'failure.json').read_text());check(failure['rejectedHex']==raw.hex(),'rejectedbytes');return failure['reason']
test('B_SEQUENCE_GAP',lambda:rejected('gap',event(2)))
test('C_MULTIPLE_TID',lambda:rejected('multi',event(1,tid=43)))
test('D_FOREIGN_KIND',lambda:rejected('kind',event(1,kind=77)))
def truncation():
 d=m.StageDrainer(out/'truncated','run01','epoch01','boot01',events_per_chunk=2,max_events=8);d.feed(event(0));d.feed(b'123')
 try:d.finish(ap_exit=0,eof=True);raise AssertionError('truncated complete')
 except RuntimeError:pass
 check(d.failed and d.total==1,'lost prefix');check(not(out/'truncated/terminal.json').exists(),'false terminal');return json.loads((out/'truncated/failure.json').read_text())['pendingTailHex']
test('E_TRUNCATED_TAIL_NO_COMPLETE',truncation)
def capacity():
 d=m.StageDrainer(out/'capacity','run01','epoch01','boot01',events_per_chunk=1,max_events=1);d.feed(event(0))
 try:d.feed(event(1));raise AssertionError('capacity overwrite')
 except ValueError:pass
 check(d.failed and d.total==1,'capacity not fenced');return {'retained':d.total,'failure':json.loads((out/'capacity/failure.json').read_text())['reason']}
test('F_CAPACITY_NO_OVERWRITE',capacity)
def syncfail():
 d=m.StageDrainer(out/'sync-fail','run01','epoch01','boot01',events_per_chunk=1,max_events=8);old=m.os.fsync
 def broken(fd):raise OSError('QA_FSYNC')
 try:
  m.os.fsync=broken
  try:d.feed(event(0));raise AssertionError('syncfail accepted')
  except OSError:pass
 finally:m.os.fsync=old
 check(d.failed and not(out/'sync-fail/terminal.json').exists(),'false complete');return {'failed':d.failed,'eventsObservedBeforeSealFailure':d.total}
test('G_FSYNC_FAILURE_NO_TERMINAL',syncfail)
after=hashlib.sha256(source.read_bytes()).hexdigest();data={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':after,'sourceChanged':before!=after,'results':results,'status':'PASS'if all(r['pass']for r in results)and before==after else'FAIL','APAndroidSocketRuntimeLaunches':0,'scope':'Independent synthetic pipe byte feed +actualfilesystem/fault seam; no real AP producer/execution'}
(out/'results.json').open('x').write(json.dumps(data,indent=2)+'\n');print(json.dumps({'status':data['status'],'groups':len(results),'failed':[r['id']for r in results if not r['pass']],'sourceChanged':before!=after}))
