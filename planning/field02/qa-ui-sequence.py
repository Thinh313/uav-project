"""QA only: real ADB UI input plus read-only host observation. No control POST."""
import importlib.util,json,time,urllib.request,sys,re,subprocess,math,unicodedata
from pathlib import Path
p=Path(__file__).with_name('qa-android.py');spec=importlib.util.spec_from_file_location('qa',p);q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
out=q.E/('qa-ui-sequence-'+sys.argv[1]+'.jsonl');assert not out.exists()
def log(v):
 with out.open('a')as f:f.write(json.dumps({'at':time.time(),**v},ensure_ascii=False)+'\n')
def state():return json.load(urllib.request.urlopen('http://127.0.0.1:8872/api/state',timeout=3))['flight']
def wait(pred,label,limit=20):
 end=time.monotonic()+limit
 while time.monotonic()<end:
  f=state()
  if pred(f):log({'observed':label,'run':f.get('run'),'stage':(f.get('live')or{}).get('stage'),'autoGate':f.get('autoGate')});return f
  if f.get('error'):raise RuntimeError(f['error'])
  time.sleep(.15)
 raise TimeoutError(label)
def tap(i):
 # Fresh screenshot and local OCR: UIAutomator can stall the WebView heartbeat.
 name='android-qa-'+sys.argv[1]+'-'+i.replace('field-','')+'-'+str(time.monotonic_ns())
 q.capture(name)
 rows=json.loads(subprocess.check_output([str(q.R/'.local/field02/qa-ocr'),str(q.E/(name+'.png'))]))
 labels={'field-preflight':'Đọc preflight','field-grant':'Cấp quyền bay','field-upload':'Upload / readback','field-arm':'Arm trên đất','field-auto':'Duyệt Home','cut':'Cắt kết nối SITL','reboot':'Restart tiến trình AP'}
 hits=[r for r in rows if labels[i].lower() in r['text'].lower()];assert len(hits)==1,(i,hits)
 r=hits[0];x=round(r['x']+r['width']/2);y=round(r['y']+r['height']/2)
 q.adb('shell','input','tap',x,y);log({'uiTap':i,'observedOCR':r,'point':[x,y]});time.sleep(.2)
tap('field-preflight');wait(lambda f:(f.get('live')or{}).get('preflight63',{}).get('ready')and not f['busy'],'preflight-ready',90);time.sleep(1)
tap('field-grant');wait(lambda f:f.get('authority'),'authority-explicit');time.sleep(.5)
tap('field-upload');wait(lambda f:(f.get('live')or{}).get('readback63')and not f['busy'],'readback',50)
time.sleep(1);tap('field-preflight');wait(lambda f:not f['busy']and(f.get('live')or{}).get('preflight63',{}).get('ready'),'pre-arm-cohort',20)
time.sleep(.6);tap('field-arm');f=wait(lambda f:(f.get('live')or{}).get('stage')=='ARMED_HOME_REVIEW'and not f['busy'],'home-after-arm',30)
h=f['live']['homeReview'];log({'homeReview':h})
# The fixture must remain the declared local simulator site; no firmware/config writes.
home=h['postArmHome'];delta=math.hypot((home['lat']-10.854)*111319,(home['lon']-106.807)*109300)
assert delta<=1 and abs(home['amsl']-10)<=.5,'UNEXPECTED_HOME_REQUIRE_MANUAL_REVIEW'
time.sleep(.4);q.capture('android-auto-home-'+sys.argv[1]);f=state();assert f.get('autoGate',{}).get('eligible') is True,'AUTO_GATE_REFUSED';assert f['autoGate']['effectiveRemainingMs']>1800,'INSUFFICIENT_UI_CONFIRMATION_WINDOW'
tap('field-auto');wait(lambda f:(f.get('live')or{}).get('stage') in ['AUTO','FLYING','COMPLETED','RTL','GROUND'] or(f.get('live')or{}).get('autoObserved'),'auto-observed',20)
q.capture('android-auto-start-'+sys.argv[1]);log({'result':'UI_SEQUENCE_COMPLETED_NOT_FLIGHT_ACCEPTANCE'})
if len(sys.argv)>2:
 fault=sys.argv[2];assert fault in ['cut','reboot']
 f=wait(lambda f:(f.get('latestPosition')or{}).get('relativeHomeM',0)>5 and f.get('positionAgeMs',9999)<1000 and (f.get('live')or{}).get('armed') is True,'airborne-fault-admission',30)
 log({'beforeFault':{'run':f['run'],'position':f['latestPosition'],'armed':f['live']['armed'],'fault':fault}})
 # Expand the observed disclosure using OCR, then scroll only the right console.
 name='android-fault-controls-'+sys.argv[1];q.capture(name)
 rows=json.loads(subprocess.check_output([str(q.R/'.local/field02/qa-ocr'),str(q.E/(name+'.png'))]))
 def norm(v):return ''.join(c for c in unicodedata.normalize('NFD',v.lower())if unicodedata.category(c)!='Mn')
 hits=[r for r in rows if 'thu hoi & loi' in norm(r['text'])and r['x']>750 and r['y']>400];assert len(hits)==1,hits
 r=hits[0];q.adb('shell','input','tap',round(r['x']+r['width']/2),round(r['y']+r['height']/2));q.adb('shell','input','swipe',1157,550,1157,300,500);time.sleep(.3)
 tap(fault);wait(lambda f:not f['run']and not f['busy'],'fault-run-closed',60);q.capture('android-fault-closed-'+sys.argv[1]);log({'result':'FAULT_UI_ACTION_CLOSED_REQUIRES_RAW_VERIFICATION'})
