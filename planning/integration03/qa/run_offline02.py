"""Run pinned production modules once, preserve failure stdout/stderr, independent geometry oracle."""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib,math,datetime
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'pilot/mission55/vendor'))
from geographiclib.geodesic import Geodesic
from geographiclib.polygonarea import PolygonArea
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--freeze',required=True,type=Path);a.add_argument('--attempt',required=True);q=a.parse_args();out=ROOT/'evidence/integration03-qa'/q.attempt;out.mkdir(exist_ok=False)
 adapter=ROOT/'planning/integration03/qa/production_adapter02.mjs';cmd=['node','--experimental-vm-modules',str(adapter),'--freeze',str(q.freeze.resolve())];result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'NOT_RUN','command':cmd,'sourceFreezeSha256':sha(q.freeze),'adapterSha256':sha(adapter),'actualRuntime':False}
 try:
  try:r=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=90);stdout,stderr,code=r.stdout,r.stderr,r.returncode
  except subprocess.TimeoutExpired as e:stdout=e.stdout or b'';stderr=e.stderr or b'';code=None
  (out/'stdout.bin').write_bytes(stdout);(out/'stderr.txt').write_bytes(stderr)
  if code!=0:raise RuntimeError('production adapter failure/timeout:'+str(code)+':'+stderr.decode(errors='replace')[-1400:])
  d=json.loads(stdout);observed=d['rawObserved'];poly=observed['polygon']['document']['features'][0]['coordinates'];pa=PolygonArea(Geodesic.WGS84,False)
  for lon,lat,z in poly[:-1]:pa.AddPoint(lat,lon)
  _,perim,area=pa.Compute(False,True);d['observations']['H01.area']={'areaM2':abs(area),'perimeterM':perim}
  supplement=json.loads((ROOT/'evidence/integration03-qa/supplement-H01b02.json').read_text());assert supplement['provenance']=='QA_AUTHORED_AFTER_SOURCE_INSPECTION_NOT_UNSEEN';assert d['observations']['H01.source']['sourceSha256']==supplement['rawSha256'];assert all(abs(d['observations']['H01.area'][k]-v)<=supplement['absoluteTolerance'][k] for k,v in supplement['expected'].items())
  line=observed['corridor']['document']['features'][0]['coordinates'];length=sum(Geodesic.WGS84.Inverse(a[1],a[0],b[1],b[0])['s12'] for a,b in zip(line,line[1:]));d['observations']['H02.length']={'centerlineLengthM':length}
  supplementary=[]
  for name,obj in observed.items():
   plan=obj['compiled']['plan'];p=plan['acquisition']['plan'];legs=p['legs'];distance=0;photos=0
   spacing=p['metrics']['footprintAlongM']*(1-p['options']['frontOverlapPct']/100)
   for j,l in enumerate(legs):
    a,b=l['start'],l['end'];leg=Geodesic.WGS84.Inverse(a['lat'],a['lon'],b['lat'],b['lon'])['s12'];distance+=leg
    photos+=math.ceil(leg/spacing-1e-9)+1
    if j:
     a=legs[j-1]['end'];distance+=Geodesic.WGS84.Inverse(a['lat'],a['lon'],b['lat'] if False else l['start']['lat'],l['start']['lon'])['s12']
   # Pixel/command estimates are design-only, never proof of camera execution.
   if abs(distance-p['metrics']['distanceM'])>.03:raise RuntimeError(name+': independent route-distance mismatch')
   if abs(distance/p['options']['speedMS']-p['metrics']['nominalSeconds'])>.03:raise RuntimeError(name+': independent design-ETA mismatch')
   if photos!=p['metrics']['photoCommands']:raise RuntimeError(name+': independent endpoint-policy command count mismatch')
   start206=[x for x in plan['compiled']['items'] if x['command']==206 and x['param1']>0]
   if not start206 or any(abs(x['param1']-spacing)>1e-5 for x in start206):raise RuntimeError(name+': compiled camera distance semantics mismatch')
   supplementary.append({'kind':name,'independentRouteDistanceM':distance,'declaredRouteDistanceM':p['metrics']['distanceM'],'independentEndpointPolicyPhotoCommands':photos,'declaredDesignSeconds':p['metrics']['nominalSeconds'],'actualImages':0})
  d['supplementaryIndependentGeometry']=supplementary;d['mapping']['geometry']='Independent GeographicLib on actual parsed feature+compiled leg coordinates; not product area UI/field metric certification';d['mapping']['optics']='Nominal spacing from actual generated request before float32 wire normalization; separately check actual compiled206 tolerance1e-5'
  observation=out/'observations.json';observation.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
  import importlib.util
  spec=importlib.util.spec_from_file_location('qa01checker',ROOT/'planning/integration03/qa/check_offline01.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);original=module.strict(ROOT/'evidence/integration03-qa/heldout-corpus01.json');module.verify({'checks':[x for x in original['checks'] if x['id']=='H01.optics']},{'H01.optics':d['observations']['H01.optics']})
  selected={k:v for k,v in d['observations'].items() if not k.startswith('H01.')};d['observations']=selected;observation.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
  checker=ROOT/'planning/integration03/qa/check_offline02.py';c=subprocess.run([sys.executable,'-B',str(checker),'--groups','H02,H03,H04,H05','--observations',str(observation),'--source-freeze',str(q.freeze),'--adapter',str(adapter),'--output',str(out/'checked.json')],cwd=ROOT,capture_output=True,timeout=15);(out/'checker-stdout.txt').write_bytes(c.stdout);(out/'checker-stderr.txt').write_bytes(c.stderr)
  if c.returncode!=0:raise RuntimeError('independent normalized checker failed:'+c.stdout.decode(errors='replace'))
  result.update(status='PASS_SCOPED_OFFLINE_I01_I02_NOT_RUNTIME',sourceId=d['sourceId'],executedGroups=['H02','H03','H04','H05'],supplementalH01b='PASS_POST_INSPECTION_NOT_UNSEEN',originalH01='REFUSED_CORRECTLY_QA_EXPECTATION_ERROR_NOT_POSITIVE_PASS',positiveUnseenPolygonCoverage=False,supplementaryGeometry=supplementary,observationSha256=sha(observation),checkerSha256=sha(checker),checkerReceiptSha256=sha(out/'checked.json'))
 except Exception as e:result.update(status='FAIL_OR_HARNESS_UNSUPPORTED',errorType=type(e).__name__,error=str(e))
 result['runnerSha256']=sha(Path(__file__));(out/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,ensure_ascii=False));return 0 if result['status'].startswith('PASS') else 2
if __name__=='__main__':raise SystemExit(main())
