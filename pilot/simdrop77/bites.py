"""Fault evidence mutations in memory only; no socket, control or raw rewrite."""
import copy
import hashlib
import json
import pathlib
import audit

R=pathlib.Path(__file__).resolve().parents[2];E=R/'evidence/simdrop77';raw=(E/'run01/wire.jsonl').read_bytes()
original_rows=[json.loads(line) for line in raw.splitlines()]


class Memory:
    def __init__(self,b):self.b=b
    def read_bytes(self):return self.b


def seal(rows):
    prev='0'*64;out=[]
    for i,r in enumerate(rows):
        r.pop('sha256',None);r['n']=i+1;r['prev']=prev
        body=json.dumps(r,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode();prev=hashlib.sha256(body).hexdigest();r['sha256']=prev
        out.append(json.dumps(r,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())
    return b'\n'.join(out)+b'\n'


def replay(rows):
    b=seal(rows);parsed=[json.loads(line) for line in b.splitlines()];data=audit.core.wire.analyze(Memory(b));return audit.verify_all(data,parsed,'rep01')


results=[]
def reject(id,fn):
    try:fn()
    except (AssertionError,ValueError,KeyError) as e:results.append({'id':id,'rejected':True,'reason':str(e),'type':type(e).__name__})
    else:raise AssertionError('DID_NOT_BITE:'+id)


rows=copy.deepcopy(original_rows);cut=next(i for i,r in enumerate(rows) if r.get('name')=='DROP_CUT_COMMITTED')
sensor=next(copy.deepcopy(r) for r in rows if r['kind']=='TX_INTENT' and r['reason']=='VIRTUAL_RAYS')
sensor.update(reason='INJECTED_AFTER_CUT',at=rows[cut]['at']+1);returned={'kind':'TX_WRITE_RETURN','reason':sensor['reason'],'rawHex':sensor['rawHex'],'at':sensor['at']+1}
rows[cut+1:cut+1]=[sensor,returned]
reject('sensor-continued-after-claimed-cut-valid-chain',lambda:replay(rows))
rows=copy.deepcopy(original_rows);cut=next(i for i,r in enumerate(rows) if r.get('name')=='DROP_CUT_COMMITTED')
neutral=next(copy.deepcopy(r) for r in rows if r['kind']=='TX_INTENT' and r['reason']=='HELD_RC_INPUT' and audit.core.wire.Parser().push(bytes.fromhex(r['rawHex']),0)[0]['fields']['chan2_raw']==1500)
neutral.update(at=rows[cut]['at']+1);returned={'kind':'TX_WRITE_RETURN','reason':neutral['reason'],'rawHex':neutral['rawHex'],'at':neutral['at']+1};rows[cut+1:cut+1]=[neutral,returned]
reject('hidden-neutral-before-observation-end-valid-chain',lambda:replay(rows))
rows=copy.deepcopy(original_rows);cut=next(i for i,r in enumerate(rows) if r.get('name')=='DROP_CUT_COMMITTED')
param=next(copy.deepcopy(r) for r in rows if r['kind']=='TX_INTENT' and r['reason']=='SET_AVOID:0');param['at']=rows[cut]['at']+1
returned={'kind':'TX_WRITE_RETURN','reason':param['reason'],'rawHex':param['rawHex'],'at':param['at']+1};rows[cut+1:cut+1]=[param,returned]
reject('hidden-disable-avoidance-during-loss-valid-chain',lambda:replay(rows))
rows=copy.deepcopy(original_rows)
for r in rows:
    if r.get('name')=='DROP_END':r['data']['guestDurationMs']=8000
reject('forged-eight-second-window-valid-chain',lambda:replay(rows))
rows=[copy.deepcopy(r) for r in original_rows if r.get('name')!='EXPERIMENTER_NEUTRAL_AFTER_ENDPOINT']
reject('missing-intervention-boundary-valid-chain',lambda:replay(rows))
rows=[copy.deepcopy(r) for r in original_rows if r.get('name')!='LANDED_DISARMED']
reject('missing-landing-evidence-valid-chain',lambda:replay(rows))
data=audit.core.wire.analyze(Memory(raw));valid=audit.verify_all(data,original_rows,'rep01')
assert valid['loss']['classification']=='UNSAFE_VIRTUAL_CONTACT' and valid['safetyPass'] is False
def false_claim():
    assert valid['loss']['classification']=='SAFE_STOP_OBSERVED','FALSE_SAFE_LABEL'
reject('unsafe-observation-cannot-be-labelled-safe',false_claim)
receipt={'status':'PASS_NO_FALSE_SAFE_BITES','passed':len(results),'total':len(results),'rows':results,
         'diagnosticObservationAccepted':valid['observationsAccepted'],'safetyPass':valid['safetyPass'],
         'rawSha256':hashlib.sha256(raw).hexdigest(),'originalUnchanged':hashlib.sha256((E/'run01/wire.jsonl').read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest(),
         'scope':'Six resealed raw/evidence adversaries and one explicit false-safe assertion; no mutated raw files or control commands'}
with (E/'bites.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps({'passed':len(results),'total':len(results),'safetyPass':False}))
