#!/usr/bin/env python3
"""Read-only source checks and disposable negative controls; writes one new receipt."""
import copy, datetime, hashlib, json, os, re, shutil, sys
from pathlib import Path
import yaml

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
sys.path.insert(0,'/Users/os/.codex/skills/refinery')
import refinery

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert shutil.disk_usage(REPO).free >=20*1024**3+64*1024**2, 'Resource floor/headroom'
out=REPO/'evidence/future-rd-20261021/verification01.json'
assert not out.exists(), 'Append new receipt; never overwrite'
cfg,claims,registry,agg,b=refinery.run_pipeline(ROOT)
assert b==(ROOT/'registry.json').read_bytes()
assert refinery.run_pipeline(ROOT)[4]==b
sources=json.loads((ROOT/'registry-sources.json').read_text())
capture_checks=[]
for s in sources:
    if 'snapshot' not in s: continue
    p=ROOT/'snapshots'/s['snapshot']
    assert p.is_file() and sha(p)==s['sha256'], s['id']
    capture_checks.append(s['id'])
for c in claims:
    matches=[s for s in sources if s.get('snapshot')==c['capture']['snapshot']]
    assert len(matches)==1 and matches[0]['origin']==c['capture']['source']
assert all(r['fields']['installed_hera']['state']=='null' and r['fields']['price']['state']=='null' for r in registry.values())
assert all(c['meaning']=='OFFICIAL_DOCUMENTATION_CLAIM_NOT_LOCAL_TEST' for c in claims)

scratch=ROOT/'.scratch-verification'
assert not scratch.exists()
scratch.mkdir()
bites=[]
def check_bite(name,gate,mutate):
    dst=scratch/name
    dst.mkdir(); (dst/'snapshots').mkdir()
    for snap in {c['capture']['snapshot'] for c in claims}:
        # Small research captures only; never copies the project or mutates a hardlink.
        os.link(ROOT/'snapshots'/snap,dst/'snapshots'/snap)
    cc=copy.deepcopy(claims); cf={k:copy.deepcopy(v) for k,v in cfg.items() if k!='_dir'}
    mutate(dst,cf,cc)
    (dst/'domain.yaml').write_text(yaml.safe_dump(cf,allow_unicode=True))
    (dst/'claims.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cc))
    try: refinery.run_pipeline(dst)
    except refinery.GateError as e:
        assert e.gate==gate,(name,e.gate,gate)
        bites.append(dict(case=name,expected=gate,observed=e.gate,result='REJECTED_AS_EXPECTED'))
    else: raise AssertionError(f'Gate did not bite: {name}')
    finally: shutil.rmtree(dst)

try:
    check_bite('missing-capture','CAPTURE_MISSING',lambda d,c,r:(d/'snapshots'/r[0]['capture']['snapshot']).unlink())
    check_bite('invented-span','SPAN_NOT_FOUND',lambda d,c,r:r[0].update(evidence_span='INVENTED_EVIDENCE_NOT_IN_ANY_SOURCE_987654'))
    check_bite('invalid-tier','SOURCED_ATTR',lambda d,c,r:r[0].update(tier='Z'))
    check_bite('variant-merge','AMBIGUOUS_MERGE_UNFLAGGED',lambda d,c,r:c['alias_map'].update({'gremsy-pixylr-sportv2':'gremsy-pixylr-standard'}))
    check_bite('inference-as-fact','NO_INFERRED',lambda d,c,r:r[0].update(extraction='inferred'))
    os.environ['REFINERY_BITE_NONDET']='1'
    try: check_bite('nondeterminism','IDEMPOTENT',lambda d,c,r:None)
    finally: os.environ.pop('REFINERY_BITE_NONDET',None)
finally:
    shutil.rmtree(scratch)

# Reconciliation controls use in-memory copies, independently assert selected cell semantics.
dup=copy.deepcopy(claims[0]); dup['capture']['url']+='?same-origin-control'
same=refinery.build(cfg,claims+[dup])[claims[0]['entity']]['fields'][claims[0]['field']]
assert same['state']=='sourced', 'Same vendor must not become independent corroboration'
conflict=copy.deepcopy(claims[0]); conflict['value']='contradictory test value'
cell=refinery.build(cfg,claims+[conflict])[claims[0]['entity']]['fields'][claims[0]['field']]
assert cell['state']=='disputed' and cell['value'] is None and len(cell['claims'])==2

pins=[]
baseline=json.loads((ROOT/'internal-baseline.json').read_text())
for p in baseline['files']:
    path=REPO/p['path']; actual=sha(path) if path.is_file() else None
    assert actual==p['sha256'],p['path']
    pins.append(dict(path=p['path'],sha256=actual,kind='INTERNAL_SOURCE_BASELINE'))
for manifest in ['evidence/big02/builder/source-ready04.json','evidence/phone06/builder/source-ready07.json']:
    m=json.loads((REPO/manifest).read_text())
    for rel,expected in m['files'].items():
        p=REPO/rel; actual=sha(p) if p.is_file() else None
        assert actual==expected,rel
        pins.append(dict(path=rel,sha256=actual,kind=manifest))
apk=REPO/'native/phone06/dist/aeris-phone06-development01.apk'
assert sha(apk)=='0a1423e38f29565b4b22c9c14b1ae1beaffce6dcb46618ee583bd7b2871a9c2b'
pins.append(dict(path=str(apk.relative_to(REPO)),sha256=sha(apk),kind='EXISTING_APK'))

plan=json.loads((REPO/'planning/future-rd-20261021/reference-configs.json').read_text())
ids={c['id'] for c in claims}
for h in plan['hypotheses']:
    assert h['tier']=='H' and len(set(h['support']))>=3 and set(h['support'])<=ids
    assert h['falsification'] and h['ethicalReview']
for p in plan['profiles']:
    assert set(p['sourceFacts'])<=ids and p['unknowns']
assert plan['status']=='PROPOSED_RD_TARGETS_NOT_INSTALLED_CONFIGURATION'
assert not (ROOT/'.scratch-verification').exists()

# All artifact-relative links in the two authored Markdown deliverables must resolve.
links=[]
for doc in [REPO/'delivery/RESEARCH-FUTURE-RD-20261021.md',REPO/'planning/future-rd-20261021/ACCEPTANCE.md']:
    for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
        if '://' in target: continue
        target=target.split('#')[0]
        p=(doc.parent/target).resolve()
        # Receipt being written by this run is the single permitted forward reference.
        assert p.is_file() or p==out, (doc,target)
        links.append(str(p.relative_to(REPO)))

artifact_paths=list(ROOT.rglob('*'))+list((REPO/'planning/future-rd-20261021').rglob('*'))+[REPO/'delivery/RESEARCH-FUTURE-RD-20261021.md']
artifacts={str(p.relative_to(REPO)):sha(p) for p in artifact_paths if p.is_file()}
bytecount=sum(p.stat().st_size for p in artifact_paths if p.is_file())
assert bytecount<64*1024**2
receipt=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='PASS_RESEARCH_STRUCTURAL_AND_SCOPED_PRESERVATION_NOT_HARDWARE_ACCEPTANCE',
    claims=len(claims),entities=len(registry),captureShaChecks=len(capture_checks),
    registrySha256=hashlib.sha256(b).hexdigest(),idempotent=True,deterministicAuditor=True,
    limitations='Engine auditor re-derives selected claims, not independent human semantic review or real equipment testing',
    negativeControls=bites,semanticControls=dict(sameOriginNotCorroborated=True,conflictRetained=True,unknownPriceAndInstalledHeraRemainNull=True),
    notApplicableGates=['distribution: no rollup and no market denominator','Chinese-original, incident and geopolitical-stratum gates: not this schema'],
    sourceFailuresRetained=['Sony product403 and reader timeouts','FLIR/Doodle original403; exact reader fallback labeled','Qualcomm rawJS shell; reader failure, no specifications promoted'],
    internalPins=pins,scopePreservation='13 internal source fingerprints +25 BIG02 pins +248 PHONE06 pins +existing APK; not a fresh all-ENDURE or full-history audit',
    historicalIncident='Prior missing-path incidents remain unresolved; no restoration or continuous-original-presence claim',
    targetRequirements=12,proposalHypotheses=len(plan['hypotheses']),hardwareMeasuredInThisTask=False,
    resource=dict(newArtifactBytes=bytecount,freeBytes=shutil.disk_usage(REPO).free,floorBytes=20*1024**3),
    cleanup=dict(removed=['research/future-rd-20261021/.scratch-verification'],outsideRepoScratch=False,newServices=False,newDependencies=False),
    localLinksChecked=links,toolSha256={p.name:sha(p) for p in [Path(refinery.__file__),ROOT/'verify.py']},artifactSha256=artifacts)
assert receipt['resource']['freeBytes']>=receipt['resource']['floorBytes']
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('x') as f: json.dump(receipt,f,ensure_ascii=False,indent=2); f.write('\n')
print(json.dumps({k:receipt[k] for k in ['status','claims','entities','captureShaChecks','resource']},ensure_ascii=False))
print('Pin checks:',len(pins),'Negative controls:',len(bites),'Scope: research, not product qualification')
