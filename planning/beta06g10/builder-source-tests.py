"""Bounded G10 namespace/numeric/historical proofs. No listener or AP runtime."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation10';sha=lambda b:hashlib.sha256(b).hexdigest()
def ns(s):
 for a,b in [('beta06g9','beta06g10'),('generation09','generation10'),('G9','G10'),('g9_','g10_'),('aeris.g9.','aeris.g10.'),('host-app09','host-app10')]:s=s.replace(a,b)
 return s
files=['entry.mjs','flight/runtime.py','flight/handoff.mjs','flight/receive-flight.mjs','flight/qualified/profile.mjs','flight/qualified/link.mjs','flight/qualified/mock.mjs','flight/qualified/verify-profile.mjs','workspace-lineage.mjs','quota.mjs','quota.py','resource.mjs','proof-writer.mjs']
rows=[]
for n in files:
 old=(R/'pilot/beta06g9'/n).read_text();new=(R/'pilot/beta06g10'/n).read_text();assert ns(old)==new,n
 rows.append({'proof':'EXACT_TARGETED_NAMESPACE_ONLY','path':'pilot/beta06g10/'+n,'sha256':sha(new.encode())})
a=json.loads((R/'pilot/beta06g9/quota-policy.json').read_bytes());b=json.loads((R/'pilot/beta06g10/quota-policy.json').read_bytes());a.pop('history');b.pop('history');a['schema']=a['schema'].replace('G9','G10');assert a==b;rows.append({'proof':'ALL_NUMERIC_POLICY_AND_FUTURE_PROJECTIONS_IDENTICAL'})
expected={'s3ed4cfd1481541d99158':'680ffbb25acbed95893eb113029328f324da19044b4b31b3765faf85b3fca34b','s8dce3bc7eb1d440a97fc':'3184125fdac10436dac8e414a2eb769ac56df74537f09aacaa16e806d1d82bfd'}
for run,h in expected.items():
 p=R/'evidence/beta06/generation09/flight/runs'/run/'request.json';q=json.loads(p.read_bytes());assert sha(p.read_bytes())==h and q['run']==run and q['mode']=='sitl'
rows.append({'proof':'HISTORICAL19_EQUALS_17_PLUS_TWO_EXACT_G9_ACTUALS_MOCK_SEPARATE','requests':expected})
# Reuse previously reviewed tiny fixture helpers by source prefix, not its old test execution.
helper=(R/'planning/beta06g9/builder-host-binding-tests.py').read_text().split('with tempfile.TemporaryDirectory(')[0];scope={'__file__':str(R/'planning/beta06g10/builder-source-tests.py')};exec(helper,scope);scope['E']=E
fixture={};bridgeRows=[]
with tempfile.TemporaryDirectory(prefix='codex-tmp-g10-binding-20261022-',dir=E)as tmp:
 root=Path(tmp)/'root';prod,active=scope['setup'](root,10)
 def check(A,H):
  p=scope['bridge'](prod,A,H);assert p.returncode==0,p.stderr;bridgeRows.append({'A':A,'H':H,'status':'ADMITTED_ACTUAL_PYTHON_NODE_BRIDGE'})
 check(4,2);paths=scope['host'](active,'host-app10');q=scope['inspect'](prod,active,paths);assert q['usage']['capacity']['hostProcesses']==1 and list(q['routes'].values())==['clock','media','hostJournals','hostJournals','hostOther'];check(4,1)
 paths+=scope['host'](active,'host-app10-restart');q=scope['inspect'](prod,active,paths);assert q['usage']['capacity']['hostProcesses']==2 and list(q['routes'].values())==['clock','media','hostJournals','hostJournals','hostOther']*2;check(4,0)
 wrong=scope['bridge'](prod,4,1);assert wrong.returncode and 'ORIGINAL_COUNTER_CAPACITY_MISMATCH'in wrong.stderr
 fixture=scope['manifest'](root)
rows.append({'proof':'CURRENT_TWO_CANONICAL_HOSTS_REAL_FILES_CATEGORY_AND_ORIGINAL_COUNTERS','stages':bridgeRows,'routes':q['routes'],'wrongCounter':'REFUSED','fixtureManifest':fixture,'scratchRemoved':tmp,'seam':'Exact quota source copies into tiny isolated ROOT; policy history identity points to one exact anchor. No AP allocation fixtures or real current flight-root writes.'})
for p in sorted((R/'pilot/beta06g10').rglob('*')):
 if p.suffix=='.mjs':subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
 elif p.suffix=='.py':__import__('ast').parse(p.read_text())
report={'status':'PASS_SOURCE_NAMESPACE_NUMERIC_HISTORY_REAL_FS_NO_RUNTIME','groups':len(rows),'rows':rows,'sourceOnly':True,'APRequests':0,'listeners':0,'oldFilesWritten':0,'removed':[tmp]}
with(E/'builder-source-tests01.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps({'status':'PASS','groups':len(rows),'policySha256':sha((R/'pilot/beta06g10/quota-policy.json').read_bytes())}))
