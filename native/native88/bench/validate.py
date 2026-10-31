"""Intake checker only: no hardware IO, firmware writes, flight commands or acceptance from mock data."""
import json,sys,hashlib
from pathlib import Path
FIELDS={
 'controller':['model','serial','firmware','androidApi','screenPixels','sdkVersion','mcuProtocolVersion'],
 'aircraft':['model','serial','autopilotFirmware','autopilotCommit','systemId','componentId'],
 'input':['transport','deviceIds','calibrationId','axisMapping','neutralDeadzone','emergencyButtonPolicy','latencyP95BudgetMs'],
 'video':['transport','codec','width','height','frameRate','cameraTimestampContract','staleThresholdMs','latencyP95BudgetMs'],
 'radio':['model','firmware','topology','lossPolicyVersion'],
 'dualOperator':['policyVersion','pilotIdentity','payloadIdentity','emergencyOverride','receiverEnforcement'],
 'approval':['criteriaOwner','criteriaVersion','benchOperator','site']}
PAYLOAD=['slot','family','model','serial','firmware','lens','sdkApiVersion','gimbalModel','gimbalFirmware','controlTarget','originalMediaPath']
def validate(d):
 assert d.get('format')=='aeris-herahub-bench88-intake'and d.get('version')==1,'SCHEMA'
 missing=[]
 def unknown(v):return v is None or v==''or isinstance(v,str)and v.upper()in ['UNKNOWN','NOT_CHECKED','TBD']
 for group,fields in FIELDS.items():
  for f in fields:
   if unknown(d.get(group,{}).get(f)):missing.append(group+'.'+f)
 p=d.get('payloads',[])
 if not isinstance(p,list)or not 1<=len(p)<=4:missing.append('payloads.1_TO_4_REQUIRED');p=[]
 targets=[]
 for i,item in enumerate(p):
  for f in PAYLOAD:
   if unknown(item.get(f)):missing.append('payloads.%d.%s'%(i,f))
  if item.get('controlTarget')is not None:targets.append(json.dumps(item['controlTarget'],sort_keys=True))
 if len(targets)!=len(set(targets)):missing.append('payloads.AMBIGUOUS_TARGET_ROUTING')
 for group,fields in [('input',['latencyP95BudgetMs']),('video',['width','height','frameRate','staleThresholdMs','latencyP95BudgetMs'])]:
  for f in fields:
   v=d.get(group,{}).get(f)
   if v is not None and(not isinstance(v,(int,float))or isinstance(v,bool)or not 0<v<100000):missing.append(group+'.'+f+'.POSITIVE_BUDGET_REQUIRED')
 def integer(path,lo,hi):
  group,key=path.split('.');v=d.get(group,{}).get(key)
  if v is not None and(not isinstance(v,int)or isinstance(v,bool)or not lo<=v<=hi):missing.append(path+'.INTEGER_RANGE')
 integer('controller.androidApi',26,100);integer('aircraft.systemId',1,255);integer('aircraft.componentId',1,255)
 screen=d.get('controller',{}).get('screenPixels')
 if screen is not None and(not isinstance(screen,list)or len(screen)!=2 or any(not isinstance(v,int)or not 320<=v<=8192 for v in screen)):missing.append('controller.screenPixels.WIDTH_HEIGHT_REQUIRED')
 deadzone=d.get('input',{}).get('neutralDeadzone')
 if deadzone is not None and(not isinstance(deadzone,(int,float))or isinstance(deadzone,bool)or not 0<=deadzone<1):missing.append('input.neutralDeadzone.NORMALIZED_RANGE')
 for i,item in enumerate(p):
  target=item.get('controlTarget')
  if target is not None and(not isinstance(target,dict)or any(not isinstance(target.get(k),int)or isinstance(target.get(k),bool)or not 1<=target[k]<=255 for k in ['system','component'])):missing.append('payloads.%d.controlTarget.TYPED_IDENTITY_REQUIRED'%i)
 if d.get('dualOperator',{}).get('pilotIdentity')is not None and d.get('dualOperator',{}).get('pilotIdentity')==d.get('dualOperator',{}).get('payloadIdentity'):missing.append('dualOperator.DISTINCT_IDENTITIES_REQUIRED')
 return {'status':'BLOCKED_MISSING_INPUTS'if missing or d.get('hardwareAvailable')is not True else 'READY_FOR_BENCH_REVIEW_ONLY','missing':missing,'hardwareAvailable':d.get('hardwareAvailable')is True,'hardwareAcceptance':'NOT_CHECKED','productionAccepted':False,'authorityRestorable':False,'interpretation':'Completeness is not compatibility, measured performance, hardware identity authentication or permission to fly.'}
if __name__=='__main__':
 p=Path(sys.argv[1]);assert p.stat().st_size<=65536;raw=p.read_bytes();r=validate(json.loads(raw));r['inputSha256']=hashlib.sha256(raw).hexdigest();print(json.dumps(r,indent=2));sys.exit(2 if r['status']=='BLOCKED_MISSING_INPUTS'else 0)
