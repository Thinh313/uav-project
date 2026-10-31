"""Bounded presentation derivative, original WAL unchanged; input is recorded local TX, not execution."""
from pathlib import Path
import bisect,hashlib,importlib.util,json,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/showcase78';rid='rad3ab2ece4a54e38a4ba';run=R/'evidence/simtrain53/runs'/rid
assert shutil.disk_usage(R).free>20.25*2**30
spec=importlib.util.spec_from_file_location('readback53',R/'pilot/simtrain53/readback.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
receipt=json.loads((run/'readback.json').read_text());assert receipt['status']=='PASS_RAW_CAPTURE_ORIGINAL_ORACLE_AND_CORRELATION'
with(run/'frames.wal').open('rb')as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
assert sha==receipt['filesSha256']['frames.wal']
with(run/'mavlink.jsonl').open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==receipt['filesSha256']['mavlink.jsonl']
events=[json.loads(l)for l in(run/'mavlink.jsonl').open()];brackets=[];commands=[];pending=None
for e in events:
 if e['kind']=='CLOCK_NODE_BACKEND_BRACKET' and e['data']['status']=='MATCHED':
  d=e['data'];lo=int(d['nodeMinusBackendLowNs']);hi=int(d['nodeMinusBackendHighNs']);brackets.append({'backend':int(d['backendSendNs']),'mid':(lo+hi)//2,'widthMs':(hi-lo)/1e6})
 elif e['kind']=='RC_TX_INTENT':pending=e
 elif e['kind']=='RC_LOCAL_WRITE_RETURN':
  assert pending and pending['index']+1==e['index'];commands.append({'node':int(e['nodeNs']),'channels':pending['data']['channels'],'index':pending['index']});pending=None
assert brackets and commands
brackets.sort(key=lambda x:x['backend']);bt=[x['backend']for x in brackets];ct=[x['node']for x in commands];rows=[];records=0;intents=0
for rec in m.records(run/'frames.wal'):
 records+=1
 if rec['kind']!='INTENT':continue
 intents+=1
 if rec['frame']%40:continue
 body,snapshot=m.unpack_intent(rec['body']);assert not snapshot;d=json.loads(body);a=d['modelAux'];stamp=d['hostReceiveNs'];bi=bisect.bisect_right(bt,stamp)-1;extra={'inputAxes':None,'inputRecorded':False}
 if bi>=0 and 0<=stamp-brackets[bi]['backend']<=10_000_000_000:
  b=brackets[bi];node=stamp+b['mid'];ci=bisect.bisect_right(ct,node)-1
  if ci>=0 and 0<=node-commands[ci]['node']<=200_000_000:
   c=commands[ci];p=c['channels'][:4]
   if all(1000<=x<=2000 for x in p):extra={'inputAxes':[(p[0]-1500)/300,(1500-p[1])/300,(p[3]-1500)/300,(p[2]-1500)/300],'inputRecorded':True,'inputLocalTxIndex':c['index'],'inputApproximateAgeMs':(node-c['node'])/1e6,'inputClockBracketWidthMs':b['widthMs']}
 rows.append({k:a[k]for k in ['timestamp','position','velocity','quaternion','rpmEstimated','massKg','ground']}|{'frame':rec['frame']}|extra)
assert intents==receipt['frames']==134632
active=[p for p in rows if p['inputRecorded'] and any(x!=0 for x in p['inputAxes'])];assert active
report={'id':rid,'label':'E2E vừa kiểm · không tải / lặng gió','mode':'REPLAY_ACTUAL_REFERENCE_SITL','physicsCalibration':'NOT_HERA','source':str((run/'frames.wal').relative_to(R)),'sourceSha256':sha,'walRecordsVerified':records,'originalIntentFrames':intents,'renderSelection':'Every40th frame only; original1200Hz WAL unchanged','sampleHz':30,'inputSource':str((run/'mavlink.jsonl').relative_to(R)),'inputSourceSha256':receipt['filesSha256']['mavlink.jsonl'],'inputAlignment':'APPROXIMATE_CLOCK_BRACKET_MIDPOINT; recorded local TX, not AP RC echo/execution or measured one-way latency','firstNonNeutralTime':active[0]['timestamp'],'samples':rows}
with(E/'flight-replay.json').open('x')as f:json.dump(report,f,separators=(',',':'),ensure_ascii=False);f.write('\n')
data=(E/'flight-replay.json').read_bytes();assert len(data)<4*2**20
descriptor={k:v for k,v in report.items()if k!='samples'}|{'file':'showcase78-flight.json','duration':rows[-1]['timestamp'],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'nonNeutralRenderSamples':len(active)}
with(E/'replay-descriptor.json').open('x')as f:json.dump(descriptor,f,indent=2,ensure_ascii=False);f.write('\n')
print(json.dumps({k:descriptor[k]for k in ['originalIntentFrames','bytes','nonNeutralRenderSamples','firstNonNeutralTime']}))
