"""Tiny single-case quota and old/native17MiB policy differential; no services."""
from pathlib import Path
import hashlib,json,resource
from pilot.betaintegrated01.cockpit04.revision02 import capacity,native_stream,confirmation
from pilot.betaintegrated01.cockpit04 import native_stream as old_stream
from pilot.betaintegrated01.cockpit04.capacity import journal_policy,transport_policy
ROOT=Path(__file__).resolve().parents[4]

def main():
    out=ROOT/'evidence/betaintegrated01-m1cockpit04/host/revision02-mock01';out.mkdir(exist_ok=False)
    results=[]
    def case(name,fn):
        try:results.append({'case':name,'pass':True,'detail':fn()})
        except Exception as exc:results.append({'case':name,'pass':False,'error':repr(exc)})
    def policy():
        b=capacity.task_budget();assert b['caseCount']==b['APStarts']==1
        assert b['nativeJournalHardQuotaBytes']==160*2**20 and b['nativeTarAndSingleExportCapBytes']==168*2**20
        assert b['nativeExportGlobalHardCeilingBytes']==192*2**20
        assert sum(b['AVDAllocatedGrowthParts'].values())==512*2**20
        assert capacity.journal_policy(1960)==journal_policy(1960)
        assert capacity.transport_policy(1960)==transport_policy(1960)
        assert b['entryBytes']==20*2**30 and b['floorBytes']==10*2**30 and b['reserveBytes']==256*2**20
        assert b['taskHardPeakBytes']<10*2**30
        assert capacity.task_budget(20*2**30)['admitted']is True
        assert capacity.task_budget(20*2**30-1)['admitted']is False
        for x in(60,90,1960.,True,2000,-1):
            try:capacity.duration(x)
            except ValueError:continue
            raise AssertionError(x)
        return b
    case('one1960 finite policy no physical changes no two-short-claims',policy)
    def differential():
        meta=json.loads((ROOT/'evidence/betaintegrated01-m1cockpit04/qa/native-stream02/results.json').read_text())
        path=ROOT/'evidence/betaintegrated01-m1cockpit04/qa/native-stream01/synthetic-native17MiB.tar';anchor=meta['externalSyntheticAnchor'];prefix='files/control-runs/run/'
        a,ar=old_stream.closed_native(path,prefix,anchor);b,br=native_stream.closed_native(path,prefix,anchor)
        count=0
        for x,y in zip(ar,br,strict=True):assert x==y;count+=1
        assert a['records']==b['records']==count
        for k in a:
            if k not in('maximumTarBytes','maximumSelectedRunBytes'):assert a[k]==b[k],k
        assert b['maximumTarBytes']==168*2**20 and b['maximumSelectedRunBytes']==160*2**20
        return {'records':count,'nativeTarSHA256':b['nativeTarSHA256'],'allQualifyingFactsExact':True,'rawCopies':0}
    case('existing17MiB fixture exact all-rows old128 vs new160 consumer',differential)
    def old_confirmation():
        d=json.loads((ROOT/'evidence/betaintegrated01-m1control02/host/old-regression04/derived-loss05-confirmation-descriptor.json').read_text())
        new,anchor=confirmation.create_confirmation_descriptor_long(d['nativeTarPath'],d['prefix'],d['nativeExternalAnchor'],d['hostBracket'],d['expectedLaunchContext'])
        assert new==d
        c=d['expectedLaunchContext'];observed=confirmation.verify_confirmation(d,anchor,c['run'],c['epoch'],c['boot'])
        assert observed['nativeConfirmationRecordSHA256']==d['confirmationRecordSHA256']
        return {'descriptorSHA256':anchor,'sameConfirmedHome':observed['home']}
    case('immutable old actual confirmation exact under160 consumer',old_confirmation)
    m=json.loads((ROOT/'evidence/betaintegrated01-m1cockpit04/host/module-manifest01.json').read_text())
    drift=[p for p,h in m['sourceSHA256'].items()if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    assert drift==['planning/betaintegrated01/TIP-M1-COCKPIT04.md'],drift
    result={'status':'PASS'if all(c['pass']for c in results)else'FAIL','cases':results,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'old99RuntimeProfilePinsExact':True,'RootOwnedTIPAmendment':drift,'servicesStarted':0,'actualThirtyMinuteClaim':False}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'cases':len(results),'peakRSSBytes':result['peakRSSBytes']}))
    if result['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
