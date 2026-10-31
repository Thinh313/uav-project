"""Pure sampled-stat fault tests; runtime DiskGuard never receives these inputs."""
from pathlib import Path
import hashlib
import json
import sys
from collections import deque
R=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime02.journal.admission import ForecastWindow,DiskGuardError,DISK_POLICY


def main():
    cases=[]
    w=ForecastWindow()
    for i in range(15001):
        w.observe(i*1_000_000,24*2**30,priming=True)
    assert w.primed and len(w.samples)<=152 and w.last['historySpanNs']>=15_000_000_000
    cases.append({'case':'dense15001checks_preserve_true15s','checks':w.checks,'sampleCount':len(w.samples),'historySpanNs':w.last['historySpanNs'],'status':'PASS'})
    old=deque(maxlen=64)
    for i in range(64):
        ns=15_001_000_000+i*1_000
        free=24*2**30-(80*2**20 if i==63 else 0)
        old.append((ns,free))
        w.observe(ns,free)
    span=(old[-1][0]-old[0][0])/1e9
    old_forecast=old[-1][1]-(old[0][1]-old[-1][1])/max(.001,span)*15
    assert old_forecast<10*2**30+256*2**20
    assert w.last['forecastFreeBytes']>10*2**30+256*2**20 and w.last['historySpanNs']>=15_000_000_000
    cases.append({'case':'80MiB_APFS_like_burst_old64false_refusal_new_fullwindow_pass','oldSpanNs':old[-1][0]-old[0][0],
                  'oldForecast':old_forecast,'newForecast':w.last['forecastFreeBytes'],'newSpanNs':w.last['historySpanNs'],'status':'PASS'})
    s=ForecastWindow()
    try:
        for i in range(151):
            s.observe(i*100_000_000,25*2**30-int(i*.1*.5*2**30),priming=True)
        raise AssertionError('MUST_FAIL_PERSISTENT_DECLINE')
    except DiskGuardError as exc:
        assert str(exc)=='ACTUAL_HOST_DISK_FORECAST15_FLOOR10_RESERVE256'
        cases.append({'case':'persistent500MiBplus_persec_decline_still_refuses','diagnostic':exc.diagnostic,'status':'PASS'})
    for name,operation,expected in [
        ('no_synthetic_prime',lambda x:x.observe(0,24*2**30),'NOT_REAL_15S_PRIMED'),
        ('instant_perwrite_floor',lambda x:x.observe(0,10*2**30+256*2**20,1,priming=True),'FLOOR10_RESERVE256'),
        ('clock_regression',lambda x:(x.observe(100,24*2**30,priming=True),x.observe(99,24*2**30,priming=True)),'MONOTONIC_REGRESSION'),
        ('observation_gap',lambda x:(x.observe(0,24*2**30,priming=True),x.observe(3_000_000_000,24*2**30,priming=True)),'OBSERVATION_GAP'),
    ]:
        f=ForecastWindow()
        try:operation(f);raise AssertionError('MUST_FAIL_'+name)
        except DiskGuardError as exc:
            assert expected in str(exc)
            try:f.observe(3_100_000_000,30*2**30,priming=True);raise AssertionError('MUST_STAY_FENCED')
            except DiskGuardError as next_exc:assert 'GUARD_FAILED' in str(next_exc)
            cases.append({'case':name,'reason':str(exc),'status':'PASS'})
    out=R/'evidence/betaintegrated01-m1runtime/host02/guard-tests01.json'
    out.open('x').write(json.dumps({'status':'PASS_PURE_SAMPLED_STAT_FAULT_TESTS','cases':cases,
                       'sourceSHA256':hashlib.sha256((R/'pilot/betaintegrated01/runtime02/journal/admission.py').read_bytes()).hexdigest(),
                       'actualRuntimeGuardMocked':False,'liveRuntimeLaunches':0,'inputs':'DETERMINISTIC_TEST_SCENARIOS_NOT_ACTUAL01_GUARD_LOG'},indent=2)+'\n')
    print(json.dumps({'status':'PASS','cases':len(cases),'newSampleSpanNs':w.last['historySpanNs']}))


if __name__=='__main__':main()
