from pathlib import Path
import sys,json,hashlib,datetime
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control01.oracles03 import control_outcome,paired_ground_observations
out=R/'evidence/betaintegrated01-m1control01/qa/oracle03';out.mkdir();cases=[]
def check(id,value):cases.append({'id':id,'pass':bool(value)})
old=json.loads((out.parent/'oracle02/results.json').read_bytes())['fixture'];check('ORIGINAL_COUNTERFEIT_NOT_READY',control_outcome(old,'nominal')['status']=='CONTROL_NOT_READY')
bad=json.loads((out.parent/'oracle02/ground-contradiction.json').read_bytes())['fixture'];check('NEWER_ARMED_LANDED2_OVERRIDES_OLD_GOOD',paired_ground_observations(bad,0)==0)
def row(t,k,**kw):return {'hostNs':int(t*1e9),'kind':k,**kw}
def pos(t,lat=108540000,alt=3000):return row(t,'position',relativeMm=alt,latE7=lat,lonE7=1068070000,headingCentiDeg=0,vxCms=0,vyCms=0,vzCms=0)
ground=[row(5.2,'heartbeat',armed=False,mode=9),row(5.21,'landed',state=1),pos(5.22,108540050,0),row(5.4,'heartbeat',armed=False,mode=9),row(5.41,'landed',state=1),pos(5.42,108540050,0)]
check('TWO_INDEPENDENT_GOOD_GROUPS_ACCEPTED',paired_ground_observations(ground,int(5e9))==2)
check('ONE_GROUP_INSUFFICIENT',paired_ground_observations(ground[:3],int(5e9))==1)
check('OLD_BEFORE_LAND_NOT_USED',paired_ground_observations(ground,int(6e9))==0)
rows=[row(0,'battery',milliVolt=24000)]
for t in (.75,1,1.25,1.5,1.75,2,2.25,2.5,2.75):rows.extend([row(t,'heartbeat',armed=True,mode=5),row(t,'landed',state=2),pos(t)])
rows.extend([pos(3.5,108540050),pos(4,108540050),row(5,'heartbeat',armed=True,mode=9),*ground])
commands=[row(0,'COMMAND_LONG',command=400,params=[1,0,0,0,0,0,0]),row(.1,'COMMAND_LONG',command=22,params=[0,0,0,0,0,0,3])]+[row(t,'RC_OVERRIDE',forwardPitchHeld=True,channels=[1500,1450,1500,1500])for t in (3,3.25,3.5,3.75,4)]
audit={'passiveTimeline':rows,'nativeForwardedTimeline':commands,'passiveApplicationTXBytes':0,'cutClosedHostNs':None};positive=control_outcome(audit,'nominal');check('COMPLETE_POSITIVE_NOMINAL_ACCEPTED',positive['status']=='CONTROL_OBSERVATIONS_PASS')
p=R/'pilot/betaintegrated01/control01/oracles03.py';report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if all(x['pass']for x in cases)else'FAIL','cases':cases,'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'positiveFixture':audit,'positiveOutcome':positive,'scope':'Final bounded oracle-family repair check, pure fixtures only; no flight/Android/network execution'}
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'failed':[x for x in cases if not x['pass']]}))
