"""Independent closed-raw 20-parameter cohort/wire/request checker. No runtime."""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,math,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];UTIL=ROOT/'evidence/operator01-qa/tools/receiver04.py';PIN='a848da18ae5a84fadc7fc3a7effe991d93f0953fdd1eaa9196db89266df3f7f2'
TYPES={'MAV_SYSID':4,'MAV_GCS_SYSID':4,'SERIAL0_PROTOCOL':2,'ARMING_SKIPCHK':6,'BATT_MONITOR':2,'BATT_ARM_VOLT':9,'FENCE_ENABLE':2,'FENCE_TYPE':2,'FENCE_ACTION':2,'FENCE_RADIUS':9,'FENCE_MARGIN':9,'FS_GCS_ENABLE':2,'FS_GCS_TIMEOUT':9,'FS_OPTIONS':6,'RTL_ALT_M':9,'RTL_ALT_FINAL_M':9,'RTL_LOIT_TIME':6,'RTL_ALT_TYPE':2,'FENCE_ALT_MAX_TP':2,'GPS_HDOP_GOOD':4}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def verify(run,pins):
 need(sha(UTIL)==PIN,'pinned upstream utility');s=importlib.util.spec_from_file_location('typed_u',UTIL);u=importlib.util.module_from_spec(s);s.loader.exec_module(u);m=u.oracle();rows,head,rawsha=u.chain(run/'android-raw.jsonl');need(rows[0]['kind']=='META' and rows[-1]['kind']=='CLOSED','closed raw');dec=lambda r:json.loads(base64.b64decode(r['dataBase64']));meta=dec(rows[0]);need(meta['sourceId']==pins['sourceId'] and meta['ownedLaunchAssertion']['run']==run.name,'exact source/run');stream=u.Stream(m);params=[];requests=[];receipts=[]
 for r in rows:
  b=base64.b64decode(r['dataBase64'],validate=True)
  if r['kind']=='RX':
   for f in stream.feed(b):
    if(f.get_srcSystem(),f.get_srcComponent(),f.get_msgId())==(42,1,22):params.append((r,f,bytes(f.get_msgbuf())))
  elif r['kind']=='TX_WRITTEN':
   f=u.single(m,b);need(f.get_msgId()!=23,'no parameter write in preflightmissionrun')
   if f.get_msgId()==20 and(f.target_system,f.target_component)==(42,1):requests.append((r,f))
  elif r['kind']=='PREFLIGHT':receipts.append((r,dec(r)))
 stream.finish();result=[];previous=0
 for rr,q in receipts:
  d=q.get('diagnostics03',{})
  if d.get('totalClassifiedFrames',0)<=20000:previous=rr['n'];continue
  a=q['assessment'];p=q['parameters'];need(a['state']=='READY_SCOPED_READONLY' and not a['reasons'] and a['parameterWrites']==0 and a['armPermission']is False,'read-only scoped ready');need(set(p['values'])==set(TYPES)==set(a['parameters']),'exact20 required parameter names');need(p['id']==a['cohortId'] and p['firstAt']==a['cohortFirstAtMs'] and p['lastAt']==a['cohortLastAtMs'],'cohort time/context binding');span=p['lastAt']-p['firstAt'];need(0<=span<=3000,'unchanged3000ms native-read receiptspan');proof=[];lastrow=previous
  for name,type_ in TYPES.items():
   v=p['values'][name];b=bytes.fromhex(v['rawHex']);f=u.single(m,b);nameOnWire=f.param_id.decode()if isinstance(f.param_id,bytes)else f.param_id;need((f.get_srcSystem(),f.get_srcComponent(),f.get_msgId())==(42,1,22) and nameOnWire==name and f.param_type==v['type']==type_ and math.isclose(f.param_value,v['value'],abs_tol=1e-6) and v['value']==a['parameters'][name],'independent CRC/type/value/name:'+name)
   matches=[(r,x)for r,x,w in params if w==b and previous<r['n']<rr['n'] and 0<=r['elapsedMs']-v['at']<=1500];need(len(matches)==1,'unique samecohort rawframe:'+name);r,x=matches[0];need(r['n']>lastrow,'ordered formal cohort arrival');lastrow=r['n'];req=[(tr,tf)for tr,tf in requests if previous<tr['n']<r['n'] and tf.param_id==name];need(req,'actual ordered PARAM_REQUEST_READ:'+name);tr,tf=req[-1];need(tf.param_index==-1,'read by exact name');need(x.param_count==p['count'] and x.param_count>0 and x.param_index in(65535,v['index']),'count/index context');proof.append({'name':name,'type':type_,'value':v['value'],'nativeReadReceiptMs':v['at'],'requestTXRow':tr['n'],'responseRXCompleteRow':r['n'],'responseRXAppendMs':r['elapsedMs'],'wireSha256':hashlib.sha256(b).hexdigest()})
  proxySpan=proof[-1]['responseRXAppendMs']-proof[0]['responseRXAppendMs'];need(proxySpan<=3000,'independent raw append proxy span exceeds3000, timingdisagreementmustinvestigate');result.append({'preflightRow':rr['n'],'cohortId':p['id'],'generation':a['generation'],'state':a['state'],'typedValues':proof,'nativeReadReceiptSpanMs':span,'independentNativeAppendProxySpanMs':proxySpan,'historyClassifiedFrames':d['totalClassifiedFrames'],'automaticArmPermission':False});previous=rr['n']
 need(len(result)>=3,'three post20k actual typed ready cohorts mandatory');return{'status':'PASS_THREE_ACTUAL_POST20K_TYPED_COHORTS_RAW_REQUEST_RESPONSE_LAYER','run':run.name,'sourceId':pins['sourceId'],'rawSha256':rawsha,'rawHead':head,'rawRecords':len(rows),'results':result,'limitations':['Native receipt times are durableadapter self-report bound to independently decoded exact rawframes and native append-time proxy; no AP sensor acquisition/flight permission claim.','This is separate from diagnostic-counter/fullRX conservation receiver, missionacceptedreview and wholemilestone acceptance.']}
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--pins',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();need(not a.output.exists(),'immutableoutput')
 try:r=verify(a.run,json.loads(a.pins.read_text()));code=0
 except Exception as e:r={'status':'FAIL_OR_SCHEMA_UNSUPPORTED','errorType':type(e).__name__,'error':str(e),'run':str(a.run)};code=2
 r['receiverSha256']=sha(Path(__file__));a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x')as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({'status':r['status'],'error':r.get('error'),'output':str(a.output)}));return code
if __name__=='__main__':raise SystemExit(main())
