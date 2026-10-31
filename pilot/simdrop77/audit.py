"""Supplementary independent source/config/clock checks, no flight commands."""
import argparse
import hashlib
import json
import math
import pathlib
import shutil
import verify as core

R=pathlib.Path(__file__).resolve().parents[2]


def verify_all(data,rows,replication):
    result=core.verify(data,rows,replication);frames=data['frames'];marks=data['marks'];tx=data['tx']
    checks=[]
    for name,expected in [('BASELINE',0),('ENABLED',2),('DROP_APPROACH',2)]:
        start,end=marks[name+'_START']['at'],marks[name+'_END']['at']
        sets=[f for f in tx if f['id']==23 and f['fields']['param_id']=='AVOID_ENABLE' and f['at']<=start]
        assert sets and sets[-1]['fields']['param_type']==2 and sets[-1]['fields']['param_value']==expected,'CONFIG_SET_NOT_BOUND'
        reads=[f for f in frames if f['id']==22 and f['fields']['param_id']=='AVOID_ENABLE' and sets[-1]['at']<=f['at']<=start]
        assert reads and reads[-1]['fields']['param_type']==2 and reads[-1]['fields']['param_value']==expected,'CONFIG_READBACK_NOT_BOUND'
        assert not any(f['id']==23 and start<f['at']<end for f in tx),'HIDDEN_PARAM_CHANGE'
        checks.append({'phase':name,'avoidanceReadback':expected,'readbackHostMs':reads[-1]['at']})
    assert not any(f['id']==23 and marks['DROP_REQUEST']['at']<=f['at']<=marks['DROP_END']['at'] for f in tx),'PARAM_CHANGE_DURING_LOSS'
    old={}
    for f in frames:
        p=f['fields']
        if 'time_boot_ms' in p:
            t=p['time_boot_ms']
            if f['id'] in old:assert (t-old[f['id']])%2**32<2**31,'BOOT_CLOCK_REGRESSION'
            old[f['id']]=t
        if f['id'] in [30,32]:assert all(math.isfinite(v) for v in p.values()),'NONFINITE_TRAJECTORY'
    connects=[r for r in rows if r['kind']=='CONNECT'];assert len(connects)==1
    m=connects[0]['manifest'];assert m['scope']=='OWNED_REAL_SIMDROP77' and m['target']=='42/1' and m['boot']==m['startedAt']
    result['configurationChecks']=checks;result['bootClocksChecked']=len(old)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args()
    run=pathlib.Path(a.run).resolve();out=pathlib.Path(a.out).resolve();assert run.is_relative_to(R/'evidence/simdrop77') and out.is_relative_to(R/'evidence/simdrop77')
    launch=json.loads((run/'launch.json').read_text());close=json.loads((run/'closure.json').read_text());driver=json.loads((run/'driver-result.json').read_text())
    assert close['containerRemoved'] and close['containerId']==launch['containerId'] and close['driverExitCode']==0 and close['error'] is None
    raw=(run/'wire.jsonl').read_bytes();rows=[json.loads(line) for line in raw.splitlines()];data=core.wire.analyze(run/'wire.jsonl')
    header=rows[0]['manifest'];assert header['containerId']==launch['containerId'] and header['pid']==launch['pid'] and header['startedAt']==launch['startedAt']
    result=verify_all(data,rows,launch['replication']);assert result['loss']['classification']==driver['loss']['classification']
    receipt={'status':'OBSERVATIONS_VERIFIED_NOT_BLANKET_SAFETY_PASS','run':launch['run'],'replication':launch['replication'],'order':core.SCHEDULE[launch['replication']],**result,
             'apFrames':len(data['frames']),'txFrames':len(data['tx']),'rawRows':data['rows'],'rawSha256':hashlib.sha256(raw).hexdigest(),'head':data['head'],
             'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_HERA_OR_SIM32','independentHumanReview':False}
    assert shutil.disk_usage(R).free>20*2**30+65536
    with out.open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps({k:receipt[k] for k in ['status','run','replication','safetyPass','loss','apFrames']}))


if __name__=='__main__':main()
