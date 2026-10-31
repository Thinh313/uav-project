"""Pure boundary/math/source equivalence checks. No actual priming or launch."""
from importlib import import_module
from pathlib import Path
import hashlib,json
H='planning.betaintegrated01.cockpit05-entry10.host'
p=import_module(H+'.policy');a=import_module(H+'.admission')
from pilot.betaintegrated01.runtime02.journal import admission as old
from pilot.betaintegrated01.cockpit04.revision02.capacity import task_budget as old_budget
R=Path(__file__).resolve().parents[4]


def check():
    cases=[]
    def test(name,fn):
        try:detail=fn();cases.append({'case':name,'pass':True,'detail':detail})
        except Exception as e:cases.append({'case':name,'pass':False,'error':repr(e)})
    def boundary():
        b=p.task_budget();required=b['requiredFreeBytes'];assert required==old_budget()['taskHardPeakBytes']+10*2**30+256*2**20
        assert b['entryBytes']==10*2**30 and b['floorBytes']==10*2**30 and b['reserveBytes']==256*2**20
        for free,expected in[(required-1,False),(required,True),(required+1,True),(13*2**30,False),(10*2**30,False),(9*2**30,False)]:assert p.task_budget(free)['admitted']is expected
        for bad in(True,13.0,-1,2**63):
            try:p.task_budget(bad)
            except ValueError:continue
            raise AssertionError(bad)
        return {'requiredBytes':required,'requiredGiB':required/2**30,'wholeCaseGiB':b['taskHardPeakBytes']/2**30}
    test('entry10 plus exact wholecase floor reserve boundaries',boundary)
    def equivalent():
        source=(R/'pilot/betaintegrated01/runtime02/journal/admission.py').read_text()
        expected=source.replace('free_bytes>=20*GIB','free_bytes>=10*GIB').replace('free_bytes<20*GIB','free_bytes<10*GIB').replace('ENTRY_BELOW20_GIB','ENTRY_BELOW10_GIB').replace("'entryBytes': 20*GIB","'entryBytes': 10*GIB")
        assert (R/'planning/betaintegrated01/cockpit05-entry10/host/admission.py').read_text()==expected
        assert {k:v for k,v in a.DISK_POLICY.items()if k!='entryBytes'}=={k:v for k,v in old.DISK_POLICY.items()if k!='entryBytes'}
        return 'Only entry threshold comparisons/constants and entry error labels differ; floor/forecast/cadence/real prime/constructor unchanged'
    test('isolated guard exact allowed textual diff',equivalent)
    def forecast():
        one=old.ForecastWindow();two=a.ForecastWindow();free=19*2**30
        for tick in range(151):
            ns=tick*100_000_000;f=free-tick*1024
            x=one.observe(ns,f,priming=True);y=two.observe(ns,f,priming=True);assert x==y
        assert one.primed and two.primed
        assert one.observe(15_100_000_000,free-152*1024)==two.observe(15_100_000_000,free-152*1024)
        return {'pureMathTicks':152,'realClockPrimingClaim':False}
    test('old and new forecast outputs exact for same deterministic inputs',forecast)
    def floor():
        w=a.ForecastWindow()
        try:w.observe(0,10*2**30+256*2**20-1,priming=True)
        except a.DiskGuardError as e:assert 'FLOOR10_RESERVE256'in str(e);return 'Entry10 does not weaken floor10 plus256MiB reserve'
        raise AssertionError('flooraccepted')
    test('live floor and reserve still refuse below10.25GiB',floor)
    def notprimed():
        w=a.ForecastWindow()
        try:w.observe(0,19*2**30)
        except a.DiskGuardError as e:assert 'NOT_REAL_15S_PRIMED'in str(e);return 'No synthetic seed/no priming bypass'
        raise AssertionError('unprimedaccepted')
    test('real15s-prime requirement remains',notprimed)
    def ui():
        b=p.ui_budget();assert 10.881<b['requiredFreeBytes']/2**30<10.883
        assert p.ui_budget(b['requiredFreeBytes']-1)['admitted']is False
        assert p.ui_budget(b['requiredFreeBytes'])['admitted']is True
        assert p.ui_budget(13*2**30)['admitted']is True
        assert b['APOrFlightAuthorizedByThisBudget']is False and b['maximumSeconds']==900
        return {'requiredBytes':b['requiredFreeBytes'],'requiredGiB':b['requiredFreeBytes']/2**30,'13GiBUISubsetFits':True,'13GiBFullSoakFits':p.task_budget(13*2**30)['admitted']}
    test('distinct900s UI budget boundaries no flight promotion',ui)
    def guardian():
        import ast
        path=R/'planning/betaintegrated01/cockpit05-entry10/host/android_guardian.py';source=path.read_text();tree=ast.parse(source)
        assert "DiskGuard=import_module(H+'.admission').DiskGuard"in source
        assert source.count("policy.ui_budget(__import__('shutil').disk_usage(R).free)['admitted']")==2
        assert "contract.build_input_contract(R)"in source and 'selectedAPKInputs=37'in source
        assert 'now-start>900'in source and 'EMULATOR_CONSOLE16MiB_CAP'in source
        assert "if allocated(E.parent)+allocated(R/'planning/betaintegrated01/cockpit05-entry10')>32*2**20"in source
        assert 'NEW_NATIVE05_POSITIVE_GROWTH_OTHER_BUDGET'in source
        assert 'AVD_GROWTH_CAP'in source and 'ANDROID_UI_SUBSET_NO_AP_NO_FLIGHT'in source
        module=import_module(H+'.android_guardian')
        assert not module.E.exists(),'Buildermustnotcreateactualemulatordirectory'
        return 'Import/AST only; freshwholeUIbudget before andafterrealprime; no execution'
    test('new guardian scoping fresh entry guard and selected37 APKpins',guardian)
    return {'status':'PASS'if all(x['pass']for x in cases)else'FAIL','cases':cases,'runtimeLaunches':0,'actualPrimeRuns':0,'buildSignOrADB':False}

if __name__=='__main__':print(json.dumps(check(),indent=2))
