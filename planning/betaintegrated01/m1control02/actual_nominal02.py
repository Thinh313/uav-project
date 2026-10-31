"""Bounded Contractor Android-SITL tests. Root-only launcher, no MAVLink broker.
Read raw, never infer execution from an ACK or a successful UI client. No retries.
"""
import os,sys,json,time,uuid,hashlib,subprocess,signal,socket,shutil,threading,collections,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];os.chdir(R);sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from planning.betaintegrated01.m1control01.root_operator01 import RootOperator
from planning.betaintegrated01.m1control01.host.launch_fixture import build_config,verify_pins,prepare_fresh_case_state,host_argv,supervisor_argv,cut_request
from pilot.betaintegrated01.runtime.capacity import estimate
OLD=R/'evidence/betaintegrated01-m1control01';E=R/'evidence/betaintegrated01-m1control02';IMAGE='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84';APK=R/'native/betaintegrated01/control02/dist/aeris-control01-development-02.apk'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,d):
    with Path(p).open('x')as f:json.dump(d,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def read(p):return json.loads(Path(p).read_text())
def power_observation(raw):
    ac="'AC Power'"in raw;m=re.search(r'(\d+)%',raw);percent=int(m.group(1))if m else None
    if not ac and percent is None:raise RuntimeError('UNKNOWN_POWER_STATE')
    return {'raw':raw,'AC':ac,'batteryPercent':percent,'userAuthorizedBattery':True}
def main():
    scenario='nominal';attempt=sys.argv[1] if len(sys.argv)>1 else '01';assert attempt in ('01','02','03')
    O=E/('actual-nominal'+attempt);O.mkdir();C=O/'control';C.mkdir();D=O/'raw';D.mkdir()
    run='m1c02-nominal'+attempt;epoch=uuid.uuid4().hex;boot=uuid.uuid4().hex;generation=uuid.uuid4().hex;case='m1control-reboot02'if scenario.startswith('ground')else run
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
                power=power_observation(subprocess.check_output(['pmset','-g','batt'],text=True));wall=time.time()
                row={'hostNs':time.monotonic_ns(),'freeBytes':free,'forecast15sBytes':forecast,'historySeconds':now-history[0][0],
                     'AC':power['AC'],'batteryPercent':power['batteryPercent'],'userAuthorizedBattery':True,'hostExit':host.poll()if host else None,'wallMonoGapSeconds':(wall-lastutc)-(now-last)}
                f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
                last,lastutc=now,wall
                if forecast<10*2**30+256*2**20 or (not row['AC']and row['batteryPercent']<=20) or abs(row['wallMonoGapSeconds'])>2 or (E/'emulator01/closure.json').exists() or now-began>150:
                    fault.append('LIVE_GUARD_REFUSED');return
    def guard_entry():
        try:guard()
        except Exception as exc:
            fault.append('GUARD_EXCEPTION:'+type(exc).__name__+':'+str(exc))
            try:put(C/'guard-exception.json',{'error':fault[-1],'hostNs':time.monotonic_ns()})
            except Exception:pass
    def check():
        if guardThread is not None and not guardThread.is_alive()and not stop.is_set():raise RuntimeError('GUARD_THREAD_DIED')
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
        manifest=verify_pins(R,OLD/'host/runtime-manifest05.json');native=read(OLD/'native/build-02.json')
        oracle_manifest=read(E/'host/module-manifest02.json')
        for n,h in oracle_manifest['sourceSHA256'].items():assert sha(R/n)==h,('ORACLE_SOURCE_DRIFT',n)
        put(C/'input-pins.json',{'hostManifestSHA256':sha(OLD/'host/runtime-manifest05.json'),'nativeBuildSHA256':sha(OLD/'native/build-02.json'),'oracleManifestSHA256':sha(E/'host/module-manifest02.json'),'oracleSourceSHA256':oracle_manifest['sourceSHA256'],'controllerSHA256':sha(__file__),'powerPolicySHA256':sha(E/'power-policy01.json')})
        for n,h in native['sourcePins'].items():assert sha(R/n)==h,('NATIVE_SOURCE_DRIFT',n)
        assert sha(APK)==native['sha256'];assert shutil.disk_usage(R).free>=20*2**30
        power=power_observation(cmd(['pmset','-g','batt']));assert power['AC']or power['batteryPercent']>=30,'POWER_ENTRY_REFUSED';put(C/'actual-power-entry.json',power)
        used=sum(p.stat().st_size for p in E.rglob('*')if p.is_file());seconds=60 if scenario.startswith('ground')else 90
        capacity=estimate(seconds,shutil.disk_usage(R).free,evidence_remaining=4*2**30-used)
        extra=96*2**20 # separate transport original/copy/export32MiB each
        capacity.update(extraTransportPeakBytes=extra,totalReservedPeakBytes=capacity['originalCopyExportPeakBytesBound']+extra)
        assert capacity['admittedByArithmetic'] and capacity['totalReservedPeakBytes']<=4*2**30-used and capacity['totalReservedPeakBytes']+10*2**30+256*2**20<=shutil.disk_usage(R).free
        put(C/'capacity.json',capacity)
        assert not(E/'emulator01/closure.json').exists()
        for port,kind in [(5961,socket.SOCK_STREAM),(5962,socket.SOCK_STREAM),(5963,socket.SOCK_STREAM),(9012,socket.SOCK_DGRAM),(9014,socket.SOCK_DGRAM)]:
            with socket.socket(socket.AF_INET,kind)as sock:sock.bind(('127.0.0.1',port))
        assert cmd(['docker','image','inspect',IMAGE,'--format','{{.Id}}']).strip()==IMAGE
        assert not cmd(['docker','ps','-aq','--filter','name=^/'+name+'$']).strip()
        installed=op.command(['shell','pm','path','vn.rtr.aeris.control01'])[0].decode().strip()[8:]
        assert op.command(['shell','sha256sum',installed])[0].decode().split()[0]==native['sha256']
        state=E/'reboot-case-state02' if scenario.startswith('ground')else O/'AP-state'
        reuse=None
        if scenario=='ground2':
            old=read(E/'actual-ground102/control/reboot-ready.json');assert old['groundDisarmedObserved']
            put(D/'caller-ground-disarmed.json',old)
            reuse={'previousBoot':old['previousBoot'],'eepromSHA256':sha(state/'eeprom.bin'),'eepromBytes':(state/'eeprom.bin').stat().st_size,'groundDisarmedReceiptSHA256':sha(D/'caller-ground-disarmed.json')}
            assert reuse['eepromSHA256']==old['eepromSHA256']
        else:prepare_fresh_case_state(R,state,case)
        cfg=build_config(R,'loss'if scenario=='loss'else'nominal',run,epoch,boot,D,case,maximum_seconds=seconds,wipe_state=scenario!='ground2',state_reuse=reuse)
        put(D/'run-config.json',cfg)
        providers=read(R/'planning/betaintegrated01/m1control01/native/expected-providers02.json')['profiles'];provider=providers['M1-CONTROL01-LOSS'if scenario=='loss'else'M1-CONTROL01-NOMINAL']
        binding={k:provider[k]for k in ['version','mode','profileId','binarySHA256','modelSHA256','configSHA256','endpoint','firmware']};binding.update(rootOwnedContainer=True,targetSystem=42,run=run,epoch=epoch,boot=boot,operator='root-simulator-QA',generation=generation,inputProvenance='ROOT_INJECTED_ANDROID_TOUCH')
        put(C/'launch-binding.json',binding)
        docker=['docker','run','--rm','--name',name,'--label','aeris.task=m1control02','--label','aeris.run='+run,'--cpus','4','--memory','2g','--pids-limit','128','--read-only','--tmpfs','/tmp:size=16m','-p','127.0.0.1:5963:5760/tcp','-p','127.0.0.1:5962:5762/tcp','-p','127.0.0.1:9014:9004/udp','-v',str(R)+':/src:ro','-v',str(R/'runtime/betaintegrated01/dist')+':/candidate:ro','-v',str(R/'runtime/betaintegrated01/control01')+':/control:ro','-v',str(D)+':/evidence:rw','-v',str(state)+':/state:rw','-w','/src','-e','PYTHONDONTWRITEBYTECODE=1',IMAGE,*supervisor_argv()]
        ledger=E/'actual-launch-ledger.jsonl';entries=[json.loads(x)for x in ledger.read_text().splitlines()]if ledger.exists()else[]
        assert len(entries)<3 # max3host/AP starts +one ownedemulator; noautomaticretry
        with ledger.open('a')as f:f.write(json.dumps({'run':run,'hostNs':time.monotonic_ns(),'controllerSHA256':sha(__file__),'rootOperatorSHA256':sha(R/'planning/betaintegrated01/m1control01/root_operator01.py'),'host':['python3','-B','-m','pilot.betaintegrated01.control05.backend','--config',str(D/'run-config.json')],'docker':docker})+'\n');f.flush();os.fsync(f.fileno())
        logs=[(C/'backend-control-stdout.txt').open('xb'),(C/'container-control-stdout.txt').open('xb')]
        host=subprocess.Popen(['python3','-B','-m','pilot.betaintegrated01.control05.backend','--config',str(D/'run-config.json')],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=logs[0],stderr=subprocess.STDOUT,start_new_session=True)
        guardThread=threading.Thread(target=guard_entry);guardThread.start()
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
        passive_deadline=time.monotonic()+8
        while True:
            check();observed_passive=passive();hb=observed_passive.get('passive',{}).get('latest',{}).get('HEARTBEAT')
            if hb is not None and 0<=time.monotonic_ns()-hb['observedHostNs']<=1_500_000_000:
                put(C/'passive-heartbeat-before-native-connect.json',observed_passive);break
            if time.monotonic()>passive_deadline:raise RuntimeError('PASSIVE_VALID_AP_HEARTBEAT_NOT_OBSERVED_NO_NATIVE_CONNECT')
            time.sleep(.1)
        tmp='/data/local/tmp/aeris-control01-'+run+'.json';op.command(['push',str(C/'launch-binding.json'),tmp]);op.command(['shell','run-as','vn.rtr.aeris.control01','cp',tmp,'files/launch-binding.json'])
        assert op.command(['shell','run-as','vn.rtr.aeris.control01','sha256sum','files/launch-binding.json'])[0].decode().split()[0]==sha(C/'launch-binding.json')
        connected=True;op.command(['shell','am','start','-n','vn.rtr.aeris.control01/.ControlActivity','--es','m1Action','CONNECT','--es','m1ActionId',run+'-connect','--es','launchBindingSHA256',sha(C/'launch-binding.json')])
        wait(lambda s:s.get('preflightReady')is True,60);ground_observe(4)
        if not scenario.startswith('ground') and time.monotonic()-began>75:raise RuntimeError('LESS_THAN_30S_FLIGHT_CAPTURE_BUDGET_NO_ARM')
        if scenario.startswith('ground'):
            s=op.state();assert s['input']['consent']is False
            op.explicit_tap('close');wait(lambda s:s.get('closed')is True,5)
        else:
            for key,pred in [('consent',lambda s:s['input']['consent']),('guided',lambda s:s['flight']['mode']==4),('arm',lambda s:s['flight']['armed'])]:
                op.explicit_tap(key);observed=wait(pred,6)
                if key=='consent':first_lease=observed['input']['leaseId'];put(C/'first-consent-observed.json',{'hostNs':time.monotonic_ns(),'state':observed})
            wait(lambda s:s['flight'].get('postArmHomePending')and s['flight'].get('homeObservedAtMs',-1)>s['flight'].get('armObservedAtMs',2**63),4)
            before_confirm=time.monotonic_ns();op.explicit_tap('confirm-home');confirmed=wait(lambda s:s['flight']['homeConfirmed'],3);after_confirm=time.monotonic_ns()
            put(C/'confirm-home-bracket.json',{'beforeActionHostNs':before_confirm,'afterObservedConfirmedHostNs':after_confirm,'run':run,'epoch':epoch,'boot':boot,'generation':generation,'displayedHomeHash':confirmed['flight']['homeHash']})
            op.explicit_tap('takeoff');wait(lambda s:s['flight']['landedState']==2 and s['flight']['hoverObservedMs']>=1000,15)
            op.explicit_tap('loiter');wait(lambda s:s['flight']['mode']==5,4)
            gesture=op.start_stick_hold('control01-right-stick',0,.6,1800)
            if scenario=='loss':
                time.sleep(2);s=op.state();assert gesture.process.poll()is None and s['input']['consent']and s['rcOverrideActiveLocally'];p=passive();assert p['passive']['latest']['HEARTBEAT']['armed']and p['passive']['latest']['EXTENDED_SYS_STATE']['landedState']==2
                put(C/'root-cut-observed.json',{'state':s,'passive':p,'gesturePID':gesture.process.pid})
                request=cut_request(run,epoch,boot,uuid.uuid4().hex);put(D/'cut-request.staged',request);os.rename(D/'cut-request.staged',D/'cut-request.json');fd=os.open(D,os.O_RDONLY);os.fsync(fd);os.close(fd)
                gesture.wait(10);ground_observe(22)
            else:
                gesture.wait(6);released=wait(lambda s:s['flight']['mode']==17 and not s['rcOverrideActiveLocally']and not s['input']['consent']and s['releaseState']=='RELEASED',5)
                put(C/'release-observed.json',{'hostNs':time.monotonic_ns(),'state':released})
                # Await independent passive HB17 BEFOREnewconsent/LAND, no mode/timingguess.
                brake_deadline=time.monotonic()+3
                while True:
                    check();pbrake=passive();h=pbrake.get('passive',{}).get('latest',{}).get('HEARTBEAT',{})
                    if h.get('customMode')==17 and h.get('armed')is True and 0<=time.monotonic_ns()-h['observedHostNs']<=1_500_000_000:
                        put(C/'passive-brake-before-second-consent.json',pbrake);break
                    if time.monotonic()>brake_deadline:raise RuntimeError('PASSIVE_BRAKE17_NOT_OBSERVED_NO_NEW_CONSENT_OR_LAND')
                    time.sleep(.1)
                op.explicit_tap('consent');renewed=wait(lambda s:s['input']['consent']and s['input']['grants']==2,3)
                assert renewed['input']['leaseId']!=first_lease and renewed['input']['leaseId']is not None,'NEW_CONSENT_MUST_DIFFER'
                put(C/'second-consent-observed.json',{'hostNs':time.monotonic_ns(),'state':renewed})
                op.explicit_tap('land');landed=wait(lambda s:s['flight']['mode']==9 and not s['input']['consent'],4)
                put(C/'explicit-land-observed.json',{'hostNs':time.monotonic_ns(),'state':landed});ground_observe(24)
                op.explicit_tap('close');wait(lambda s:s.get('closed')is True,5)
        put(C/'driver-observed.json',{'status':'DRIVER_FINISHED_NOT_RAW_ACCEPTANCE','scenario':scenario,'groundGroups':len(ground),'elapsedSeconds':time.monotonic()-began})
    except Exception as exc:
        failure=type(exc).__name__+':'+str(exc);put(C/'failure.json',{'error':failure,'hostNs':time.monotonic_ns(),'noRetry':True})
    finally:
        # Simulator-only abort: stop native GCS, keep AP/FDM/passive alive bounded to observe failsafe.
        if connected:
            if failure:
                try:
                    abort_state=op.state()
                    if abort_state.get('flight',{}).get('armed')is False and abort_state.get('flight',{}).get('landedState')==1 and not abort_state.get('closed'):
                        op.explicit_tap('close');wait(lambda x:x.get('closed'),3)
                except Exception as exc:put(C/'graceful-abort-close-refused.json',{'error':str(exc)})
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
