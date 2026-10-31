"""Four-replicate aggregation with raw/source consistency and honest outcome."""
import argparse
import hashlib
import json
import pathlib
import shutil
import audit

R=pathlib.Path(__file__).resolve().parents[2];E=R/'evidence/simdrop77'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args();out=pathlib.Path(args.out).resolve();assert out.is_relative_to(E)
    receipts=[];common=None;timings=[];rawcount=0;txcount=0;qualified=set();ledgers=[]
    for f in sorted(E.glob('run*/container-created.json')):
        run=f.parent;closure=json.loads((run/'closure.json').read_text());assert closure['containerRemoved']
        ledgers.append({'run':run.name,'containerId':closure['containerId'],'driverExitCode':closure['driverExitCode'],'error':closure['error']})
    for f in sorted(E.glob('cold-run*.json')):
        receipt=json.loads(f.read_text());rep=receipt['replication'];assert rep not in qualified;qualified.add(rep)
        assert receipt['observationsAccepted'] and receipt['status']=='OBSERVATIONS_VERIFIED_NOT_BLANKET_SAFETY_PASS'
        run=E/receipt['run'];assert sha(run/'wire.jsonl')==receipt['rawSha256']
        pins=json.loads((run/'source-pins.json').read_text())['files']
        if common is None:common=pins
        else:assert pins==common,'MIXED_CONFIG_OR_OPERATIONAL_SOURCE'
        for name,h in pins.items():assert sha(R/name)==h,'SOURCE_DRIFT'
        data=audit.core.wire.analyze(run/'wire.jsonl');rows=[json.loads(line) for line in (run/'wire.jsonl').read_bytes().splitlines()]
        checked=audit.verify_all(data,rows,rep);assert checked['loss']==receipt['loss'] and checked['controls']==receipt['controls']
        start,end=data['marks']['DROP_REQUEST']['at'],data['marks']['DROP_END']['at'];cut_boot=data['marks']['DROP_CUT_COMMITTED']['data']['bootMs']
        positions=[f for f in data['frames'] if f['id']==32 and start<=f['at']<=end]
        contacts=[i for i,f in enumerate(positions) if f['fields']['x']+.3>=12]
        bracket=None
        if contacts:
            i=contacts[0];bracket={'lastNoncontactGuestMs':positions[i-1]['fields']['time_boot_ms']-cut_boot if i else None,
                                'firstSampledContactGuestMs':positions[i]['fields']['time_boot_ms']-cut_boot,
                                'scope':'Sampling bracket relative to AP boot reference at committed cutoff; not exact impact/one-way latency'}
        timings.append({'replication':rep,'run':receipt['run'],'contactTiming':bracket})
        receipts.append(receipt);rawcount+=receipt['apFrames'];txcount+=receipt['txFrames']
    assert qualified==set(audit.core.SCHEDULE),'FOUR_REQUIRED_REPLICATIONS_NOT_COMPLETE'
    counts={}
    for r in receipts:counts[r['loss']['classification']]=counts.get(r['loss']['classification'],0)+1
    assert sum(r['order'][0]=='BASELINE' for r in receipts)==2 and sum(r['order'][0]=='ENABLED' for r in receipts)==2
    enabled=[next(c for c in r['controls'] if c['name']=='ENABLED') for r in receipts]
    baseline=[next(c for c in r['controls'] if c['name']=='BASELINE') for r in receipts]
    result={'status':'DIAGNOSTIC_COMPLETE_SAFETY_GAP_CONFIRMED' if any(not r['safetyPass'] for r in receipts) else 'DIAGNOSTIC_COMPLETE_SCOPED_SAFE_OBSERVATIONS',
            'qualifiedReplications':4,'actualContainerLedger':ledgers,'orders':{r['replication']:r['order'] for r in receipts},'lossClassifications':counts,
            'lossSafetyPass':all(r['safetyPass'] for r in receipts),'controlsQualified':4,'apFrames':rawcount,'txFrames':txcount,
            'enabledMinimumClearanceRangeM':[min(c['minimumClearanceM'] for c in enabled),max(c['minimumClearanceM'] for c in enabled)],
            'enabledTailMaxSpeedRangeMps':[min(c['tailMaxSpeedMps'] for c in enabled),max(c['tailMaxSpeedMps'] for c in enabled)],
            'baselineMaximumXRangeM':[min(c['maximumX'] for c in baseline),max(c['maximumX'] for c in baseline)],
            'lossObservationDurationRangeGuestMs':[min(r['loss']['guestDurationMs'] for r in receipts),max(r['loss']['guestDurationMs'] for r in receipts)],
            'contactTiming':timings,'replicateReceipts':{r['run']:sha(E/('cold-'+r['run']+'.json')) for r in receipts},
            'sameOperationalSourceAndConfig':True,'statisticalSuperiorityClaim':False,'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_HERA_OR_SIM32',
            'limits':['four functional trials only','no actual collision response/Hera/HID/SDK','no loaded/gust or real sensor noise/FOV','no stable1x external backend acceptance']}
    assert shutil.disk_usage(R).free>20*2**30+65536
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:result[k] for k in ['status','qualifiedReplications','lossClassifications','apFrames','enabledMinimumClearanceRangeM']}))


if __name__=='__main__':main()
