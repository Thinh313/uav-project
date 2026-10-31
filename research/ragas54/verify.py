#!/usr/bin/env python3
"""Research integrity checks and injected faults, not application acceptance."""
import copy, datetime, hashlib, json, os, runpy, shutil, subprocess, sys, tempfile
from html.parser import HTMLParser
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
METHOD=ROOT.parent/'02_Refinery_MethodBox'
sys.path.insert(0,str(METHOD))
import refinery

checks=[]
def check(name, condition, scope='RESEARCH_INTEGRITY'):
    checks.append({'check':name,'pass':bool(condition),'scope':scope})
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,value):(HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
sources=json.loads((HERE/'sources.json').read_text())
for s in sources:
    p=HERE/'snapshots'/s['snapshot']
    check('snapshot-sha:'+s['id'],p.exists() and digest(p)==s['sha256'] and p.stat().st_size==s['bytes'])
    if 'derived_from' in s:
        parent=HERE/'snapshots'/s['derived_from']
        check('derived-parent:'+s['id'],digest(parent)==s['parent_sha256'])

cfg,claims,registry,aggregate,canonical=refinery.run_pipeline(str(HERE))
dump('registry.json',{'registry':registry,'aggregates':aggregate,'build_digest':refinery.digest(canonical),
                      'scope':'Sourced publisher claims only; null runtime_test_evidence and installed_apk_version'})
check('registry-auditor',refinery.audit(cfg,claims,registry,aggregate))
check('registry-idempotent',canonical==refinery.run_pipeline(str(HERE))[-1])
check('no-runtime-promotion',all(r['fields']['runtime_test_evidence'].get('value') is None for r in registry.values()))
check('publisher-not-corroborated-by-own-mirrors',all(r['fields']['publisher_statement']['state']=='sourced' for r in registry.values()))

# Use existing unchanged applicability runner, but constrain temporary directory names.
# Only this small research domain is copied; no checkout copy/build/install.
scratch=[]
mkdtemp=tempfile.mkdtemp
def task_tmp(*args,**kwargs):
    kwargs['prefix']='codex-tmp-ragas54-20261015-'
    p=mkdtemp(*args,**kwargs);scratch.append(p);return p
tempfile.mkdtemp=task_tmp
old_argv=sys.argv[:]
try:
    from contextlib import redirect_stdout
    from io import StringIO
    output=StringIO()
    sys.argv=[str(ROOT/'tools/refinery_project_bites.py'),str(HERE)]
    with redirect_stdout(output):
        try:runpy.run_path(str(ROOT/'tools/refinery_project_bites.py'),run_name='__main__')
        except SystemExit as e:
            if e.code not in (None,0):raise
    bite=json.loads(output.getvalue())
    dump('refinery-bites.json',bite)
    for b in bite['results']:
        if b['status']!='N/A':check('refinery-bite:'+b['check'],b['status']=='PASS','INJECTED_FAULT')
finally:
    sys.argv=old_argv
    tempfile.mkdtemp=mkdtemp
    for p in scratch:
        if Path(p).exists():shutil.rmtree(p)
check('scratch-removed',all(not Path(p).exists() for p in scratch))

matrix=json.loads((HERE/'verification-matrix.json').read_text())
rows=matrix['cases']
claim_ids={c['id'] for c in claims}
required=['feature','priority','required_behavior','test_data','independent_oracle','pass_criterion','fail_criterion',
          'required_evidence','terminal_first','retained_evidence','threshold_status','published_note_presence']
check('matrix-25-unique',len(rows)==25 and len({x['id'] for x in rows})==25)
for c in rows:
    check('matrix-contract:'+c['id'],all(c.get(k) for k in required) and set(c['publisher_claim_ids'])<=claim_ids)
    check('not-run-remains-not-checked:'+c['id'],c['ragas_runtime_result']=='NOT_CHECKED' and c['new_aeris_runtime_result']=='NOT_CHECKED')

def evidence_gate(row):
    if row['ragas_runtime_result']!='NOT_CHECKED':raise ValueError('No RAGAS runtime capture exists in research increment')
    if not row.get('independent_oracle'):raise ValueError('Missing independent oracle')
    if not row.get('fail_criterion'):raise ValueError('Missing fail criterion')
for key,value in [('ragas_runtime_result','PASS'),('independent_oracle',''),('fail_criterion','')]:
    target=copy.deepcopy(rows[1]);target[key]=value
    try:evidence_gate(target)
    except ValueError:check('reject-'+key,True,'INJECTED_FAULT')
    else:check('reject-'+key,False,'INJECTED_FAULT')

b=json.loads((HERE/'baseline.json').read_text())
raw=json.loads((HERE/'snapshots/releases.json').read_text())
old=json.loads((ROOT/'research/ragas-baseline/snapshots/ragas-releases.json').read_text())
new=next(r for r in raw if r['tag_name']=='v4.0.14-b111')
prior=next(r for r in old if r['tag_name']=='v4.0.14-b111')
check('release-dates',b['published_at']==new['published_at'] and b['updated_at']==new['updated_at'])
check('old-new-note-equivalence',new['body'].splitlines()==prior['body'].splitlines())
manifest=json.loads((HERE/'snapshots/v4.0.14-b111--manifest-prod.json').read_text())
apk=next(a for a in new['assets'] if a['name'].endswith('.apk'))
check('identity-discrepancy-observed',manifest['buildNumber']==112 and '+111-' in apk['name'] and new['tag_name'].endswith('b111'))
check('metadata-finding-is-not-runtime-fail',b['metadata_gate']['status']=='FAIL_METADATA_IDENTITY_CONSISTENCY' and b['runtime_ragas']=='NOT_CHECKED')
check('notes-comparison-no-invented-first-introduction','first-introduction' in b['comparison_4010_to_4014']['method'])
for platform,suffix in [('android','.apk'),('linux','.deb')]:
    asset=next(a for a in new['assets'] if a['name'].endswith(suffix))
    mpath=HERE/'snapshots'/('v4.0.14-b111--manifest-prod.json' if platform=='android' else 'v4.0.14-b111--manifest-prod-linux-u20.json')
    m=json.loads(mpath.read_text())
    checksum=(HERE/'snapshots'/('v4.0.14-b111--'+asset['name']+'.sha256')).read_text().split()[0]
    check(platform+'-publisher-checksum-agreement',asset['digest']=='sha256:'+m['sha256']=='sha256:'+checksum and m['sizeBytes']==asset['size'])
    # Agreement only across publisher channels, not local binary verification.
check('readme-badge-observed','version-4.0.0%20(build%204)' in (HERE/'snapshots/readme-main.md').read_text())
reuse=json.loads((HERE/'reuse.json').read_text())
for c in reuse['receipt_checks']+reuse['fixtures']:
    check('retained-hash:'+c['path'],c['matches'] and digest(ROOT/c['path'])==c['expected'])

class ReportParser(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.rows=0;self.script=False
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='a':self.links.append(d.get('href',''))
        if tag=='tr':self.rows+=1
        if tag=='script':self.script=True
p=ReportParser();p.feed((HERE/'index.html').read_text());p.close()
check('html-no-active-runtime',not p.script)
check('html-matrix-row-count',p.rows==25+13+2)
for link in p.links:
    if not link.startswith(('http:','https:','#')):
        check('html-local-link:'+link,(HERE/link).is_file())
check('source-candidate-sot-not-output-targets',all((HERE/name).is_file() for name in ['baseline.json','verification-matrix.json','index.html']))
report={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'result':'PASS_RESEARCH_INTEGRITY' if all(c['pass'] for c in checks) else 'FAIL_RESEARCH_INTEGRITY',
 'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks),'checks':checks,
 'refinery_digest':refinery.digest(canonical),'claims':len(claims),'matrix_cases':len(rows),
 'scratch_removed':scratch,'dependency_installs':0,'binary_downloads':0,'new_application_runs':0,
 'ragas_runtime':'NOT_CHECKED','release_identity_metadata':'FAIL_METADATA_IDENTITY_CONSISTENCY',
 'visual_browser_review':'NOT_CHECKED: browser policy refuses file protocol; no workaround attempted. Static HTML/link audit only.',
 'verification_limits':'One agent; schema/hash/bites do not independently validate all semantic interpretations or certify product behavior.'}
dump('verification.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','scratch_removed']},ensure_ascii=False))
if report['failed']:
    print(json.dumps([c for c in checks if not c['pass']],ensure_ascii=False))
sys.exit(bool(report['failed']))
