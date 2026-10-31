"""Bounded Contractor Android-SITL tests. Root-only launcher, no MAVLink broker.
Read raw, never infer execution from an ACK or a successful UI client. No retries.
"""
import os,sys,json,time,uuid,hashlib,subprocess,signal,socket,shutil,threading,collections,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];os.chdir(R);sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from planning.betaintegrated01.m1cockpit04.android.root_operator import RootOperator
from planning.betaintegrated01.m1cockpit04.host.launch_fixture import build_config,verify_pins,prepare_fresh_case_state,host_argv,supervisor_argv,cut_request
from pilot.betaintegrated01.cockpit04.revision02.capacity import task_budget
from planning.betaintegrated01.m1cockpit04.resources02 import ResourceGuard,capture_native
OLD=R/'evidence/betaintegrated01-m1control01';E=R/'evidence/betaintegrated01-m1cockpit04';IMAGE='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84';APK=R/'native/betaintegrated01/cockpit04/dist/aeris-cockpit04-development-02.apk'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,d):
    with Path(p).open('x')as f:json.dump(d,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def read(p):return json.loads(Path(p).read_text())
def power_observation(raw):
    ac="'AC Power'"in raw;m=re.search(r'(\d+)%',raw);percent=int(m.group(1))if m else None
    if not ac and percent is None:raise RuntimeError('UNKNOWN_POWER_STATE')
    return {'raw':raw,'AC':ac,'batteryPercent':percent,'userAuthorizedBattery':True}
def qualified_battery_mv(value):
    # MAVLink uses 65535 for unknown voltage; bool is not a measurement.
    return type(value)is int and 21000<=value<65535
def device_inventory(op,run):
    paths=['files/control-runs/'+run,'files/workspace03','files/review-links']
    out=op.command(['exec-out','run-as','vn.rtr.aeris.cockpit04','find',*paths,'-type','f','-exec','sha256sum','{}','+'],timeout=20)[0].decode()
    values={}
    for line in out.splitlines():
        digest,name=line.split(None,1);name=name.strip()
        assert re.fullmatch('[0-9a-f]{64}',digest)and name.startswith(tuple(paths))and '..'not in Path(name).parts and name not in values
        values[name]=digest
    assert values and len(values)<=1024;return values

def restart_and_capture(op,C,run,generation,resource):
    before=device_inventory(op,run);put(C/'private-before-restart-SHA.json',before)
    beforeUI=json.loads(op.command(['shell','run-as','vn.rtr.aeris.cockpit04','cat','files/workspace-state.json'])[0]);priorEpoch=beforeUI['viewEpoch']
    put(C/'workspace-before-restart.json',beforeUI)
    op.command(['shell','am','force-stop','vn.rtr.aeris.cockpit04']);op.command(['shell','am','start','-n','vn.rtr.aeris.cockpit04/.CockpitActivity'])
    deadline=time.monotonic()+10
    while True:
        resource.check()
        w=json.loads(op.command(['shell','run-as','vn.rtr.aeris.cockpit04','cat','files/workspace-state.json'])[0]);layout=op.layout()
        if w['native']['phase']=='NO_SESSION'and w['ownerActive']is False and layout.get('bindingStagedSHA256')is None and layout.get('viewReady') is True and type(w.get('viewEpoch'))is int and w['viewEpoch']!=priorEpoch:break
        if time.monotonic()>deadline:raise RuntimeError('RESTART_DID_NOT_RESTORE_INERT_VIEW')
        time.sleep(.1)
    after=device_inventory(op,run);assert before==after
    beforeWorkspace=beforeUI['workspace'];afterWorkspace=w['workspace']
    reviewIDs=lambda workspace:{x.get('run',x.get('id'))for x in workspace['reviews']}
    assert afterWorkspace.get('error')is None and afterWorkspace['draftSHA256']==beforeWorkspace['draftSHA256']
    assert run in reviewIDs(afterWorkspace)and reviewIDs(beforeWorkspace)==reviewIDs(afterWorkspace)
    put(C/'restart-recovery.json',{'status':'PASS_EXACT_DEVICE_FILES_NO_AUTHORITY_RESTORE','files':after,'currentUI':w,'layout':layout,'beforeViewEpoch':priorEpoch,'afterViewEpoch':w['viewEpoch'],'newViewEpoch':w['viewEpoch']!=priorEpoch,'noReconnectIntentSent':True});op.screenshot()
    capture_native(op,C,run,'long',resource)

def main():
    scenario='combined';attempt=sys.argv[1] if len(sys.argv)>1 else '01';assert attempt in ('01','02','03')
    O=E/('actual-combined02-'+attempt);O.mkdir();C=O/'control';C.mkdir();D=O/'raw';D.mkdir()
    run='m1cockpit04-combined02-'+attempt;epoch=uuid.uuid4().hex;boot=uuid.uuid4().hex;generation=uuid.uuid4().hex;case='m1control-reboot02'if scenario.startswith('ground')else run
    op=RootOperator(C/'android',run,generation)
    # Fresh native measured geometry is observed for each explicit action.
    setup=read(E/'android-setup01/ui-geometry.json');op.nav_geometry=setup['navGeometry']
    logs=[];host=container=None;failure=None;connected=False;began=time.monotonic();ground=[];guardThread=None;fault_injected=False;resource=ResourceGuard(C,2250)
    name='aeris-'+run;post_flight=False
    def cmd(args,timeout=10,required=True):
        started=time.monotonic_ns()
        try:p=subprocess.run(list(map(str,args)),capture_output=True,timeout=timeout);out,err,code=p.stdout,p.stderr,p.returncode
        except subprocess.TimeoutExpired as x:out,err,code=x.stdout or b'',x.stderr or b'',124
        n=uuid.uuid4().hex; (C/(n+'-stdout.bin')).write_bytes(out);(C/(n+'-stderr.bin')).write_bytes(err)
        put(C/(n+'-command.json'),{'argv':list(map(str,args)),'exit':code,'startedNs':started,'endedNs':time.monotonic_ns(),'noRetry':True})
        if required and code:raise RuntimeError('COMMAND_FAILED:'+repr(args)+':'+err.decode(errors='replace')[:512])
        return out.decode(errors='replace')
    def passive():return read(D/'transport-state.json')
    def check():
        resource.check()
        if host and host.poll()is not None and not post_flight:raise RuntimeError('HOST_CLOSED_BEFORE_DRIVER_DONE')
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
        manifest=verify_pins(R,E/'host/module-manifest02.json');native=read(E/'native/build-02.json')
        oracle_manifest=read(E/'host/module-manifest02.json')
        for n,h in oracle_manifest['sourceSHA256'].items():assert sha(R/n)==h,('ORACLE_SOURCE_DRIFT',n)
        put(C/'input-pins.json',{'hostManifestSHA256':sha(E/'host/module-manifest02.json'),'nativeBuildSHA256':sha(E/'native/build-02.json'),'oracleManifestSHA256':sha(E/'host/module-manifest02.json'),'oracleSourceSHA256':oracle_manifest['sourceSHA256'],'controllerSHA256':sha(__file__),'powerPolicySHA256':sha(E/'power-policy01.json')})
        for n,h in native['sourcePins'].items():assert sha(R/n)==h,('NATIVE_SOURCE_DRIFT',n)
        assert sha(APK)==native['sha256'];assert shutil.disk_usage(R).free>=20*2**30
        power=power_observation(cmd(['pmset','-g','batt']));assert power['AC']or power['batteryPercent']>=30,'POWER_ENTRY_REFUSED';put(C/'actual-power-entry.json',power)
        seconds=1960;capacity=task_budget(shutil.disk_usage(R).free);assert capacity['admitted'];put(C/'capacity.json',capacity);resource.start()
        assert not(E/'emulator03/closure.json').exists()
        for port,kind in [(5961,socket.SOCK_STREAM),(5962,socket.SOCK_STREAM),(5963,socket.SOCK_STREAM),(9012,socket.SOCK_DGRAM),(9014,socket.SOCK_DGRAM)]:
            with socket.socket(socket.AF_INET,kind)as sock:sock.bind(('127.0.0.1',port))
        assert cmd(['docker','image','inspect',IMAGE,'--format','{{.Id}}']).strip()==IMAGE
        assert not cmd(['docker','ps','-aq','--filter','name=^/'+name+'$']).strip()
        installed=op.command(['shell','pm','path','vn.rtr.aeris.cockpit04'])[0].decode().strip()[8:]
        assert op.command(['shell','sha256sum',installed])[0].decode().split()[0]==native['sha256']
        state=O/'AP-state';prepare_fresh_case_state(R,state,case)
        cfg=build_config(R,'nominal',run,epoch,boot,D,case,maximum_seconds=1960)
        put(D/'run-config.json',cfg)
        providers=read(R/'planning/betaintegrated01/m1cockpit04/native/expected-providers01.json')['profiles'];provider=providers['M1-COCKPIT04-NOMINAL']
        binding={k:provider[k]for k in ['version','mode','profileId','binarySHA256','modelSHA256','configSHA256','endpoint','firmware']};binding.update(rootOwnedContainer=True,targetSystem=42,run=run,epoch=epoch,boot=boot,operator='root-simulator-QA',generation=generation,inputProvenance='ROOT_INJECTED_ANDROID_TOUCH')
        put(C/'launch-binding.json',binding)
        tmp='/data/local/tmp/aeris-control01-'+run+'.json';op.command(['push',str(C/'launch-binding.json'),tmp]);op.command(['shell','run-as','vn.rtr.aeris.cockpit04','cp',tmp,'files/launch-binding.json'])
        assert op.command(['shell','run-as','vn.rtr.aeris.cockpit04','sha256sum','files/launch-binding.json'])[0].decode().split()[0]==sha(C/'launch-binding.json')
        op.command(['shell','am','start','-n','vn.rtr.aeris.cockpit04/.CockpitActivity','--es','m1Action','STAGE_BINDING','--es','m1ActionId',run+'-stage','--es','launchBindingSHA256',sha(C/'launch-binding.json')]);time.sleep(.2)
        stage_deadline=time.monotonic()+3
        while True:
            layout=op.layout();node=layout['buttons']['control01-connect']
            if layout.get('bindingStagedSHA256')==sha(C/'launch-binding.json')and layout['view']=='preflight'and layout.get('viewReady')and node['visible']and node['enabled']:break
            if time.monotonic()>stage_deadline:raise RuntimeError('STAGE_GATE_BEFORE_AP_REFUSED')
            time.sleep(.05)
        snapshot=json.loads(op.command(['shell','run-as','vn.rtr.aeris.cockpit04','cat','files/workspace-state.json'])[0]);assert snapshot.get('ownerActive')is False and snapshot.get('native',{}).get('phase')=='NO_SESSION'
        put(C/'staging-gate-before-AP.json',{'layout':layout,'workspace':snapshot,'noWriterAtStage':True,'APStarted':False,'rootBindingSHA256':sha(C/'launch-binding.json')})
        docker=['docker','run','--rm','--name',name,'--label','aeris.task=m1cockpit04','--label','aeris.run='+run,'--cpus','4','--memory','2g','--pids-limit','128','--read-only','--tmpfs','/tmp:size=16m','-p','127.0.0.1:5963:5760/tcp','-p','127.0.0.1:5962:5762/tcp','-p','127.0.0.1:9014:9004/udp','-v',str(R)+':/src:ro','-v',str(R/'runtime/betaintegrated01/dist')+':/candidate:ro','-v',str(R/'pilot/betaintegrated01/cockpit04/profiles')+':/control:ro','-v',str(D)+':/evidence:rw','-v',str(state)+':/state:rw','-w','/src','-e','PYTHONDONTWRITEBYTECODE=1',IMAGE,*supervisor_argv()]
        ledger=E/'actual-launch-ledger.jsonl';entries=[json.loads(x)for x in ledger.read_text().splitlines()]if ledger.exists()else[]
        assert len(entries)<3 and not any(x.get('selectedCapacityRevision')==2 for x in entries),'ONE_COMBINED_START_ONLY_NO_AUTOMATIC_RETRY'
        with ledger.open('a')as f:f.write(json.dumps({'run':run,'selectedCapacityRevision':2,'hostNs':time.monotonic_ns(),'controllerSHA256':sha(__file__),'rootOperatorSHA256':sha(R/'planning/betaintegrated01/m1cockpit04/android/root_operator.py'),'host':['python3','-B','-m','pilot.betaintegrated01.cockpit04.backend','--config',str(D/'run-config.json')],'docker':docker})+'\n');f.flush();os.fsync(f.fileno())
        logs=[(C/'backend-control-stdout.txt').open('xb'),(C/'container-control-stdout.txt').open('xb')]
        host=subprocess.Popen(['python3','-B','-m','pilot.betaintegrated01.cockpit04.backend','--config',str(D/'run-config.json')],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=logs[0],stderr=subprocess.STDOUT,start_new_session=True)

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
        connected=True;op.explicit_connect()
        wait(lambda s:s.get('preflightReady')is True,60);ground_observe(4)
        ready_screen=op.screenshot();put(C/'ready-preflight-screen.json',{'path':str(ready_screen),'sha256':sha(ready_screen),'view':op.layout()['view']})
        # Caller-qualified cockpit navigation only, no flight action in JS bridge.
        op.navigate_fly()
        if not scenario.startswith('ground') and time.monotonic()-began>120:raise RuntimeError('UNEXPECTED_LONG_WARMUP_NO_ARM')
        for key,pred in [('consent',lambda s:s['input']['consent']),('guided',lambda s:s['flight']['mode']==4),('arm',lambda s:s['flight']['armed'])]:
            op.explicit_tap(key);observed=wait(pred,6)
            if key=='consent':first_lease=observed['input']['leaseId'];put(C/'first-consent-observed.json',{'hostNs':time.monotonic_ns(),'state':observed})
        armed_host=time.monotonic_ns();armed_guest=observed['flight']['armObservedAtMs'];armed_AP=observed['flight']['APBootMs']
        wait(lambda s:s['flight'].get('postArmHomePending')and s['flight'].get('homeObservedAtMs',-1)>s['flight'].get('armObservedAtMs',2**63),4)
        before_confirm=time.monotonic_ns();op.explicit_tap('confirm-home');confirmed=wait(lambda s:s['flight']['homeConfirmed'],3);after_confirm=time.monotonic_ns()
        put(C/'confirm-home-bracket.json',{'beforeActionHostNs':before_confirm,'afterObservedConfirmedHostNs':after_confirm,'run':run,'epoch':epoch,'boot':boot,'generation':generation,'displayedHomeHash':confirmed['flight']['homeHash']})
        op.explicit_tap('takeoff');air=wait(lambda s:s['flight']['landedState']==2 and s['flight']['hoverObservedMs']>=1000,15)
        airborne_host=time.monotonic_ns();airborne_guest=air['flight']['positionMs'];airborne_AP=air['flight']['APBootMs'];airborne_start=passive()
        put(C/'airborne-window-start.json',{'hostNs':airborne_host,'guestElapsedMs':airborne_guest,'APBootMs':airborne_AP,'state':air,'passive':airborne_start})
        op.explicit_tap('loiter');wait(lambda s:s['flight']['mode']==5,4)
        gesture=op.start_stick_hold('control01-right-stick',0,.6,1800);gesture.wait(6)
        released=wait(lambda s:s['flight']['mode']==17 and not s['rcOverrideActiveLocally']and not s['input']['consent']and s['releaseState']=='RELEASED',5)
        put(C/'release-observed.json',{'hostNs':time.monotonic_ns(),'state':released})
        brake_deadline=time.monotonic()+3
        while True:
            check();pbrake=passive();h=pbrake.get('passive',{}).get('latest',{}).get('HEARTBEAT',{})
            if h.get('customMode')==17 and h.get('armed')is True and 0<=time.monotonic_ns()-h['observedHostNs']<=1_500_000_000:put(C/'passive-brake-before-second-consent.json',pbrake);break
            if time.monotonic()>brake_deadline:raise RuntimeError('PASSIVE_BRAKE17_NOT_OBSERVED')
            time.sleep(.1)
        op.explicit_tap('consent');renewed=wait(lambda s:s['input']['consent']and s['input']['grants']==2,3)
        assert renewed['input']['leaseId']!=first_lease and renewed['input']['leaseId']is not None
        put(C/'second-consent-observed.json',{'hostNs':time.monotonic_ns(),'state':renewed})
        # No commands, fake motion or auto-grants during this assisted BRAKE hover.
        hold_start=time.monotonic_ns();hold_guest=renewed['flight']['positionMs'];hold_AP=renewed['flight']['APBootMs'];next_screen=hold_start;next_notice=hold_start
        put(C/'assisted-window-start.json',{'hostNs':hold_start,'guestElapsedMs':hold_guest,'APBootMs':hold_AP,'state':renewed,'passive':passive()})
        with(C/'assisted-hold-observations.jsonl').open('x')as stream:
            while True:
                check();s=op.state();f=s['flight'];now=time.monotonic_ns()
                if s.get('firstFailure')or s.get('closed')or f['mode']!=17 or not f['armed']or f['landedState']!=2 or not s['input']['consent']or s['input']['leaseId']!=renewed['input']['leaseId']:raise RuntimeError('LONG_ASSISTED_CONTEXT_OR_AUTHORITY_LOST')
                if not .4<=f['relativeAltitudeM']<=5 or not qualified_battery_mv(f.get('batteryWireMillivolts')):raise RuntimeError('LONG_FLIGHT_SAFETY_PROFILE_REFUSED')
                v={'hostNs':now,'state':s,'passive':passive()};stream.write(json.dumps(v)+'\n');stream.flush();os.fsync(stream.fileno())
                host_span=(now-hold_start)/1e9;guest_span=(f['positionMs']-hold_guest)/1000;AP_span=(f['APBootMs']-hold_AP)/1000
                if now>=next_screen:op.screenshot();next_screen=now+60_000_000_000
                if now>=next_notice:print(json.dumps({'phase':'ASSISTED_HOLD_RUNNING_NOT_FINAL','hostAirborneSeconds':host_span,'guestSeconds':guest_span,'APSeconds':AP_span,'freeGiB':shutil.disk_usage(R).free/2**30}),flush=True);next_notice=now+60_000_000_000
                if min(host_span,guest_span,AP_span)>=1802:break
                time.sleep(2)
        put(C/'pre-cut-observed.json',{'hostNs':time.monotonic_ns(),'state':s,'passive':passive(),'airborneHostSeconds':host_span,'guestSeconds':guest_span,'APSeconds':AP_span,'source':'INDEPENDENT_CLOCK_WINDOW_NOT_FINAL_ACCEPTANCE'})
        request=cut_request(run,epoch,boot,uuid.uuid4().hex);put(D/'cut-request.staged',request);os.rename(D/'cut-request.staged',D/'cut-request.json');fd=os.open(D,os.O_RDONLY);os.fsync(fd);os.close(fd);fault_injected=True
        ground_observe(30);post_flight=True
        closed_deadline=time.monotonic()+10
        while True:
            check();s=op.state()
            if s.get('closed')and not s['input']['consent']:break
            if time.monotonic()>closed_deadline:raise RuntimeError('NATIVE_DID_NOT_CLOSE_AFTER_CUT')
            time.sleep(.1)
        put(C/'native-expected-link-failure.json',{'state':s,'deliberateCut':True,'appFailurePreservedNotRenamed':True})
        op.navigate_review()
        review_end=time.monotonic()+60
        while True:
            check();view=json.loads(op.command(['shell','run-as','vn.rtr.aeris.cockpit04','cat','files/workspace-state.json'])[0])
            if view.get('chosenView')=='review'and any(x.get('run',x.get('id'))==run for x in view.get('workspace',{}).get('reviews',[])):
                put(C/'app-review-observed.json',view);screen=op.screenshot();put(C/'app-review-screen.json',{'path':str(screen),'sha256':sha(screen)});break
            if time.monotonic()>review_end:raise RuntimeError('APP_REVIEW_NOT_PERSISTED')
            time.sleep(.2)
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
                try:op.command(['shell','am','force-stop','vn.rtr.aeris.cockpit04'])
                except Exception as exc:put(C/'native-stop-error.json',{'error':str(exc)})
                try:
                    if host and host.poll()is None:ground_observe(18)
                except Exception as exc:put(C/'abort-ground-unknown.json',{'error':str(exc),'forcedAPStopIsNotLandingProof':True})
            try:
                current=op.state(require_context=False);put(C/'native-last-external-observation.json',current)
                put(C/'native-before-restart-state.json',current)
            except Exception as exc:put(C/'native-export-error.json',{'error':str(exc)})
        if host and host.poll()is None:
            os.killpg(host.pid,signal.SIGTERM)
            try:host.wait(timeout=6)
            except subprocess.TimeoutExpired:os.killpg(host.pid,signal.SIGKILL);host.wait(timeout=3)
        if container and container.poll()is None:
            cmd(['docker','stop','--time','6',name],timeout=10,required=False)
            try:container.wait(timeout=10)
            except subprocess.TimeoutExpired:container.terminate();container.wait(timeout=3)
        try:
            if connected:restart_and_capture(op,C,run,generation,resource)
        except Exception as exc:
            put(C/'restart-capture-error.json',{'error':repr(exc)});failure=failure or 'RESTART_CAPTURE_FAILED:'+repr(exc)
        resource.close()
        for f in logs:f.flush();os.fsync(f.fileno());f.close()
        put(C/'closure.json',{'failure':failure,'scenario':scenario,'hostExit':host.poll()if host else None,'APClientExit':container.poll()if container else None,'groundGroups':len(ground),'elapsedSeconds':time.monotonic()-began,'guardFailures':resource.fault,'forcedAPStopIsNotLandingProof':True,'noAutomaticRetry':True})
        print(json.dumps({'scenario':scenario,'failure':failure,'path':str(O)}),flush=True)
if __name__=='__main__':main()
