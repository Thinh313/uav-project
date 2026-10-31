"""Real guard, fsync journal capacity tests; no AP/network/runtime launches."""
from pathlib import Path
import sys,ast,json,hashlib
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime02.journal import SegmentedJournal,Policy,verify_journal,JournalError


def policy_from_frozen_transport():
    tree=ast.parse((R/'pilot/betaintegrated01/control03/transport.py').read_text())
    calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='Policy']
    assert len(calls)==1
    args={k.arg:eval(compile(ast.Expression(k.value),'policy','eval'),{'__builtins__':{}},{})for k in calls[0].keywords}
    assert args==dict(segment_bytes=1024*1024,quota_bytes=32*1024*1024,max_record_bytes=16384,max_segments=40,termination_reserve_bytes=32768)
    return Policy(**args)


def main():
    base=R/'evidence/betaintegrated01-m1control01/host/quota03-mock01';base.mkdir()
    policy=policy_from_frozen_transport();payload={'rawHex':'ab'*4096,'boundedMock':True};cases=[]
    good=SegmentedJournal(base/'close-after-old8MiB', 'quota-close','epoch-close',policy)
    while good.used<9*1024*1024:good.append_event('BOUNDED_TRANSPORT_RX',payload)
    assert good.used>8*1024*1024 and good.guard.prime_receipt['elapsedRealMonotonicNs']>=15_000_000_000
    commit=good.close();cold=verify_journal(good.root,'quota-close','epoch-close',expected_commit=commit['commitAnchor'])
    assert cold['state']=='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'
    cases.append({'case':'continues_beyond_old8MiB_then_closes_fsync_anchor','status':'PASS','usedBytes':good.used,'records':good.seq,'segments':good.segment+1,'coldState':cold['state']})
    full=SegmentedJournal(base/'finite32MiB-rejection-prefix','quota-full','epoch-full',policy)
    rejected=False
    try:
        while True:full.append_event('BOUNDED_TRANSPORT_RX',payload)
    except JournalError as e:
        assert str(e)=='FRAME_ADMISSION_QUOTA',str(e);rejected=True
    assert rejected and 31*1024*1024<full.used<32*1024*1024 and full.failed is not None
    before=full.used;full.abort('EXPECTED_FINITE_TRANSPORT_QUOTA')
    assert full.used>=before and full.used<=policy.quota_bytes
    assert not(full.root/'commit.json').exists()
    cases.append({'case':'finite32MiB_fails_closed_preserves_prefix_and_termination_reserve','status':'PASS','usedBytes':full.used,'segments':full.segment+1,'error':'FRAME_ADMISSION_QUOTA','hasCommit':False})
    result={'status':'PASS_REAL_GUARD_QUOTA_AND_TERMINATION','cases':cases,'policy':policy.__dict__,'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(R/'pilot/betaintegrated01/control03').glob('*.py')},'APStarts':0,'AndroidStarts':0,'realSocketsCreated':0,'budgetBytesOriginalCopyExport':96*1024*1024,'guardsUnchanged':True}
    (base/'results.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'cases':len(cases)}))
if __name__=='__main__':main()
