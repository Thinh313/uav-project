"""Cold-process readback with independently expressed SHA/count/model checks.

Pinned manifest is local, not trusted external authentication. No writes except
exclusive output receipt supplied under this module's evidence directory.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import shutil
import sys
import oracle

ROOT=pathlib.Path(__file__).resolve().parents[2]


def H(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args()
    run=pathlib.Path(a.run).resolve();out=pathlib.Path(a.out).resolve()
    if not run.is_relative_to(ROOT/'evidence/simfeedback75') or not out.is_relative_to(ROOT/'evidence/simfeedback75'):
        raise ValueError('OUTPUT_SCOPE')
    index=json.loads((run/'corpus-index.json').read_text());results=json.loads((run/'results.json').read_text())
    assert results['passed']==results['total']==len(results['rows']) and all(r['pass'] for r in results['rows'])
    sys.path.insert(0,str(ROOT/'pilot/sim32'))
    spec=importlib.util.spec_from_file_location('cold_reference75',ROOT/'pilot/sim32/physics.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    frames=0;recomputed=0;rows=[]
    for entry in index['traces']:
        path=(run/entry['file']).resolve();assert path.is_relative_to(run) and path.is_file()
        d=json.loads(path.read_text());t=d['trace'];h=t['header'];assert h==entry['header'] and t['head']==entry['head']
        assert h['assurance']=='MOCK_ONLY' and h['units']=='SI' and h['world']=='NED' and h['body']=='FRD'
        assert h['modelSha256']==H({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [
            'pilot/sim32/physics.py','pilot/sim32/kernel.c','pilot/sim32/_sim32_kernel.cpython-314-darwin.so']})
        previous=H(h);last=-1.
        assert t['count']==len(t['rows'])>0
        if 'case' in d:
            c=d['case'];m=mod.Model(mod.profile(c['load'],c['wind'],c['seed']));m.y[2]=-20.;m.u=[math.sqrt(m.mass*mod.G/88)]*4
            assert h['profileSha256']==H(m.p) and len(d['inputs'])==len(t['rows'])
        else:
            assert h['profileSha256']==H(d['policy'])
        for i,row in enumerate(t['rows']):
            assert row['seq']==i and row['previous']==previous
            assert row['sha256']==H({k:row[k] for k in ['seq','previous','sample']})
            s=row['sample'];assert s['t']>last and all(s[k]==h[k] for k in ['target','session','boot'])
            assert s['kind']=='MODEL_STATE' and abs(sum(x*x for x in s['quaternion'])-1)<1e-9
            assert all(math.isfinite(x) for k in ['position','velocity','quaternion'] for x in s[k])
            last=s['t'];previous=row['sha256'];frames+=1
            if 'case' in d:
                m.step(d['inputs'][i],c['dt'])
                assert m.y[:3]==s['position'] and m.y[3:6]==s['velocity'] and m.y[6:10]==s['quaternion'] and m.t==s['t']
                recomputed+=1
            else:
                assert s['position'][0]+.3 <= 9.+1e-10
        assert previous==t['head'];rows.append({'id':entry['id'],'frames':len(t['rows']),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for c in index['cases']:
        if c['id'].startswith('COL-'):
            result=oracle.first_contact(c['start'],c['end'],c['radius'],c['shape']);expected=c['expectedFraction']
            assert (result is None)==(expected is None)
            if result is not None:assert abs(result-expected)<1e-7
    assert frames==6300 and recomputed==6000
    assert shutil.disk_usage(ROOT).free >= 20*1024**3+32*1024**2
    receipt={'status':'PASS_COLD_MOCK_READBACK','traces':len(rows),'frames':frames,'recomputedPhysicsFrames':recomputed,'rows':rows,
             'independentHumanReview':False,'heraValidated':False,'realFlightCommands':0,'scope':'Second hash/count implementation + frozen model deterministic replay; not physical calibration'}
    with out.open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps({k:v for k,v in receipt.items() if k!='rows'}))


if __name__=='__main__':main()
