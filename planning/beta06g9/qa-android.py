# BETA06g2 isolated QA helper; previous helpers remain immutable.
"""Contractor UI helpers: screenshot/OCR/real tap only; no UIAutomator or control HTTP."""
from pathlib import Path
import importlib.util,sys
if 'g9_native_writer'not in sys.modules:
 _w=importlib.util.spec_from_file_location('g9_native_writer',Path(__file__).with_name('qa-native-budget.py'));b=importlib.util.module_from_spec(_w);sys.modules[_w.name]=b;_w.loader.exec_module(b)
else:b=sys.modules['g9_native_writer']
import subprocess,time,json,hashlib,os,re,urllib.request,unicodedata
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation09';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';P='vn.rtr.aeris.field02';OCR=R/'.local/cockpitvideo04/qa-ocr-fast'
MAX_PNG=5*2**20

def adb(*a,timeout=5,allow=False):
    assert not any('uiautomator'in str(x).lower()for x in a),'UIAUTOMATOR_FORBIDDEN_HEARTBEAT_RISK'
    assert E.is_dir(),'CONTROLLER_EVIDENCE_ROOT_REQUIRED';b.prepare_append(E/'qa-adb-commands.jsonl');t=time.monotonic();r=subprocess.run([ADB,'-s',S,*map(str,a)],capture_output=True,timeout=timeout)
    assert E.is_dir(),'CONTROLLER_EVIDENCE_ROOT_REQUIRED';log=E/'qa-adb-commands.jsonl';assert not log.exists()or log.stat().st_size<512*2**10,'ADB_LOG_BOUND'
    b.append(log,(json.dumps({'at':time.time(),'args':list(map(str,a)),'exit':r.returncode,'elapsedMs':(time.monotonic()-t)*1000,'stdoutSha256':hashlib.sha256(r.stdout).hexdigest(),'stderr':r.stderr.decode(errors='replace')[-500:]})+'\n').encode())
    if not allow:assert r.returncode==0,r.stderr.decode(errors='replace')
    return r.stdout

def owned(attempt):
    assert attempt in ['18','19'];l=json.loads((E/f'android-launch{attempt}.json').read_text());assert not(E/f'android-closure{attempt}.json').exists(),'OWNED_EMULATOR_ALREADY_CLOSED';os.kill(l['pid'],0);assert l['avd']=='aeris-field02'and l['serial']==S
    assert adb('shell','getprop','ro.boot.qemu').strip()==b'1';assert adb('emu','avd','name').splitlines()[0]==b'aeris-field02'
    return l

def state():
    with urllib.request.urlopen('http://127.0.0.1:8872/api/state',timeout=2)as r:v=json.load(r)
    assert v.get('ok')is True,v;return v

def norm(v):return ''.join(c for c in unicodedata.normalize('NFD',v.lower().replace('đ','d'))if unicodedata.category(c)!='Mn')
def capture(attempt,name,kind='direct'):
    p=E/(name+'.png');b.ensure_claim(p,MAX_PNG,category='screenshots',kind=kind);owned(attempt);assert re.fullmatch('[a-z0-9-]{1,100}',name);raw=adb('exec-out','screencap','-p');assert raw.startswith(b'\x89PNG')and len(raw)<=MAX_PNG,'SCREENSHOT_BOUND';b.write_bytes(p,raw,maximum=MAX_PNG,category='screenshots',kind=kind);return p

def ocr(*args,**kwargs):
    raise AssertionError('NO_OCR_IN_BETA06_USE_FRESH_UI_OBSERVATION_AND_ROOT_SCREENSHOT')

def tap_text(*args,**kwargs):
    raise AssertionError('GEN03_USE_OBSERVED_COORDINATES_OR_STRICT_VISIBLE_5_AUTO_ONLY')

def swipe(attempt,x1,y1,x2,y2,name):
    owned(attempt);assert all(0<=x<1280 for x in[x1,x2])and all(0<=y<800 for y in[y1,y2]);adb('shell','input','swipe',x1,y1,x2,y2,350);time.sleep(.15);return capture(attempt,name)

if __name__=='__main__':
    import sys
    op,attempt=sys.argv[1:3]
    if op=='capture':print(capture(attempt,sys.argv[3]))
    elif op=='ocr':print(json.dumps(ocr(attempt,sys.argv[3]),ensure_ascii=False))
    elif op=='tap':print(json.dumps(tap_text(attempt,sys.argv[3],sys.argv[4]),ensure_ascii=False))
    elif op=='xy':
        owned(attempt);x,y=map(int,sys.argv[3:5]);assert 0<=x<1280 and 0<=y<800;adb('shell','input','tap',x,y);print(capture(attempt,sys.argv[5]))
    elif op=='swipe':print(swipe(attempt,*map(int,sys.argv[3:7]),sys.argv[7]))
    else:raise ValueError('EXPLICIT_UI_ACTION_REQUIRED')
