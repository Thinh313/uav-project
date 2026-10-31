"""Source captures, applicable unchanged Refinery gates and frozen candidate checks.
No whole-project scratch copy; small domain fault copies removed in finally.
"""
from pathlib import Path
import json,hashlib,sys,shutil,tempfile,copy,os
ROOT=Path(__file__).resolve().parents[2]
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path.insert(0,str(ROOT.parent/'02_Refinery_MethodBox'))
import refinery,bites
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,ok,detail=None):
    checks.append({'name':name,'pass':bool(ok),'detail':detail})
    assert ok,name
domain=ROOT/'research/payload21'
sources=json.loads((domain/'sources.json').read_text())
for s in sources:check('original source hash '+s['id'],sha(domain/'snapshots'/s['snapshot'])==s['sha256'])
cfg,claims,registry,agg,canonical=refinery.run_pipeline(str(domain))
(domain/'registry.json').write_bytes(canonical+b'\n')
check('clean refinery build and independent derivation auditor',bool(claims))
removed=[]
for name,fn in bites.BITES:
    if name=='DISTRIBUTION_NO_DENOMINATOR' and cfg.get('rollup_field') is None:
        continue # No distribution/coverage is published. Raw CLI failure retained.
    tmp=Path(tempfile.mkdtemp(prefix='codex-tmp-aeris-payload21-20261013-'))
    try:
        dst=tmp/'domain';shutil.copytree(domain,dst)
        if name=='CAPTURE_MISSING':
            (dst/'snapshots'/claims[0]['capture']['snapshot']).unlink()
            bit,last=bites._expect_bite(dst,name)
        else:bit,last=fn(dst)
        if bit is not None:check('applicable refinery bite '+name,bit,last)
    finally:shutil.rmtree(tmp);removed.append(str(tmp))
for name,target in [('derived cell',copy.deepcopy(registry)),('derived aggregate',copy.deepcopy(agg))]:
    if name=='derived cell':
        next(c for r in target.values() for c in r['fields'].values() if c.get('value') is not None)['value']='fabricated'
        args=(cfg,claims,target,agg)
    else:target['n']=999;args=(cfg,claims,registry,target)
    try:refinery.audit(*args)
    except refinery.GateError:check('audit refuses '+name,True)
    else:check('audit refuses '+name,False)
m=json.loads((ROOT/'pilot/payload21/matrix.json').read_text())
check('comparative winner is null; RAGAS runtime unmeasured',m['winner'] is None and m['ragasRuntime']=='NOT_CHECKED')
check('matrix source/evidence paths and scoped labels',len(m['rows'])==12 and all((ROOT/f).is_file() for r in m['rows'] for f in r['evidence']) and all(r['status'] in {'MEASURED_SITL','MEASURED_BOUNDED','MEASURED_HOST','SIMULATED','MISSING','DIAGNOSTIC_ONLY','NOT_CHECKED'} for r in m['rows']))
check('matrix published rows trace to sourced claims; runtime remains null',all(any(c['entity']=='RAGAS' and c['field']==r['ragasClaimField'] for c in claims) for r in m['rows'] if r['id']!='comparison') and registry['RAGAS']['fields']['runtime_ab']['value'] is None)
f=json.loads((ROOT/'evidence/endure20/freeze.json').read_text())
check('all140 frozen ENDURE20 payload bytes preserved',len(f['files'])==140 and all(sha(ROOT/p['path'])==p['sha256'] for p in f['files']))
pins=json.loads((ROOT/'evidence/endure20/controller-pins.json').read_text())
check('all5 ENDURE20 controller fingerprints preserved',len(pins['files'])==5 and all(sha(ROOT/p)==h for p,h in pins['files'].items()))
check('all method scratch domain copies removed',all(not Path(p).exists() for p in removed))
receipt=dict(checks=checks,removed=removed,notApplicable=['Full generic denominator bite: rollup_field=null, no population distribution published','Domain-specific gates not configured'],scope='Capture integrity and applicable deterministic gates; external claims remain sourced, not physical/runtime verification')
(ROOT/'evidence/payload21/sources-qa.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
