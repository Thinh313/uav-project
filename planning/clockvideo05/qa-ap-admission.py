"""Read-only AP admission replay. Never starts/stops/arms or changes runtime data."""
from pathlib import Path
import json,hashlib,re,math,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/field02/clockvideo05';GIB=2**30

def admission_decision(a):
    samples=a['samples'];assert len(samples)==31,'AP_ADMISSION31_SAMPLES';assert isinstance(a['durationMs'],(int,float))and math.isfinite(a['durationMs'])and a['durationMs']>=30000,'AP_ADMISSION_DECLARED30S';assert a['minimumBytes']==29*GIB,'AP_ADMISSION_DECLARED29GIB'
    last=None;peak=0;decline=0
    for s in samples:
        t=s['hostMonoMs'];free=s['freeBytes'];assert isinstance(t,(int,float))and math.isfinite(t)and isinstance(free,int)and not isinstance(free,bool),'AP_ADMISSION_FINITE_SAMPLE';assert last is None or t>last,'AP_ADMISSION_MONOTONIC_SAMPLE';last=t;assert free>=29*GIB,'AP_ADMISSION29GIB';peak=max(peak,free);decline=max(decline,peak-free);assert decline<=256*2**20,'AP_ADMISSION_PEAK_DECLINE256MIB'
    assert samples[-1]['hostMonoMs']-samples[0]['hostMonoMs']>=30000,'AP_ADMISSION_OBSERVED30S';return{'samples':31,'observedSpanMs':samples[-1]['hostMonoMs']-samples[0]['hostMonoMs'],'minimumFreeBytes':min(s['freeBytes']for s in samples),'maximumPeakDeclineBytes':decline,'notFlightAcceptance':True}

def check(run,name):
    assert re.fullmatch('s[a-f0-9]{20}',run)and re.fullmatch('[a-z0-9-]{1,100}',name),'OWNED_RUN_AND_EXCLUSIVE_NAME_REQUIRED';out=E/(name+'.json');assert not out.exists(),'ADMISSION_RECEIPT_EXISTS';base=R/'evidence/field02/flight/runs'/run;report={'run':run,'status':'REFUSED_NOT_ARMED','readonlyReplay':True,'inputs':{}}
    try:
        for file in['request.json','admission.json','source-pins.json']:
            p=base/file;assert p.is_file()and not p.is_symlink()and p.stat().st_size<=256*2**10,'ADMISSION_INPUT_BOUND';b=p.read_bytes();report['inputs'][str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
        expectedPins=R/'evidence/field02/clockvideo05/flight-pins03.json';expectedBytes=expectedPins.read_bytes();assert (base/'source-pins.json').read_bytes()==expectedBytes,'CURRENT_FIXED_SOURCE_PINS_EXACT_BYTES';report['expectedPinsSha256']=hashlib.sha256(expectedBytes).hexdigest();request=json.loads((base/'request.json').read_text());pins=json.loads((base/'source-pins.json').read_text());assert request['run']==run and request['mode']=='sitl'and pins['format']=='aeris-clockvideo05-flight-pins'and run not in[r['run']for r in pins['priorSITLRequests']],'CURRENT_CLOCKVIDEO05_RUN_REQUIRED';report['decision']=admission_decision(json.loads((base/'admission.json').read_text()));report['status']='PASS_READONLY_AP_ADMISSION_NOT_FLIGHT_ACCEPTANCE';return report
    except BaseException as e:report['error']=str(e);raise
    finally:out.open('x').write(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':assert len(sys.argv)==4 and sys.argv[1]=='--check-admission';print(json.dumps(check(sys.argv[2],sys.argv[3]),indent=2))
