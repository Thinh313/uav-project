"""Exact runtime remainder normalization plus isolated actual identity predicate, no subprocess."""
from pathlib import Path
import ast,json,hashlib,datetime,copy
p=Path('pilot/beta06g2/flight/runtime.py');old=Path('pilot/beta06/flight/runtime.py').read_text();s=p.read_text();tree=ast.parse(s);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='qualified_identity');ns={'Path':Path,'IMAGE':'rtr-aeris-sim32-trace-builder@sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84','AP':Path.cwd()/'evidence/sim32-instrument01/direct-uncorrected-source/arducopter'};exec(compile(ast.Module(body=[function],type_ignores=[]),'<actualidentity>','exec'),ns)
rows=[]
def test(n,f):
 try:f();rows.append({'name':n,'status':'PASS'})
 except Exception as e:rows.append({'name':n,'status':'FAIL','error':str(e)})
def predicate_fixture():return {'Image':ns['IMAGE'].split('@')[1],'Config':{'Entrypoint':None,'Cmd':['/aeris/arducopter','-w','--model','quad','--speedup','1'],'Env':['PATH=/bin','AERIS_DIRECT_TRACE=0']},'HostConfig':{'NanoCpus':1000000000,'Memory':268435456,'CapDrop':['ALL'],'CapAdd':None,'Privileged':False,'SecurityOpt':['no-new-privileges'],'NetworkMode':'bridge'},'Mounts':[{'Destination':'/aeris/arducopter','Type':'bind','RW':False,'Source':str(ns['AP'])}]}
test('actual_runtime_identity_function_noDocker_positive_fixture',lambda:ns['qualified_identity'](predicate_fixture()))
for name,fn in [('wrongimage',lambda i:i.update(Image='other')),('preload',lambda i:i['Config']['Env'].append('LD_PRELOAD=bad')),('trace1',lambda i:i['Config']['Env'].append('AERIS_DIRECT_TRACE=1')),('APtrace',lambda i:i['Config']['Env'].append('AERIS_AP_TRACE=/state/huge')),('wrongCPU',lambda i:i['HostConfig'].update(NanoCpus=2000000000)),('wrongmemory',lambda i:i['HostConfig'].update(Memory=512*2**20)),('rwmount',lambda i:i['Mounts'][0].update(RW=True)),('wrongbinarypath',lambda i:i['Mounts'][0].update(Source='/old/arducopter')),('entrywrapper',lambda i:i['Config']['Cmd'].__setitem__(0,'entry.sh'))]:
 def f(fn=fn):
  i=predicate_fixture();fn(i)
  try:ns['qualified_identity'](i)
  except(AssertionError,ValueError,KeyError):return
  raise AssertionError('EXPECTED_IDENTITY_REFUSAL')
 test(name,f)
def normalized():
 lines=s.splitlines(keepends=True);r=''.join(lines[:function.lineno-1]+lines[function.end_lineno:]);oldlines=old.splitlines();newlines=r.splitlines()
 # Replace only explicitly enumerated profile/bootstrap identity lines; all other runtime including AP540/fault/resource loop stays exact.
 for prefix in ['R=Path(__file__)','i=json.loads(command([DOCKER,\'image\'','a=[DOCKER,',' put(out/\'launch.json\'']:
  matching=[l for l in oldlines if l.startswith(prefix)];assert len(matching)==1,prefix
  indices=[i for i,l in enumerate(newlines)if l.startswith(prefix)];assert len(indices)==1,prefix;newlines[indices[0]]=matching[0]
 r='\n'.join(newlines)+'\n';r=r.replace("R/'evidence/beta06/generation02/flight-pins.json'","R/'evidence/beta06/flight-pins.json'").replace('assert sha(AP)==BINARY',"assert sha(R/'runtime/sitl/arducopter')==BINARY").replace('qualified_identity(observed);','').replace('qualified_identity(after);','')
 assert r==old,'UNENUMERATED_RUNTIME_SEMANTIC_DIFF'
test('all_nonqualified_runtime_algorithm_bytes_exact_AP540_speedup1_resources_faults_noReconnect',normalized)
env=Path('evidence/beta06/generation02/root-cached-image-env01.json');v=json.loads(env.read_text());test('actualRootreadonly_imageEnv_ONLY_PATH_no_preload_or_trace',lambda:__import__('builtins').exec("assert v['architecture']=='arm64' and v['os']=='linux' and v['imageId']==ns['IMAGE'].split('@')[1];assert all(x.startswith('PATH=')for x in v['config']['Env'])"))
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_ARM_RUNTIME_REMAINDER_AND_IDENTITY_PREDICATE_SOURCE_MOCK_ONLY'if all(x['status']=='PASS'for x in rows)else'FAIL','sources':{str(q):hashlib.sha256(q.read_bytes()).hexdigest()for q in[p,Path('pilot/beta06/flight/runtime.py'),env]},'rows':rows,'scope':'Actual identity function extractedAST with fake inspectvalues; exact remainder byte normalization excludes enumerated qualified metadata/command identity lines. No runtime import/top-level execution, Docker, socket, AP or build. Actual inspect/pins/firmware beforeARM mandatory.'};out=Path(__import__('sys').argv[1]if len(__import__('sys').argv)>1 else'evidence/beta06/generation02/qa-runtime-arm-source01.json');out.open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'groups':len(rows),'failures':[x for x in rows if x['status']=='FAIL']}));assert r['status'].startswith('PASS')
