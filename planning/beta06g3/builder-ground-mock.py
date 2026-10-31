"""Builder adapted actual ground policy functions, fake samples/clock and owned labelled fixtures."""
from pathlib import Path
import importlib.util,json,hashlib,datetime,copy,sys,types
p=Path('planning/beta06g3/qa-ground-soak.py');s=importlib.util.spec_from_file_location('independent_ground_g3',p);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
rows=[]
def test(n,fn):
 try:fn();rows.append({'name':n,'status':'PASS'})
 except Exception as e:rows.append({'name':n,'status':'FAIL','error':str(e)})
def refuse(fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):return
 raise AssertionError('EXPECTED_REFUSAL')
def fixture(t=0):
 sampled=(t//30000)*30000;counts={'started':10,'acknowledged':10,'failed':0,'deadline':0};o={'documentId':'document','clientId':'client','clientEpoch':1,'clientInstance':'instance','configId':'config','modelSha256':'a'*64,'planSha256':'b'*64,'foreground':True,'run':None,'seq':1,'observedAtClientMonoMs':t+100,'lifecycleDiagnostics':{'format':'aeris-beta06g2-lifecycle-diagnostic/1','desiredForeground':True,'documentHidden':False,'nativeForeground':True,'localSessionActive':True,'clientEpoch':1,'counts':counts},'mediaReadiness':{'active':True,'clockStatus':'CALIBRATED_BOUNDS','clockDegraded':False,'previewReady':True,'frameAgeMs':5,'clockSessionId':'viewer-clock','clockMappingSampledBrowserMs':sampled,'clockMappingValidUntilBrowserMs':sampled+60000}};v={'ok':True,'ageMs':10,'observation':o};state={'flight':{'run':None,'authority':None},'payloadLeaseObservation':{'leaseCount':0},'client':{'active':True,'id':'client','epoch':1,'instance':'instance','ageMs':10}};return v,state
v,state=fixture();baseline_row=g.sample_decision(v,state);binding=baseline_row['binding'];baseline={'counts':baseline_row['counts'],'clockSessionId':baseline_row['clockSessionId']}
test('strict_positive_actual_sample_function_only',lambda:g.sample_decision(*fixture(),binding,baseline))
for name,change in [
 ('viewer_restart_same_sourceconfig',lambda v,s:v['observation']['mediaReadiness'].update(clockSessionId='viewer-NEW')),
 ('lifecycle_failed_since_interval',lambda v,s:v['observation']['lifecycleDiagnostics']['counts'].update(failed=1)),
 ('new_lease_during_ground',lambda v,s:s['payloadLeaseObservation'].update(leaseCount=1)),
 ('clientTTL_exact3000',lambda v,s:s['client'].update(ageMs=3000)),
 ('frame_age_over1000',lambda v,s:v['observation']['mediaReadiness'].update(frameAgeMs=1000.01)),
 ('clock_expired_exactexpiry',lambda v,s:v['observation'].update(observedAtClientMonoMs=60000)),
 ('wrong_client_instance',lambda v,s:s['client'].update(instance='other')),
 ('native_background',lambda v,s:v['observation']['lifecycleDiagnostics'].update(nativeForeground=False)),
 ('stale_DOM_observation',lambda v,s:v.update(ageMs=1200.01)),
]:
 def negative(change=change):
  v,s=fixture();change(v,s);refuse(lambda:g.sample_decision(v,s,binding,baseline))
 test(name,negative)
source={'run':'source','boot':'sourceBoot','configId':'config','feed':'rgb','profileId':'profile'}
def records():
 r=[{'seq':1,'hostMonoMs':1,'kind':'SOURCE_CONFIGURED','data':{'serverBoot':'server','session':{**source,'viewerId':'routeOnly'}}}]
 for i,t in enumerate([30000,60000]):
  mapping={'lowerMs':1,'upperMs':2,'sampledBrowserMs':t,'validUntilBrowserMs':t+60000,'roundtripMs':1}
  r.append({'seq':len(r)+1,'hostMonoMs':t,'kind':'SOURCE_MAPPING_APPLIED','data':{'serverBoot':'server','configId':'config','sourceClock':mapping}})
  r.append({'seq':len(r)+1,'hostMonoMs':t+1,'kind':'BROWSER_CLOCK_EVENT','data':{'serverBoot':'server','role':'publisher','event':{'kind':'CALIBRATION_APPLIED','reason':'PERIODIC_30S','session':dict(source),'mapping':mapping}}})
  r.append({'seq':len(r)+1,'hostMonoMs':t+2,'kind':'BROWSER_CLOCK_EVENT','data':{'serverBoot':'server','role':'viewer','event':{'kind':'CALIBRATION_APPLIED','reason':'PERIODIC_30S','session':{'run':'viewer-clock','boot':'server','configId':'viewer-clock-1','feed':'browser-viewer','profileId':'MONOTONIC_HOST_BOUNDS'},'mapping':mapping}}})
 return r
test('two_periodic_source_and_viewer_renewals_bound_exact_config_and_mappings',lambda:g.renewals(records(),1,'viewer-clock','config','server'))
for name,change in [
 ('publisher_sameconfig_wrong_run',lambda r:r[2]['data']['event']['session'].update(run='wrong')),
 ('source_mapping_not_same_applied_clock',lambda r:r[1]['data'].update(sourceClock={**r[1]['data']['sourceClock'],'lowerMs':0})),
 ('wrong_serverboot',lambda r:r[3]['data'].update(serverBoot='other')),
 ('viewer_boot_wrong',lambda r:r[3]['data']['event']['session'].update(boot='other')),
 ('only_initial_not_periodic',lambda r:r[5]['data']['event'].update(reason='INITIAL')),
 ('clock_bound_relaxed_to21',lambda r:r[5]['data']['event']['mapping'].update(roundtripMs=21)),
]:
 def negative(change=change):
  r=copy.deepcopy(records());change(r);refuse(lambda:g.renewals(r,1,'viewer-clock','config','server'))
 test(name,negative)
fixture_dir=Path('evidence/beta06/generation03/qa-ground-fixture02');fixture_dir.mkdir(exist_ok=False);file=fixture_dir/'clock.jsonl';head='0'*64
def append(r):
 global head
 body={**r,'previousSha256':head};raw=json.dumps(body,separators=(',',':')).encode();head=hashlib.sha256(raw).hexdigest();line=raw[:-1]+b',"sha256":"'+head.encode()+b'"}\n'
 with file.open('ab')as f:f.write(line)
rawrows=records();append(rawrows[0]);clock=[0];added=0
def pause(dt):
 global added
 clock[0]+=dt
 while added<2 and clock[0]>=[30,60][added]:
  for r in rawrows[1+3*added:4+3*added]:append(r)
  added+=1
ui=types.SimpleNamespace(observation=lambda:fixture(clock[0]*1000)[0],q=types.SimpleNamespace(state=lambda:fixture(clock[0]*1000)[1]))
def collect_positive():
 result=g.collect('qa-ground-collect-mock02',file,clock=lambda:clock[0],pause=pause,ui=ui);assert result['status']=='PASS_GROUND_INTERVAL_NOT_AP_AUTHORITY'and result['observedPythonSpanS']==75;assert len(result['samples'])==151
test('actual_collect75_fake_seconds_journal_append_prefix_and151_samples_not_runtime',collect_positive)
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_BUILDER_GROUND_POLICY_AND_BOUNDED_COLLECT_MOCK_ONLY'if all(r['status']=='PASS'for r in rows)else'FAIL','sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()},'rows':rows,'fixtureClassification':'SYNTHETIC_FAKE_CLOCK_JOURNAL_NOT_ACTUAL75S_ANDROID','scope':'Actual sample/renewal/journal/collect functions with labelled tiny ownfixtures and fakeclock/ui; no listener, AP, browser, ADB or wallclock waiting. Root actual75s steady source/viewer and inputs remain required.'};out=Path(__import__('sys').argv[1]if len(__import__('sys').argv)>1 else'evidence/beta06/generation03/builder-ground02.json');out.open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'groups':len(rows),'failures':[r for r in rows if r['status']=='FAIL']}));assert result['status'].startswith('PASS')
