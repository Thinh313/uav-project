from pathlib import Path
import sys,subprocess,time,json,shutil,struct
from archive_v2 import archive
R=Path(__file__).resolve().parents[2];E=R/'evidence/isolate61';out=E/'mock'/sys.argv[1];out.mkdir();(out/'guest-state').mkdir();name='aeris-isolate61-mock';image='rtr-aeris-sim32-trace-builder:local';trace_mode=sys.argv[2];checks=[]
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
assert shutil.disk_usage(R).free>22.5*2**30
assert subprocess.run(['docker','container','inspect',name],capture_output=True).returncode!=0
args=['docker','run','--rm','-d','--name',name,'--label','aeris.task=isolate61-mock','--cpus','2','--memory','384m','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/probe:rw,noexec,nosuid,size=32m','--tmpfs','/ap-trace:rw,noexec,nosuid,size=144m','-v',str(R/'pilot/isolate61')+':/diagnostics:ro','-v',str(R/'pilot/sim32-pipe03')+':/instrument:ro','-v',str(out)+':/evidence','-v',str(out/'guest-state')+':/state','-e','AERIS_TRACE_MODE='+trace_mode,image,'/bin/sh','/diagnostics/guest-entry-v2.sh','python3','-B','/diagnostics/mock-ap-v2.py']
cid=subprocess.check_output(args,text=True).strip();archived=False
try:
 deadline=time.monotonic()+5
 while not(out/'guest-state/ap.pid').exists():assert time.monotonic()<deadline;time.sleep(.05)
 time.sleep(.4);files=archive(cid,out,trace_mode);archived=True
 ck('TERM-ignoring mock writer reaped via recorded KILL before export',(out/'ap-exit-code').read_text().strip()=='137')
 ck('all source/copy files same immutable SHA',len(files)==6 and all(v['sameImmutableSourceBytes']for v in files))
 raw=(out/'ap-timing.bin').read_bytes();magic,cap,n,failed,w=struct.unpack('<8s4Q',raw[:40]);ck('full original synthetic trace with valid committed prefix',magic==b'AERISD02'and 0<n<=cap and failed==0 and len(raw)==4096+cap*64)
 for i in range(n):assert struct.unpack_from('<Q',raw,4096+i*64)[0]==i
 ck('no synthetic event loss/gap',True)
 rows=[json.loads(s)for s in(out/'guest-scheduler.jsonl').read_text().splitlines()];ck('guest kernel samples task identities and counters',len([v for v in rows if v['tasks']])>3 and all(not v['tasks']for v in rows[next((j for j,v in enumerate(rows)if not v['tasks']),len(rows)):]))
 ck('kernel AP task CPU counter advances',[v for v in rows if v['tasks']][-1]['tasks'][0]['schedstat'][0]>=[v for v in rows if v['tasks']][0]['tasks'][0]['schedstat'][0]>0)
 result={'status':'PASS_GUEST_MOCK_SUPERVISION_ARCHIVE','checks':checks,'kernelRunqueueWaitAvailable':any(t['schedstat'][1]>0 for v in rows for t in v['tasks']),'syntheticEvents':n,'actualAP':False,'files':files}
 with(E/('qa-'+sys.argv[1]+'.json')).open('x')as f:json.dump(result,f,indent=2)
 print(json.dumps({'checks':len(checks),'runqueueWaitAvailable':result['kernelRunqueueWaitAvailable'],'syntheticEvents':n}))
finally:
 if archived:
  subprocess.run(['docker','stop','-t','2',cid],check=True,capture_output=True)
  with(out/'docker-image-prune.txt').open('x')as f:subprocess.run(['docker','image','prune','-f'],stdout=f,check=True)
 else:
  with(out/'archive-failure-container-retained.json').open('x')as f:json.dump({'containerId':cid,'name':name,'mustNotStopBeforeVerifiedExport':True},f)
