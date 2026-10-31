"""Independent bounded analysis of sealed stage03 traces and typed cohort receipts.
No live raw reads, no runtime mutation, no cross-domain timestamp subtraction.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,math,sys,tarfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
RUN='s1195d1b6617880adb6c3'
D=ROOT/'evidence/integration03-runtime/runs'/RUN
OUT=ROOT/'evidence/integration03-qa/aged-cohorts01.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(xs):
 xs=sorted(xs)
 return {'n':len(xs),'min':xs[0] if xs else None,'p50':xs[math.ceil(.5*len(xs))-1] if xs else None,'p95':xs[math.ceil(.95*len(xs))-1] if xs else None,'max':xs[-1] if xs else None,'sum':round(sum(xs),4)}
def keyed(events,a,b,clock):
 by={};ds=[]
 for e in events:
  k=str(e.get('key',''))
  if not k:continue
  if e['stage']==a:by[k]=e[clock]
  if e['stage']==b and k in by:
   dt=e[clock]-by.pop(k)
   if dt<0:raise ValueError('negative same-domain duration')
   ds.append(round(dt,4))
 return {**stats(ds),'unmatchedBeginKeys':sorted(by)}
def ordered(events,a,b,clock):
 # Pair each response with immediately following same-name continuation only.
 return keyed(events,a,b,clock)
def main():
 if OUT.exists():raise ValueError('immutable output exists')
 oracle=ROOT/'pilot/apstream40/oracle-v2.py'
 sp=importlib.util.spec_from_file_location('i03_stage_upstream',oracle);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 src=json.loads((D/'aged-cohorts.json').read_text());traces=[]
 with tarfile.open(D/'preflight-stage-and-crew.tar') as t:
  members=[x for x in t.getmembers() if x.isfile() and x.name.startswith('stage03/')]
  assert len(members)==3 and all(x.size<200000 for x in members)
  for x in members:
   raw=t.extractfile(x).read();v=json.loads(raw);j=json.loads(v['clientTraceJson'])
   traces.append((min(e['nativeElapsedMs'] for e in v['events']),x.name,hashlib.sha256(raw).hexdigest(),v,j))
 traces.sort();results=[]
 for receipt,(_,name,digest,n,j) in zip(src['results'],traces):
  pf=receipt['preflight'][1];a=pf['assessment'];p=pf['parameters'];vals=p['values'];assert len(vals)==20
  assert a['state']=='READY_SCOPED_READONLY' and not a['reasons'] and a['readonly'] is True
  assert a['parameterWrites']==0 and a['armPermission'] is False and a['operationalAllowed'] is False
  assert receipt['explicitIntent'] is True and receipt['automaticRetry'] is False
  decoded=[]
  for key,v in vals.items():
   frame=bytes.fromhex(v['rawHex']);parser=m.MAVLink(None);msgs=parser.parse_buffer(frame)
   assert msgs and len(msgs)==1
   msg=msgs[0];assert msg.get_type()=='PARAM_VALUE' and msg.get_srcSystem()==42 and msg.get_srcComponent()==1
   param=msg.param_id.decode() if isinstance(msg.param_id,bytes) else msg.param_id
   assert param==key and msg.param_type==v['type'] and math.isclose(msg.param_value,v['value'],abs_tol=1e-6)
   assert a['parameters'][key]==v['value'] and p['firstAt']<=v['at']<=p['lastAt']
   decoded.append({'name':key,'type':msg.param_type,'value':msg.param_value,'nativeReceiptAtMs':v['at'],'wireSha256':hashlib.sha256(frame).hexdigest()})
  assert min(v['at'] for v in vals.values())==p['firstAt'] and max(v['at'] for v in vals.values())==p['lastAt']
  assert a['cohortFirstAtMs']==p['firstAt'] and a['cohortLastAtMs']==p['lastAt'] and a['cohortSha256']==p['sha256']
  span=p['lastAt']-p['firstAt'];assert 0<=span<=3000
  assert a['cohortId']==p['id']==receipt['trial']
  assert n['clock']=='ANDROID_ELAPSED_REALTIME_MS' and j['clock']=='WEBVIEW_PERFORMANCE_MS' and n['id']==j['id']
  assert n['overflow']==j['overflow']==0 and n['sampleEveryRx']==j['sampleEveryRx']==8
  assert min(e['nativeElapsedMs'] for e in n['events'])<=p['firstAt']<p['lastAt']<=max(e['nativeElapsedMs'] for e in n['events'])+20
  assert j['events'][-1]['stage']=='INSPECTION_END' and j['events'][-1]['outcome']=='COMPLETE'
  natives={}
  for kind in ['direct95:write','crew02:heartbeat']:
   natives[kind]={
    'bridgeToMainMs':keyed(n['events'],'BRIDGE_REQUEST:'+kind,'MAIN_ADMISSION:'+kind,'nativeElapsedMs'),
    'mainToIOStartMs':keyed(n['events'],'MAIN_ADMISSION:'+kind,'IO_START:'+kind,'nativeElapsedMs')}
  natives['replyQueuedToMainMs']=keyed(n['events'],'REPLY_QUEUED','REPLY_MAIN_READY','nativeElapsedMs')
  jspairs={
   'parameterIntentToWrittenMs':keyed(j['events'],'PARAM_INTENT','ADAPTER_WRITTEN','performanceMs'),
   'parameterResponseToContinuationMs':ordered(j['events'],'PARAM_RESPONSE','PARAM_CONTINUATION','performanceMs')}
  counts=collections.Counter(e['stage'] for e in n['events']);jc=collections.Counter(e['stage'] for e in j['events'])
  assert sum(n['stageCounts'].values())==len(n['events'])+n['sampledOut']
  assert sum(j['stageCounts'].values())==len(j['events'])+j['sampledOut']
  results.append({'trial':receipt['trial'],'cohortId':p['id'],'generation':a['generation'],'state':a['state'],'spanMs':span,'limitMs':3000,'marginMs':3000-span,'assessedAgeOfFirstMs':a['assessedAtMs']-p['firstAt'],'firstAtMs':p['firstAt'],'lastAtMs':p['lastAt'],'typedValues':decoded,'preExistingConnectedHistory':receipt['before'],'trace':{'member':name,'sha256':digest,'nativeEventN':len(n['events']),'jsEventN':len(j['events']),'nativeCounters':n['stageCounts'],'jsCounters':j['stageCounts'],'nativeRetainedCounts':dict(counts),'jsRetainedCounts':dict(jc),'nativeSampledOut':n['sampledOut'],'jsSampledOut':j['sampledOut'],'nativeOverflow':n['overflow'],'jsOverflow':j['overflow'],'nativeMatchedIntervals':natives,'jsMatchedIntervals':jspairs,'jsInspectionDurationMs':j['events'][-1]['performanceMs']-j['events'][0]['performanceMs'],'inFlightTail':{'receiptMinusWalDone':n['stageCounts'].get('RX_RECEIPT',0)-n['stageCounts'].get('RX_WAL_DONE',0),'deliveryMainMinusCallback':n['stageCounts'].get('DELIVERY_MAIN_READY',0)-n['stageCounts'].get('DELIVERY_JS_CALLBACK',0)},'allRXTimingsMeasured':False}})
 assert not src['errors'] and src['passiveTailOnlyDuringCohort'] is True
 old=ROOT/'evidence/crew02-qa/window04-causal06.json'
 r={'status':'PASS_SCOPED_THREE_AGED_TYPED_COHORTS_NOT_MISSION_ACCEPTANCE','run':RUN,'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [D/'aged-cohorts.json',D/'preflight-stage-and-crew.tar',oracle,old]},'decoder':'Pinned upstream MAVLink parser validates CRC and source42/1; read-only receipt rawHex is not final full-WAL continuity proof','sourceId':'6dbcdc048416df7a84f7eefb2a5f724517d80b42a40e14656cd34d1e249663a7','results':results,'oldC07Comparison':{'observedTypedCountBeforeFailure':10,'nativeSpanMs':3303,'jsObservedSpanLowerBoundMs':3470,'unchangedLimitMs':3000,'sameHardwareLoadMatchedAB':False,'rootCauseExclusiveAttribution':'UNKNOWN','interpretation':'Current three complete20-value cohorts pass this bounded workload; does not establish universal scheduling reliability or exclusive cause of improvement.'},'clockRules':['Only same-domain intervals subtracted; no WebView performance/native elapsed/host mono subtraction.','Native raw receipt and PARAM_VALUE timestamps are WAL append proxy; true AP acquisition/socket-to-append age UNKNOWN.','RX/DELIVERY sampling1-in8 and an in-flight tail prevent treating retainedEventComplete as complete RX stage causality.'],'scopeLimits':['Three stage files only; live crew snapshot in same tar is excluded.','No arm/AUTO/mission/review/authority/physical proof from this receipt.','Typed receipt rawHex CRC validated independently; final closed raw identity/sequence and mission receiver remain mandatory.']}
 r['analyzerSha256']=sha(Path(__file__))
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('x') as f:json.dump(r,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
 print(json.dumps({'status':r['status'],'output':str(OUT),'spansMs':[x['spanMs'] for x in results],'nativeStats':[x['trace']['nativeMatchedIntervals'] for x in results],'jsStats':[x['trace']['jsMatchedIntervals'] for x in results]}))
if __name__=='__main__':main()
