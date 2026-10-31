"""Bounded synthetic helper checks only; no services, real prime or Android."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
from types import SimpleNamespace
import ast,json
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-clockorder08.flight';S=import_module(H+'.setup_ui');P=import_module(H+'.preservation');L=import_module(H+'.ledger');X=import_module(H+'.export_native')
def main():
 out=R/'evidence/betaintegrated01-cockpit05-clockorder08/host/helper-mock01';out.mkdir(parents=True,exist_ok=False);results=[]
 def test(name,f):
  try:results.append(dict(case=name,pass_=True,detail=f()))
  except BaseException as e:results.append(dict(case=name,pass_=False,error=repr(e)))
 def parse():
  for p in Path(__file__).parent.glob('*.py'):ast.parse(p.read_text())
  return 'all modules parse, no execution of runtime'
 test('AST',parse)
 def baseline():
  counts={p:len(P.expected_old(p))for p in P.BASELINES};assert list(counts.values())==[233,25,10,11]
  ds={p:P.diagnostic_baseline(p)[2:]for p in P.DIAGNOSTICS};assert [v[1]for v in ds.values()]==[101959,103157]
  for p,c in counts.items():
   v=P.expected_old(p);raw=''.join(h+'  '+n+'\n'for n,h in v.items()).encode();assert P.parse_private_map(raw,c)==v
  return dict(standard=counts,diagnostic=ds,totalStandard=279,diagnosticCount=2)
 test('four immutable maps and two distinct diagnostic facts',baseline)
 def ledger():
  v=L.verify_prior_allocation();cap=L.short_tar_cap();assert cap==192*L.MIB-v['priorExportBytes']-int(167.75*L.MIB)-512*1024
  assert L.avd_growth(v['closed07AVDAllocatedBytes'])==11206656
  assert v['priorExportBytes']+cap+int(167.75*L.MIB)+512*1024==192*L.MIB
  assert sum(p.stat().st_size for p in X.exports())==2409205
  with patch.object(L,'metadata_total',return_value=64*L.MIB):L.assert_shared_caps(v['cumulativeAVDOriginalBaseline']+512*L.MIB)
  for metadata,avd in [(64*L.MIB+1,v['closed07AVDAllocatedBytes']),(0,v['cumulativeAVDOriginalBaseline']+512*L.MIB+1)]:
   with patch.object(L,'metadata_total',return_value=metadata):
    try:L.assert_shared_caps(avd)
    except ValueError:pass
    else:raise AssertionError('shared limit accepted')
  return dict(priorExportBytes=v['priorExportBytes'],shortCap=cap,longCap=int(167.75*L.MIB),globalCap=192*L.MIB,metadataAtCapAllowed=True,metadataAndAVDAboveCapRefused=True)
 test('cumulative boundaries including retained partial exports',ledger)
 def ime():
  for method in (S.Setup.name_r1,S.Setup.reference_r1):
   import inspect
   s=inspect.getsource(method);assert 'KEYCODE_TAB'in s and '430,190'not in s;assert 'keyboard_settle()'in s
  s=Path(S.__file__).read_text();assert s.index('setup.device_ready()')<s.index(".preservation').observe")
  return 'TAB after hidden2; actual control-flow mock supplied independently; no real IME claim'
 test('IME focus and device-ready source wiring',ime)
 v=dict(status='PASS'if all(x['pass_']for x in results)else'FAIL',cases=results,realAndroid=False,AP=False,syntheticDiskPrime=False)
 (out/'results.json').open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(v));assert v['status']=='PASS'
if __name__=='__main__':main()
