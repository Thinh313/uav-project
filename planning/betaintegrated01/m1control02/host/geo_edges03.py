from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from geo_mock import base,row,run,rejected,HOME

def main():
 cases=[]
 def check(n,v):assert v,n;cases.append({'case':n,'status':'PASS'})
 check('qualified_baseline',run(base())['status']=='GEOGRAPHY_FULL_ARMED_WINDOW_PASS')
 for kind,index,change,fresh in [('gps',2,{'fix':1},{'fix':6,'satellites':10,'hdop':121}),('ekf',3,{'flags':167},{'flags':831}),('home',1,{'home':{**HOME,'datum':'AGL'}},{'home':HOME})]:
  r=base();r[index].update(change);r.insert(5,row(1.05,kind,**fresh));check('bad_preauthority_'+kind+'_not_hidden_by_later_good',rejected(r))
 out=R/'evidence/betaintegrated01-m1control02/host/geo-edges03';out.mkdir();(out/'results.json').open('x').write(json.dumps({'status':'PASS','groups':len(cases),'cases':cases,'sourceSHA256':hashlib.sha256((R/'pilot/betaintegrated01/control04/geography.py').read_bytes()).hexdigest(),'servicesStarted':0},indent=2)+'\n');print(json.dumps({'status':'PASS','groups':len(cases)}))
if __name__=='__main__':main()
