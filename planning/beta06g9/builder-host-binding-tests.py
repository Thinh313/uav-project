"""Real tiny filesystem roots; exact source copies, fixture history identity only. No AP runtime."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,tempfile
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation09';E.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();rows=[];manifests={}
def run(argv):
 p=subprocess.run(argv,cwd=R,capture_output=True,text=True,timeout=20);assert len(p.stdout.encode())<256*1024 and len(p.stderr.encode())<64*1024;return p
def setup(root,g):
 ns='beta06g'+str(g);prod=root/'pilot'/ns;prod.mkdir(parents=True);active=root/'evidence/beta06'/('generation%02d'%g);active.mkdir(parents=True)
 for n in ['quota.mjs','quota.py']:(prod/n).write_bytes((R/'pilot'/ns/n).read_bytes())
 anchor=root/'evidence/beta06/historical.txt';anchor.write_bytes(b'IMMUTABLE_TEST_HISTORY_ONLY\n');st=anchor.stat();key='evidence/beta06/historical.txt';hist={'schema':'G%d_IMMUTABLE_HISTORY_V1'%g,'root':'evidence/beta06','excludedScope':'evidence/beta06/generation%02d'%g,'entries':{key:{'kind':'REGULAR_FILE','mode':oct(st.st_mode&0o777),'bytes':st.st_size,'sha256':sha(anchor.read_bytes()),'mtimeNs':str(st.st_mtime_ns)}},'totals':{'entries':1,'files':1,'directories':0,'bytes':st.st_size}}
 hp=active/'qa-history-inventory-fixture.json';hp.write_text(json.dumps(hist));policy=json.loads((R/'pilot'/ns/'quota-policy.json').read_bytes());policy['history']={'path':str(hp.relative_to(root)),'sha256':sha(hp.read_bytes())};(prod/'quota-policy.json').write_text(json.dumps(policy));return prod,active
bridge_code="import importlib.util,json,sys;s=importlib.util.spec_from_file_location('fixture_quota',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(json.dumps(m.admit('before-connect',remaining_ap=int(sys.argv[2]),remaining_hosts=int(sys.argv[3]),closed_runs=[],claim_id='ISOLATED_FIXTURE_CAPACITY_NOT_FLIGHT')))"
def bridge(prod,A,H):return run(['python3','-B','-c',bridge_code,str(prod/'quota.py'),str(A),str(H)])
def inspect(prod,active,files):
 code="const q=await import("+json.dumps((prod/'quota.mjs').as_uri())+");const usage=await q.scan();console.log(JSON.stringify({usage,routes:Object.fromEntries("+json.dumps([str(p.relative_to(prod.parents[1]))for p in files])+".map(p=>[p,q.category(p)]))}));"
 p=run(['node','--input-type=module','-e',code]);assert p.returncode==0,p.stderr;return json.loads(p.stdout)
def host(active,name):
 d=active/name;paths=[]
 for rel in ['media/clock-events.jsonl','media/report-01.json','overlap-events.jsonl','ui-diagnostics/events.jsonl','app-launch.json']:
  p=d/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}\n');paths.append(p)
 return paths
def manifest(root):
 return{str(p.relative_to(root)):{'kind':'DIRECTORY'if p.is_dir()else'REGULAR_FILE','bytes':0 if p.is_dir()else p.stat().st_size,'sha256':None if p.is_dir()else sha(p.read_bytes())}for p in sorted(root.rglob('*'))}
with tempfile.TemporaryDirectory(prefix='codex-tmp-g9-binding-20261022-',dir=E)as tmp:
 base=Path(tmp);old,oa=setup(base/'old',8);new,na=setup(base/'new',9)
 assert (old/'quota.mjs').read_bytes()==(R/'pilot/beta06g8/quota.mjs').read_bytes();assert (new/'quota.mjs').read_bytes()==(R/'pilot/beta06g9/quota.mjs').read_bytes()
 p=bridge(new,4,2);assert p.returncode==0,p.stderr;rows.append({'stage':'new-before-first-host','A':4,'H':2,'status':'PASS_ACTUAL_PYTHON_NODE_BRIDGE'})
 of=host(oa,'host-app08');old_result=inspect(old,oa,of);assert old_result['usage']['capacity']['hostProcesses']==0;assert set(old_result['routes'].values())=={'sourceQA'};p=bridge(old,4,1);assert p.returncode!=0 and 'ORIGINAL_COUNTER_CAPACITY_MISMATCH'in p.stderr;rows.append({'stage':'frozen-G8-first-host','status':'EXPECTED_REPRODUCED_BINDING_FAILURE','hostProcesses':0,'wrongRoutes':old_result['routes'],'bridgeError':'ORIGINAL_COUNTER_CAPACITY_MISMATCH','guardNotBypassed':True})
 nf=host(na,'host-app09');expected=['clock','media','hostJournals','hostJournals','hostOther'];z=inspect(new,na,nf);assert list(z['routes'].values())==expected;assert z['usage']['capacity']['hostProcesses']==1;p=bridge(new,4,1);assert p.returncode==0,p.stderr;rows.append({'stage':'new-first-host','A':4,'H':1,'routes':z['routes'],'status':'PASS_REAL_FILES_AND_ORIGINAL_COUNTERS'})
 ap=na/'flight/runs'/('s'+'1'*20);ap.mkdir(parents=True);(ap/'request.json').write_text(json.dumps({'run':ap.name,'mode':'sitl','source':'HOST_NODE_GCS_SIM_ONLY','classification':'ISOLATED_CAPACITY_FIXTURE_NOT_EXECUTION'}));p=bridge(new,3,1);assert p.returncode==0,p.stderr;rows.append({'stage':'new-first-allocation','A':3,'H':1,'status':'PASS_ISOLATED_ALLOCATION_METADATA_NO_AP'})
 nf2=host(na,'host-app09-restart');z=inspect(new,na,nf+nf2);assert list(z['routes'].values())==expected+expected;assert z['usage']['capacity']['hostProcesses']==2;p=bridge(new,3,0);assert p.returncode==0,p.stderr;rows.append({'stage':'new-second-host','A':3,'H':0,'routes':z['routes'],'status':'PASS_REAL_FILES_AND_ORIGINAL_COUNTERS'})
 for count in [2,3,4]:
  ap=na/'flight/runs'/('s'+str(count)*20);ap.mkdir();(ap/'request.json').write_text(json.dumps({'run':ap.name,'mode':'sitl','source':'HOST_NODE_GCS_SIM_ONLY','classification':'ISOLATED_CAPACITY_FIXTURE_NOT_EXECUTION'}));p=bridge(new,4-count,0);assert p.returncode==0,p.stderr;rows.append({'stage':'new-allocation-'+str(count),'A':4-count,'H':0,'status':'PASS_ISOLATED_COUNTER_BRIDGE'})
 p=bridge(new,4,0);assert p.returncode!=0 and 'ORIGINAL_COUNTER_CAPACITY_MISMATCH'in p.stderr;rows.append({'stage':'wrong-original-counter','status':'EXPECTED_REFUSAL'})
 manifests={'old':manifest(base/'old'),'new':manifest(base/'new')};assert not (E/'flight/runs').exists()or not any(p.name.startswith('s')for p in(E/'flight/runs').iterdir())
report={'status':'PASS_REAL_FS_BINDING_CORRECTION_NO_RUNTIME','groups':len(rows),'rows':rows,'fixtureManifest':manifests,'testSeam':'Exact quota.mjs/quota.py copied into tiny isolated roots; only policy.history points to one-file fixture history with exact metadata/SHA. Function bodies, counters, classifications, filesystem traversal and Python-Node bridge unmodified. No production test mode.','scratchRemoved':tmp,'actualGlobalAPRequests':0}
with(E/'builder-host-binding-tests01.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps({'status':'PASS','groups':len(rows),'temporaryBodyRemoved':True}))
