"""Readiness waits are bounded readonly observations, no input retry."""
from pathlib import Path
import importlib.util,json
s=importlib.util.spec_from_file_location('air05',Path(__file__).with_name('qa-airborne.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);o={'documentId':'d','clientId':'c','clientEpoch':1,'clientInstance':'i','run':'r','boot':'b','configId':'cfg','modelSha256':'h','planSha256':'p','tab':'flight','viewport':{'width':1280,'height':716},'format':'clockvideo05-ui-observation-v1','foreground':True,'seq':1,'targets':[{'id':'field-arm','enabled':True,'visible':True,'fullyVisible':True,'unoccluded':True,'rect':{'x':10,'y':10,'width':44,'height':44}}]};ref={'observed':{'observation':o}};t=[0];calls=[0];cases=[]
def pause(v):t[0]+=v
def reader():
 calls[0]+=1;v={**o,'targets':[{**o['targets'][0],'enabled':calls[0]>=3}]};return {'observation':v,'ageMs':0}
assert m.wait_target_ready(ref,'field-arm',reader,lambda:t[0],pause)['observation']['targets'][0]['enabled'];assert calls[0]==3 and t[0]<=2;cases.append('busy_unpainted_twice_then_ready_no_input')
for name,read in [('permanently_disabled',lambda:{'observation':{**o,'targets':[{**o['targets'][0],'enabled':False}]},'ageMs':0}),('wrong_context',lambda:{'observation':{**o,'clientEpoch':2},'ageMs':0})]:
 t[0]=0
 try:m.wait_target_ready(ref,'field-arm',read,lambda:t[0],pause);raise RuntimeError('MUST_FAIL')
 except AssertionError:assert t[0]<=2;cases.append(name)
t[0]=0
def deferred():t[0]=3;return {'observation':o,'ageMs':0}
try:m.wait_target_ready(ref,'field-arm',deferred,lambda:t[0],pause);raise RuntimeError('MUST_FAIL')
except AssertionError as e:assert str(e)=='TARGET_READINESS2S_DEADLINE';cases.append('late_ready_after2s_refused')
print(json.dumps({'status':'PASS','checks':len(cases),'cases':cases,'adbCalls':0,'inputRetries':0,'readinessDeadlineSeconds':2},indent=2))
