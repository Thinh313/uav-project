import ast,hashlib,datetime,math,json,re
from pathlib import Path
p=Path('planning/clockvideo05/qa-ui.py');nodes=[x for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef)and x.name in ['mapping','native_point','window_frame_signature']];ns={'math':math,'re':re,'hashlib':hashlib};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-mapping>','exec'),ns);rows=[]
def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except Exception as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
def reject(fn):
 try:fn()
 except Exception:return
 raise AssertionError('MISSING_REJECTION')
def offset():
 m=ns['mapping']({'width':1280,'height':752,'dpr':1},[0,24,1280,776],[1280,800]);assert ns['native_point']({'x':10,'y':100,'width':100,'height':48},m)==[60,148]
test('actualDOMcenteraddsdeclared24pxnativeoffset',offset)
def twice():
 m=ns['mapping']({'width':640,'height':376,'dpr':2},[0,24,1280,776],[1280,800]);assert ns['native_point']({'x':10,'y':10,'width':100,'height':44},m)==[120,88]
test('uniform2xDPRmappingpreservesnativecenter',twice)
def wrong():
 for frame,screen in [([0,24,1280,800],[1280,800]),([0,24,1280,776],[800,1280]),([-1,24,1280,776],[1280,800]),([0,24,1280,900],[1280,800])]:reject(lambda:ns['mapping']({'width':1280,'height':752,'dpr':1},frame,screen))
 reject(lambda:ns['mapping']({'width':1280,'height':752,'dpr':2},[0,24,1280,776],[1280,800]))
test('aspectrotationoutsideframeandDPRmismatchreject',wrong)
text='mCurrentFocus=Window{abc u0 vn.rtr.aeris.field02/vn.rtr.aeris.field02.ShellActivity}\nWindow #0 Window{abc u0 vn.rtr.aeris.field02/vn.rtr.aeris.field02.ShellActivity}:\n  mFrame=[0,24][1280,776]\n  mContentFrame=[0,24][1280,776]\n'
def signature():
 a=ns['window_frame_signature'](text);b=ns['window_frame_signature'](text.replace('[0,24]','[0,0]'));assert a['sha256']!=b['sha256'];reject(lambda:ns['window_frame_signature']('Window #0 Window{abc unrelated}:\n mFrame=[0,0][10,10]'));reject(lambda:ns['window_frame_signature'](text+text.replace('#0','#1')))
test('ownedShellwindowuniqueandchangedframehashdifferent',signature)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_NATIVE_MAPPING_MOCK'if all(x['status']=='PASS'for x in rows)else'FAIL','source':str(p),'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':rows,'scope':'ActualpureASTmapping/signaturefunctions onfakeframe/windowtext, noADB/Androidscreens. Rootmustground-observeactualcontentframe/screenshot andvalidateonebenignvisibleactionbeforeflight; no guessedoffsetoruniversalframeclaim.'}
with Path(__import__('sys').argv[1]).open('x')as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r));assert r['status'].startswith('PASS')
