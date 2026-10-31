from pathlib import Path
import base64,collections,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];P=R/'evidence/integration03-runtime/runs/s1195d1b6617880adb6c3/android-raw-current-diagnosis.jsonl';O=R/'evidence/integration03-qa/nominal-attempt01-unarmed.json'
assert not O.exists()
uPath=R/'evidence/operator01-qa/tools/receiver04.py';assert hashlib.sha256(uPath.read_bytes()).hexdigest()=='a848da18ae5a84fadc7fc3a7effe991d93f0953fdd1eaa9196db89266df3f7f2'
s=importlib.util.spec_from_file_location('u',uPath);u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
m=u.oracle();rows,head,digest=u.chain(P);stream=u.Stream(m);kinds=collections.Counter();events={};out=[];hb=[]
for r in rows:
 kinds[r['kind']]+=1;b=base64.b64decode(r['dataBase64'],validate=True)
 if r['kind']=='RX':
  for f in stream.feed(b):
   if f.get_msgId()==0 and f.get_srcSystem()==42 and f.get_srcComponent()==1:hb.append({'n':r['n'],'atMs':r['elapsedMs'],'armed':bool(f.base_mode&128),'mode':f.custom_mode})
 elif r['kind']=='TX_WRITTEN':
  f=u.single(m,b);out.append({'n':r['n'],'atMs':r['elapsedMs'],'message':f.get_type(),'msgId':f.get_msgId(),'command':getattr(f,'command',None),'customMode':getattr(f,'custom_mode',None),'targetSystem':getattr(f,'target_system',None),'targetComponent':getattr(f,'target_component',None)})
 elif r['kind'] in ['CLOSED','FLIGHT_DOMAIN_FAILURE01','AUTO_INTENT','AUTO_OBSERVED','ARM_INTENT','POST_ARM_HOME_REVIEW_REQUIRED','CREW_REVOKE']:
  try:q=json.loads(b)
  except Exception:q={'nonJson':True}
  events.setdefault(r['kind'],[]).append({'n':r['n'],'atMs':r['elapsedMs'],'data':q})
stream.finish()
arm=[q for q in out if q['command']==400];auto=[q for q in out if q['msgId']==11 and q['customMode']==3 or q['command']==176]
assert rows[-1]['kind']=='CLOSED' and not arm and not auto and not any(q['armed'] for q in hb)
assert not events.get('AUTO_INTENT') and not events.get('AUTO_OBSERVED') and not events.get('POST_ARM_HOME_REVIEW_REQUIRED')
r={'status':'UNARMED_ATTEMPT_CLOSED_NOT_NOMINAL_ACCEPTANCE','run':'s1195d1b6617880adb6c3','input':str(P.relative_to(R)),'sha256':digest,'rawHead':head,'records':len(rows),'kinds':dict(kinds),'decodedOutgoingCount':len(out),'armCommand400':arm,'setModeAutoOrCommand176':auto,'heartbeatN':len(hb),'anyObservedArmed':any(x['armed'] for x in hb),'observedModes':sorted(set(x['mode'] for x in hb)),'closureAndSafetyEvents':events,'sourceOrHarnessCause':'UNKNOWN_FROM_RAW_ALONE','qualification':'Closed raw proves no arm/AUTO in this interval. Root reports mistaken proposal sid comparison and UI coordinates; raw cannot identify the physical tap/hitbox cause by itself. Existing aged-cohort proof is separately retained; this attempt does not satisfy nominal mission/consent/capture AC.'}
with O.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({'status':r['status'],'records':len(rows),'outgoing':len(out),'heartbeatN':len(hb),'events':events,'output':str(O)}))
