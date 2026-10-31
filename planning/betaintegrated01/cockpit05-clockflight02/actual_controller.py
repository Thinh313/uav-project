"""Bounded Contractor Android-SITL tests. Root-only launcher, no MAVLink broker.
Read raw, never infer execution from an ACK or a successful UI client. No retries.
"""
import os,sys,json,time,uuid,hashlib,subprocess,signal,socket,shutil,threading,collections,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];os.chdir(R);sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from importlib import import_module
ROOT_PACKAGE='planning.betaintegrated01.cockpit05-clockflight02'
sys.path.insert(0,str(R/'planning/betaintegrated01/cockpit05-soak/android'))
from cockpit05_root_operator import RootOperator
contract=import_module(ROOT_PACKAGE+'.contract')
receiver05=import_module(ROOT_PACKAGE+'.receiver05')
from planning.betaintegrated01.m1cockpit04.host.launch_fixture import build_config,verify_pins,prepare_fresh_case_state,host_argv,supervisor_argv,cut_request
from importlib import import_module
task_budget=contract.task_budget
_resources=import_module(ROOT_PACKAGE+'.resources');ResourceGuard=_resources.ResourceGuard;capture_native=_resources.capture_native
OLD=R/'evidence/betaintegrated01-m1control01';E=R/'evidence/betaintegrated01-cockpit05-clockflight02';IMAGE='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84';APK=R/'native/betaintegrated01/cockpit05/dist/aeris-cockpit05-development-02.apk'
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
    out=op.command(['exec-out','run-as','vn.rtr.aeris.cockpit05','find',*paths,'-type','f','-exec','sha256sum','{}','+'],timeout=20)[0].decode()
    values={}
    for line in out.splitlines():
        digest,name=line.split(None,1);name=name.strip()
        assert re.fullmatch('[0-9a-f]{64}',digest)and name.startswith(tuple(paths))and '..'not in Path(name).parts and name not in values
        values[name]=digest
    assert values and len(values)<=1024;return values

def retain_initial_baselines(C):
    for name in('initial-private-SHA.json','initial-workspace-SHA.json','initial-workspace-state.json'):
        raw=(E/name).read_bytes();assert len(raw)<=131072,'BASELINE_METADATA_BOUND'
        with(C/name).open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
        assert sha(C/name)==sha(E/name)


def all_device_inventory(op):
    raw=op.command(['exec-out','run-as',contract.PACKAGE,'find','files/control-runs','files/workspace03','files/review-links','-type','f','-exec','sha256sum','{}','+'],timeout=20)[0].decode();values={}
    for line in raw.splitlines():
        h,name=line.split(None,1);name=name.strip();assert re.fullmatch('[0-9a-f]{64}',h)and name.startswith(('files/control-runs/','files/workspace03/','files/review-links/'))and '..'not in Path(name).parts and name not in values;values[name]=h
    assert 134<=len(values)<=4096;return values

def assert_prior_private_preserved(current):
    old=read(E/'initial-private-SHA.json');assert type(old)is dict and len(old)==134
    assert all(current.get(k)==h for k,h in old.items()),'PRIOR134_PRIVATE_FILE_CHANGED_OR_MISSING'
    return old

def check_initial_workspace(op,C,run):
    current=all_device_inventory(op);assert_prior_private_preserved(current)
    snapshot=json.loads(op.command(['shell','run-as',contract.PACKAGE,'cat','files/workspace-state.json'])[0]);w=snapshot['workspace'];draft=w['draft']
    initial=read(E/'initial-workspace-state.json')['workspace'];assert draft==initial['draft']and draft['revision']==6 and draft['altitudeM']==3 and draft['trainingOnly']is True
    assert w['draftSHA256']==initial['draftSHA256'];oldreviews={x['id']:x for x in initial['reviews']};nowreviews={x['id']:x for x in w['reviews']}
    assert all(nowreviews.get(k)==x for k,x in oldreviews.items()),'PRIOR_MOCK_FAILED_REVIEW_CHANGED'
    assert snapshot.get('ownerActive')is False and snapshot.get('native',{}).get('phase')=='NO_SESSION'
    put(C/'all-private-before-case-SHA.json',current);put(C/'workspace-r6-before-actual.json',{'currentFilesSHA256':current,'workspaceState':snapshot,'old134Preserved':True,'priorMOCKsRemainNonAuthoritative':True})
    return snapshot

def native_terminal_ready(state,layout,run,epoch,boot,generation):
    if type(state)is not dict or type(layout)is not dict:return False
    if any(state.get(k)!=v for k,v in [('run',run),('epoch',epoch),('boot',boot),('generation',generation)]):return False
    j=state.get('journal');authority=state.get('input')
    if type(j)is not dict or type(authority)is not dict:return False
    return state.get('closed')is True and j.get('closed')is True and j.get('run')==run and j.get('epoch')==epoch and type(j.get('commitAnchor'))is str and re.fullmatch('[0-9a-f]{64}',j['commitAnchor'])is not None and type(j.get('records'))is int and j['records']>0 and state.get('authorityRestorable')is False and authority.get('consent')is False and authority.get('leaseId')is None and authority.get('authorityRestorable')is False and layout.get('ownerActive')is False

def observe_native_terminal(op,C,run,epoch,boot,generation,resource,seconds=8):
    deadline=time.monotonic()+seconds;last=None
    while True:
        resource.check();state=op.state(allow_absent=True,require_context=False);layout=op.layout();last={'hostNs':time.monotonic_ns(),'state':state,'layout':layout,'qualified':native_terminal_ready(state,layout,run,epoch,boot,generation)}
        with(C/'native-closure-observations.jsonl').open('a')as f:f.write(json.dumps(last)+'\n');f.flush();os.fsync(f.fileno())
        if last['qualified']:
            put(C/'native-closed-outside-proof.json',last);return state
        if time.monotonic()>=deadline:raise RuntimeError('NATIVE_CLOSED_OUTSIDE_ANCHOR_NOT_OBSERVED')
        time.sleep(.1)

def restart_inert_ready(state,layout,prior_epoch):
    # New epoch is a prerequisite; missing phase remains NOT_READY, never a KeyError.
    if type(state)is not dict or type(layout)is not dict:return False
    epoch=state.get('viewEpoch')
    if type(epoch)is not int or epoch==prior_epoch:return False
    if state.get('chosenView')not in('survey','preflight','fly','review'):return False
    if 'viewEpoch'in layout and(type(layout['viewEpoch'])is not int or layout['viewEpoch']!=epoch):return False
    native=state.get('native')
    return type(native)is dict and native.get('phase')=='NO_SESSION'and native.get('authorityRestorable')is False and state.get('ownerActive')is False and layout.get('ownerActive')is False and layout.get('bindingStagedSHA256')is None and state.get('viewReady')is True and layout.get('viewReady')is True and state.get('chosenView')==state.get('presentedView')==layout.get('view')==layout.get('presentedView')

def restart_and_capture(op,C,run,generation,resource):
    before=device_inventory(op,run);allbefore=all_device_inventory(op);assert_prior_private_preserved(allbefore);priorcase=read(C/'all-private-before-case-SHA.json');assert all(allbefore.get(k)==h for k,h in priorcase.items()),'CASE_PRIOR_PRIVATE_HISTORY_CHANGED';put(C/'all-private-before-restart-SHA.json',allbefore);put(C/'private-before-restart-SHA.json',before)
    beforeUI=json.loads(op.command(['shell','run-as','vn.rtr.aeris.cockpit05','cat','files/workspace-state.json'])[0]);priorEpoch=beforeUI['viewEpoch']
    put(C/'workspace-before-restart.json',beforeUI)
    op.command(['shell','am','force-stop','vn.rtr.aeris.cockpit05']);op.command(['shell','am','start','-n','vn.rtr.aeris.cockpit05/.CockpitActivity'])
    deadline=time.monotonic()+10
    while True:
        resource.check()
        w=json.loads(op.command(['shell','run-as','vn.rtr.aeris.cockpit05','cat','files/workspace-state.json'])[0]);layout=op.layout()
        if restart_inert_ready(w,layout,priorEpoch):break
        if time.monotonic()>deadline:raise RuntimeError('RESTART_DID_NOT_RESTORE_INERT_VIEW')
        time.sleep(.1)
    after=device_inventory(op,run);assert before==after;allafter=all_device_inventory(op);assert allbefore==allafter;assert_prior_private_preserved(allafter);put(C/'all-private-after-restart-SHA.json',allafter)
    beforeWorkspace=beforeUI['workspace'];afterWorkspace=w['workspace']
    reviewIDs=lambda workspace:{x.get('run',x.get('id'))for x in workspace['reviews']}
    assert afterWorkspace.get('error')is None and afterWorkspace['draftSHA256']==beforeWorkspace['draftSHA256']
    assert run in reviewIDs(afterWorkspace)and reviewIDs(beforeWorkspace)==reviewIDs(afterWorkspace)
    put(C/'restart-recovery.json',{'status':'PASS_EXACT_DEVICE_FILES_NO_AUTHORITY_RESTORE','files':after,'currentUI':w,'layout':layout,'beforeViewEpoch':priorEpoch,'afterViewEpoch':w['viewEpoch'],'newViewEpoch':w['viewEpoch']!=priorEpoch,'noReconnectIntentSent':True,'allPriorPrivateFilesPreserved':len(allbefore)});op.screenshot()
    capture_native(op,C,run,'short'if C.parent.name=='actual-short01'else'long',resource)

def main():
    contract.verify_full_inputs()
    scenario=sys.argv[1]if len(sys.argv)>1 else'short';assert scenario in contract.CASES
    selectedcase=contract.CASES[scenario];attempt='01';seconds=selectedcase['maximumSeconds'];holdSeconds=selectedcase['holdSeconds']
    assert contract.case_budget(shutil.disk_usage(R).free,seconds)['admitted'],'ACTUAL_WHOLE_BUDGET_ENTRY10_BEFORE_CASE_DIRECTORY'
    assert (E/'initial-private-SHA.json').is_file()and(E/'initial-workspace-state.json').is_file(),'CURRENT134_PRIVATE_BASELINE_REQUIRED'
    assert (E/'emulator01/launch.json').is_file()and not(E/'emulator01/closure.json').exists(),'OWNED_GUARDIAN_ACTIVE_REQUIRED'
    if scenario=='long':
        gate=read(E/'qa/short-cold01/results.json');assert gate.get('status')=='SHORT_PASS_CLOSED_RAW_ONLY'and gate.get('actualThirtyMinuteAccepted')is False,'SHORT_COLD_GATE_REQUIRED_BEFORE_LONG'
    O=E/selectedcase['directory'];O.mkdir();C=O/'control';C.mkdir();D=O/'raw';D.mkdir()
    run=selectedcase['run'];epoch=uuid.uuid4().hex;boot=uuid.uuid4().hex;generation=uuid.uuid4().hex;case=run
    op=RootOperator(C/'android',run,generation)
    # Fresh native measured geometry is observed for each explicit action.
    setup=read(E/'android-setup01'/('ui-geometry-long.json'if scenario=='long'else'ui-geometry.json'));op.nav_geometry=setup['navGeometry']
    logs=[];host=container=None;failure=None;connected=False;terminalProof=None;began=time.monotonic();ground=[];guardThread=None;fault_injected=False;resource=ResourceGuard(C,seconds+290,seconds)
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
        selected=contract.build_input_contract(R);selectedFull=read(E/'host/input-contract01.json');assert selectedFull['runtimeEntryModule']==contract.RUNTIME;manifest=verify_pins(R,E/'host/input-contract01.json');native=read(R/'evidence/betaintegrated01-cockpit05-native/build-02.json')
        oracle_manifest=read(E/'host/input-contract01.json')
        for n,h in oracle_manifest['sourceSHA256'].items():assert sha(R/n)==h,('ORACLE_SOURCE_DRIFT',n)
        put(C/'input-pins.json',{'hostManifestSHA256':sha(E/'host/input-contract01.json'),'nativeBuildSHA256':sha(R/'evidence/betaintegrated01-cockpit05-native/build-02.json'),'oracleManifestSHA256':sha(E/'host/input-contract01.json'),'oracleSourceSHA256':oracle_manifest['sourceSHA256'],'controllerSHA256':sha(__file__),'powerPolicySHA256':sha(E/'power-policy01.json')})
        for n,h in native['sourcePins'].items():assert sha(R/n)==h,('NATIVE_SOURCE_DRIFT',n)
        assert sha(APK)==native['sha256'];assert contract.case_budget(shutil.disk_usage(R).free,seconds)['admitted']
        power=power_observation(cmd(['pmset','-g','batt']));assert power['AC']or power['batteryPercent']>=30,'POWER_ENTRY_REFUSED';put(C/'actual-power-entry.json',power)
        guardian=read(E/'emulator01/launch.json');guardianAdmission=read(E/'emulator01/admission.json')
        assert guardian['maximumSeconds']==5400 and guardian['scope']=='ANDROID_SITL_TEST'and guardian['guardianSourceSHA256']==sha(R/'planning/betaintegrated01/cockpit05-clockflight02/android_guardian.py')
        assert guardianAdmission['sourceSHA256']==guardian['guardianSourceSHA256']and guardianAdmission['maximumSeconds']==5400
        assert cmd(['ps','-p',str(guardian['guardianPID']),'-o','lstart=']).strip()==guardian['guardianProcessStart']
        assert cmd(['ps','-p',str(guardian['pid']),'-o','lstart=']).strip()==guardian['processStart']
        put(C/'owned-guardian-observation.json',{'launch':guardian,'admission':guardianAdmission,'sourceCurrent':True,'closureAbsent':True})
        capacity=contract.case_budget(shutil.disk_usage(R).free,seconds);assert capacity['admitted'];put(C/'capacity.json',capacity);resource.start()
        assert not(E/'emulator01/closure.json').exists()
        for port,kind in [(5961,socket.SOCK_STREAM),(5962,socket.SOCK_STREAM),(5963,socket.SOCK_STREAM),(9012,socket.SOCK_DGRAM),(9014,socket.SOCK_DGRAM)]:
            with socket.socket(socket.AF_INET,kind)as sock:sock.bind(('127.0.0.1',port))
        assert cmd(['docker','image','inspect',IMAGE,'--format','{{.Id}}']).strip()==IMAGE
        assert not cmd(['docker','ps','-aq','--filter','name=^/'+name+'$']).strip()
        path_read=op.command(['shell','pm','path','vn.rtr.aeris.cockpit05']);installed=path_read[0].decode().strip()[8:]
        apk_read=op.command(['shell','sha256sum',installed]);assert apk_read[0].decode().split()[0]==native['sha256']==contract.APK_SHA256
        packageEvidence={'package':contract.PACKAGE,'APKPathReadCommandReceipt':str(path_read[3]/'receipt.json'),'APKPathReadCommandReceiptSHA256':sha(path_read[3]/'receipt.json'),'APKHashReadCommandReceipt':str(apk_read[3]/'receipt.json'),'APKHashReadCommandReceiptSHA256':sha(apk_read[3]/'receipt.json'),'installedAPK_SHA256':apk_read[0].decode().split()[0],'selectedAPKSourceSHA256':native['sourceSHA256'],'sourceBinding':'INSTALLED_APK_EXACT_HASH_MATCHES_FROZEN_SELECTED05_APK_AND_PACKAGED_SOURCE_IDENTITY','expectedPackage':contract.PACKAGE}
        put(C/'installed-package-observation-evidence.json',packageEvidence)
        packageObservation={'package':contract.PACKAGE,'sourceSHA256':native['sourceSHA256'],'apkSHA256':native['sha256'],'run':run,'epoch':epoch,'boot':boot,'generation':generation,'observedHostNs':time.monotonic_ns(),'observationEvidencePath':str(C/'installed-package-observation-evidence.json'),'observationEvidenceSHA256':sha(C/'installed-package-observation-evidence.json')}
        put(C/'installed-package-observation.json',packageObservation)
        retain_initial_baselines(C)
        check_initial_workspace(op,C,run)
        state=O/'AP-state';prepare_fresh_case_state(R,state,case)
        cfg=contract.build_config(R,'nominal',run,epoch,boot,D,case,maximum_seconds=seconds)
        put(D/'run-config.json',cfg)
        providers=read(R/'planning/betaintegrated01/m1cockpit04/native/expected-providers01.json')['profiles'];provider=providers['M1-COCKPIT04-NOMINAL']
        binding={k:provider[k]for k in ['version','mode','profileId','binarySHA256','modelSHA256','configSHA256','endpoint','firmware']};binding.update(rootOwnedContainer=True,targetSystem=42,run=run,epoch=epoch,boot=boot,operator='root-simulator-QA',generation=generation,inputProvenance='ROOT_INJECTED_ANDROID_TOUCH')
        put(C/'launch-binding.json',binding)
        tmp='/data/local/tmp/aeris-control01-'+run+'.json';op.command(['push',str(C/'launch-binding.json'),tmp]);op.command(['shell','run-as','vn.rtr.aeris.cockpit05','cp',tmp,'files/launch-binding.json'])
        assert op.command(['shell','run-as','vn.rtr.aeris.cockpit05','sha256sum','files/launch-binding.json'])[0].decode().split()[0]==sha(C/'launch-binding.json')
        op.command(['shell','am','start','-n','vn.rtr.aeris.cockpit05/.CockpitActivity','--es','m1Action','STAGE_BINDING','--es','m1ActionId',run+'-stage','--es','launchBindingSHA256',sha(C/'launch-binding.json')]);time.sleep(.2)
        stage_deadline=time.monotonic()+3
        while True:
            layout=op.layout();node=layout['buttons']['control01-connect']
            if layout.get('bindingStagedSHA256')==sha(C/'launch-binding.json')and layout['view']=='preflight'and layout.get('viewReady')and node['visible']and node['enabled']:break
            if time.monotonic()>stage_deadline:raise RuntimeError('STAGE_GATE_BEFORE_AP_REFUSED')
            time.sleep(.05)
        snapshot=json.loads(op.command(['shell','run-as','vn.rtr.aeris.cockpit05','cat','files/workspace-state.json'])[0]);assert snapshot.get('ownerActive')is False and snapshot.get('native',{}).get('phase')=='NO_SESSION'
        put(C/'staging-gate-before-AP.json',{'layout':layout,'workspace':snapshot,'noWriterAtStage':True,'APStarted':False,'rootBindingSHA256':sha(C/'launch-binding.json')})
        docker=['docker','run','--rm','--name',name,'--label','aeris.task=cockpit05-clockflight02','--label','aeris.run='+run,'--cpus','4','--memory','2g','--pids-limit','128','--read-only','--tmpfs','/tmp:size=16m','-p','127.0.0.1:5963:5760/tcp','-p','127.0.0.1:5962:5762/tcp','-p','127.0.0.1:9014:9004/udp','-v',str(R)+':/src:ro','-v',str(R/'runtime/betaintegrated01/dist')+':/candidate:ro','-v',str(R/'pilot/betaintegrated01/cockpit04/profiles')+':/control:ro','-v',str(D)+':/evidence:rw','-v',str(state)+':/state:rw','-w','/src','-e','PYTHONDONTWRITEBYTECODE=1',IMAGE,*[x.replace('pilot.betaintegrated01.cockpit04.ap_supervisor','planning.betaintegrated01.cockpit05-clockowner02.runtime.ap_supervisor')for x in supervisor_argv()]]
        ledger=E/'actual-launch-ledger.jsonl';entries=[json.loads(x)for x in ledger.read_text().splitlines()]if ledger.exists()else[]
        assert not any(x['run']==run for x in entries),'EACH_CASE_ONE_START_NO_AUTOMATIC_RETRY'
        assert len(entries)<2,'ONLY_SHORT_THEN_LONG'
        assert (scenario=='short'and not entries)or(scenario=='long'and len(entries)==1 and entries[0]['run']==contract.CASES['short']['run']),'ORDER_SHORT_THEN_LONG_ONLY'
        with ledger.open('a')as f:f.write(json.dumps({'run':run,'selectedCapacityRevision':2,'hostNs':time.monotonic_ns(),'controllerSHA256':sha(__file__),'rootOperatorSHA256':sha(R/'planning/betaintegrated01/cockpit05-soak/android/cockpit05_root_operator.py'),'host':['python3','-B','-m',contract.RUNTIME,'--config',str(D/'run-config.json')],'docker':docker})+'\n');f.flush();os.fsync(f.fileno())
        logs=[(C/'backend-control-stdout.txt').open('xb'),(C/'container-control-stdout.txt').open('xb')]
        assert contract.case_budget(shutil.disk_usage(R).free,seconds)['admitted'],'HOST_WHOLE_BUDGET_ENTRY10_IMMEDIATELY_BEFORE_POPEN'
        host=subprocess.Popen(['python3','-B','-m',contract.RUNTIME,'--config',str(D/'run-config.json')],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=logs[0],stderr=subprocess.STDOUT,start_new_session=True)

        deadline=time.monotonic()+40
        while not(D/'backend-identity.json').exists():
            check();assert time.monotonic()<deadline,'PRIME_DEADLINE';time.sleep(.2)
        identity=read(D/'backend-identity.json');assert identity['guardPrimed']and identity['transportReady'];assert all(identity[k]['elapsedRealMonotonicNs']>=15_000_000_000 for k in ('guardPriming','transportGuardPriming','clockGuardPriming'));put(C/'actual-prime.json',identity)
        assert contract.case_budget(shutil.disk_usage(R).free,seconds)['admitted'],'AP_WHOLE_BUDGET_ENTRY10_IMMEDIATELY_BEFORE_POPEN'
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
                if min(host_span,guest_span,AP_span)>=holdSeconds:break
                time.sleep(2)
        if scenario=='short':
            put(C/'short-hold-finished.json',{'hostNs':time.monotonic_ns(),'hostSeconds':host_span,'guestSeconds':guest_span,'APSeconds':AP_span,'state':s})
            op.explicit_tap('land');wait(lambda x:x['flight']['mode']==9,4);ground_observe(20)
            wait(lambda x:not x['flight']['armed']and x['flight']['landedState']==1 and abs(x['flight']['relativeAltitudeM'])<=.4,5)
            op.explicit_tap('close');wait(lambda x:x.get('closed')and not x['input']['consent'],4);post_flight=True
        else:
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
            check();view=json.loads(op.command(['shell','run-as','vn.rtr.aeris.cockpit05','cat','files/workspace-state.json'])[0])
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
                try:terminalProof=observe_native_terminal(op,C,run,epoch,boot,generation,resource,3)
                except Exception as exc:put(C/'native-terminal-before-force-stop-unknown.json',{'error':str(exc),'noClosedAnchorInferred':True})
                try:
                    if terminalProof is None:op.command(['shell','am','force-stop','vn.rtr.aeris.cockpit05'])
                except Exception as exc:put(C/'native-stop-error.json',{'error':str(exc)})
                try:
                    if host and host.poll()is None:ground_observe(18)
                except Exception as exc:put(C/'abort-ground-unknown.json',{'error':str(exc),'forcedAPStopIsNotLandingProof':True})
            try:
                current=terminalProof if terminalProof is not None else observe_native_terminal(op,C,run,epoch,boot,generation,resource,8);put(C/'native-last-external-observation.json',current)
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
