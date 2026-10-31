import ast, hashlib, json, pathlib, types
R=pathlib.Path.cwd();E=R/'evidence/beta06/generation17'
current=R/'planning/beta06g17/qa-native-budget.py';prior=R/'planning/beta06g17/nativebuilder-budget-before-dispatch-age.py'
src=current.read_text();old=prior.read_text();a=ast.parse(src);b=ast.parse(old)
an=[n for n in a.body if not isinstance(n,ast.ClassDef)or n.name!='QuotaWatch'];bn=[n for n in b.body if not isinstance(n,ast.ClassDef)or n.name!='QuotaWatch']
assert ast.dump(ast.Module(body=an,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=bn,type_ignores=[]),include_attributes=False)
class Event:
 def __init__(self):self.value=False
 def is_set(self):return self.value
 def set(self):self.value=True
 def wait(self,n):return True
class Thread:
 def __init__(self,**k):pass
 def start(self):pass
 def join(self,**k):pass
 def is_alive(self):return False
clock=[0.0];delay=[9.0];mode=['normal'];holder={}
def admit(*args,**kwargs):
 clock[0]+=delay[0]
 if mode[0]=='closed':kwargs['cancel_event'].set()
 return {'policySha256':'test-only'}
ns={'threading':types.SimpleNamespace(Event=Event,Thread=Thread),'admit':admit,'load':lambda:{'scanner':{'staleMs':15000}}}
exec(compile(ast.Module(body=[n for n in a.body if isinstance(n,ast.ClassDef)and n.name=='QuotaWatch'],type_ignores=[]),str(current),'exec'),ns)
Q=ns['QuotaWatch'];cases=[]
q=Q(clock=lambda:clock[0]);assert q.last==0 and q.check()['auditAgeS']==9;cases.append('DISPATCH_ANCHOR_9S_DELIVERY_NOT_RENEWED')
clock[0]=15;assert q.check()['auditAgeS']==15;cases.append('EXACT15_ACCEPTED')
def reject(fn,text):
 try:fn()
 except AssertionError as e:assert text in str(e);return
 raise AssertionError('EXPECTED_REFUSAL:'+text)
clock[0]=15.001;reject(q.check,'STALE');cases.append('15_PLUS1MS_REFUSED')
clock[0]=-0.001;reject(q.check,'STALE');cases.append('BACKWARD_REFUSED')
clock[0]=0;delay[0]=15.001;reject(lambda:Q(clock=lambda:clock[0]),'STALE_OR_CLOSED');cases.append('LATE_COMPLETION_REFUSED')
clock[0]=0;delay[0]=-0.001;reject(lambda:Q(clock=lambda:clock[0]),'STALE_OR_CLOSED');cases.append('NEGATIVE_COMPLETION_REFUSED')
clock[0]=0;delay[0]=9;mode[0]='closed';reject(lambda:Q(clock=lambda:clock[0]),'STALE_OR_CLOSED');cases.append('CLOSE_DURING_AUDIT_NO_PUBLISH')
mode[0]='normal';clock[0]=0;delay[0]=0;q=Q(clock=lambda:clock[0]);q.close();reject(q.check,'CLOSED');cases.append('CLOSED_CHECK_REFUSED')
value={'status':'PASS_NATIVE_DISPATCH_AGE_8','cases':cases,'sourceSha256':hashlib.sha256(current.read_bytes()).hexdigest(),'priorSha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'outsideQuotaWatchASTUnchanged':True,'scope':'Actual current QuotaWatch class compiled with inert Thread/Event and injected local clock/admit only. No thread/process/ledger/OS clock read; no absolute Node/Python clock subtraction.'}
p=E/'qa-native-age01.json'
with p.open('x')as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cases':len(cases)}))
