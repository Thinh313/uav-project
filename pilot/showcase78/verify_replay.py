"""Check presentation poses against exact WAL samples and controller axes against actual logged TX."""
import hashlib,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=R/'evidence/showcase78';run=R/'evidence/simtrain53/runs/rad3ab2ece4a54e38a4ba'
desc=json.loads((E/'replay-descriptor.json').read_text());data=(E/'flight-replay.json').read_bytes();replay=json.loads(data);receipt=json.loads((run/'readback.json').read_text())
assert hashlib.sha256(data).hexdigest()==desc['sha256']
for n,expected in [('frames.wal',replay['sourceSha256']),('mavlink.jsonl',replay['inputSourceSha256'])]:
 with(run/n).open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected==receipt['filesSha256'][n]
events={e['index']:e for e in map(json.loads,(run/'mavlink.jsonl').open())};samples={p['frame']:p for p in replay['samples']};assert len(samples)==len(replay['samples'])==3366
spec=importlib.util.spec_from_file_location('reader53',R/'pilot/simtrain53/readback.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);checked=0;input_checked=0
for rec in m.records(run/'frames.wal'):
 if rec['kind']!='INTENT' or rec['frame']%40:continue
 body,_=m.unpack_intent(rec['body']);a=json.loads(body)['modelAux'];p=samples[rec['frame']]
 assert all(p[k]==a[k]for k in ['timestamp','position','velocity','quaternion','rpmEstimated','massKg','ground'])
 if p['inputRecorded']:
  e=events[p['inputLocalTxIndex']];assert e['kind']=='RC_TX_INTENT' and events[e['index']+1]['kind']=='RC_LOCAL_WRITE_RETURN'
  roll,pitch,lift,yaw=e['data']['channels'][:4];assert p['inputAxes']==[(roll-1500)/300,(1500-pitch)/300,(yaw-1500)/300,(lift-1500)/300];assert 0<=p['inputApproximateAgeMs']<=200;input_checked+=1
 else:assert p['inputAxes'] is None
 checked+=1
assert checked==3366 and input_checked==1073 and 'not AP RC echo' in replay['inputAlignment']
result={'status':'PASS_EXACT_SELECTED_WAL_POSES_AND_LOGGED_TX_AXES','selectedPoses':checked,'recordedInputSamples':input_checked,'nonNeutralInputSamples':desc['nonNeutralRenderSamples'],'sourceRawIntents':receipt['frames'],'alignment':'APPROXIMATE_CLOCK_BRACKET_MIDPOINT_NOT_LATENCY_OR_AP_EXECUTION','flightCommandsSentByReplay':0,'sha256':desc['sha256'],'scope':'Single-agent check; selected display frames only, original WAL unchanged'}
with(E/'replay-verification.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
