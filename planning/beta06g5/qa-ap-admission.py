"""Read-only AP admission replay. Never starts/stops/arms or changes runtime data."""
from pathlib import Path
import json,hashlib,re,math,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation05';GIB=2**30

def admission_decision(a):
    samples=a['samples'];assert len(samples)==31,'AP_ADMISSION31_SAMPLES';assert isinstance(a['durationMs'],(int,float))and math.isfinite(a['durationMs'])and a['durationMs']>=30000,'AP_ADMISSION_DECLARED30S';assert a['minimumBytes']==29*GIB,'AP_ADMISSION_DECLARED29GIB'
    last=None;peak=0;decline=0
    for s in samples:
        t=s['hostMonoMs'];free=s['freeBytes'];assert isinstance(t,(int,float))and math.isfinite(t)and isinstance(free,int)and not isinstance(free,bool),'AP_ADMISSION_FINITE_SAMPLE';assert last is None or t>last,'AP_ADMISSION_MONOTONIC_SAMPLE';last=t;assert free>=29*GIB,'AP_ADMISSION29GIB';peak=max(peak,free);decline=max(decline,peak-free);assert decline<=256*2**20,'AP_ADMISSION_PEAK_DECLINE256MIB'
    assert samples[-1]['hostMonoMs']-samples[0]['hostMonoMs']>=30000,'AP_ADMISSION_OBSERVED30S';return{'samples':31,'observedSpanMs':samples[-1]['hostMonoMs']-samples[0]['hostMonoMs'],'minimumFreeBytes':min(s['freeBytes']for s in samples),'maximumPeakDeclineBytes':decline,'notFlightAcceptance':True}

QUALIFIED_PROFILE='beta06g5-native-arm64-exec-4.7.1'
QUALIFIED_BINARY='1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41'
QUALIFIED_PATH='.local/beta06g3/arducopter'
QUALIFIED_IMAGE='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84'
def qualified_launch_decision(launch,root=R):
    expected={'qualifiedProfile':QUALIFIED_PROFILE,'binarySha256':QUALIFIED_BINARY,'binaryPath':QUALIFIED_PATH,'platform':'linux/arm64','observerEnabled':False,'imageId':QUALIFIED_IMAGE,'port':5972,'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_SIM32_OR_HERA','speedup':1,'hardDeadlineS':540,'attemptTotalMaximumS':600,'binaryMode':'0755','retained':True}
    assert all(launch.get(k)==v and(type(launch.get(k))is type(v))for k,v in expected.items()),'EXACT_QUALIFIED_NATIVE_ARM_LAUNCH_REQUIRED'
    run=launch.get('run');name=launch.get('containerName');assert isinstance(name,str)and re.fullmatch('aeris-beta06g5-s[a-f0-9]{20}',name),'EXACT_GENERATED_CONTAINER_NAME_REQUIRED';run=name.removeprefix('aeris-beta06g5-');assert launch.get('labels')=={'aeris.task':'beta06g5','aeris.run':run}and launch.get('createReceipt')=='diagnostics/create-result.json','EXACT_RETAINED_LABELS_AND_CREATE_RECEIPT_REQUIRED'
    a=launch.get('command');assert isinstance(a,list)and all(isinstance(x,str)for x in a)and len(a)<=100,'BOUNDED_LAUNCH_COMMAND_REQUIRED'
    assert len(a)>=2 and a[1]=='create'and '--rm'not in a,'EXCLUSIVE_RETAINED_CREATE_REQUIRED'
    required={'--name':name,'--platform':'linux/arm64','--pull':'never','--network':'bridge','--cpus':'1','--memory':'256m','--cap-drop':'ALL','--security-opt':'no-new-privileges','-p':'127.0.0.1:5972:5760'}
    for k,v in required.items():assert a.count(k)==1 and a.index(k)+1<len(a)and a[a.index(k)+1]==v,'NATIVE_PROFILE_COMMAND_OPTION:'+k
    assert not any(x in a for x in ['--entrypoint','--privileged','--env'])and not any(x.startswith(('--entrypoint=','--env=','--platform='))for x in a),'NATIVE_PROFILE_ALTERNATE_OVERRIDE_REFUSED'
    labels=[a[i+1]for i,x in enumerate(a[:-1])if x=='--label'];assert labels==['aeris.task=beta06g5','aeris.run='+run],'EXACT_OWNED_CREATE_LABELS_REQUIRED'
    env=[a[i+1]for i,x in enumerate(a[:-1])if x=='-e'];assert env==['AERIS_DIRECT_TRACE=0'],'OBSERVER_EXPLICITLY_DISABLED_REQUIRED'
    mounts=[a[i+1]for i,x in enumerate(a[:-1])if x=='-v'];assert str(root/QUALIFIED_PATH)+':/aeris/arducopter:ro'in mounts,'EXACT_READONLY_NATIVE_BINARY_MOUNT_REQUIRED'
    image='rtr-aeris-sim32-trace-builder@'+QUALIFIED_IMAGE;assert a.count(image)==1 and a[a.index(image)+1:]==['/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1'],'DIRECT_STOCK_QUAD_ENTRYPOINT_REQUIRED'
    assert type(launch.get('pid'))is int and launch['pid']>0 and isinstance(launch.get('containerId'),str)and re.fullmatch('[a-f0-9]{64}',launch['containerId']),'ACTUAL_LAUNCH_PROCESS_IDENTITY_REQUIRED'
    return {'profile':QUALIFIED_PROFILE,'binarySha256':QUALIFIED_BINARY,'imageId':QUALIFIED_IMAGE,'observerEnabled':False,'basis':'RECORDED_EXACT_LAUNCH_AND_PIN_BYTES_NOT_INDEPENDENT_LIVE_DOCKER_ATTESTATION','liveRuntimeAndIncomingFirmwareGuardStillRequired':True}

def historical_runs(pins):
    names=['priorSITLRequests','priorBetaSITLRequests','priorGeneration02SITLRequests','priorGeneration03SITLRequests','priorGeneration04SITLRequests'];expected=[11,1,1,1,1];rows=[]
    for name,count in zip(names,expected):
        value=pins.get(name);assert isinstance(value,list)and len(value)==count,'EXACT_FIFTEEN_HISTORICAL_REQUESTS_REQUIRED';rows.extend(value)
    runs=[r.get('run')for r in rows];assert all(isinstance(run,str)and re.fullmatch('s[a-f0-9]{20}',run)for run in runs)and len(set(runs))==15,'EXACT_DISTINCT_HISTORICAL_REQUESTS_REQUIRED';assert pins['priorGeneration02SITLRequests'][0]['run']=='sb9aef33470bc49bf84ff'and pins['priorGeneration03SITLRequests'][0]['run']=='se15994472d0e479cbaa8','EXACT_CLOSED_G2_G3_REQUESTS_REQUIRED';assert pins['priorGeneration04SITLRequests'][0]['run']=='sfae933b8b0fe4d6192c5','EXACT_CLOSED_G4_REQUEST_REQUIRED';old=R/'evidence/beta06/generation04/flight/runs/sfae933b8b0fe4d6192c5/request.json';assert old.is_file()and not old.is_symlink()and old.stat().st_size<=16*2**10,'BOUNDED_PRIOR_G4_REQUEST_REQUIRED';raw=old.read_bytes();assert pins['priorGeneration04SITLRequests'][0].get('requestSha256')==hashlib.sha256(raw).hexdigest()and json.loads(raw).get('mode')=='sitl','EXACT_PRIOR_G4_REQUEST_SHA_REQUIRED';return runs

def check(run,name):
    assert re.fullmatch('s[a-f0-9]{20}',run)and re.fullmatch('[a-z0-9-]{1,100}',name),'OWNED_RUN_AND_EXCLUSIVE_NAME_REQUIRED';out=E/(name+'.json');assert not out.exists(),'ADMISSION_RECEIPT_EXISTS';base=R/'evidence/beta06/generation05/flight/runs'/run;report={'run':run,'status':'REFUSED_NOT_ARMED','readonlyReplay':True,'inputs':{}}
    try:
        for file in['request.json','admission.json','source-pins.json','launch.json']:
            p=base/file;assert p.is_file()and not p.is_symlink()and p.stat().st_size<=256*2**10,'ADMISSION_INPUT_BOUND';b=p.read_bytes();report['inputs'][str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
        expectedPins=R/'evidence/beta06/generation05/flight-pins.json';expectedBytes=expectedPins.read_bytes();assert (base/'source-pins.json').read_bytes()==expectedBytes,'CURRENT_FIXED_SOURCE_PINS_EXACT_BYTES';report['expectedPinsSha256']=hashlib.sha256(expectedBytes).hexdigest();request=json.loads((base/'request.json').read_text());pins=json.loads((base/'source-pins.json').read_text());assert request['run']==run and request['mode']=='sitl'and pins['format']=='aeris-beta06g5-flight-pins'and run not in historical_runs(pins),'CURRENT_BETA06G5_RUN_REQUIRED';launch=json.loads((base/'launch.json').read_text());assert launch.get('containerName')=='aeris-beta06g5-'+run,'LAUNCH_REQUEST_RUN_MISMATCH';report['qualifiedLaunch']=qualified_launch_decision(launch);report['decision']=admission_decision(json.loads((base/'admission.json').read_text()));report['status']='PASS_READONLY_AP_ADMISSION_NOT_FLIGHT_ACCEPTANCE';return report
    except BaseException as e:report['error']=str(e);raise
    finally:out.open('x').write(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':assert len(sys.argv)==4 and sys.argv[1]=='--check-admission';print(json.dumps(check(sys.argv[2],sys.argv[3]),indent=2))
