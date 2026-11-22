"""Strict source/context proof predicates; receipt clocks never become AP event clocks."""
import hashlib,json,re,math
from .lifecycle import Context
from .audit.native_chain_json import strict_json
H=re.compile('[a-f0-9]{64}')
def need(ok,why):
 if not ok:raise ValueError('MISSION_PROOF:'+why)
def integer(x):return type(x)is int and 0<=x<2**63
def validate_native_ack(request,ack,snapshot_raw,*,pid,source,expected_context=None,host_sent_ns,host_received_ns):
 need(integer(host_sent_ns)and integer(host_received_ns)and 0<=host_received_ns-host_sent_ns<=10_000_000_000,'PUBLIC_NATIVE10S')
 s=strict_json(snapshot_raw);need(0<len(snapshot_raw)<=131072,'COHERENT128KiB')
 need(ack.get('format')=='aeris-mission-live-ack'and type(ack.get('version'))is int and ack['version']==1 and s.get('format')=='aeris-mission-snapshot'and type(s.get('version'))is int and s['version']==1,'FORMAT')
 need(type(pid)is int and pid>0 and ack.get('pid')==s.get('pid')==pid and type(ack.get('pid'))is int,'ACTUAL_PROCESS_PID')
 for k in('requestNonce','processEpoch','revision','sourceSHA256','context','viewEpoch'):
  need(k in ack and k in s and json.dumps(ack[k],sort_keys=True,separators=(',',':'))==json.dumps(s[k],sort_keys=True,separators=(',',':')),'ACK_CARRIER_'+k)
 need(ack['requestNonce']==request['requestNonce']and ack['sourceSHA256']==source and H.fullmatch(source)and re.fullmatch('[a-f0-9]{32}',ack['processEpoch'])is not None,'NONCE_SOURCE_EPOCH')
 need(type(ack['revision'])is int and ack['revision']>0 and type(ack['viewEpoch'])is int and ack['viewEpoch']>0,'REVISION_VIEW')
 need(ack.get('snapshotSHA256')==hashlib.sha256(snapshot_raw).hexdigest()and ack.get('snapshotPath')in('files/runtime/response.json','files/runtime/current.json'),'EXACT_CARRIER_HASH_PATH')
 need(ack.get('event')==s.get('event') and ack.get('event') in ('STATUS','READY'),'EXPLICIT_RESPONSE_EVENT')
 need(ack['snapshotPath']=='files/runtime/response.json','REQUEST_RESPONSE_SLOT')
 need(all(integer(ack.get(k)) for k in ('requestReceivedElapsedNs','committedElapsedNs','ackElapsedNs','emittedElapsedNs')) and integer(s.get('observedElapsedNs')) and type(s.get('requestReceivedElapsedNs')) is int and s['requestReceivedElapsedNs']==ack['requestReceivedElapsedNs'],'MANDATORY_ORIGINAL_CLOCKS')
 need(ack['requestReceivedElapsedNs']<=s['observedElapsedNs']<=ack['committedElapsedNs']<=ack['ackElapsedNs']<=ack['emittedElapsedNs'] and ack['emittedElapsedNs']-ack['requestReceivedElapsedNs']<=10_000_000_000,'ORIGINAL_RECEIPT_EMISSION_DEADLINE')
 need(type(s.get('state')) is dict and type(s.get('layout')) is dict and s['state'].get('viewEpoch')==ack['viewEpoch'] and type(s['state'].get('viewEpoch')) is int,'COHERENT_SELECTED_VIEW')
 for layout_key,state_key in (('view','chosenView'),('presentedView','presentedView'),('viewReady','viewReady'),('ownerActive','ownerActive')):
  need(layout_key in s['layout'] and state_key in s['state'] and json.dumps(s['layout'][layout_key],sort_keys=True)==json.dumps(s['state'][state_key],sort_keys=True),'COHERENT_LAYOUT_'+layout_key)
 need(type(s['state'].get('viewReady')) is bool and type(s['state'].get('ownerActive')) is bool and integer(s['layout'].get('sourceNs')) and s['layout']['sourceNs']<=s['observedElapsedNs'],'LAYOUT_ORIGINAL_CLOCK_AND_FLAGS')
 if expected_context is not None:need(ack['context']==expected_context,'SELECTED_GENERATION_CONTEXT')
 if request.get('processEpoch')is not None:
  need(ack['processEpoch']==request['processEpoch']and ack['viewEpoch']==request['viewEpoch']and ack['revision']>request['baseRevision'],'BOOTSTRAP_ORIGINAL_BASE')
 need(ack['event']==('READY' if 'baseRevision' in request else 'STATUS'),'REQUEST_EVENT');workspace_projection(s,ready=ack['event']=='READY')
 if 'navigation'in s['layout']:navigation_measurement(s)
 if 'trajectoryProjection'in s['state']:trajectory_projection(s)
 return s

def native_sealed(snapshot,context):
 need(snapshot.get('context')==context,'SEAL_CONTEXT');state=snapshot.get('state',{});native=state.get('native',{});j=native.get('journal',{});a=native.get('input',{});lc=native.get('lifecycle',{})
 need(state.get('ownerActive')is False and state.get('authorityRestorable')is False and snapshot.get('lifecycle',{}).get('phase')in('NATIVE_SEALED','TERMINAL_DURABLE','REVIEW_READY') and snapshot['lifecycle'].get('failure')is None,'SOURCE_DERIVED_OWNER_NO_LONGER_ACTIVE')
 need(all(native.get(k)==context[k]for k in('run','epoch','boot','generation')),'NATIVE_OWNER_CONTEXT')
 need(native.get('closed')is True and native.get('authorityRestorable')is False and j.get('closed')is True and j.get('failed')is False and type(j.get('commitAnchor'))is str and H.fullmatch(j['commitAnchor']),'ORIGINAL_CONTROL_JOURNAL_SEALED')
 need(a.get('consent')is False and a.get('leaseId')is None and a.get('authorityRestorable')is False and native.get('rcOverrideActiveLocally')is False,'REVOKED_NOT_QUEUED')
 need(integer(lc.get('resourcesClosedNs')) and lc.get('run')==context['run'] and lc.get('generation')==context['generation'] and lc.get('leaseActive') is False and lc.get('leaseId') is None and j.get('run')==context['run'] and j.get('epoch')==context['epoch'],'NATIVE_RESOURCES_CLOSED_BARRIER')
 return {'nativeJournalAnchor':j['commitAnchor'],'snapshotRevision':snapshot['revision'],'processEpoch':snapshot['processEpoch'],'resourcesClosedNs':lc['resourcesClosedNs'],'checkpointOrReviewUsedAsSeal':False}

def evidence_durable(snapshot,context):
 proof=native_sealed(snapshot,context);cp=snapshot.get('state',{}).get('checkpoint',{})
 need(cp.get('format')=='aeris-terminal-checkpoint14-ack'and cp.get('phase')=='COMMITTED'and cp.get('context')==context and cp.get('reviewStatus')=='DURABLE'and type(cp.get('reviewSHA256'))is str and H.fullmatch(cp['reviewSHA256'])and cp.get('terminalAnchor')==proof['nativeJournalAnchor'],'CHECKPOINT_REVIEW_LIVE_DURABLE')
 need(cp.get('APKSourceSHA256')==snapshot['sourceSHA256'] and cp.get('authorityRestorable') is False and cp.get('ownerIdentity')==context['run']+':'+context['generation'] and type(cp.get('version')) is int and cp['version']==1,'CHECKPOINT_SOURCE_OWNER')
 need(all(integer(cp.get(k)) for k in ('canonicalDurableNs','ackElapsedNs')) and integer(snapshot['state'].get('checkpointObservedElapsedNs')) and cp['canonicalDurableNs']<=cp['ackElapsedNs']<=snapshot['state']['checkpointObservedElapsedNs']<=snapshot['observedElapsedNs'],'CHECKPOINT_ORIGINAL_CLOCKS')
 need(all(type(cp.get(k)) is str and H.fullmatch(cp[k]) for k in ('terminalSHA256','statusSHA256','reviewSHA256')),'CHECKPOINT_HASHES')
 proof.update(reviewSHA256=cp['reviewSHA256'],terminalSHA256=cp['terminalSHA256'],statusSHA256=cp['statusSHA256']);return proof

def workspace_projection(snapshot,*,ready=False):
 state=snapshot['state'];need(type(state.get('renderedWorkspaceVersion'))is int and state['renderedWorkspaceVersion']>=0,'TYPED_RENDERED_WORKSPACE_VERSION');p=state.get('workspaceProjection')
 legacy={'version','sha256','canonicalJSON','observedElapsedNs','mutationSerial','pendingRefresh','initialized','scope'}
 public=type(p)is dict and p.get('format')=='aeris-public-workspace-projection'
 fields=legacy|{'format','projectionVersion','sourceCacheSHA256','sourceCacheBytes','encoding'}if public else legacy
 need(type(p)is dict and set(p)==fields,'WORKSPACE_PROJECTION_SCHEMA')
 scope='PUBLIC_BOUNDED_VIEW_FROM_IMMUTABLE_FULL_WORKSPACE_CACHE'if public else'LAST_PUBLISHED_IMMUTABLE_WORKSPACE_NOT_NEWEST_DISK_WHILE_PENDING'
 need(type(p['version'])is int and p['version']>=0 and type(p['mutationSerial'])is int and p['mutationSerial']>=0 and type(p['pendingRefresh'])is bool and type(p['initialized'])is bool and p['scope']==scope,'WORKSPACE_PROJECTION_TYPED_FIELDS')
 need(type(p['canonicalJSON'])is str and type(p['sha256'])is str and H.fullmatch(p['sha256']) and hashlib.sha256(p['canonicalJSON'].encode()).hexdigest()==p['sha256'],'ORIGINAL_CACHED_WORKSPACE_BYTES_SHA')
 need(json.dumps(strict_json(p['canonicalJSON']),sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(state.get('workspace'),sort_keys=True,separators=(',',':'),allow_nan=False),'WORKSPACE_DTO_FROM_SAME_CAPTURED_CACHE')
 if public:
  need(type(p['projectionVersion'])is int and p['projectionVersion']==1 and type(p['sourceCacheSHA256'])is str and H.fullmatch(p['sourceCacheSHA256'])is not None and type(p['sourceCacheBytes'])is int and 0<p['sourceCacheBytes']<=131072 and p['encoding']=='AERIS_PRINTABLE_ASCII_SORTED_JSON_V1','PUBLIC_WORKSPACE_ORIGINAL_SOURCE_PROVENANCE')
  w=state['workspace'];need(type(w)is dict and set(w)=={'draft','draftSHA256','reviews','authorityRestorable','format','projectionVersion','scope','encoding'}and w['format']=='aeris-public-workspace-view'and type(w['projectionVersion'])is int and w['projectionVersion']==1 and w['scope']=='PUBLIC_REVIEW_METADATA_REFERENCES_FULL_PRIVATE_RECORDS_RETAINED'and w['encoding']=='AERIS_PRINTABLE_ASCII_SORTED_JSON_V1'and w['authorityRestorable']is False and type(w['reviews'])is list and len(w['reviews'])<=16,'PUBLIC_WORKSPACE_VIEW_SCHEMA')
  runs=set()
  for review in w['reviews']:
   need(type(review)is dict and set(review)=={'id','run','status','reviewCacheSHA256','reviewCacheBytes','scope','acceptanceEvidence'},'PUBLIC_REVIEW_EXACT_REFERENCE')
   need(all(type(review[k])is str and 0<len(review[k])<=128 and all(32<=ord(c)<=126 for c in review[k])for k in('id','run','status'))and review['id']==review['run']and review['run']not in runs,'PUBLIC_REVIEW_IDENTITY_NO_DUPLICATE');runs.add(review['run'])
   need(type(review['reviewCacheSHA256'])is str and H.fullmatch(review['reviewCacheSHA256'])is not None and type(review['reviewCacheBytes'])is int and 0<review['reviewCacheBytes']<=131072 and review['scope']=='REFERENCE_NOT_ACCEPTANCE'and review['acceptanceEvidence']is False,'PUBLIC_REVIEW_REFERENCE_NOT_ACCEPTANCE')
 if p['initialized']:need(p['version']>=1 and integer(p['observedElapsedNs']) and p['observedElapsedNs']<=snapshot['observedElapsedNs'],'ORIGINAL_PUBLISHED_WORKSPACE_CLOCK')
 else:need(p['version']==0 and p['observedElapsedNs']==-1 and type(p['observedElapsedNs'])is int,'TRUTHFUL_UNINITIALIZED_WORKSPACE')
 if ready:need(p['initialized']is True and p['pendingRefresh']is False and type(state.get('renderedWorkspaceVersion'))is int and state['renderedWorkspaceVersion']==p['version'],'READY_WAITED_ACTUAL_WORKSPACE_RENDER')
 return p

def preflight_context_canonical(value):
 """AERIS_PRINTABLE_ASCII_SORTED_JSON_V1, matching native Values/Json.quote.

 Restrict this version explicitly; never guess UTF-8/C0/float codecs. Full
 immutable review/link bytes remain the acceptance evidence in the TAR.
 """
 def check(v,depth=0):
  need(depth<=16,'PREFLIGHT_REFERENCE_CANONICAL_DEPTH')
  if type(v)is dict:
   need(len(v)<=256,'PREFLIGHT_REFERENCE_CANONICAL_MAP_BOUND')
   for k,item in v.items():need(type(k)is str and all(32<=ord(c)<=126 for c in k),'PREFLIGHT_REFERENCE_ASCII_KEY');check(item,depth+1)
  elif type(v)is str:need(all(32<=ord(c)<=126 for c in v),'PREFLIGHT_REFERENCE_ASCII_STRING')
  elif type(v)is bool or v is None:pass
  elif type(v)is int:need(-2**63<=v<2**63,'PREFLIGHT_REFERENCE_INTEGER64')
  else:need(False,'PREFLIGHT_REFERENCE_UNSUPPORTED_TYPE')
 need(type(value)is dict,'PREFLIGHT_REFERENCE_OBJECT');check(value)
 raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();need(0<len(raw)<=131072,'PREFLIGHT_REFERENCE_CANONICAL_BYTES');return raw


def navigation_measurement(snapshot,*,action=None,receipt=None,before_tap_ns=None):
 """Original ticket clocks stay native; whole host request bounds tap age."""
 n=snapshot.get('layout',{}).get('navigation');state=snapshot['state']
 trajectory_projection(snapshot)
 need(workspace_projection(snapshot).get('format')=='aeris-public-workspace-projection','NAVIGATION_PUBLIC_WORKSPACE_PROJECTION')
 fields={'format','version','ready','issue','ticket','requestNonce','startedElapsedNs','completedElapsedNs','sourceSHA256','pid','processEpoch','viewEpoch','context','bootstrapSHA256','view','presentedView','workspaceVersion','renderedWorkspaceVersion','foreground','windowFocus','webView','dom','targets'}
 need(type(n)is dict and set(n)==fields and n['format']=='aeris-visible-navigation'and type(n['version'])is int and n['version']==1,'NAVIGATION_EXACT_SCHEMA')
 need(len(json.dumps(n,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())<=4096,'NAVIGATION4KiB')
 need(type(n['ready'])is bool and type(n['foreground'])is bool and type(n['windowFocus'])is bool and n['issue']in('NONE','NAVIGATION_PUBLISH_CHANGED_OR_LATE','NAVIGATION_PAYLOAD_BOUND','NAVIGATION_BUSY','NAVIGATION_CALLBACK_TIMEOUT','NAVIGATION_CALLBACK_INVALID','NAVIGATION_NATIVE_UNAVAILABLE','NAVIGATION_CAPTURE_CHANGED'),'NAVIGATION_FLAGS')
 need(type(n['ticket'])is str and re.fullmatch('[a-f0-9]{32}',n['ticket'])is not None and type(n['requestNonce'])is str and re.fullmatch('[a-f0-9]{32}',n['requestNonce'])is not None and n['requestNonce']==snapshot['requestNonce'],'NAVIGATION_REQUEST_TICKET')
 need(all(k in snapshot for k in('sourceSHA256','pid','processEpoch','viewEpoch','context','bootstrapSHA256')),'NAVIGATION_SNAPSHOT_BINDING_FIELDS')
 for k in('sourceSHA256','pid','processEpoch','viewEpoch','context','bootstrapSHA256'):
  need(type(n[k])is type(snapshot[k])and json.dumps(n[k],sort_keys=True,separators=(',',':'))==json.dumps(snapshot[k],sort_keys=True,separators=(',',':')),'NAVIGATION_CARRIER_'+k)
 need(type(n['pid'])is int and n['pid']>0 and type(n['viewEpoch'])is int and n['viewEpoch']>0 and type(n['sourceSHA256'])is str and H.fullmatch(n['sourceSHA256'])is not None and type(n['processEpoch'])is str and re.fullmatch('[a-f0-9]{32}',n['processEpoch'])is not None and(n['bootstrapSHA256']is None or type(n['bootstrapSHA256'])is str and H.fullmatch(n['bootstrapSHA256'])is not None)and n['view']in('survey','preflight','fly','review')and n['presentedView']in(None,'survey','preflight','fly','review'),'NAVIGATION_TYPED_IDENTITY')
 need(all(integer(n[k])for k in('startedElapsedNs','completedElapsedNs','workspaceVersion','renderedWorkspaceVersion'))and snapshot['requestReceivedElapsedNs']<=n['startedElapsedNs']<=n['completedElapsedNs']<=snapshot['observedElapsedNs'],'NAVIGATION_ORIGINAL_TICKET_CLOCK')
 need(n['view']==state['chosenView']and n['presentedView']==state['presentedView']and n['workspaceVersion']==state['workspaceProjection']['version']and n['renderedWorkspaceVersion']==state['renderedWorkspaceVersion'],'NAVIGATION_CURRENT_PRESENTATION')
 if not n['ready']:
  need(n['issue']!='NONE'and n['webView']is None and n['dom']is None and n['targets']=={},'NAVIGATION_UNAVAILABLE_NO_GEOMETRY');need(action is None,'NAVIGATION_UNAVAILABLE');return n
 workspace_projection(snapshot,ready=True)
 need(n['issue']=='NONE'and n['foreground']is True and n['windowFocus']is True and state['viewReady']is True and n['view']==n['presentedView']and n['workspaceVersion']==n['renderedWorkspaceVersion']and n['completedElapsedNs']-n['startedElapsedNs']<=100_000_000,'NAVIGATION_READY_FRESH_VISIBLE')
 w=n['webView'];d=n['dom'];targets=n['targets']
 def number(v):return type(v)in(int,float)and math.isfinite(v)
 def rect(v):return type(v)is list and len(v)==4 and all(type(x)is int and 0<=x<8192 for x in v)
 need(type(w)is dict and set(w)=={'bounds','visibleBounds','width','height','scale','scrollX','scrollY','orientation','identityTransform'},'NAVIGATION_WEBVIEW_SCHEMA')
 need(rect(w['bounds'])and rect(w['visibleBounds'])and w['bounds']==w['visibleBounds'],'NAVIGATION_WEBVIEW_VISIBLE_RECT')
 left,top,right,bottom=w['bounds'];need(left<right and top<bottom and type(w['width'])is int and type(w['height'])is int and w['width']==right-left and w['height']==bottom-top,'NAVIGATION_WEBVIEW_DIMENSIONS')
 need(number(w['scale'])and 0<w['scale']<=8 and type(w['scrollX'])is int and w['scrollX']==0 and type(w['scrollY'])is int and w['scrollY']==0 and type(w['orientation'])is int and w['orientation']in(1,2)and w['identityTransform']is True,'NAVIGATION_NATIVE_TRANSFORM')
 need(type(d)is dict and set(d)=={'width','height','dpr','scrollX','scrollY','visualScale','offsetX','offsetY','viewEpoch','view','workspaceVersion','dirty','ownerActive'},'NAVIGATION_DOM_SCHEMA')
 need(all(number(d[k])and 0<d[k]<=8192 for k in('width','height','dpr'))and d['dpr']<=8 and all(number(d[k])and d[k]==0 for k in('scrollX','scrollY','offsetX','offsetY'))and number(d['visualScale'])and d['visualScale']==1,'NAVIGATION_DOM_VIEWPORT')
 need(type(d['viewEpoch'])is int and d['viewEpoch']==n['viewEpoch']and d['view']==n['view']and type(d['workspaceVersion'])is int and d['workspaceVersion']==n['workspaceVersion']and type(d['dirty'])is bool and type(d['ownerActive'])is bool and d['ownerActive']==state['ownerActive'],'NAVIGATION_DOM_CURRENT_VERSION')
 need(abs(w['scale']*d['width']-w['width'])<=1 and abs(w['scale']*d['height']-w['height'])<=1,'NAVIGATION_PROVABLE_CSS_SCREEN_SCALE')
 ids={'nav-survey','nav-preflight','nav-fly','nav-review'};need(type(targets)is dict and set(targets)==ids,'NAVIGATION_EXACT_FOUR_TARGETS')
 for name,node in targets.items():
  need(type(node)is dict and set(node)=={'cssBounds','bounds','visible','enabled','hit','currentaction'}and node['currentaction']==name and all(type(node[k])is bool for k in('visible','enabled','hit')),'NAVIGATION_TARGET_SCHEMA')
  c=node['cssBounds'];b=node['bounds'];need(type(c)is list and len(c)==4 and all(number(v)and -8192<v<8192 for v in c)and rect(b),'NAVIGATION_TARGET_BOUNDS')
  expected=[math.ceil(left+c[0]*w['scale']),math.ceil(top+c[1]*w['scale']),math.floor(left+c[2]*w['scale']),math.floor(top+c[3]*w['scale'])]
  need(b==expected,'NAVIGATION_ORIGINAL_CSS_SCREEN_MAPPING')
  need(0<=c[0]<c[2]<=d['width']and 0<=c[1]<c[3]<=d['height']and left<=b[0]<b[2]<=right and top<=b[1]<b[3]<=bottom,'NAVIGATION_VISIBLE_TARGET_RECT')
 if action is not None:
  need(action in ids and d['dirty']is False,'NAVIGATION_FIXED_ACTION_NO_UNSAVED_EDITS');node=targets[action];need(node['visible']is True and node['enabled']is True and node['hit']is True,'NAVIGATION_ACTIONABLE_TARGET')
  need(not state['ownerActive']or action=='nav-'+n['view']or action=='nav-fly','NAVIGATION_ORIGINAL_ACTIVE_OWNER_POLICY')
 if before_tap_ns is not None:
  need(type(receipt)is dict and receipt.get('action')=='STATUS'and receipt.get('request',{}).get('requestNonce')==n['requestNonce']and type(before_tap_ns)is int and receipt['hostSentNs']<=receipt['hostReceivedNs']<=before_tap_ns and before_tap_ns-receipt['hostSentNs']<=200_000_000 and before_tap_ns-receipt['hostReceivedNs']<=200_000_000,'NAVIGATION_WHOLE_REQUEST_AND_DISPATCH200MS')
 return n


def trajectory_projection(snapshot):
 """Public summary is not raw/frame/trajectory acceptance evidence."""
 state=snapshot['state'];p=state.get('trajectoryProjection')
 need('trajectory'not in state and type(p)is dict and set(p)=={'format','version','presentationPointCount','firstNativeRecordNs','lastNativeRecordNs','scope','acceptanceEvidence'},'TRAJECTORY_PROJECTION_EXACT_SCHEMA')
 need(p['format']=='aeris-public-trajectory-projection'and type(p['version'])is int and p['version']==1 and type(p['presentationPointCount'])is int and 0<=p['presentationPointCount']<=512 and p['scope']=='SAMPLED_PRESENTATION_BUFFER_NOT_FULL_RAW'and p['acceptanceEvidence']is False,'TRAJECTORY_PROJECTION_NOT_ACCEPTANCE')
 if p['presentationPointCount']==0:need(p['firstNativeRecordNs']is None and p['lastNativeRecordNs']is None,'TRAJECTORY_EMPTY_CLOCKS')
 else:need(integer(p['firstNativeRecordNs'])and integer(p['lastNativeRecordNs'])and p['firstNativeRecordNs']<=p['lastNativeRecordNs']<=snapshot['observedElapsedNs'],'TRAJECTORY_ORIGINAL_NATIVE_CLOCKS')
 return p
