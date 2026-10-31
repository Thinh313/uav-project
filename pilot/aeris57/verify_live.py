"""Read retained runs only. Never launches, repairs, retries or modifies source records."""
import datetime,hashlib,importlib.util,json,sys,math,collections
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=R/'evidence/aeris57'
spec=importlib.util.spec_from_file_location('retained_readback53',R/'pilot/simtrain53/readback.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def digest(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
runs=[]
ledger=[json.loads(p.read_text())for p in sorted((E/'workspace').glob('*.json'))];ids=[x['data']['owner']['run']for x in ledger if x['kind']=='OUTCOME'and x['data'].get('route')=='start'and 'owner'in x['data']]
assert len(ids)==len(set(ids))
for rid in ids:
    out=R/'evidence/simtrain53/runs'/rid
    launch=json.loads((out/'launch.json').read_text());closed=json.loads((out/'closure.json').read_text());backend=json.loads((out/'backend-result.json').read_text())
    assert launch['rateHz']==1200 and launch['speedup']==1 and launch['negativeDebtCapUs']==500000
    assert closed['backendExited'] and closed['ownedContainerStopped']
    row={'run':rid,'closure':closed,'rateHz':launch['rateHz'],'speedup':1,'capUs':500000,'backendFrames':backend['frames'],'actualImages':0,'apSha256':launch['apSha256'],'backendRTF':backend['activeReceiveRTF'],'fullG1Accepted':False}
    if (out/'readback.json').exists():
        rb=json.loads((out/'readback.json').read_text());assert rb['status']=='PASS_RAW_CAPTURE_ORIGINAL_ORACLE_AND_CORRELATION' and closed['error']is None
        row['currentRawFiles']=[{'file':n,'pass':digest(out/n)==h,'sha256':h} for n,h in rb['filesSha256'].items()]
        assert all(x['pass']for x in row['currentRawFiles'])
        row.update({'readbackStatus':rb['status'],'oracleFrames':rb['exactOriginalSensorAndAuxFrames'],'takeoffAndLandObserved':rb['takeoffAndLandPhysicalObservations'],'nonNeutralRCFrames':rb['manualNonNeutralRCFrames'],'releaseReasons':rb['releaseReasons'],'fiveSecondWindows':rb['fiveSecondWindows'],'receiveGapsMs':rb['hostReceiveGapsMs'],'nodeBackendClockIntervalWidthMs':rb['nodeBackendClockIntervalWidthMs'],'guestHostClock':rb['guestHostClock']})
    else:
        assert closed['error']=='UNREQUESTED_BACKEND_END_OR_DEADLINE'
        row['readbackStatus']='NOT_ACCEPTED_FAILED_DEADLINE'
    # Re-read WAL CRC/hash-chain and RX/INTENT/SENT conservation for successful AND failed run.
    kinds=collections.Counter();last=None;phase='HEADER';frames=0
    for record in mod.records(out/'frames.wal'):
        kind=record['kind'];kinds[kind]+=1
        if kind=='HEADER':assert phase=='HEADER';phase='RX';continue
        if kind=='CLOSE':assert phase=='RX';phase='CLOSED';continue
        assert kind==phase
        if kind=='RX':
            if last is not None:assert record['frame']==last+1
            last=record['frame'];phase='INTENT'
        elif kind=='INTENT':assert record['frame']==last;phase='SENT'
        elif kind=='SENT':assert record['frame']==last;frames+=1;phase='RX'
    assert phase=='CLOSED'and frames==backend['frames']
    row.update({'walCRCChain':'PASS','walKinds':dict(kinds),'conservedFrames':frames,'failedClosureStillFailed':closed['error']is not None})
    runs.append(row)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_RETAINED_INTEGRITY_NOT_PACING_ACCEPTANCE','runs':runs,'successfulRawOracleFrames':sum(x.get('oracleFrames',0)for x in runs),'failedRunFramesKeptSeparate':sum(x['backendFrames']for x in runs if x['failedClosureStillFailed']),'allRunFramesPreserved':sum(x['conservedFrames']for x in runs),'fullG1Accepted':False,'scope':'Independent phase readback by same agent; source53 original-model validator remains original implementation, no independent human reviewer'}
with(E/'live-verification-complete.json').open('x')as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items()if k!='runs'}))
