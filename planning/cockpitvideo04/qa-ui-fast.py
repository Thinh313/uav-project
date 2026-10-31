"""Root-only flight UI chains: exact numeric/text OCR bindings, no fuzzy fallback or control POST."""
from pathlib import Path
import importlib.util,json,time,sys,subprocess,re,math,hashlib
spec=importlib.util.spec_from_file_location('qa_android04',Path(__file__).with_name('qa-android.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
FAST=q.R/'.local/cockpitvideo04/qa-ocr-fast';RIGHT=(740,250,1190,650)
PATTERNS={'preflight':r'^1[\s.·•:\-]+.*preflight','grant':r'^2[\s.·•:\-]+.+','upload':r'^3[\s.·•:\-]+upload','arm':r'^4[\s.·•:\-]+arm','auto':r'^5[\s.·•:\-]+.*auto'}
def bind(rows,action):
    pattern=PATTERNS[action];hits=[]
    for r in rows:
        x,y,w,h=[r[k]for k in['x','y','width','height']]
        if r['confidence']>=.45 and RIGHT[0]<=x and RIGHT[1]<=y and x+w<=RIGHT[2]and y+h<=RIGHT[3]and re.search(pattern,q.norm(r['text'])):hits.append(r)
    assert len(hits)==1,{'action':action,'strictPattern':pattern,'matches':hits,'disposition':'NO_ACTION_NO_FUZZY_FALLBACK'}
    return hits[0]

def run(attempt,phase,expected_mode='sitl'):
    assert attempt in ['01','02']and phase in ['preflight-grant-upload','arm-home-auto'];assert expected_mode in ['mock','sitl'];q.owned(attempt);initial=q.state();f=initial['flight'];run=f['run'];assert run and f['mode']==expected_mode and run.startswith('s'if expected_mode=='sitl'else'm'),'EXACT_EXPECTED_SIMULATION_MODE_REQUIRED';out=q.E/f'qa-ui-fast-{attempt}-{expected_mode}-{run}-{phase}.jsonl';assert not out.exists(),'CHAIN_ALREADY_RECORDED_NO_RETRY';counter=0;start=time.monotonic();budget=30 if phase=='preflight-grant-upload'else 10;deadline=start+budget;r=f['request'];identity={k:r[k]for k in['instance','run','session','boot','modelSha256','planSha256']};client={k:initial['client'][k]for k in['id','epoch','instance']}
    def log(v):
        assert not out.exists()or out.stat().st_size<128*2**10
        with out.open('a')as fp:fp.write(json.dumps({'at':time.time(),'mono':time.monotonic(),'elapsedMs':(time.monotonic()-start)*1000,'mode':expected_mode,'initialRun':run,'notSITLProof':expected_mode=='mock',**v},ensure_ascii=False)+'\n')
    def state():
        assert time.monotonic()<deadline,'FAST_CHAIN_DEADLINE_NO_RETRY';s=q.state();f=s['flight'];assert f['run']==run and all(f['request'].get(k)==v for k,v in identity.items()),'FLIGHT_BINDING_CHANGED_NO_ACTION';assert s['client'].get('active')is True and all(s['client'].get(k)==v for k,v in client.items()),'CLIENT_EPOCH_CHANGED_NO_ACTION';return s
    def wait(pred,label):
        while True:
            s=state()
            if pred(s['flight']):log({'observed':label,'binding':identity,'client':client,'autoGate':s['flight'].get('autoGate')});return s
            if s['flight'].get('error'):raise RuntimeError(s['flight']['error'])
            time.sleep(.1)
    def tap(action,admit):
        nonlocal counter
        counter+=1;name=f'android-fast-{attempt}-{expected_mode}-{run}-{phase}-{counter:02d}';image=q.capture(attempt,name);before=time.monotonic();p=subprocess.run([str(FAST),str(image)],capture_output=True,text=True,timeout=min(2,max(.05,deadline-time.monotonic())));assert p.returncode==0,{'ocrExit':p.returncode,'stderr':p.stderr[-500:]};rows=json.loads(p.stdout);ocrRecord={'imageSha256':hashlib.sha256(image.read_bytes()).hexdigest(),'ocrBinarySha256':hashlib.sha256(FAST.read_bytes()).hexdigest(),'ocrElapsedMs':(time.monotonic()-before)*1000,'rows':rows};(q.E/(name+'.ocr.json')).open('x').write(json.dumps(ocrRecord,ensure_ascii=False,indent=2)+'\n');
        try:hit=bind(rows,action)
        except AssertionError as exc:log({'result':'NO_ACTION_STRICT_OCR_REFUSAL','action':action,'strictPattern':PATTERNS[action],'detail':str(exc)});raise
        s=state();admit(s['flight']);x,y=round(hit['x']+hit['width']/2),round(hit['y']+hit['height']/2);log({'beforeTap':action,'strictPattern':PATTERNS[action],'OCR':hit,'point':[x,y],'binding':identity,'client':client,'autoGate':s['flight'].get('autoGate')});q.adb('shell','input','tap',x,y);log({'actualTapSent':action})
    def disarmed(f):assert not f['busy']and(f.get('live')or{}).get('stage')=='DISARMED','DISARMED_IDLE_REQUIRED'
    def ready(f):disarmed(f);assert(f.get('live')or{}).get('preflight63',{}).get('ready')is True,'PREFLIGHT_READY_REQUIRED'
    def grant_live(f):ready(f);assert f.get('authority'),'EXPLICIT_AUTHORITY_REQUIRED'
    def arm_ready(f):grant_live(f);assert(f.get('live')or{}).get('readback63'),'READBACK_REQUIRED'
    if phase=='preflight-grant-upload':
        tap('preflight',disarmed);wait(lambda f:not f['busy']and(f.get('live')or{}).get('preflight63',{}).get('ready'),'preflight-ready')
        tap('grant',ready);wait(lambda f:bool(f.get('authority'))and not f['busy'],'explicit-grant')
        tap('upload',grant_live);wait(lambda f:not f['busy']and(f.get('live')or{}).get('readback63'),'readback-observed')
    else:
        tap('preflight',disarmed);wait(lambda f:not f['busy']and(f.get('live')or{}).get('preflight63',{}).get('ready'),'fresh-prearm-ready')
        tap('arm',arm_ready);s=wait(lambda f:not f['busy']and(f.get('live')or{}).get('stage')=='ARMED_HOME_REVIEW','post-arm-home');h=s['flight']['live']['homeReview'];home=h['postArmHome'];assert math.hypot((home['lat']-10.854)*111319,(home['lon']-106.807)*109300)<=1 and abs(home['amsl']-10)<=.5,'UNEXPECTED_HOME_MANUAL_REVIEW';log({'observedHomeReview':h})
        def auto_ready(f):assert not f['busy']and f.get('autoGate',{}).get('eligible')is True and f['autoGate']['effectiveRemainingMs']>1800,'HOME_PARAMETER_WINDOW_REFUSED_NO_RETRY'
        tap('auto',auto_ready);wait(lambda f:(f.get('live')or{}).get('stage')in['AUTO','FLYING','COMPLETED','RTL','GROUND']or(f.get('live')or{}).get('autoObserved'),'AUTO-observed')
    log({'result':'UI_CHAIN_COMPLETE_NOT_FLIGHT_ACCEPTANCE','budgetSeconds':budget})

if __name__=='__main__':
    assert len(sys.argv)in[3,4]and(len(sys.argv)==3 or sys.argv[3]=='--mock');run(sys.argv[1],sys.argv[2],'mock'if len(sys.argv)==4 else'sitl')
