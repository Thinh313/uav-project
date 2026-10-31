from pathlib import Path
import ast,sys,types,os,json,subprocess,hashlib
R=Path(__file__).resolve().parents[2];P=R/'.local/simstability03/receiver01/pilot/simhand01';E=R/'evidence/simstability03/closure-fault04';E.mkdir(exist_ok=False)
g=types.SimpleNamespace(budget=lambda:{'apSeconds':300,'runtimeStopUTC':'2099-01-01T00:00:00+00:00'},admit_ap=lambda rid:None);sys.modules['guard']=g
ns={'__file__':str(P/'projection.py')};exec(compile((P/'projection.py').read_text(),str(P/'projection.py'),'exec'),ns);runtime=ns['runtime_source']()[1]
results=[]
for case in ['cancel-after-admit','docker125-absent','docker125-owned','docker125-foreign']:
 d=E/case;d.mkdir();n={'__file__':str(P/'runtime.py'),'__name__':'mock_runtime'};exec(compile(runtime,'projected-runtime','exec'),n);n['E']=d;n['R']=R;n['sha']=lambda _: 'MOCK_HASH';calls=[]
 marker=d/'cancel.json';os.environ['AERIS_SIMHAND_STOP_REQUEST']=str(marker)
 g.admit_ap=(lambda rid:marker.write_text('{}'))if case=='cancel-after-admit'else(lambda rid:None)
 class Proc:
  pid=123;returncode=None
  def poll(self):return self.returncode
  def terminate(self):self.returncode=0
  def wait(self,timeout=None):return self.returncode
  def kill(self):self.returncode=-9
 def popen(*args,**kw):
  out=d/'rMOCK';intent=json.loads((out/'resource-intent.json').read_text());assert intent['run']=='rMOCK' and 'PLANNED_OWNERSHIP' in intent['scope'];(out/'backend-ready.json').write_text('{}');return Proc()
 def inspect_run(args,**kw):
  calls.append(args)
  if not (d/'rMOCK/backend-ready.json').exists():return types.SimpleNamespace(returncode=1,stdout='',stderr='No such object')
  if case=='docker125-absent':return types.SimpleNamespace(returncode=1,stdout='',stderr='Error: No such object: name')
  info={'Id':'cidMOCK','Config':{'Labels':{'aeris.run':'rOTHER'if case.endswith('foreign')else'rMOCK','aeris.task':'simhand01'}}}
  return types.SimpleNamespace(returncode=0,stdout=json.dumps([info]),stderr='')
 def command(args):
  calls.append(args)
  if args[1]=='run':raise subprocess.CalledProcessError(125,args)
  return 'cidMOCK'if args[1]=='stop'else'MOCK_OUTPUT'
 n['subprocess']=types.SimpleNamespace(run=inspect_run,Popen=popen,STDOUT=subprocess.STDOUT,TimeoutExpired=subprocess.TimeoutExpired);n['command']=command
 try:n['launch']('rMOCK','empty','calm')
 except (SystemExit,RuntimeError)as e:err=str(e)
 finally:os.environ.pop('AERIS_SIMHAND_STOP_REQUEST',None)
 if case=='cancel-after-admit':assert err=='CANCELLED_BEFORE_AP' and not calls;record={'case':case,'status':'PASS','allocationCalls':0}
 else:
  q=json.loads((d/'rMOCK/closure.json').read_text());assert q['backendExited']
  if case.endswith('absent'):assert q['noContainerObserved'] and not q['ownedContainerStopped']
  elif case.endswith('owned'):assert q['ownedContainerStopped'] and q['containerObservation']=='EXACT_OWNED_CONTAINER'
  else:assert not q['noContainerObserved'] and not q['ownedContainerStopped'] and 'CLOSURE_UNCONFIRMED' in q['error']
  record={'case':case,'status':'PASS','closure':q}
 results.append(record)
receipt={'status':'PASS','scope':'FAULT_INJECTION_NO_DOCKER_OR_PROCESS_STARTED','cases':results,'projectionSHA256':hashlib.sha256((P/'projection.py').read_bytes()).hexdigest()};(E.parent/'closure-fault04.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
