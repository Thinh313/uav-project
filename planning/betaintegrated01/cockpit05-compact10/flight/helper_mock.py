"""Bounded cold helper tests only. No subprocess, Android, socket or admissionprime."""
from pathlib import Path
from importlib import import_module
import ast,hashlib,json,shutil
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-compact10.flight'
def main():
 E=R/'evidence/betaintegrated01-cockpit05-compact10/host/helper-mock02';E.mkdir(parents=True,exist_ok=False);scratch=E/'scratch';scratch.mkdir();results=[]
 try:
  C=import_module(H+'.contract');v=C.make_manifest();assert v['selectedAPKInputs']==40;old=json.loads((R/'evidence/betaintegrated01-cockpit05-iocommit09/host/input-contract01.json').read_text());assert all(v['sourceSHA256'][p]==h for p,h in old['sourceSHA256'].items())and all(v['metadataSHA256'][p]==h for p,h in old['metadataSHA256'].items());results.append(dict(case='40newAPK_inputs_and_old427_38_exact_additive',pass_=True))
  for p in Path(__file__).parent.glob('*.py'):ast.parse(p.read_text());import_module(H+'.'+p.stem)
  results.append(dict(case='all_helpers_import_no_runtime_execution',pass_=True))
  P=import_module(H+'.preservation');counts={p:len(P.expected_old(p))for p in P.BASELINES};assert list(counts.values())==[233,25,10,11,11,17];assert [P.diagnostic_baseline(p)[3]for p in P.DIAGNOSTICS]==[101959,103157,103288,103471];results.append(dict(case='old6package307records_and4separate_diagnostics',pass_=True,counts=counts))
  L=import_module(H+'.ledger');assert L.baseline()['allocatedBytes']==789549056;assert L.avd_growth(789549056)==0 and L.avd_growth(789549056+512*2**20)==512*2**20;assert L.short_tar_cap()==int(23.75*2**20);results.append(dict(case='fresh10_baseline_not_prior_campaign_debit',pass_=True))
  policy=C.policy();b=policy.build_config(R,'nominal','run','epoch','boot',scratch,'case',maximum_seconds=180);policy.validate_recording_policy(b)
  for key,value in(('requestedSpeedup',True),('capMs',500.0)):
   bad=dict(b);bad[key]=value
   try:policy.validate_recording_policy(bad)
   except ValueError:pass
   else:raise AssertionError('typedphysicalprofilewaiver')
  results.append(dict(case='new_runtime_exact_amendment_physical_typed_profile_unchanged',pass_=True))
  profile=import_module('planning.betaintegrated01.cockpit05-compact10.runtime.profile').Profile()
  for name in('serialize','guard','STAGE','recvwait'):
   for _ in range(17):
    with profile.measure(name):pass
  for name in('write','fsync'):
   for n in range(3):profile.observe(name,n,n+1,1)
  data=profile.snapshot();data.update(run='run',epoch='epoch',boot='boot',journalClosed=True);p=scratch/'host-profile.json';raw=(json.dumps(data)+'\n').encode();p.write_bytes(raw);a={'liveParentBackend':{'hostProfileSHA256':hashlib.sha256(raw).hexdigest()}};V=import_module(H+'.host_profile');V.verify(scratch,a,dict(run='run',epoch='epoch',boot='boot'))
  data['phases']['guard']['measuredCount']=17;raw=json.dumps(data).encode();p.write_bytes(raw);a['liveParentBackend']['hostProfileSHA256']=hashlib.sha256(raw).hexdigest()
  try:V.verify(scratch,a,dict(run='run',epoch='epoch',boot='boot'))
  except ValueError:pass
  else:raise AssertionError('fake_all_guard_metrics_accepted')
  results.append(dict(case='profile_sourcebound_coverage_sampling_refuses_claimed_full',pass_=True))
 finally:
  removed=sum(p.stat().st_size for p in scratch.rglob('*')if p.is_file());shutil.rmtree(scratch)
 out=dict(status='PASS',cases=results,actualServices=False,syntheticProfileOnly=True,actualGuardPrime=False,scratchRemoved=True,removedBytes=removed);(E/'results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'cases':len(results),'removedBytes':removed}))
if __name__=='__main__':main()
