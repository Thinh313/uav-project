#!/usr/bin/env python3
"""Separate receipt/provenance/CLI verification, not independent human review."""
import ast,copy,datetime,hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];E=ROOT/'evidence/mission55';OUT=E/'verify1'
if OUT.exists():raise SystemExit('Verification receipt already exists')
fs=os.statvfs(ROOT)
if fs.f_bavail*fs.f_frsize<20*1024**3+1024**2:raise SystemExit('Disk floor')
OUT.mkdir();checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,value):checks.append({'name':name,'pass':bool(value)})
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
report=json.loads((E/'run5/verification.json').read_text());corpus=json.loads((E/'run5/corpus.json').read_text())
check('functional-count-rederived',report['passed']==sum(x['pass'] for x in report['checks']) and report['failed']==sum(not x['pass'] for x in report['checks']))
check('functional-final-pass-only',report['failed']==0 and report['passed']==234 and report['RAGASRuntime']=='NOT_CHECKED' and report['flightReady'] is False)
for name,h in json.loads((E/'run5/source-at-start.json').read_text())['files'].items():check('tested-source-pin:'+name,sha(ROOT/name)==h)
for c in corpus['generated']:
    check('new-corpus-sha:'+c['id'],sha(ROOT/c['path'])==c['sha256'])
    check('new-corpus-not-called-QGC-output:'+c['id'],c['producer'].endswith('NOT QGC application'))
    parent=c.get('parent')
    if isinstance(parent,dict):check('derivative-parent:'+c['id'],sha(ROOT/parent['path'])==parent['sha256'])
for c in corpus['retained']:check('retained-source-sha:'+c['path'],sha(ROOT/c['path'])==c['expected'])
for s in json.loads((E/'oracle-sources.json').read_text()):check('oracle-sha:'+s['id'],sha(ROOT/s['path'])==s['sha256'])
wheel=E/'sources/geographiclib-2.1-py3-none-any.whl'
with zipfile.ZipFile(wheel) as z:
    for path in (HERE/'vendor').rglob('*'):
        if not path.is_file():continue
        rel=str(path.relative_to(HERE/'vendor'))
        check('vendor-matches-pinned-wheel:'+rel,path.read_bytes()==z.read(rel))
check('geographiclib-license-retained',any('LICENSE' in p.name.upper() for p in (HERE/'vendor').rglob('*')))
for path in HERE.glob('*.py'):
    ast.parse(path.read_text());check('python-syntax:'+path.name,True)
for path in HERE.glob('*.mjs'):
    r=subprocess.run(['node','--check',str(path)],capture_output=True,text=True)
    check('node-syntax:'+path.name,r.returncode==0)

cases=[('equal','app/fixtures/qgc/roundtrip03/simple-relative-input.plan','app/fixtures/qgc/roundtrip03/simple-relative-input.plan',0,'EQUAL_DECLARED_SCOPE'),
 ('Home-diff','app/fixtures/qgc/roundtrip03/simple-relative-input.plan','app/fixtures/qgc/roundtrip03/simple-relative-qgc-saved.plan',2,'DIFFERENT'),
 ('extension-review','pilot/mission55/fixtures/run5/extension-retained.plan','pilot/mission55/fixtures/run5/extension-retained.plan',3,'REVIEW_REQUIRED')]
for name,body in [('invalid-utf8',b'\xff'),('oversize',b' '*262145),('duplicate-key',b'{"version":1,"version":2}')]:
    p=OUT/(name+'.input');p.write_bytes(body)
    cases.append((name,str(p.relative_to(ROOT)),str(p.relative_to(ROOT)),4,'REJECTED'))
cli=[]
for name,a,b,exit_code,verdict in cases:
    r=subprocess.run([sys.executable,'-B',str(HERE/'cli.py'),'compare',str(ROOT/a),str(ROOT/b)],capture_output=True,text=True,timeout=10)
    d=json.loads(r.stdout);check('CLI:'+name,r.returncode==exit_code and d['verdict']==verdict and d['flightReady'] is False)
    cli.append({'case':name,'exit':r.returncode,'result':d})
save('cli.json',cli)
replay=json.loads((E/'run5/retained-replay.json').read_text())
check('inbound-not-called-raw',all(r['inboundRawCRC']=='NOT_CHECKED' and r['bootEvidence']=='NOT_RECORDED' for r in replay))
check('38-outbound-CRC-decoded',sum(r['inventory']['decodedRawFrames'] for r in replay)==38)
check('95-foreign-session-items-quarantined',sum(r['inventory']['foreignSessionQuarantined'] for r in replay)==95)
check('8-complete-readback-inventories',sum(len(r['inventory']['cycles']) for r in replay)==8 and all(len(c)==19 for r in replay for c in r['inventory']['cycles']))

# Auditor bite: an untested or failed result cannot be promoted by changing the top count.
def accepts(r):return r['failed']==0 and all(x['pass'] is True for x in r['checks']) and r['passed']==len(r['checks']) and r['RAGASRuntime']=='NOT_CHECKED'
bad=copy.deepcopy(report);bad['checks'][0]['pass']=False
check('reject-tampered-PASS-total',not accepts(bad))
bad=copy.deepcopy(report);bad['RAGASRuntime']='PASS'
check('reject-promoting-RAGAS-runtime',not accepts(bad))
perf=json.loads((E/'run5/performance.json').read_text())
check('performance-honest-host-scope',perf['samples']==20 and perf['p95Ms']<500 and 'not RAGAS' in perf['scope'])
save('verification.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':sum(c['pass'] for c in checks),
     'failed':sum(not c['pass'] for c in checks),'checks':checks,'singleAgent':True,
     'scope':'Provenance/CLI/syntax/report audit; not an independent reviewer or new product runtime acceptance'})
print(json.dumps({'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks),'cliCases':len(cli),'performance':perf}))
sys.exit(any(not c['pass'] for c in checks))
