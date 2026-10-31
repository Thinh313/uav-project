from pathlib import Path
import json,base64,tarfile,hashlib,sys
R=Path(__file__).resolve().parents[4];case=sys.argv[1];b=R/'evidence/betaintegrated01-m1control01'/case/'control';o=R/'evidence/betaintegrated01-m1control01/qa'/case
l=json.loads((b/'native-export-location.json').read_bytes());a=json.loads((b/'external-anchors.json').read_bytes());state=a['nativeClosedCheckpoint'];binding=json.loads((b/'launch-binding.json').read_bytes());inputs={};latest=None;lease=None;consents=[];renews=0;maxintent=0;maxwritten=0;checks=0;bindings={};posthome=[];actions=[];failures=[];offsets=[]
with tarfile.open(l['path'])as t:
 for f in sorted((x for x in t.getmembers()if x.isfile()and x.name.endswith('.jsonl')),key=lambda x:x.name):
  for line in t.extractfile(f):
   r=json.loads(line);k=r['kind'];raw=base64.b64decode(r['base64']);v=json.loads(raw)if k not in ('RX','TX_INTENT','TX_WRITTEN')else None
   if k=='CONTROL_INPUT':
    assert all(v[x]==state[x]for x in ('run','epoch','boot','generation'));assert v['operator']==binding['operator'];inputs[v['sequence']]=v;latest=v;offsets.append(v['elapsedNs']-v['uptimeNs'])
   elif k=='CONTROL_CONSENT':
    i=inputs[v['neutralInputSequence']];assert i['pointers']==0 and all(x==0 for x in i['axes'])and not i['release'];assert v['expiresNs']==i['elapsedNs']+200000000;lease=v['leaseId'];consents.append(v)
   elif k=='CONTROL_LEASE_RENEWED':assert v['leaseId']==lease and v['inputSequence']==latest['sequence']and v['expiresNs']==latest['elapsedNs']+200000000;renews+=1
   elif k=='CONTROL_REVOKED':lease=None
   elif k=='CONTROL_FAILURE':lease=None;failures.append(v)
   elif k=='CONTROL_INPUT_WIRE_BINDING':
    i=inputs[v['inputSequence']];assert lease==v['leaseId']and i['source']==v['source'];assert 0<=v['sendCheckNs']-i['elapsedNs']<=200000000;bindings[v['wireSHA256']]=i;checks+=1
   elif k in ('TX_INTENT','TX_WRITTEN'):
    i=bindings.get(hashlib.sha256(raw).hexdigest())
    if i:
     age=r['monotonicNs']-i['elapsedNs'];assert 0<=age<=200000000
     if k=='TX_INTENT':maxintent=max(maxintent,age)
     else:maxwritten=max(maxwritten,age)
   elif k=='POST_ARM_HOME_EXPLICITLY_CONFIRMED':
    assert v['postArmHomeObservedAtMs']>v['armObservedAtMs']and v['atMs']>=v['postArmHomeObservedAtMs'];h=v['confirmedHome'];assert hashlib.sha256(json.dumps(h,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==v['displayedHomeHash'];posthome.append(v)
   elif k=='OPERATOR_TOUCH_ACTION':actions.append(v['action'])
if inputs:assert max(offsets)-min(offsets)<=5000000
assert lease is None and state['closed']is True and state['input']['consent']is False and state['lifecycle']['phase']=='SEALED'
r={'status':'PASS_CLOSED_NATIVE_INPUT_AUTHORITY_BINDING_LOCAL_TIMING','inputs':len(inputs),'explicitConsents':len(consents),'producerLeaseRenewals':renews,'inputWireBindings':checks,'maxProducerToIntentNs':maxintent,'maxProducerToWrittenNs':maxwritten,'guestElapsedUptimeOffsetRangeNs':max(offsets)-min(offsets)if offsets else None,'postArmHome':posthome,'actions':actions,'failures':failures,'closedNoAuthorityRestore':True,'physicalTouchAttested':False,'remoteNetworkAge':'NOT_MEASURED'}
(o/'native-authority01.json').open('x').write(json.dumps(r,indent=2)+'\n');print(r['status'],checks,maxintent,maxwritten)
