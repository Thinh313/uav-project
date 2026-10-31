"""Strict source/context proof predicates; receipt clocks never become AP event clocks."""
import hashlib,json,re
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
 need(ack['event']==('READY' if 'baseRevision' in request else 'STATUS'),'REQUEST_EVENT');workspace_projection(s,ready=ack['event']=='READY');return s

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
 state=snapshot['state'];need(type(state.get('renderedWorkspaceVersion'))is int and state['renderedWorkspaceVersion']>=0,'TYPED_RENDERED_WORKSPACE_VERSION');p=state.get('workspaceProjection');need(type(p)is dict and set(p)=={'version','sha256','canonicalJSON','observedElapsedNs','mutationSerial','pendingRefresh','initialized','scope'},'WORKSPACE_PROJECTION_SCHEMA')
 need(type(p['version'])is int and p['version']>=0 and type(p['mutationSerial'])is int and p['mutationSerial']>=0 and type(p['pendingRefresh'])is bool and type(p['initialized'])is bool and p['scope']=='LAST_PUBLISHED_IMMUTABLE_WORKSPACE_NOT_NEWEST_DISK_WHILE_PENDING','WORKSPACE_PROJECTION_TYPED_FIELDS')
 need(type(p['canonicalJSON'])is str and type(p['sha256'])is str and H.fullmatch(p['sha256']) and hashlib.sha256(p['canonicalJSON'].encode()).hexdigest()==p['sha256'],'ORIGINAL_CACHED_WORKSPACE_BYTES_SHA')
 need(json.dumps(strict_json(p['canonicalJSON']),sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(state.get('workspace'),sort_keys=True,separators=(',',':'),allow_nan=False),'WORKSPACE_DTO_FROM_SAME_CAPTURED_CACHE')
 if p['initialized']:need(p['version']>=1 and integer(p['observedElapsedNs']) and p['observedElapsedNs']<=snapshot['observedElapsedNs'],'ORIGINAL_PUBLISHED_WORKSPACE_CLOCK')
 else:need(p['version']==0 and p['observedElapsedNs']==-1 and type(p['observedElapsedNs'])is int,'TRUTHFUL_UNINITIALIZED_WORKSPACE')
 if ready:need(p['initialized'] is True and p['pendingRefresh'] is False and type(state.get('renderedWorkspaceVersion'))is int and state['renderedWorkspaceVersion']==p['version'],'READY_WAITED_ACTUAL_WORKSPACE_RENDER')
 return p
