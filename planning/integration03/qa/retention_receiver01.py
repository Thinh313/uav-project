"""Independent actual native-WAL/Preflight03 diagnostic conservation receiver.
Closed canonical raw only. No runtime, ADB, or application writes.
"""
from pathlib import Path
import argparse,base64,collections,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];UTIL=ROOT/'evidence/operator01-qa/tools/receiver04.py';UTIL_SHA='a848da18ae5a84fadc7fc3a7effe991d93f0953fdd1eaa9196db89266df3f7f2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,msg):
 if not v:raise ValueError(msg)
def verify(run,pins):
 need(sha(UTIL)==UTIL_SHA,'upstream QA utility pin')
 sp=importlib.util.spec_from_file_location('retention_pinned_qa',UTIL);u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
 path=run/'android-raw.jsonl';rows,head,rawsha=u.chain(path);need(rows[0]['kind']=='META' and rows[-1]['kind']=='CLOSED','closed raw boundaries')
 dec=lambda r:json.loads(base64.b64decode(r['dataBase64'],validate=True));meta=dec(rows[0]);need(meta['sourceId']==pins['sourceId'] and meta['ownedLaunchAssertion']['run']==run.name,'source/run pins')
 req=[]
 for r in rows:
  if r['kind']=='PREFLIGHT':
   q=dec(r)
   if 'diagnostics03'in q:req.append((r,q))
 need(len(req)>=3,'at least3 durable diagnostics-bearing preflight receipts')
 offsets={};total=0
 with path.open('rb')as f:
  for n,line in enumerate(f,1):total+=len(line);offsets[n]=total
 byN={r['n']:r for r in rows};oracle=u.oracle();out=[];previous=None
 for receipt,q in req:
  d=q['diagnostics03'];a=q['assessment'];need(a['state']=='READY_SCOPED_READONLY' and not a['reasons'],'ready scoped20typed assessment')
  need(d['mode']=='NATIVE_WAL_SUMMARY03' and d['completeEventLog'] is False and d['headLimit']==32 and d['tailLimit']==256,'diagnostic-only contract')
  first,last=d['firstNativeWal'],d['lastNativeWal'];need(first['sequence']<=last['sequence']<receipt['n'],'diagnostic prefix before receipt')
  for v in [first,last]:
   r=byN[v['sequence']];b=base64.b64decode(r['dataBase64'],validate=True)
   need(r['kind']=='RX' and v['head']==r['sha256'] and v['walBytes']==offsets[r['n']],'exact committed RX prefix head/bytes')
   need(v['run']==run.name and v['sourceId']==pins['sourceId'] and v['session']==meta['session'] and v['boot']==meta['boot'],'prefix identity')
   need(v['byteLength']==len(b) and v['dataHexSha256']==hashlib.sha256(b.hex().encode()).hexdigest(),'immutable chunk bytes digest')
   need(0<=r['elapsedMs']-v['receiptMs']<=1500,'native receipt precedes bounded append proxy')
  rx=[r for r in rows if first['sequence']<=r['n']<=last['sequence'] and r['kind']=='RX']
  need(len(rx)==d['nativeChunks'] and sum(len(base64.b64decode(r['dataBase64']))for r in rx)==d['nativeBytes'],'every RX chunk/byte conserved through pinned prefix')
  stream=u.Stream(oracle);labels=collections.Counter(dict(ACCEPTED=0,FOREIGN=0,DUPLICATE=0,REORDERED=0));selectedSeq=None
  for r in rx:
   for f in stream.feed(base64.b64decode(r['dataBase64'],validate=True)):
    label='ACCEPTED'
    if(f.get_srcSystem(),f.get_srcComponent())!=(42,1):label='FOREIGN'
    elif selectedSeq is not None:
     delta=(f.get_seq()-selectedSeq)%256;need(delta!=128,'unexpected ambiguous selected seq in successful receipt')
     if delta==0:label='DUPLICATE'
     elif delta>128:label='REORDERED'
    labels[label]+=1
    if label=='ACCEPTED':selectedSeq=f.get_seq()
  n=sum(labels.values());need(n==d['totalClassifiedFrames'] and dict(labels)==d['labels'],'every complete frame/classification conserved')
  need(d['retainedEvents']==min(n,288) and d['evictedEvents']==max(0,n-288),'bounded disclosed retention arithmetic')
  if previous:
   need(first==previous['firstNativeWal'] and last['generation']==previous['lastNativeWal']['generation'],'no backing/session reset across cohorts')
   need(d['nativeChunks']>previous['nativeChunks'] and n>previous['totalClassifiedFrames'],'lifetime counters grow across explicit cohorts')
  previous=d
  out.append({'receiptRow':receipt['n'],'cohortId':a['cohortId'],'cohortSpanMs':a['cohortLastAtMs']-a['cohortFirstAtMs'],'nativeRXChunks':len(rx),'nativeRXBytes':d['nativeBytes'],'independentlyClassifiedFrames':n,'independentLabels':dict(labels),'retainedEvents':d['retainedEvents'],'evictedEvents':d['evictedEvents'],'prefixHead':last['head'],'prefixRow':last['sequence'],'partialMavlinkBytesAtPrefix':stream.parser.buf_len(),'startupTextBytes':stream.noise,'prefixClosed':False})
 need(sum(x['independentlyClassifiedFrames']>20000 for x in out)>=3,'three actual post20k successful cohorts mandatory')
 return {'status':'PASS_ACTUAL_NATIVE_WAL_BACKED_DIAGNOSTIC_CONSERVATION','run':run.name,'sourceId':pins['sourceId'],'canonicalRawSha256':rawsha,'canonicalRawHead':head,'canonicalRecords':len(rows),'results':out,'limits':['Each receipt proves its exact committed prefix; later raw must be separately accepted by mission receiver.','Native committed prefix is trusted pinned APK evidence, not hardware attestation/nonrepudiation.','No diagnostic frame log completeness claim; only authoritative raw byte/frame conservation recomputed.','Partial MAVLink boundary is disclosed and is not a dropped frame.','Three cohorts after20k do not certify indefinite session duration;900s native deadline/quotas remain.']}
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--pins',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();need(not a.output.exists(),'immutable output exists')
 try:r=verify(a.run,json.loads(a.pins.read_text()));code=0
 except Exception as e:r={'status':'FAIL_OR_SCHEMA_UNSUPPORTED','errorType':type(e).__name__,'error':str(e),'run':str(a.run)};code=2
 r['receiverSha256']=sha(Path(__file__));r['pinnedQARawUtilitySha256']=UTIL_SHA;a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x')as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({'status':r['status'],'error':r.get('error'),'output':str(a.output)}));return code
if __name__=='__main__':raise SystemExit(main())
