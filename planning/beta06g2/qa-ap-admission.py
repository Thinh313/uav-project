"""Read-only AP admission replay. Never starts/stops/arms or changes runtime data."""
from pathlib import Path
import json,hashlib,re,math,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation02';GIB=2**30

def admission_decision(a):
    samples=a['samples'];assert len(samples)==31,'AP_ADMISSION31_SAMPLES';assert isinstance(a['durationMs'],(int,float))and math.isfinite(a['durationMs'])and a['durationMs']>=30000,'AP_ADMISSION_DECLARED30S';assert a['minimumBytes']==29*GIB,'AP_ADMISSION_DECLARED29GIB'
    last=None;peak=0;decline=0
    for s in samples:
        t=s['hostMonoMs'];free=s['freeBytes'];assert isinstance(t,(int,float))and math.isfinite(t)and isinstance(free,int)and not isinstance(free,bool),'AP_ADMISSION_FINITE_SAMPLE';assert last is None or t>last,'AP_ADMISSION_MONOTONIC_SAMPLE';last=t;assert free>=29*GIB,'AP_ADMISSION29GIB';peak=max(peak,free);decline=max(decline,peak-free);assert decline<=256*2**20,'AP_ADMISSION_PEAK_DECLINE256MIB'
    assert samples[-1]['hostMonoMs']-samples[0]['hostMonoMs']>=30000,'AP_ADMISSION_OBSERVED30S';return{'samples':31,'observedSpanMs':samples[-1]['hostMonoMs']-samples[0]['hostMonoMs'],'minimumFreeBytes':min(s['freeBytes']for s in samples),'maximumPeakDeclineBytes':decline,'notFlightAcceptance':True}

QUALIFIED_PROFILE='beta06-native-arm64-4.7.1'
QUALIFIED_BINARY='1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41'
QUALIFIED_PATH='evidence/sim32-instrument01/direct-uncorrected-source/arducopter'
QUALIFIED_IMAGE='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84'
def qualified_launch_decision(launch,root=R):
    expected={'qualifiedProfile':QUALIFIED_PROFILE,'binarySha256':QUALIFIED_BINARY,'binaryPath':QUALIFIED_PATH,'platform':'linux/arm64','observerEnabled':False,'imageId':QUALIFIED_IMAGE,'port':5972,'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_SIM32_OR_HERA','speedup':1,'hardDeadlineS':540,'attemptTotalMaximumS':600}
    assert all(launch.get(k)==v and(type(launch.get(k))is type(v))for k,v in expected.items()),'EXACT_QUALIFIED_NATIVE_ARM_LAUNCH_REQUIRED'
    a=launch.get('command');assert isinstance(a,list)and all(isinstance(x,str)for x in a)and len(a)<=100,'BOUNDED_LAUNCH_COMMAND_REQUIRED'
    required={'--platform':'linux/arm64','--pull':'never','--network':'bridge','--cpus':'1','--memory':'256m','--cap-drop':'ALL','--security-opt':'no-new-privileges','-p':'127.0.0.1:5972:5760'}
    for k,v in required.items():assert a.count(k)==1 and a.index(k)+1<len(a)and a[a.index(k)+1]==v,'NATIVE_PROFILE_COMMAND_OPTION:'+k
    assert not any(x in a for x in ['--entrypoint','--privileged','--env'])and not any(x.startswith(('--entrypoint=','--env=','--platform='))for x in a),'NATIVE_PROFILE_ALTERNATE_OVERRIDE_REFUSED'
    env=[a[i+1]for i,x in enumerate(a[:-1])if x=='-e'];assert env==['AERIS_DIRECT_TRACE=0'],'OBSERVER_EXPLICITLY_DISABLED_REQUIRED'
    mounts=[a[i+1]for i,x in enumerate(a[:-1])if x=='-v'];assert str(root/QUALIFIED_PATH)+':/aeris/arducopter:ro'in mounts,'EXACT_READONLY_NATIVE_BINARY_MOUNT_REQUIRED'
    image='rtr-aeris-sim32-trace-builder@'+QUALIFIED_IMAGE;assert a.count(image)==1 and a[a.index(image)+1:]==['/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1'],'DIRECT_STOCK_QUAD_ENTRYPOINT_REQUIRED'
    assert type(launch.get('pid'))is int and launch['pid']>0 and isinstance(launch.get('containerId'),str)and re.fullmatch('[a-f0-9]{64}',launch['containerId']),'ACTUAL_LAUNCH_PROCESS_IDENTITY_REQUIRED'
    return {'profile':QUALIFIED_PROFILE,'binarySha256':QUALIFIED_BINARY,'imageId':QUALIFIED_IMAGE,'observerEnabled':False,'basis':'RECORDED_EXACT_LAUNCH_AND_PIN_BYTES_NOT_INDEPENDENT_LIVE_DOCKER_ATTESTATION','liveRuntimeAndIncomingFirmwareGuardStillRequired':True}

def check(run,name):
    assert re.fullmatch('s[a-f0-9]{20}',run)and re.fullmatch('[a-z0-9-]{1,100}',name),'OWNED_RUN_AND_EXCLUSIVE_NAME_REQUIRED';out=E/(name+'.json');assert not out.exists(),'ADMISSION_RECEIPT_EXISTS';base=R/'evidence/beta06/generation02/flight/runs'/run;report={'run':run,'status':'REFUSED_NOT_ARMED','readonlyReplay':True,'inputs':{}}
    try:
        for file in['request.json','admission.json','source-pins.json','launch.json']:
            p=base/file;assert p.is_file()and not p.is_symlink()and p.stat().st_size<=256*2**10,'ADMISSION_INPUT_BOUND';b=p.read_bytes();report['inputs'][str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
        expectedPins=R/'evidence/beta06/generation02/flight-pins.json';expectedBytes=expectedPins.read_bytes();assert (base/'source-pins.json').read_bytes()==expectedBytes,'CURRENT_FIXED_SOURCE_PINS_EXACT_BYTES';report['expectedPinsSha256']=hashlib.sha256(expectedBytes).hexdigest();request=json.loads((base/'request.json').read_text());pins=json.loads((base/'source-pins.json').read_text());assert request['run']==run and request['mode']=='sitl'and pins['format']=='aeris-beta06g2-flight-pins'and run not in[r['run']for r in(pins['priorSITLRequests']+pins['priorBetaSITLRequests'])],'CURRENT_BETA06G2_RUN_REQUIRED';report['qualifiedLaunch']=qualified_launch_decision(json.loads((base/'launch.json').read_text()));report['decision']=admission_decision(json.loads((base/'admission.json').read_text()));report['status']='PASS_READONLY_AP_ADMISSION_NOT_FLIGHT_ACCEPTANCE';return report
    except BaseException as e:report['error']=str(e);raise
    finally:out.open('x').write(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':assert len(sys.argv)==4 and sys.argv[1]=='--check-admission';print(json.dumps(check(sys.argv[2],sys.argv[3]),indent=2))
