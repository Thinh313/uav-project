from pathlib import Path
import hashlib,json,sys,datetime
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
if len(sys.argv)>1 and sys.argv[1]=='02':
 from pilot.betaintegrated01.control01.oracles02 import control_outcome
 variant='02'
else:
 from pilot.betaintegrated01.control01.oracles import control_outcome
 variant='01'
out=R/('evidence/betaintegrated01-m1control01/qa/oracle'+variant);out.mkdir()
def ns(s):return int(s*1e9)
def row(s,kind,**extra):return {'hostNs':ns(s),'kind':kind,**extra}
rows=[row(0,'battery',milliVolt=24000),row(.8,'heartbeat',armed=True,mode=5),row(.81,'landed',state=2),row(.9,'position',relativeMm=3000,latE7=108540000,lonE7=1068070000,headingCentiDeg=0),row(1.5,'position',relativeMm=3000,latE7=108540050,lonE7=1068070000,headingCentiDeg=0),row(2,'heartbeat',armed=True,mode=9),row(2.1,'landed',state=1),row(2.2,'heartbeat',armed=False,mode=9)]
cmd=[row(0,'COMMAND_LONG',command=400,params=[1,0,0,0,0,0,0]),row(.1,'COMMAND_LONG',command=22,params=[0,0,0,0,0,0,3])]+[row(t,'RC_OVERRIDE',forwardPitchHeld=True,channels=[1500,1450,1500,1500])for t in (1,1.25,1.5)]
for r in rows:
 if r['kind']=='position':r.update(vxCms=0,vyCms=0,vzCms=0)
audit={'passiveTimeline':rows,'nativeForwardedTimeline':cmd,'passiveApplicationTXBytes':0,'cutClosedHostNs':None}
actual=control_outcome(audit,'nominal');checks={'reject500msInputInsteadOf1s':actual['status']!='CONTROL_OBSERVATIONS_PASS','rejectNo1sObservedHover':actual['status']!='CONTROL_OBSERVATIONS_PASS','rejectNoNearGroundPositionAndOnlyOneLandedDisarmGroup':actual['status']!='CONTROL_OBSERVATIONS_PASS'}
p=R/('pilot/betaintegrated01/control01/oracles02.py'if variant=='02'else'pilot/betaintegrated01/control01/oracles.py');report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'PASS'if all(checks.values())else'FAIL','expectedRootPredeclaredMetrics':'hold>=1s,hover3m+/-0.75>=1s speed<=0.5,groundabsrelalt<=.4 withtwofreshindependentlanded/disarmedgroups','checks':checks,'fixture':audit,'actualOutcome':actual,'scope':'Pure cold-oracle counterfeit-evidence test, no AP/socket/Android'}
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'actualStatus':actual['status']}))
