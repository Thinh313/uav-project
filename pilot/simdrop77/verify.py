"""Independent raw decoding via read-only76 Python parser, new77 semantics.

Success of evidence collection and the safety behavior outcome are separate.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import shutil

R=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('read_only_sit76',R/'pilot/simsitl76/verify.py');wire=importlib.util.module_from_spec(spec);spec.loader.exec_module(wire)
SCHEDULE={'rep01':['BASELINE','ENABLED'],'rep02':['ENABLED','BASELINE'],'rep03':['ENABLED','BASELINE'],'rep04':['BASELINE','ENABLED']}


def classification(clearance,duration,speed):
    if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in [clearance,duration,speed]):raise ValueError('FINITE')
    if duration<0 or speed<0:raise ValueError('DOMAIN')
    if clearance<=0:return 'UNSAFE_VIRTUAL_CONTACT'
    if clearance<1.2:return 'UNSAFE_CLEARANCE_LOSS'
    if duration>=8000 and speed<=.5:return 'SAFE_STOP_OBSERVED'
    return 'INCONCLUSIVE'


def verify(data,rows,replication):
    frames=data['frames'];marks=data['marks'];order=SCHEDULE[replication];controls=[]
    def window(a,b):return [f for f in frames if marks[a]['at']<=f['at']<=marks[b]['at']]
    def metrics(f):
        positions=[p for p in f if p['id']==32];assert len(positions)>20
        tail=[p for p in positions if p['at']>=positions[-1]['at']-3000]
        return {'samples':len(positions),'minimumClearanceM':min(11.7-p['fields']['x'] for p in positions),
                'maximumX':max(p['fields']['x'] for p in positions),'tailMaxSpeedMps':max(abs(p['fields']['vx']) for p in tail)}
    assert marks[order[0]+'_START']['n']<marks[order[1]+'_START']['n']
    for name in order:
        w=window(name+'_START',name+'_END');m=metrics(w)
        if name=='BASELINE':assert m['maximumX']>12.3
        else:
            assert m['maximumX']>7 and m['minimumClearanceM']>=1.2 and m['tailMaxSpeedMps']<=.5
            assert any(f['id']==132 and f['fields']['orientation']==0 and f['fields']['current_distance']<350 for f in w)
        assert any(f['id']==65 and f['fields']['chan2_raw']==1400 for f in w)
        controls.append({'name':name,**m})
    stable=metrics(window('DROP_APPROACH_START','DROP_APPROACH_END'));assert stable['minimumClearanceM']>=1.2 and stable['tailMaxSpeedMps']<=.5 and stable['maximumX']>7
    request,cut,end=marks['DROP_REQUEST'],marks['DROP_CUT_COMMITTED'],marks['DROP_END']
    assert request['n']<cut['n']<end['n']<marks['EXPERIMENTER_NEUTRAL_AFTER_ENDPOINT']['n']
    drop=window('DROP_REQUEST','DROP_END');m=metrics(drop);tx=[]
    for row in rows:
        if row['kind']!='TX_INTENT' or not request['n']<row['n']<end['n']:continue
        p=wire.Parser();decoded=p.push(bytes.fromhex(row['rawHex']),row['at']);assert not p.buffer
        for f in decoded:
            if row['n']>cut['n']:assert f['id']!=132,'SENSOR_SENT_AFTER_COMMITTED_CUT'
            if f['id']==70:
                assert [f['fields'][f'chan{i}_raw'] for i in range(1,5)]==[1500,1400,1500,1500],'FORWARD_NOT_HELD'
                tx.append(f)
            assert f['id']!=84 and not(f['id']==76 and f['fields']['command'] in [176,400,22]),'MODE_OR_CONTROL_INTERVENTION'
    assert len(tx)>=5
    echoed=[f for f in drop if f['id']==65];assert len(echoed)>=4 and all(f['fields']['chan2_raw']==1400 and f['fields']['chan4_raw']==1500 for f in echoed),'RC_ECHO_NOT_HELD'
    heartbeats=[f for f in drop if f['id']==0];assert heartbeats and all(f['fields']['custom_mode']==5 and f['fields']['base_mode']&128 for f in heartbeats),'MODE_OR_ARM_CHANGED'
    at_cut=[f for f in frames if f['id']==30 and f['at']<=cut['at']][-1]
    boot=cut['data']['bootMs'];assert abs(at_cut['fields']['time_boot_ms']-boot)<=100,'CUT_CLOCK_BIND'
    last=[f for f in drop if f['id']==30][-1];duration=last['fields']['time_boot_ms']-boot
    assert abs(duration-end['data']['guestDurationMs'])<=100,'END_CLOCK_BIND'
    prox=[f for f in frames if f['id']==132 and f['fields']['orientation']==0 and f['at']<=end['at']][-1]
    age=last['fields']['time_boot_ms']-prox['fields']['time_boot_ms'];assert age>700,'PROXIMITY_NOT_EXPIRED'
    outcome=classification(m['minimumClearanceM'],duration,m['tailMaxSpeedMps']);assert outcome!='INCONCLUSIVE','INCONCLUSIVE_FAULT_WINDOW'
    assert end['data']['reason'] in ['VIRTUAL_PLANE_BOUND','GUEST_8S']
    if end['data']['reason']=='VIRTUAL_PLANE_BOUND':assert m['maximumX']>12.3
    else:assert duration>=8000
    restore=marks['SENSOR_RESTORE_REQUEST'];assert restore['n']>end['n']
    assert any(f['id']==132 and f['at']>restore['at'] for f in frames),'NO_RESTORE_OUTPUT'
    land_at=marks['LANDED_DISARMED']['at'];hb=[f for f in frames if f['id']==0 and f['at']<=land_at][-1];land=[f for f in frames if f['id']==245 and f['at']<=land_at][-1]
    assert not(hb['fields']['base_mode']&128) and land['fields']['landed_state']==1
    return {'controls':controls,'stableBeforeCut':stable,'loss':{**m,'classification':outcome,'guestDurationMs':duration,'expiredAgeGuestMs':age,'heldTxFrames':len(tx),'rcEchoFrames':len(echoed),'neutralInterventionAfterEndpoint':True},'observationsAccepted':True,'safetyPass':outcome=='SAFE_STOP_OBSERVED'}


def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args();run=pathlib.Path(a.run).resolve();out=pathlib.Path(a.out).resolve()
    assert run.is_relative_to(R/'evidence/simdrop77') and out.is_relative_to(R/'evidence/simdrop77')
    launch=json.loads((run/'launch.json').read_text());closure=json.loads((run/'closure.json').read_text());driver=json.loads((run/'driver-result.json').read_text())
    assert closure['containerRemoved'] and closure['containerId']==launch['containerId'] and closure['driverExitCode']==0 and closure['error'] is None
    data=wire.analyze(run/'wire.jsonl');rows=[json.loads(line) for line in (run/'wire.jsonl').read_bytes().splitlines()];result=verify(data,rows,launch['replication'])
    assert result['loss']['classification']==driver['loss']['classification'],'DRIVER_COLD_CLASSIFICATION_MISMATCH'
    receipt={'status':'OBSERVATIONS_VERIFIED_NOT_BLANKET_SAFETY_PASS','replication':launch['replication'],'run':launch['run'],'order':SCHEDULE[launch['replication']],**result,
             'raw':{k:data[k] for k in ['rows','head','sensorBatches','sha256','bootNoiseBytes']},'apFrames':len(data['frames']),'txFrames':len(data['tx']),
             'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_HERA_OR_SIM32','independentHumanReview':False}
    assert shutil.disk_usage(R).free>20*2**30+65536
    with out.open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps({k:receipt[k] for k in ['status','replication','safetyPass','loss','apFrames']}))


if __name__=='__main__':main()
