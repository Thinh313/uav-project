"""Strict terminal checkpoint14 evidence. Visible files never substitute a live ACK."""
import hashlib,json,re
H=re.compile('[a-f0-9]{64}')
CONTEXT=('run','epoch','boot','operator','generation','profileId')
CANONICAL='files/latest-state.json';STATUS='files/checkpoint14/status.json';LOCK='files/checkpoint14/writer.lock'
MUTABLE={CANONICAL,STATUS,LOCK}
def require(ok,why):
 if not ok:raise ValueError('CHECKPOINT14_'+why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def context_hash(c):
 require(type(c)is dict and set(c)==set(CONTEXT)and all(type(c[k])is str and c[k]for k in CONTEXT),'CONTEXT')
 return sha(json.dumps({k:c[k]for k in CONTEXT},ensure_ascii=False,separators=(',',':')).encode())
def classification(files):
 immutable={k:v for k,v in files.items()if k not in MUTABLE};mutable={k:v for k,v in files.items()if k in MUTABLE}
 for p in files:
  if p.startswith('files/checkpoint14/')and p not in MUTABLE:require(re.fullmatch(r'files/checkpoint14/terminal-[a-f0-9]{64}\.json',p)is not None,'UNKNOWN_OR_PENDING_PATH')
 archives=[p for p in immutable if p.startswith('files/checkpoint14/')];require(len(archives)<=8,'ARCHIVE8')
 return {'immutable':immutable,'mutableInfrastructure':mutable,'allFileCount':len(files),'mutableFileCount':len(mutable)}
def preserved(before,after):
 b=classification(before)['immutable'];a=classification(after)['immutable'];require(all(a.get(k)==h for k,h in b.items()),'IMMUTABLE_HISTORY_CHANGED');return b

def verify(ack,terminalRaw,statusRaw,archiveRaw,expected,source,*,observed_ns,require_review=True):
 require(type(ack)is dict and ack.get('format')=='aeris-terminal-checkpoint14-ack'and type(ack.get('version'))is int and ack['version']==1 and ack.get('phase')=='COMMITTED','LIVE_COMMITTED_ACK_REQUIRED')
 c={k:expected[k]for k in CONTEXT};ch=context_hash(c);terminal=json.loads(terminalRaw);status=json.loads(statusRaw)
 require(0<len(terminalRaw)<=65536 and 0<len(statusRaw)<=16384 and archiveRaw==terminalRaw,'EXACT_ARCHIVE_CANONICAL_BYTES')
 require(terminal.get('format')=='aeris-control01-state'and type(terminal.get('version'))is int and terminal['version']==1,'TERMINAL_SCHEMA')
 require(ack.get('failure')is None and ack.get('authorityRestorable')is False,'ACK_FAILED_OR_AUTHORITY')
 for k,v in {'context':c,'contextSHA256':ch,'ownerIdentity':c['run']+':'+c['generation'],'APKSourceSHA256':source,'terminalSHA256':sha(terminalRaw),'canonicalPath':CANONICAL,'archivePath':'files/checkpoint14/terminal-'+ch+'.json'}.items():require(ack.get(k)==v and status.get(k)==v,'ACK_STATUS_'+k)
 require(status.get('format')=='aeris-terminal-checkpoint14-status'and type(status.get('version'))is int and status['version']==1 and status.get('phase')=='CANDIDATE_COMMIT'and status.get('scope')=='CANDIDATE_ONLY_REQUIRE_LATER_LIVE_ACK'and status.get('authorityRestorable')is False,'STATUS_CANDIDATE_NOT_ACK')
 require(ack.get('statusSHA256')==sha(statusRaw),'STATUS_SHA')
 require(type(ack.get('canonicalDurableNs'))is int and type(ack.get('ackElapsedNs'))is int and type(observed_ns)is int and 0<=ack['canonicalDurableNs']<=ack['ackElapsedNs']<=observed_ns<2**63,'ACTUAL_COMPLETION_CLOCK')
 require(type(ack.get('serial'))is int and ack['serial']>0 and ack['serial']==status.get('serial'),'SERIAL')
 require(all(terminal.get(k)==c[k]for k in('run','epoch','boot','generation'))and terminal.get('closed')is True and terminal.get('authorityRestorable')is False,'TERMINAL_CONTEXT_CLOSED')
 j=terminal.get('journal',{});a=terminal.get('input',{});anchor=j.get('commitAnchor')
 require(j.get('run')==c['run']and j.get('epoch')==c['epoch']and type(j.get('records'))is int and j['records']>0 and type(j.get('head'))is str and H.fullmatch(j['head'])and j.get('publicationAllowed')is False,'TERMINAL_JOURNAL_CONTEXT')
 require(j.get('closed')is True and j.get('failed')is False and type(anchor)is str and H.fullmatch(anchor)and ack.get('terminalAnchor')==status.get('terminalAnchor')==anchor,'CLOSED_ANCHOR')
 require(a.get('consent')is False and a.get('leaseId')is None and a.get('authorityRestorable')is False,'TERMINAL_AUTHORITY')
 history=status.get('history');require(type(history)is list and 1<=len(history)<=8 and all(history[-1].get(k)==status.get(k)for k in('context','contextSHA256','ownerIdentity','APKSourceSHA256','terminalSHA256','terminalAnchor','reviewStatus','reviewSHA256')),'HISTORY')
 seen=set()
 for item in history:
  require(type(item)is dict and set(item)=={'context','contextSHA256','ownerIdentity','APKSourceSHA256','terminalSHA256','terminalAnchor','reviewStatus','reviewSHA256'},'HISTORY_SCHEMA')
  ih=context_hash(item['context']);require(item['contextSHA256']==ih and ih not in seen and item['ownerIdentity']==item['context']['run']+':'+item['context']['generation']and all(type(item.get(k))is str and H.fullmatch(item[k])for k in('APKSourceSHA256','terminalSHA256','terminalAnchor')),'HISTORY_BINDING');seen.add(ih)
  require(item['reviewStatus']in('PENDING','FAILED','DURABLE')and ((type(item.get('reviewSHA256'))is str and H.fullmatch(item['reviewSHA256']))if item['reviewStatus']=='DURABLE'else item.get('reviewSHA256')is None),'HISTORY_REVIEW_DISPOSITION')
 if require_review:require(ack.get('reviewStatus')==status.get('reviewStatus')=='DURABLE'and type(ack.get('reviewSHA256'))is str and H.fullmatch(ack['reviewSHA256'])and ack['reviewSHA256']==status.get('reviewSHA256'),'STRICT_REVIEW_DURABLE')
 return {'status':'LIVE_ACK_AND_EXACT_CANDIDATE_FILES_VERIFIED','contextSHA256':ch,'terminalSHA256':sha(terminalRaw),'statusSHA256':sha(statusRaw),'archivePath':ack['archivePath'],'terminalAnchor':anchor,'reviewSHA256':ack.get('reviewSHA256'),'diskStatusIsPositiveACK':False,'restartRestoresLiveACK':False}

def verify_live_carrier(workspace,expected,source,expected_view_epoch):
 require(type(workspace)is dict and type(expected_view_epoch)is int and expected_view_epoch>0 and type(workspace.get('viewEpoch'))is int and workspace['viewEpoch']==expected_view_epoch,'LIVE_VIEW_EPOCH')
 require(workspace.get('chosenView')in('survey','preflight','fly','review')and workspace.get('chosenView')==workspace.get('presentedView')and workspace.get('viewReady')is True and workspace.get('ownerActive')is False,'LIVE_VIEW_OR_OWNER')
 ack=workspace.get('checkpoint');observed=workspace.get('checkpointObservedElapsedNs')
 require(type(observed)is int and 0<=observed<2**63 and type(ack)is dict and ack.get('phase')=='COMMITTED'and ack.get('context')=={k:expected[k]for k in CONTEXT}and ack.get('APKSourceSHA256')==source,'ORIGINAL_SOURCE_BOUND_LIVE_CARRIER')
 require(type(ack.get('ackElapsedNs'))is int and 0<=ack['ackElapsedNs']<=observed,'ACK_AFTER_ORIGINAL_CARRIER')
 native=workspace.get('native');require(type(native)is dict and all(native.get(k)==expected[k]for k in('run','epoch','boot','generation'))and native.get('closed')is True and native.get('authorityRestorable')is False,'LIVE_NATIVE_CONTEXT_CLOSED')
 authority=native.get('input',{});journal=native.get('journal',{});require(authority.get('consent')is False and authority.get('leaseId')is None and authority.get('authorityRestorable')is False and journal.get('closed')is True and journal.get('commitAnchor')==ack.get('terminalAnchor'),'LIVE_NATIVE_AUTHORITY_ANCHOR')
 return observed

def verify_review(item,terminal_raw,review_raw):
 require(0<len(review_raw)<=131072,'REVIEW128KiB')
 c=item['context'];r=json.loads(review_raw);t=json.loads(terminal_raw);link=r.get('preflightContext',{})
 require(sha(review_raw)==item['reviewSHA256']and r.get('format')=='aeris-cockpit03-review'and type(r.get('version'))is int and r['version']==1 and r.get('id')==c['run']and r.get('authorityRestorable')is False and r.get('completionClaim')is False,'REVIEW_FILE_SHA_SCHEMA')
 require(all(r.get(k)==c[k]for k in('run','epoch','boot','generation'))and all(link.get(k)==c[k]for k in CONTEXT),'REVIEW_CONTEXT')
 require(r.get('nativeTerminalSHA256')==item['terminalAnchor']==t['journal']['commitAnchor']and r.get('nativeTerminalHead')==t['journal']['head'],'REVIEW_TERMINAL')
 require(link.get('sourceSHA256')==link.get('sourceIdentity',{}).get('sourceSHA256')==item['APKSourceSHA256']and link.get('authorityRestorable')is False,'REVIEW_SOURCE')
 require(all(type(link.get(k))is str and H.fullmatch(link[k])for k in('APSHA256','modelSHA256','configSHA256','surveySHA256'))and type(link.get('surveyRevision'))is int and link['surveyRevision']>0 and type(r.get('surveyRevision'))is int and r['surveyRevision']==link['surveyRevision']and r.get('surveySHA256')==link['surveySHA256'],'REVIEW_PREFLIGHT_SURVEY')
 return {'reviewSHA256':sha(review_raw),'fullRawReplayedByThisFileBinding':False}
def verify_history(table,status_raw):
 status=json.loads(status_raw);history=status['history'];expected=set();results=[];total=0
 for item in history:
  path='files/checkpoint14/terminal-'+context_hash(item['context'])+'.json';require(path in table,'HISTORY_ARCHIVE_MISSING');expected.add(path);tr=table[path];total+=len(tr);t=json.loads(tr)
  require(0<len(tr)<=65536 and sha(tr)==item['terminalSHA256']and all(t.get(k)==item['context'][k]for k in('run','epoch','boot','generation'))and t.get('closed')is True and t.get('authorityRestorable')is False and t.get('journal',{}).get('closed')is True and t['journal'].get('failed')is False and t['journal'].get('publicationAllowed')is False and t['journal'].get('commitAnchor')==item['terminalAnchor'],'HISTORY_EXACT_CLOSED_ARCHIVE')
  if item['reviewStatus']=='DURABLE':
   rp='files/workspace03/review-'+item['context']['run']+'-'+item['reviewSHA256']+'.json';require(rp in table,'HISTORY_REVIEW_MISSING');results.append(verify_review(item,tr,table[rp]))
 require(total<=512*1024 and expected=={k for k in table if k.startswith('files/checkpoint14/terminal-')},'HISTORY_ARCHIVE_COMPLETE_BOUND')
 return {'historicalArchives':len(expected),'declaredDurableReviewsVerified':len(results),'fullRawOrAuthorityFromReviews':False}
