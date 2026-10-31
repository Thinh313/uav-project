"""Read-only75s ground admission. No control POST, UI input, launch or automatic retry."""
from pathlib import Path
import hashlib,json,math,time,importlib.util,sys,re
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation02'
def load_ui():
 s=importlib.util.spec_from_file_location('g2_ground_ui',Path(__file__).with_name('qa-ui.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
KEYS=['documentId','clientId','clientEpoch','clientInstance','configId','modelSha256','planSha256']
def finite(v):return isinstance(v,(int,float))and not isinstance(v,bool)and math.isfinite(v)
def media_clock_id(o):return(o.get('mediaReadiness')or{}).get('clockSessionId')
def sample_decision(view,state,binding=None,baseline=None):
 assert view.get('ok')and finite(view.get('ageMs'))and 0<=view['ageMs']<=1200,'GROUND_FRESH_OBSERVATION_REQUIRED';o=view['observation'];assert o.get('foreground')is True and not o.get('run')and not state['flight'].get('run')and not state['flight'].get('authority')and(state.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0,'GROUND_NO_RUN_AUTHORITY_OR_LEASE_REQUIRED'
 current={k:o.get(k)for k in KEYS};assert all(current[k]is not None for k in KEYS),'GROUND_CONFIG_CLIENT_MODEL_REQUIRED'
 if binding is not None:assert current==binding,'GROUND_BINDING_CHANGED_NO_AP'
 c=state['client'];assert c.get('active')is True and c.get('id')==o['clientId']and c.get('epoch')==o['clientEpoch']and c.get('instance')==o['clientInstance']and finite(c.get('ageMs'))and 0<=c['ageMs']<3000,'GROUND_ACTIVE_CURRENT_CLIENT_REQUIRED'
 d=o.get('lifecycleDiagnostics')or{};assert d.get('format')=='aeris-beta06g2-lifecycle-diagnostic/1'and d.get('desiredForeground')is True and d.get('documentHidden')is False and d.get('nativeForeground')is True and d.get('localSessionActive')is True and d.get('clientEpoch')==o['clientEpoch'],'GROUND_RAW_FOREGROUND_DIAGNOSTICS_REQUIRED';counts=d.get('counts')or{};assert all(isinstance(counts.get(k),int)and counts[k]>=0 for k in ['started','acknowledged','failed','deadline']),'GROUND_DIAGNOSTIC_COUNTS_REQUIRED'
 if baseline is not None:assert media_clock_id(o)==baseline['clockSessionId'],'GROUND_VIEWER_CLOCK_SESSION_CHANGED';assert all(counts[k]==baseline['counts'][k]for k in ['failed','deadline']),'GROUND_LIFECYCLE_FAILURE_DURING_INTERVAL'
 media=o.get('mediaReadiness')or{};assert media.get('active')is True and media.get('clockStatus')=='CALIBRATED_BOUNDS'and media.get('clockDegraded')is False and media.get('previewReady')is True and finite(media.get('frameAgeMs'))and 0<=media['frameAgeMs']<=1000 and isinstance(media.get('clockSessionId'),str)and media['clockSessionId'].startswith('viewer-'),'GROUND_CURRENT_CALIBRATED_FRESH_VIEWER_REQUIRED'
 sampled=media.get('clockMappingSampledBrowserMs');until=media.get('clockMappingValidUntilBrowserMs');at=o.get('observedAtClientMonoMs');assert all(finite(v)for v in [sampled,until,at])and sampled<=at<until and abs(until-sampled-60000)<.001,'GROUND_MAPPING_ORIGINAL_VALIDITY_REQUIRED'
 return{'binding':current,'counts':counts,'clockSessionId':media['clockSessionId'],'seq':o['seq'],'observationAgeMs':view['ageMs'],'clientAgeMs':c['ageMs'],'frameAgeMs':media['frameAgeMs'],'clockMappingSampledBrowserMs':sampled,'clockMappingValidUntilBrowserMs':until,'diagnosticLastTimerLagMs':d.get('lastTimerLagMs')}
def journal_rows(path):
 p=Path(path);assert p.resolve().is_relative_to(E.resolve())and not p.is_symlink()and p.is_file()and p.stat().st_size<=4*2**20,'OWN_GENERATION_CLOCK_JOURNAL_REQUIRED';b=p.read_bytes();assert b.endswith(b'\n'),'CLOCK_JOURNAL_COMPLETE_LINES';rows=[];head='0'*64;last=-1
 for line in b.splitlines():
  row=json.loads(line);m=re.search(br',\"sha256\":\"([a-f0-9]{64})\"}$',line);assert m and hashlib.sha256(line[:m.start()]+b'}').hexdigest()==row['sha256']==m.group(1).decode(),'CLOCK_JOURNAL_EXACT_BODY_SHA';assert row['seq']==len(rows)+1 and row['previousSha256']==head and finite(row['hostMonoMs'])and row['hostMonoMs']>=last,'CLOCK_JOURNAL_CHAIN_ORDER';head=row['sha256'];last=row['hostMonoMs'];rows.append(row)
 assert rows,'CLOCK_JOURNAL_INITIAL_RECORD_REQUIRED';boots={x.get('data',{}).get('serverBoot')for x in rows};assert len(boots)==1 and None not in boots,'CLOCK_JOURNAL_ONE_SERVER_BOOT_REQUIRED';return b,rows
def renewals(rows,start_seq,clock_session,config,server_boot):
 result={'viewer':[],'publisher':[]};publisher_applied=[];source_applied=[];publisher_identities={json.dumps((r.get('data')or{}).get('event',{}).get('session'),sort_keys=True)for r in rows if r.get('kind')=='BROWSER_CLOCK_EVENT'and r.get('data',{}).get('role')=='publisher'and((r.get('data')or{}).get('event',{}).get('session')or{}).get('configId')==config};assert len(publisher_identities)==1,'GROUND_ONE_PUBLISHER_IDENTITY_FOR_CONFIG_REQUIRED';configured=[r['data']['session']for r in rows if r.get('kind')=='SOURCE_CONFIGURED'and r.get('data',{}).get('serverBoot')==server_boot and(r.get('data',{}).get('session')or{}).get('configId')==config];assert len(configured)==1,'GROUND_ONE_CONFIGURED_SOURCE_REQUIRED';source_identity={k:configured[0].get(k)for k in ['run','boot','configId','feed','profileId']};assert all(isinstance(v,str)and v for v in source_identity.values())and publisher_identities=={json.dumps(source_identity,sort_keys=True)},'GROUND_PUBLISHER_CONFIGURED_SOURCE_IDENTITY_REQUIRED'
 def mapping(v):
  assert all(finite(v.get(k))for k in ['lowerMs','upperMs','sampledBrowserMs','validUntilBrowserMs','roundtripMs']),'GROUND_CLOCK_MAPPING_FINITE';assert 0<=v['roundtripMs']<=20 and 0<=v['upperMs']-v['lowerMs']<=20 and abs(v['validUntilBrowserMs']-v['sampledBrowserMs']-60000)<.001,'GROUND_CLOCK_LIMITS_UNCHANGED'
 for r in rows:
  if r['seq']<=start_seq:continue
  d=r.get('data')or{};assert d.get('serverBoot')==server_boot,'GROUND_CLOCK_SERVER_BOOT_CHANGED'
  if r.get('kind')=='SOURCE_MAPPING_APPLIED'and d.get('configId')==config:mapping(d['sourceClock']);source_applied.append(r)
  if r.get('kind')=='BROWSER_CLOCK_EVENT'and d.get('role')in ['viewer','publisher']:
   e=d.get('event')or{}
   identity=e.get('session')or{}
   relevant=identity.get('run')==clock_session if d['role']=='viewer'else identity.get('configId')==config
   if not relevant:continue
   if d['role']=='viewer':assert identity.get('boot')==server_boot,'GROUND_CLOCK_IDENTITY_BOOT_CHANGED'
   if e.get('kind')in ['CALIBRATION_FAILED','CLOCK_EXPIRED','CLOCK_CANCELLED']:raise AssertionError('GROUND_VIEWER_CLOCK_FAILURE_DURING_INTERVAL')
   if e.get('kind')=='CALIBRATION_APPLIED'and e.get('reason')=='PERIODIC_30S':mapping(e['mapping']);(result['viewer'].append(r['seq'])if d['role']=='viewer'else publisher_applied.append(r))
 for row in publisher_applied:
  e=row['data']['event'];matches=[x for x in source_applied if x['seq']<row['seq']and x['data']['sourceClock']==e['mapping']];assert len(matches)==1,'GROUND_PUBLISHER_APPLIED_SOURCE_MAPPING_BINDING';result['publisher'].append(row['seq'])
 assert len(result['viewer'])>=2 and len(result['publisher'])>=2,'GROUND_TWO_VALID30S_RENEWALS_EACH_ROLE_REQUIRED';return result
def collect(name,clock_path,*,clock=time.monotonic,pause=time.sleep,ui=None):
 assert isinstance(name,str)and 1<=len(name)<=64 and all(c.isalnum()or c=='-'for c in name);out=E/(name+'-ground-soak.json');assert not out.exists(),'EXCLUSIVE_GROUND_SOAK_NO_RETRY';ui=ui or load_ui();report={'status':'RUNNING_NOT_AP_AUTHORITY','samples':[],'clockPath':str(clock_path),'minimumDurationS':75,'maximumDurationS':80,'noRuntimeOrControlInput':True};start=clock();binding=None;baseline=None
 try:
  first_bytes,start_rows=journal_rows(clock_path);start_seq=start_rows[-1]['seq'];report['clockBeforeSha256']=hashlib.sha256(first_bytes).hexdigest()
  while True:
   assert clock()-start<80,'GROUND_SOAK80S_BOUND';v=ui.observation();s=ui.q.state();row=sample_decision(v,s,binding,baseline);assert clock()-start<80,'GROUND_LATE_RESPONSE_AFTER80S';binding=row['binding'];baseline=baseline or {'counts':row['counts'],'clockSessionId':row['clockSessionId']};row['elapsedPythonS']=clock()-start;report['samples'].append(row);assert len(report['samples'])<=161,'GROUND_SAMPLE_BOUND'
   if clock()-start>=75:break
   pause(.5)
  raw,rows=journal_rows(clock_path);assert raw.startswith(first_bytes),'GROUND_CLOCK_JOURNAL_PREFIX_CHANGED';server_boot=start_rows[0]['data']['serverBoot'];report['renewalEvidence']=renewals(rows,start_seq,row['clockSessionId'],binding['configId'],server_boot);report.update({'status':'PASS_GROUND_INTERVAL_NOT_AP_AUTHORITY','binding':binding,'serverBoot':server_boot,'baselineCounts':baseline['counts'],'clockSessionId':row['clockSessionId'],'clockAfterSha256':hashlib.sha256(raw).hexdigest(),'observedPythonSpanS':clock()-start,'lifecycleFailuresDuringInterval':0,'apStarts':0});return report
 except BaseException as e:report['status']='REFUSED_GROUND_ADMISSION_NO_AP';report['error']=str(e);raise
 finally:report['endedPythonMonoS']=clock();out.open('x').write(json.dumps(report,indent=2)+'\n')
