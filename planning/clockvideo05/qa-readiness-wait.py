"""Independent AST execution of readiness wait; no ADB/network/runtime."""
import ast,json,hashlib,datetime,types,copy
from pathlib import Path
p=Path('planning/clockvideo05/qa-airborne.py');s=p.read_text();f=[x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef)and x.name=='wait_target_ready'];assert len(f)==1
class Clock:
 def __init__(self):self.t=0;self.calls=0
 def now(self):return self.t
 def pause(self,n):assert n>=0;self.t+=n
c=Clock();origin={k:'SAME-'+k for k in ['documentId','clientId','clientEpoch','clientInstance','run','boot','configId','modelSha256','planSha256','tab']};origin['viewport']={'width':1280,'height':716,'dpr':1};reference={'observed':{'observation':origin}};base={'ageMs':1,'observation':{**origin,'targets':[{'id':'field-arm','enabled':True,'visible':True,'fullyVisible':True,'unoccluded':True}]}}
def target(v,i):
 a=[t for t in v['observation']['targets']if t['id']==i];assert len(a)==1,'TARGET_NOT_UNIQUE';assert all(a[0][k]is True for k in ['enabled','visible','fullyVisible','unoccluded']),'TARGET_UNAVAILABLE_OR_OCCLUDED'
ui=types.SimpleNamespace(target=target,observation=lambda:None);ns={'time':types.SimpleNamespace(monotonic=c.now,sleep=c.pause),'ui':ui};exec(compile(ast.Module(body=f,type_ignores=[]),str(p),'exec'),ns);run=ns['wait_target_ready'];rows=[]
def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except Exception as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
def reset():c.t=0;c.calls=0
def error(fn,text):
 try:fn()
 except Exception as e:assert text in str(e),(text,str(e));return
 raise AssertionError('MISSING_REJECTION')
def transient():
 reset()
 def read():
  c.calls+=1;v=copy.deepcopy(base);v['observation']['targets'][0]['enabled']=c.calls>=3;return v
 assert run(reference,'field-arm',read,c.now,c.pause)==base and c.calls==3 and c.t<2
test('two_disabled_observations_then_ready_no_input',transient)
def blocked():
 for key in ['enabled','visible','fullyVisible','unoccluded']:
  reset()
  def read():
   c.calls+=1;v=copy.deepcopy(base);v['observation']['targets'][0][key]=False;return v
  error(lambda:run(reference,'field-arm',read,c.now,c.pause),'TARGET_NOT_READY_WITHIN2S_NO_INPUT');assert c.t<=2.000001 and c.calls<=26
test('disabled_hidden_clipped_occluded_cannot_return_ready',blocked)
def context():
 for key in origin:
  reset()
  def read():return {'ageMs':1,'observation':{**base['observation'],key:'WRONG'}}
  error(lambda:run(reference,'field-arm',read,c.now,c.pause),'CONTEXT_CHANGED');assert c.t==0
test('wrong_epoch_run_boot_config_model_plan_tab_viewport_rejected_immediately',context)
def late():
 reset()
 def read():c.t=2.01;return copy.deepcopy(base)
 error(lambda:run(reference,'field-arm',read,c.now,c.pause),'READINESS2S_DEADLINE')
test('late_reader_result_after_original2s_rejected',late)
def network():
 reset()
 def read():raise TypeError('NETWORK')
 error(lambda:run(reference,'field-arm',read,c.now,c.pause),'NETWORK');assert c.t==0
 reset()
 def read2():return {'ageMs':1,'observation':{**origin,'targets':[]}}
 error(lambda:run(reference,'field-arm',read2,c.now,c.pause),'TARGET_NOT_UNIQUE')
test('network_or_wrong_target_not_retried',network)
def source():
 actual=ast.get_source_segment(s,f[0]);assert 'dispatch('not in actual and 'adb('not in actual and 'POST'not in actual;assert s.count('r=ui.dispatch(')==1;assert s.index('ready=wait_target_ready(')<s.index('r=ui.dispatch(')
test('readiness_function_no_actuation_then_exactly_one_dispatch_site',source)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_READONLY_READINESS_HELPER'if all(x['status']=='PASS'for x in rows)else'FAIL','source':str(p),'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':rows,'scope':'AST helper with fake target function/clocks/observations. No actual input, server, network, process, AP, source edit or dynamic pixel acceptance.'};out=Path('evidence/field02/clockvideo05/qa-readiness-wait01.json');out.open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps(r));assert r['status'].startswith('PASS')
