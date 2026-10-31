"""Static/import/config/metadata ledger checks only; no device or runtime execution."""
from pathlib import Path
from importlib import import_module
import ast,hashlib,json,tempfile,shutil
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-entry10.full';F=R/'planning/betaintegrated01/cockpit05-entry10/full';E=R/'evidence/betaintegrated01-cockpit05-entry10-flight'

def check():
    records=[]
    def test(name,fn):
        try:records.append({'case':name,'pass':True,'detail':fn()})
        except Exception as e:records.append({'case':name,'pass':False,'error':repr(e)})
    def imports():
        names=[]
        for path in F.glob('*.py'):
            if path.name in('setup_ui.py','static_mock.py'):continue
            ast.parse(path.read_text());import_module(H+'.'+path.stem);names.append(path.name)
        assert not(E/'actual-combined01').exists()and not(E/'emulator01').exists()
        return names
    test('all newhelper imports inert no case/device/runtime creation',imports)
    def controller():
        s=(F/'actual_controller.py').read_text();assert "run='cockpit05-entry10-combined-'+attempt"in s
        assert 'planning.betaintegrated01.cockpit05-entry10.runtime.backend'in s
        assert s.count("task_budget(shutil.disk_usage(R).free)['admitted']")>=4
        assert '20*2**30'not in s and 'contract.build_config'in s
        assert 'ONE_COMBINED_START_ONLY_NO_AUTOMATIC_RETRY'in s and '1802'in s
        return 'Explicitnewruntime+newconfig+freshwholebudget gates;1802host/guest/APclocks retained;oneexecution'
    test('controller selects newruntime and newrecordingpolicy no hard20',controller)
    def guard():
        s=(F/'android_guardian.py').read_text();assert "maximumSeconds=5400"in s and s.count("policy.task_budget(__import__('shutil').disk_usage(R).free)['admitted']")==2
        assert 'contract.verify_full_inputs()'in s and 'FULL_TASK_HARD_QUOTA'in s and 'FULL_METADATA64MiB_CAP'in s and 'OWN_EMULATOR_METADATA32MiB_CAP'in s
        assert "ANDROID_SITL_TEST"in s and '20*2**30'not in s
        return 'Newentry10guard/wholebudgetbothprime/5400taskcaps/fullselectedsourcepins'
    test('fullguardian freshwholebudget and sharedcaps',guard)
    def config():
        c=import_module(H+'.contract');p=import_module('planning.betaintegrated01.cockpit05-entry10.host.policy02')
        cfg=c.build_config(R,'nominal','cockpit05-entry10-combined-01','epoch','boot',E,'case',maximum_seconds=1960);p.validate_recording_policy(cfg)
        assert cfg['expectedConfigSHA256']=='6e8b3093e9802e20b4220fa872d57d9260bf02bd2ae40304ac161a53a0b6b17e'
        assert cfg['externalRecordingPolicy']['amendment']['diskGuardPolicy']['entryBytes']==10*2**30
        return {'fullRequiredBytes':p.task_budget()['requiredFreeBytes'],'profile02PhysicalSHAUnchanged':True}
    test('physicalconfig39bits unchanged explicitnewentry10 amendment',config)
    def cold():
        s=(F/'actual_combined_cold.py').read_text();assert 'planning.betaintegrated01.cockpit05-entry10.runtime.oracles'in s
        assert 'from planning.betaintegrated01.m1cockpit04.qa.combined_oracle import'in s
        assert 'from planning.betaintegrated01.m1cockpit04.qa.native_authority02 import audit'in s
        assert "binding['run']=='cockpit05-entry10-combined-01'"in s
        return 'Frozencombined+nativeauthoritypredicates reused,newstrictentry10rawreceiver'
    test('cold wrapper newrawreceiver with same independent1800clocks/authority',cold)
    return {'status':'PASS'if all(r['pass']for r in records)else'FAIL','cases':records,'actualDeviceAPLaunches':0,'newBuildSignOrDependencies':False}
if __name__=='__main__':
    result=check();out=E/'host/static-mock01.json';out.open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
