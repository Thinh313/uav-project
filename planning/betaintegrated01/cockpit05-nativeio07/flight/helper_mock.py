"""Synthetic IME and prior-data parser seams; no ADB, flight, resource priming."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
from types import SimpleNamespace
import json,shutil
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-nativeio07.flight';S=import_module(H+'.setup_ui');P=import_module(H+'.preservation');E=R/'evidence/betaintegrated01-cockpit05-nativeio07/host/helper-mock01'
def main():
 E.mkdir(parents=True,exist_ok=False);scratch=E/'scratch';scratch.mkdir();setup=scratch/'setup';setup.mkdir();(setup/'observed-empty-package.json').write_text('{}');results=[]
 def test(name,fn):
  try:results.append({'case':name,'pass':True,'detail':fn()})
  except Exception as e:results.append({'case':name,'pass':False,'error':repr(e)})
 def ime():
  o=object.__new__(S.Setup);events=[];state={'shown':False,'closing':0};o.reviewed=lambda *a,**kw:{'state':{'workspace':{'draft':None,'reviews':[]}},'screenSHA256':'a'*64};o.observe=lambda *a:{'mockNotScreenshot':True};o.op=SimpleNamespace()
  def command(args,**kw):
   assert args==['shell','dumpsys','input_method'];events.append(('IME',state['shown']))
   if state['closing']:
    state['closing']-=1
    if state['closing']==0:state['shown']=False
   return ('mInputShown='+str(state['shown']).lower()).encode(),b'',0,None
  o.op.command=command
  def inputs(args,**kw):
   events.append(('INPUT',args))
   if args[:3]==['shell','input','tap']:
    point=args[-2:]
    if point==list(S.FIELD):assert not state['shown'];state['shown']=True
    else:assert not state['shown'],'COORDINATE_DURING_IME'
   if args[-1]=='KEYCODE_BACK':state['closing']=3
   return b''
  o.bytes=inputs
  with patch.object(S,'guard_ready',lambda *a,**kw:None),patch.object(S,'SETUP',setup):
   o.name_r1(SimpleNamespace(step='name-r1'));assert not state['shown'];before=len(events);o.reference_r1(SimpleNamespace(step='reference-r1'));assert not state['shown']
  taps=[e for e in events if e[0]=='INPUT'and e[1][:3]==['shell','input','tap']]
  assert len(taps)==4 and not any(e[1][-2:]==list(S.SAVE)for e in taps)
  return {'asyncBackRequired3Observations':True,'allReferenceBlurCoordinatesAfterHidden2Samples':True,'nameThenSeparateReference':True,'noSAVE':True,'inputTouchCount':len(taps),'syntheticIMEOnly':True}
 test('actual helper control flow waits IME shown then asynchronous hidden before reference/blur',ime)
 def contradictions():
  o=object.__new__(S.Setup);o.op=SimpleNamespace(command=lambda *a,**kw:(b'mInputShown=true isInputViewShown=false',b'',0,None));clock=[0]
  def monotonic():clock[0]+=.5;return clock[0]
  with patch.object(S,'guard_ready',lambda *a,**kw:None),patch.object(S,'time',SimpleNamespace(monotonic=monotonic,sleep=lambda n:None)):
   try:o.keyboard_settle()
   except S.OperatorError:return 'ContradictoryIMEflags refuse, no coordinate action'
   raise AssertionError('contradictoryIMEaccepted')
 test('contradictory IME visibility never grants coordinate permission',contradictions)
 def prior():
  values={}
  for package,(_,count)in P.BASELINES.items():
   v=P.expected_old(package);assert len(v)==count;raw=''.join(h+'  '+p+'\n'for p,h in v.items()).encode();assert P.parse_private_map(raw,count)==v;values[package]=count
  d=json.loads((R/P.DIAG_RECOVERY).read_text());assert d['bytes']==101959 and d['artifactSHA256']=='7eb918e4419a83ea071636a8574bc6edeb7acdab2e3ddb9ba1df320648aa9b16';return {'standardPrivateMaps':values,'nativeio06DiagnosticSeparateBytes':d['bytes'],'totalPathsIncludingDiagnostic':sum(values.values())+1}
 test('sourcebound old233/25/10 and separate101959Bdiagnostic',prior)
 removed=sum(p.stat().st_size for p in scratch.rglob('*')if p.is_file());shutil.rmtree(scratch);v={'status':'PASS'if all(x['pass']for x in results)else'FAIL','cases':results,'realDeviceOrAPOrPriming':False,'scratchRemoved':True,'removedBytes':removed};(E/'results.json').open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2));assert v['status']=='PASS'
if __name__=='__main__':main()
