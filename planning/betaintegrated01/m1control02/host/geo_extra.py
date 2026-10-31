from pathlib import Path
import sys,json,copy
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from geo_mock import base,run,HOME,row,rejected,CTX
from pilot.betaintegrated01.control04.oracles import nominal_release_observations

def main():
 cases=[]
 def check(n,v):assert v,n;cases.append({'case':n,'status':'PASS'})
 for delta in(20,-20):
  r=base();r[5]['altAMSLmm']+=delta;check('datum_boundary_'+str(delta),run(r)['status']=='GEOGRAPHY_FULL_ARMED_WINDOW_PASS')
 for delta in(21,-21):
  r=base();r[5]['altAMSLmm']+=delta;check('datum_boundary_'+str(delta),rejected(r))
 r=base();r[5]['relativeMm']=1000;check('wrong_relative_datum',rejected(r))
 r=base();r[1]['home']={**HOME,'datum':'AGL'};check('malformed_preARMHome_cannot_support_armedposition',rejected(r))
 r=base();r[1]['home']={**HOME,'latE7':True};check('boolean_preARMHome_cannot_support_armedposition',rejected(r))
 r=base();r[-1]['hostNs']=3_600_000_000;check('terminal_disarm_edge_GPSfreshness',rejected(r))
 def cmd(t,k,**x):return {'hostNs':int(t*1e9),'kind':k,**x}
 neutral=lambda t:cmd(t,'RC_OVERRIDE',channels=[1500]*4+[65535]*14,forwardPitchHeld=False)
 cmds=[neutral(.1),neutral(.2),cmd(1,'RC_OVERRIDE',channels=[1500,1475,1500,1500]+[65535]*14,forwardPitchHeld=True),cmd(2,'SET_MODE',mode=17),neutral(3),cmd(3.1,'RC_OVERRIDE',channels=[0]*8+[65534]*10,forwardPitchHeld=False),cmd(5,'SET_MODE',mode=9)]
 states=[cmd(2.5,'heartbeat',mode=17,armed=True)]
 audit={'nativeForwardedTimeline':cmds,'passiveTimeline':states}
 check('preBrake_centered_normalRC_retained_not_cleanup',nominal_release_observations(audit)['status']=='HOST_RELEASE_WIRE_OBSERVATIONS_PASS')
 for name,mut in [('no_observed_brake',lambda a:a['passiveTimeline'].clear()),('neutral_before_observed_brake',lambda a:a['passiveTimeline'][0].update(hostNs=4_000_000_000)),('normal_after_revoke',lambda a:a['nativeForwardedTimeline'].insert(-1,cmd(4,'RC_OVERRIDE',channels=[1500,1475]+[65535]*16,forwardPitchHeld=True))),('failsafe_confounder',lambda a:a['passiveTimeline'].append(cmd(4,'text',text='GCS Failsafe')) )]:
  a=copy.deepcopy(audit);mut(a);check(name,nominal_release_observations(a)['status']=='HOST_RELEASE_NOT_READY')
 out=R/'evidence/betaintegrated01-m1control02/host/geo-extra01';out.mkdir()
 (out/'results.json').open('x').write(json.dumps({'status':'PASS_BUILDER_EXTRA','groups':len(cases),'cases':cases,'servicesStarted':0},indent=2)+'\n');print(json.dumps({'status':'PASS','groups':len(cases)}))
if __name__=='__main__':main()
