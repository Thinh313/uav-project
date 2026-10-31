"""Bounded Contractor Android-SITL tests. Root-only launcher, no MAVLink broker.
Read raw, never infer execution from an ACK or a successful UI client. No retries.
"""
import os,sys,json,time,uuid,hashlib,subprocess,signal,socket,shutil,threading,collections
from pathlib import Path
R=Path(__file__).resolve().parents[3];os.chdir(R);sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from root_operator01 import RootOperator
from host.launch_fixture import build_config,verify_pins,prepare_fresh_case_state,host_argv,supervisor_argv,cut_request
from pilot.betaintegrated01.runtime.capacity import estimate
E=R/'evidence/betaintegrated01-m1control01';IMAGE='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84';APK=R/'native/betaintegrated01/control02/dist/aeris-control01-development-02.apk'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,d):
    with Path(p).open('x')as f:json.dump(d,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def read(p):return json.loads(Path(p).read_text())
def main():
    scenario=sys.argv[1];assert scenario in ('nominal','loss','ground1','ground2')
    O=E/('actual-'+scenario+'04');O.mkdir();C=O/'control';C.mkdir();D=O/'raw';D.mkdir()
    run='m1control-'+scenario+'04';epoch=uuid.uuid4().hex;boot=uuid.uuid4().hex;generation=uuid.uuid4().hex;case='m1control-nominal02'if scenario.startswith('ground')else run
    op=RootOperator(C/'android',run,generation)
    # Exact initial visual geometry is test-only, no permission or enabled flag is cached.
    geometry=read(E/'android-setup01/initial-geometry.json');op.geometry={k:tuple(v)for k,v in geometry['geometry'].items()};op.geometry_source=geometry['sourceXML']
    put(op.root/'initial-geometry.json',geometry)
    logs=[];host=container=None;failure=None;connected=False;began=time.monotonic();stop=threading.Event();fault=[];ground=[];guardThread=None
    name='aeris-'+run
    def cmd(args,timeout=10,required=True):
        started=time.monotonic_ns()
        try:p=subprocess.run(list(map(str,args)),capture_output=True,timeout=timeout);out,err,code=p.stdout,p.stderr,p.returncode
        except subprocess.TimeoutExpired as x:out,err,code=x.stdout or b'',x.stderr or b'',124
        n=uuid.uuid4().hex; (C/(n+'-stdout.bin')).write_bytes(out);(C/(n+'-stderr.bin')).write_bytes(err)
        put(C/(n+'-command.json'),{'argv':list(map(str,args)),'exit':code,'startedNs':started,'endedNs':time.monotonic_ns(),'noRetry':True})
        if required and code:raise RuntimeError('COMMAND_FAILED:'+repr(args)+':'+err.decode(errors='replace')[:512])
        return out.decode(errors='replace')
    def passive():return read(D/'transport-state.json')
    def guard():
        history=collections.deque();last=time.monotonic();lastutc=time.time()
        with(C/'guard.jsonl').open('x')as f:
            while not stop.wait(.5):
                now=time.monotonic();free=shutil.disk_usage(R).free;history.append((now,free))
                while len(history)>1 and now-history[1][0]>15:history.popleft()
                forecast=free-max(0,(history[0][1]-free)/max(.001,now-history[0][0]))*15
                power=subprocess.check_output(['pmset','-g','batt'],text=True);wall=time.time()
                row={'hostNs':time.monotonic_ns(),'freeBytes':free,'forecast15sBytes':forecast,'historySeconds':now-history[0][0],
                     'AC':"'AC Power'"in power,'hostExit':host.poll()if host else None,'wallMonoGapSeconds':(wall-lastutc)-(now-last)}
                f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
                last,lastutc=now,wall
                if forecast<10*2**30+256*2**20 or not row['AC'] or abs(row['wallMonoGapSeconds'])>2 or (E/'emulator01/closure.json').exists() or now-began>150:
                    fault.append('LIVE_GUARD_REFUSED');return
    def check():
        if fault:raise RuntimeError(fault[0])
        if host and host.poll()is not None:raise RuntimeError('HOST_CLOSED_BEFORE_DRIVER_DONE')
    def wait(pred,seconds=12):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            check();s=op.state(allow_absent=True,require_context=False)
            if s and s.get('run')==run and s.get('generation')==generation:
                with(C/'native-live-states.jsonl').open('a')as f:f.write(json.dumps({'hostNs':time.monotonic_ns(),'state':s})+'\n')
                if s.get('firstFailure'):raise RuntimeError('NATIVE_FAILURE:'+str(s['firstFailure']))
                if pred(s):return s
            time.sleep(.2)
        raise RuntimeError('STATE_DEADLINE:'+str(s))
    def ground_observe(seconds=20):
        deadline=time.monotonic()+seconds;seen=set();facts=[]
        while time.monotonic()<deadline:
            check()
            try:p=passive();a=p['passive']['latest'];h=a['HEARTBEAT'];l=a['EXTENDED_SYS_STATE'];g=a['GLOBAL_POSITION_INT'];now=time.monotonic_ns()
            except(KeyError,FileNotFoundError):time.sleep(.2);continue
            times=tuple(x['observedHostNs']for x in (h,l,g))
            qualified=all(0<=now-t<=1_500_000_000 for t in times)and not h['armed']and l['landedState']==1 and abs(g['relativeAltitudeMm'])<=400
            if qualified and times not in seen and all(all(t!=p0[i]for i,t in enumerate(times))for p0 in seen):
                seen.add(times);facts.append(p)
                if len(facts)>=2:ground.extend(facts);put(C/('ground-'+uuid.uuid4().hex+'.json'),{'independentFreshGroups':facts});return facts
            time.sleep(.2)
        raise RuntimeError('GROUND_DISARM_NOT_PROVED')
    try:
        manifest=verify_pins(R,E/'host/runtime-manifest04.json');native=read(E/'native/build-02.json')
        for n,h in native['sourcePins'].items():assert sha(R/n)==h,('NATIVE_SOURCE_DRIFT',n)
        assert sha(APK)==native['sha256'];assert shutil.disk_usage(R).free>=20*2**30
        assert "'AC Power'"in cmd(['pmset','-g','batt'])
        used=sum(p.stat().st_size for p in E.rglob('*')if p.is_file());seconds=60 if scenario.startswith('ground')else 90
        capacity=estimate(seconds,shutil.disk_usage(R).free,evidence_remaining=6*2**30-used)
        assert capacity['admittedByArithmetic'];put(C/'capacity.json',capacity)
        assert not(E/'emulator01/closure.json').exists()
        for port,kind in [(5961,socket.SOCK_STREAM),(5962,socket.SOCK_STREAM),(5963,socket.SOCK_STREAM),(9012,socket.SOCK_DGRAM),(9014,socket.SOCK_DGRAM)]:
            with socket.socket(socket.AF_INET,kind)as sock:sock.bind(('127.0.0.1',port))
        assert cmd(['docker','image','inspect',IMAGE,'--format','{{.Id}}']).strip()==IMAGE
        assert not cmd(['docker','ps','-aq','--filter','name=^/'+name+'$']).strip()
        installed=op.command(['shell','pm','path','vn.rtr.aeris.control01'])[0].decode().strip()[8:]
        assert op.command(['shell','sha256sum',installed])[0].decode().split()[0]==native['sha256']
        state=E/'reboot-from-nominal02-state01' if scenario.startswith('ground')else O/'AP-state'
        reuse=None
        if scenario=='ground2':
            old=read(E/'ground-reboot-admission01.json');assert old['groundDisarmedObserved']
            put(D/'caller-ground-disarmed.json',old)
            reuse={'previousBoot':old['previousBoot'],'eepromSHA256':sha(state/'eeprom.bin'),'eepromBytes':(state/'eeprom.bin').stat().st_size,'groundDisarmedReceiptSHA256':sha(D/'caller-ground-disarmed.json')}
            assert reuse['eepromSHA256']==old['eepromSHA256']
        else:prepare_fresh_case_state(R,state,case)
        cfg=build_config(R,'loss'if scenario=='loss'else'nominal',run,epoch,boot,D,case,maximum_seconds=seconds,wipe_state=scenario!='ground2',state_reuse=reuse)
        put(D/'run-config.json',cfg)
        providers=read(R/'planning/betaintegrated01/m1control01/native/expected-providers02.json')['profiles'];provider=providers['M1-CONTROL01-LOSS'if scenario=='loss'else'M1-CONTROL01-NOMINAL']
        binding={k:provider[k]for k in ['version','mode','profileId','binarySHA256','modelSHA256','configSHA256','endpoint','firmware']};binding.update(rootOwnedContainer=True,targetSystem=42,run=run,epoch=epoch,boot=boot,operator='root-simulator-QA',generation=generation,inputProvenance='ROOT_INJECTED_ANDROID_TOUCH')
        put(C/'launch-binding.json',binding)
        docker=['docker','run','--rm','--name',name,'--label','aeris.task=m1control01','--label','aeris.run='+run,'--cpus','4','--memory','2g','--pids-limit','128','--read-only','--tmpfs','/tmp:size=16m','-p','127.0.0.1:5963:5760/tcp','-p','127.0.0.1:5962:5762/tcp','-p','127.0.0.1:9014:9004/udp','-v',str(R)+':/src:ro','-v',str(R/'runtime/betaintegrated01/dist')+':/candidate:ro','-v',str(R/'runtime/betaintegrated01/control01')+':/control:ro','-v',str(D)+':/evidence:rw','-v',str(state)+':/state:rw','-w','/src','-e','PYTHONDONTWRITEBYTECODE=1',IMAGE,*supervisor_argv()]
        ledger=E/'actual-launch-ledger.jsonl';entries=[json.loads(x)for x in ledger.read_text().splitlines()]if ledger.exists()else[]
        assert len(entries)<5 # one emulator + at most five host starts; max six AP too
        with ledger.open('a')as f:f.write(json.dumps({'run':run,'hostNs':time.monotonic_ns(),'controllerSHA256':sha(__file__),'rootOperatorSHA256':sha(Path(__file__).parent/'root_operator01.py'),'host':['python3','-B','-m','pilot.betaintegrated01.control02.backend','--config',str(D/'run-config.json')],'docker':docker})+'\n');f.flush();os.fsync(f.fileno())
        logs=[(C/'backend-control-stdout.txt').open('xb'),(C/'container-control-stdout.txt').open('xb')]
        host=subprocess.Popen(['python3','-B','-m','pilot.betaintegrated01.control02.backend','--config',str(D/'run-config.json')],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=logs[0],stderr=subprocess.STDOUT,start_new_session=True)
        guardThread=threading.Thread(target=guard);guardThread.start()
        deadline=time.monotonic()+40
        while not(D/'backend-identity.json').exists():
            check();assert time.monotonic()<deadline,'PRIME_DEADLINE';time.sleep(.2)
        identity=read(D/'backend-identity.json');assert identity['guardPrimed']and identity['transportReady'];assert all(identity[k]['elapsedRealMonotonicNs']>=15_000_000_000 for k in ('guardPriming','transportGuardPriming'));put(C/'actual-prime.json',identity)
        container=subprocess.Popen(docker,cwd=R,stdin=subprocess.DEVNULL,stdout=logs[1],stderr=subprocess.STDOUT,start_new_session=True)
        put(C/'launch-observation.json',{'hostPID':host.pid,'dockerClientPID':container.pid,'run':run,'epoch':epoch,'boot':boot})
        deadline=time.monotonic()+12
        while not(D/'ap-supervisor-launch.json').exists():
            check();assert time.monotonic()<deadline,'AP_DEADLINE';time.sleep(.2)
        ap=read(D/'ap-supervisor-launch.json');info=json.loads(cmd(['docker','inspect',name]))[0]
        assert info['State']['Running']and info['Image']==IMAGE and info['Config']['Labels']['aeris.run']==run
        exe=cmd(['docker','exec',name,'sha256sum','/proc/'+str(ap['APPID'])+'/exe']).split()[0];assert exe==provider['binarySHA256'];put(C/'live-AP.json',{'containerID':info['Id'],'image':info['Image'],'AP':ap,'actualExeSHA256':exe})
        tmp='/data/local/tmp/aeris-control01-'+run+'.json';op.command(['push',str(C/'launch-binding.json'),tmp]);op.command(['shell','run-as','vn.rtr.aeris.control01','cp',tmp,'files/launch-binding.json'])
        assert op.command(['shell','run-as','vn.rtr.aeris.control01','sha256sum','files/launch-binding.json'])[0].decode().split()[0]==sha(C/'launch-binding.json')
        connected=True;op.command(['shell','am','start','-n','vn.rtr.aeris.control01/.ControlActivity','--es','m1Action','CONNECT','--es','m1ActionId',run+'-connect','--es','launchBindingSHA256',sha(C/'launch-binding.json')])
        wait(lambda s:s['flight'].get('firmwareObserved')and s['flight'].get('typedParameterCount')==39 and s['flight'].get('home')and s['flight'].get('GPSFix')in (3,4,5,6,8),35)
        # Read-only reboot proof: record preflight refusal rather than require flight grant.
        ground_observe(4);put(C/'post-reboot-readonly-state.json',op.state())
        assert scenario=='ground2','THIS_VERSION_ONLY_GROUND2_NO_FLIGHT'
        if scenario.startswith('ground'):
            s=op.state();assert s['input']['consent']is False
            op.explicit_tap('close');wait(lambda s:s.get('closed')is True,5)
        else:
            for key,pred in [('consent',lambda s:s['input']['consent']),('guided',lambda s:s['flight']['mode']==4),('arm',lambda s:s['flight']['armed'])]:op.explicit_tap(key);wait(pred,6)
            wait(lambda s:s['flight'].get('postArmHomePending')and s['flight'].get('homeObservedAtMs',-1)>s['flight'].get('armObservedAtMs',2**63),4)
            op.explicit_tap('confirm-home');wait(lambda s:s['flight']['homeConfirmed'],3)
            op.explicit_tap('takeoff');wait(lambda s:s['flight']['landedState']==2 and s['flight']['hoverObservedMs']>=1000,15)
            op.explicit_tap('loiter');wait(lambda s:s['flight']['mode']==5,4)
            gesture=op.start_stick_hold('control01-right-stick',0,.6,8000 if scenario=='loss'else 2500)
            if scenario=='loss':
                time.sleep(2);s=op.state();assert gesture.process.poll()is None and s['input']['consent']and s['rcOverrideActiveLocally'];p=passive();assert p['passive']['latest']['HEARTBEAT']['armed']and p['passive']['latest']['EXTENDED_SYS_STATE']['landedState']==2
                put(C/'root-cut-observed.json',{'state':s,'passive':p,'gesturePID':gesture.process.pid})
                request=cut_request(run,epoch,boot,uuid.uuid4().hex);put(D/'cut-request.staged',request);os.rename(D/'cut-request.staged',D/'cut-request.json');fd=os.open(D,os.O_RDONLY);os.fsync(fd);os.close(fd)
                gesture.wait(10);ground_observe(22)
            else:
                gesture.wait(6);wait(lambda s:s['flight']['mode']==17 and not s['rcOverrideActiveLocally']and not s['input']['consent'],5)
                op.explicit_tap('consent');wait(lambda s:s['input']['consent'],3);op.explicit_tap('land');ground_observe(20)
                op.explicit_tap('close');wait(lambda s:s.get('closed')is True,5)
        put(C/'driver-observed.json',{'status':'DRIVER_FINISHED_NOT_RAW_ACCEPTANCE','scenario':scenario,'groundGroups':len(ground),'elapsedSeconds':time.monotonic()-began})
    except Exception as exc:
        failure=type(exc).__name__+':'+str(exc);put(C/'failure.json',{'error':failure,'hostNs':time.monotonic_ns(),'noRetry':True})
    finally:
        # Simulator-only abort: stop native GCS, keep AP/FDM/passive alive bounded to observe failsafe.
        if connected:
            if failure:
                try:op.command(['shell','am','force-stop','vn.rtr.aeris.control01'])
                except Exception as exc:put(C/'native-stop-error.json',{'error':str(exc)})
                try:
                    if host and host.poll()is None:ground_observe(18)
                except Exception as exc:put(C/'abort-ground-unknown.json',{'error':str(exc),'forcedAPStopIsNotLandingProof':True})
            try:
                current=op.state(require_context=False);put(C/'native-last-external-observation.json',current)
                archive=op.export_private('files/control-runs/'+run);put(C/'native-export-location.json',{'path':str(archive),'sha256':sha(archive)})
            except Exception as exc:put(C/'native-export-error.json',{'error':str(exc)})
        if host and host.poll()is None:
            os.killpg(host.pid,signal.SIGTERM)
            try:host.wait(timeout=6)
            except subprocess.TimeoutExpired:os.killpg(host.pid,signal.SIGKILL);host.wait(timeout=3)
        if container and container.poll()is None:
            cmd(['docker','stop','--time','6',name],timeout=10,required=False)
            try:container.wait(timeout=10)
            except subprocess.TimeoutExpired:container.terminate();container.wait(timeout=3)
        stop.set()
        if guardThread:guardThread.join(timeout=3)
        for f in logs:f.flush();os.fsync(f.fileno());f.close()
        if scenario=='ground1'and ground and not failure:
            put(C/'reboot-ready.json',{'caseID':case,'previousBoot':boot,'groundDisarmedObserved':True,'groundRawNeedsIndependentQA':True,'eepromSHA256':sha(E/'reboot-case-state02/eeprom.bin')})
        put(C/'closure.json',{'failure':failure,'scenario':scenario,'hostExit':host.poll()if host else None,'APClientExit':container.poll()if container else None,'groundGroups':len(ground),'elapsedSeconds':time.monotonic()-began,'guardFailures':fault,'forcedAPStopIsNotLandingProof':True,'noAutomaticRetry':True})
        print(json.dumps({'scenario':scenario,'failure':failure,'path':str(O)}),flush=True)
if __name__=='__main__':main()
