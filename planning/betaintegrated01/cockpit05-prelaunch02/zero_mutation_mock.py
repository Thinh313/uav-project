"""Four refusal-path mocks with all subprocess/thread/socket/file mutation denied.
Synthetic free/power seams never grant actual admission or prime a real guard.
"""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
from contextlib import ExitStack
from collections import namedtuple
import os,sys,json
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
H='planning.betaintegrated01.cockpit05-entry10.full'
D=import_module('planning.betaintegrated01.cockpit05-prelaunch02.doctor')
controller=import_module(H+'.actual_controller');guardian=import_module(H+'.android_guardian')


def check():
    before=D.check_sources();assert before['status']=='PASS';results=[];Usage=namedtuple('Usage','total used free');required=D.POLICY.task_budget()['requiredFreeBytes']
    def scenario(kind,free):
        operations=[];mkdirs=[];puts=[];prime=[];oldcwd=Path.cwd();real_open=Path.open;real_is_file=Path.is_file
        def denied(*args,**kwargs):operations.append(repr(args)[:200]);raise AssertionError('PROCESS_THREAD_SOCKET_MUTATION_DENIED')
        def directory(path,*args,**kwargs):mkdirs.append(str(path));return None # Virtualonly, no directory created.
        def opened(path,mode='r',*args,**kwargs):
            if any(c in mode for c in 'wax+'):operations.append('WRITE:'+str(path));raise AssertionError('FILE_WRITE_DENIED')
            return real_open(path,mode,*args,**kwargs)
        def exists(path):
            if path in(controller.E/'initial-workspace-SHA.json',controller.E/'initial-workspace-state.json'):return False
            return real_is_file(path)
        class GuardSpy:
            def __init__(self,*args):pass
            def prime(self):prime.append(True);raise AssertionError('PRIME_MUST_NOT_BE_CALLED')
            def diagnostic(self):return {'source':'MOCK_ONLY_NO_REAL_PRIME'}
        error=None
        try:
            with ExitStack()as stack:
                stack.enter_context(patch('subprocess.Popen',denied));stack.enter_context(patch('subprocess.run',denied));stack.enter_context(patch('subprocess.check_output',denied));stack.enter_context(patch('socket.socket',denied));stack.enter_context(patch('threading.Thread.start',denied));stack.enter_context(patch.object(Path,'mkdir',directory));stack.enter_context(patch.object(Path,'open',opened));stack.enter_context(patch.object(Path,'is_file',exists));stack.enter_context(patch('shutil.disk_usage',lambda path:Usage(500*2**30,0,free)));stack.enter_context(patch.object(sys,'argv',['mock','01']))
                if kind=='controller':controller.main()
                else:
                    stack.enter_context(patch.object(guardian,'put',lambda name,value:puts.append({'name':name,'value':value})));stack.enter_context(patch.object(guardian,'DiskGuard',GuardSpy));stack.enter_context(patch.object(guardian,'power',lambda:{'AC':False,'batteryPercent':14,'raw':'MOCK_BATTERY14_NO_ACTUAL_POWER'}));guardian.main()
        except BaseException as exc:error=repr(exc)
        finally:os.chdir(oldcwd)
        assert not operations,operations;assert not prime,'REAL_OR_MOCK_PRIME_UNEXPECTED'
        if free<required:
            assert error and 'BEFORE_'in error,error;assert not mkdirs,mkdirs
        elif kind=='controller':assert error and 'INITIAL05_BASELINE_REQUIRED'in error,error;assert not mkdirs
        else:
            assert error is None,error;assert mkdirs==[str(guardian.E)]
            assert [p['name']for p in puts]==['failure.json','closure.json'];assert 'POWER_ENTRY'in puts[0]['value']['error'];assert puts[1]['value']['exit']is None
        assert not(controller.E/'actual-combined01').exists()and not guardian.E.exists()
        return {'kind':kind,'syntheticFreeBytes':free,'observedRefusal':error or puts[0]['value']['error'],'interceptedMkdirs':mkdirs,'actualMkdirs':0,'interceptedMetadata': [p['name']for p in puts],'actualMetadataWrites':0,'processThreadSocketCalls':0,'primeCalls':0,'physicalOrClockAdmissionClaim':False}
    for kind,free in [('controller',required-1),('controller',required+2**30),('guardian',required-1),('guardian',required+2**30)]:
        try:detail=scenario(kind,free);results.append({'case':kind+('-lowbudget'if free<required else'-missingbaseline'if kind=='controller'else'-battery14'),'pass':True,'detail':detail})
        except BaseException as exc:results.append({'case':kind,'pass':False,'error':repr(exc)})
    after=D.check_sources();assert after==before
    return {'status':'PASS'if all(x['pass']for x in results)else'FAIL','cases':results,'source178AndPrior385BeforeAfterExact':True,'actualRuntimeLaunches':0,'actualDiskPriming':False,'syntheticInputsOnly':True,'frozenSourcesChanged':False}


if __name__=='__main__':
    value=check();D.save_new('zero-mutation-mock01.json',value);print(json.dumps(value,indent=2))
