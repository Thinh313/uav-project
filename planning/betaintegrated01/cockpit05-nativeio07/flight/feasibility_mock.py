"""Pure finite byte/time projection boundary tests, not actual performance proof."""
from pathlib import Path
from importlib import import_module
import json,math
R=Path(__file__).resolve().parents[4];F=import_module('planning.betaintegrated01.cockpit05-nativeio07.flight.feasibility');E=R/'evidence/betaintegrated01-cockpit05-nativeio07/host/feasibility-mock01'
def main():
 E.mkdir(parents=True,exist_ok=False);results=[]
 records=[(n*10**9,1000)for n in range(11)];m=F.native_byte_rate(iter(records));assert m['records']==11 and m['totalRecordBytes']==11000 and m['chosenBytesPerSecond']==1200
 results.append({'case':'allrecords/headerterminal-inclusive conservativewholeboundary5s','pass':True,'metric':m})
 projection={'status':'CONDITIONAL_DURATION_FEASIBLE','nativeProjectionSeconds':1000,'hostProjectionSeconds':1000};quota=160*2**20;reserve=2*2**20;rate=(quota-reserve)/1000
 yes=F.include_native_budget(projection,{'chosenBytesPerSecond':rate});no=F.include_native_budget(projection,{'chosenBytesPerSecond':rate+1})
 assert yes['status']=='CONDITIONAL_DURATION_FEASIBLE'and yes['nativeCapacity']['projectedBytes']==quota and no['status']=='DURATION_NATIVE_BYTES_NOT_FEASIBLE_STOP_BEFORE_LONG'
 results.append({'case':'exact160MiBwith2MiBreservepasses1KBmorefails','pass':True,'quotaBytes':quota,'reserveBytes':reserve})
 for name,rows in [('insufficient',[(0,100),(1,100)]),('regression',[(10,100),(0,100)]),('boolsize',[(0,True)]),('oversize',[(0,16385)])]:
  try:F.native_byte_rate(iter(rows))
  except ValueError:results.append({'case':name,'pass':True})
  else:results.append({'case':name,'pass':False})
 out={'status':'PASS'if all(x['pass']for x in results)else'FAIL','cases':results,'actualNativeDurationOrBytesMeasured':False,'nativeQuotaChanged':False,'predictionNotGuarantee':True,'runtimeStarts':0};(E/'results.json').open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['status']=='PASS'
if __name__=='__main__':main()
