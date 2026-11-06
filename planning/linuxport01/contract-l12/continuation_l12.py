"""LINUXPORT01 continuation contract for the state after g106 attempt 1 (87 files, 9 dirs).

Team code, not the owner's. contract-l10/continuation_l10.py with the state shape moved
on by the one closed-unused native session g106 attempt 1 added (generation 11, a third
new journal, three more status files), pinned to the team's exact values taken from the
team m802 raw (evidence/betarc01/m802, read-only capture with a normal SDK close).
Read-only: no device, actor, APPLY, archive, resume or authority. It does not use the
post-g103 75-file decoder (reconcile_h7.reconcile). m802 is an observation anchor only;
passing this contract grants nothing by itself.

Two independent readers must agree on every tar: this module's own registry
replay, and the owner's archive_verifier17.verify_archive_index.
"""
from pathlib import Path
import base64,hashlib,json,re,sys,tarfile
R=Path(__file__).resolve().parents[3]
for p in(str(R/'planning/nativejournal17'),str(R)):
 if p not in sys.path:sys.path.insert(0,p)
from planning.betarc01.tar_profile_h7.reader import scan as strict_scan,native_tar
from planning.nativejournal17.archive_verifier17 import verify_archive_index

FORMAT='aeris-linuxport01-m802-continuation-pin'
PROOF='aeris-linuxport01-m802-continuation-proof'
INDEX_MAGIC=b'AERIS_JOURNAL_REGISTRY17_V1\n';AJ=b'AERIS_INPUT_JOURNAL_V2\n';ZERO='0'*64;UID=10141
REGISTRY='files/product-input-registry17/highwater.aj17';ACTIVE='files/product-input01/';ARCHIVES='files/product-input-archives17/'
LIFECYCLE='files/product-input-lifecycle17/';STATUS='files/product-observations01/';WORKSPACE='files/betasim-workspace01/'
ROW_TYPES=['ENROLL_BEGIN','ENROLL_COMMIT','REQUEST_RESERVE','ARCHIVE_BEGIN','ARCHIVE_COMMIT','REQUEST_RECEIPT']+['GEN_BEGIN','GEN_COMMIT','CLOSE']*3
FILES=87;LIFETIME=11;NEW=3
META=('type','mode','uid','gid','mtime','bytes','sha256')

class ContractError(ValueError):pass
def need(v,name):
 if not v:raise ContractError('CONTINUATION_L12_'+name)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()

def read_tar(path,digest):
 """Owner's strict SAFE_GNU_LONGNAME_L_V1 transport scan, then every regular body joined to it."""
 p=Path(path);need(p.is_file()and not p.is_symlink(),'RAW_REGULAR');need(sha(p.read_bytes())==digest,'RAW_SHA')
 shape=strict_scan(p);entries={e['path']:{k:e[k]for k in META}for e in shape['entries']};data={}
 with tarfile.open(p,'r:')as t:
  for m in t:
   if m.isfile():
    b=t.extractfile(m).read();need(m.name in entries and sha(b)==entries[m.name]['sha256'],'TAR_BODY_JOIN');data[m.name]=b
 need(set(data)=={n for n,e in entries.items()if e['type']=='regular'},'TAR_REGULAR_SET');return entries,data

def replay(index):
 """Own Registry17 replay: framing, sequence, previous-head chain, row hash, canonical base64."""
 need(type(index)is bytes and index.startswith(INDEX_MAGIC)and index.endswith(b'\n')and len(index)<=8*2**20,'REGISTRY_FRAME')
 rows=[];head=ZERO;at=len(INDEX_MAGIC)
 for n,line in enumerate(index[at:].split(b'\n')[:-1],1):
  need(len(line)<4096 and all(32<=x<=126 or x==9 for x in line),'REGISTRY_ROW_ASCII');v=line.decode('ascii').split('\t')
  need(len(v)==5 and v[0]==str(n)and v[1]==head,'REGISTRY_SEQUENCE_CHAIN');need(sha('\t'.join(v[:4]).encode())==v[4],'REGISTRY_ROW_HASH')
  payload=base64.b64decode(v[3],validate=True);need(base64.b64encode(payload).decode()==v[3],'REGISTRY_PAYLOAD_CANONICAL')
  at+=len(line)+1;rows.append({'sequence':n,'type':v[2],'fields':payload.decode('ascii').split('\t'),'hash':v[4],'end':at});head=v[4]
 return rows,head

def members(f,start):
 n=int(f[start]);need(1<=n<=8 and len(f)==start+1+5*n,'REGISTRY_MEMBER_GROUP')
 return[dict(generation=f[start+1+5*i],bytes=int(f[start+2+5*i]),sha256=f[start+3+5*i],disposition=f[start+4+5*i],proofSHA256=f[start+5+5*i])for i in range(n)]

def registry_state(rows):
 """Counters and members from the replayed rows; refuses any pending transaction or unknown row."""
 c=dict.fromkeys(('reservedGenerations','committedGenerations','reservedRecords','committedRecords','reservedArchives','committedArchives','reservedRequests','committedReceipts'),0)
 enrolled=[];new=[];closed={};archives={};requests={};pending=None
 for r in rows:
  t,f=r['type'],r['fields']
  if t=='ENROLL_BEGIN':
   need(r['sequence']==1 and pending is None,'REGISTRY_ENROLL_ORDER');enrolled=members(f,3);need(len(enrolled)==8,'REGISTRY_ENROLL_EXACT8');c['reservedGenerations']+=8;c['reservedRequests']+=1;pending=r
  elif t=='ENROLL_COMMIT':need(pending is not None and pending['type']=='ENROLL_BEGIN'and len(f)==25 and f[0]==pending['hash'],'REGISTRY_ENROLL_COMMIT');c['committedGenerations']+=8;pending=None
  elif t=='REQUEST_RESERVE':
   need(pending is None and len(f)==3 and f[2]in('0','1')and f[0]not in requests,'REGISTRY_REQUEST_RESERVE');requests[f[0]]={'operation':f[1],'row':r['hash'],'receipt':None}
   if f[2]=='0':c['reservedRequests']+=1
  elif t=='REQUEST_RECEIPT':
   need(len(f)==5 and f[1]in requests and requests[f[1]]['row']==f[0]and requests[f[1]]['receipt']is None,'REGISTRY_REQUEST_RECEIPT');requests[f[1]]['receipt']=dict(path='files/'+f[2],bytes=int(f[3]),sha256=f[4]);c['committedReceipts']+=1
  elif t=='GEN_BEGIN':need(pending is None and len(f)==1,'REGISTRY_GEN_BEGIN');c['reservedGenerations']+=1;pending=r
  elif t=='GEN_COMMIT':
   need(pending is not None and pending['type']=='GEN_BEGIN'and len(f)==6 and f[0]==pending['hash']and f[1]==pending['fields'][0]and f[2]==str(len(AJ))and f[3]==ZERO,'REGISTRY_GEN_COMMIT');new.append(f[1]);c['committedGenerations']+=1;pending=None
  elif t=='CLOSE':need(pending is None and len(f)==7 and f[0]not in closed,'REGISTRY_CLOSE');closed[f[0]]=dict(records=int(f[1]),bytes=int(f[2]),head=f[3],disposition=f[4],sha256=f[5],proofSHA256=f[6])
  elif t=='ARCHIVE_BEGIN':need(pending is None and len(f)>1,'REGISTRY_ARCHIVE_BEGIN');c['reservedArchives']+=1;pending=r
  elif t=='ARCHIVE_COMMIT':
   need(pending is not None and pending['type']=='ARCHIVE_BEGIN'and len(f)==8 and f[0]==pending['hash'],'REGISTRY_ARCHIVE_COMMIT');plan=pending['fields'][0]
   archives[plan]=dict(location='files/'+f[1],intent=f[2],intentBytes=int(f[4]),commit=f[5],commitSHA256=f[6],commitBytes=int(f[7]),members=members(pending['fields'],1));c['committedArchives']+=1;pending=None
  elif t in('APPEND_BEGIN','APPEND_COMMIT'):c['reservedRecords'if t=='APPEND_BEGIN'else'committedRecords']+=1;need(False,'REGISTRY_RECORDS_NOT_IN_CONTRACT')
  else:need(False,'REGISTRY_UNKNOWN_ROW')
 need(pending is None and all(q['receipt']is not None for q in requests.values()),'REGISTRY_PENDING')
 return dict(counters=c,enrolled=enrolled,new=new,closed=closed,archives=archives,requests=requests,lifetimeGenerations=len(enrolled)+len(new))

def status_facts(raw):
 v=json.loads(raw);i=v['input'];j=i['journal']
 return dict(generation=j['generation'],lifetime=j['lifetimeReservedGenerationCount'],sequence=j['sequence'],bytes=j['bytes'],head=j['head'],journalClosed=j['closed'],durablyDrained=j['durablyDrained'],
  inputClosed=i['closed'],workerTerminated=i['workerTerminated'],configured=i['configured'],authorityRestorable=v['authorityRestorable']is False and i['authorityRestorable']is False,sourceSHA256=v['sourceSHA256'],observedElapsedNs=v['observedElapsedNs'])

def semantics(entries,data):
 """The owner's step-2 properties, derived from content (no pin needed)."""
 files={n for n,e in entries.items()if e['type']=='regular'};dirs={n for n,e in entries.items()if e['type']=='directory'}
 rows,head=replay(data.get(REGISTRY));s=registry_state(rows)
 return dict(files=files,dirs=dirs,rows=rows,head=head,state=s)

def check_state(entries,data,sem):
 """Shape of the 87-file continuation state: exact counts, owner, journals, archives, statuses, request."""
 s=sem['state'];need(len(sem['files'])==FILES and len(sem['dirs'])==9,'INDEX_87_FILES_9_DIRS')
 for n,e in entries.items():
  need(e['uid']==UID and e['gid']==UID,'UID_GID:'+n);need(e['mode']==(0o771 if n=='files'else 0o700 if e['type']=='directory'else 0o600),'MODE:'+n)
 need([r['type']for r in sem['rows']]==ROW_TYPES,'REGISTRY_ROW_TYPES');need(s['lifetimeGenerations']==LIFETIME and len(s['new'])==NEW,'LIFETIME_GENERATION_11')
 active=sorted(n for n in sem['files']if n.startswith(ACTIVE));need(active==sorted(ACTIVE+g+'.aj02'for g in s['new']),'ACTIVE_EXACT_THREE_NEW_JOURNALS')
 for g in s['new']:
  need(data[ACTIVE+g+'.aj02']==AJ,'NEW_JOURNAL_EMPTY:'+g);c=s['closed'].get(g)
  need(c==dict(records=0,bytes=len(AJ),head=ZERO,disposition='UNUSED',sha256=sha(AJ),proofSHA256=ZERO),'NEW_JOURNAL_CLOSED_UNUSED:'+g)
 need(len(s['archives'])==1,'ONE_ARCHIVE_BATCH');plan,a=next(iter(s['archives'].items()));base=a['location']+'/'
 need(a['location']==ARCHIVES+plan and [m['generation']for m in a['members']]==[m['generation']for m in s['enrolled']]and len(a['members'])==8,'ARCHIVE_EIGHT_ENROLLED')
 batch=sorted(n for n in sem['files']if n.startswith(ARCHIVES));need(batch==sorted([base+m['generation']+'.aj02'for m in a['members']]+[base+a['intent'],base+a['commit']]),'ARCHIVE_EXACT_MEMBERS')
 for m in a['members']:need(m['disposition']=='UNUSED'and m['bytes']==len(AJ)and m['sha256']==sha(AJ)and data[base+m['generation']+'.aj02']==AJ,'ARCHIVED_JOURNAL_EMPTY:'+m['generation'])
 need(sha(data[base+a['intent']])==plan and len(data[base+a['intent']])==a['intentBytes']and sha(data[base+a['commit']])==a['commitSHA256']and len(data[base+a['commit']])==a['commitBytes'],'ARCHIVE_INTENT_COMMIT_RECORDS')
 need(len(s['requests'])==1,'ONE_REQUEST');q=next(iter(s['requests'].values()))['receipt']
 need(sorted(n for n in sem['files']if n.startswith(LIFECYCLE))==sorted([LIFECYCLE+'guard.lock',q['path']])and data[LIFECYCLE+'guard.lock']==b''and len(data[q['path']])==q['bytes']and sha(data[q['path']])==q['sha256'],'REQUEST_RECEIPT_AND_GUARD')
 need(sorted(n for n in sem['files']if n.startswith('files/product-input-registry17/'))==[REGISTRY],'REGISTRY_SINGLE_FILE')

def new_statuses(sem,data,conserved):
 """Status DTOs not in the given 75-file baseline names, grouped by new journal generation, in observed order."""
 new={n for n in sem['files']if n.startswith(STATUS)}-set(conserved);out={g:[]for g in sem['state']['new']}
 for n in new:
  f=status_facts(data[n]);need(f['generation']in out,'STATUS_UNKNOWN_GENERATION:'+n);out[f['generation']].append((f['observedElapsedNs'],n,f))
 return{g:[x[1:]for x in sorted(v)]for g,v in out.items()}

def check_statuses(groups,source_sha):
 for k,(g,rows)in enumerate(groups.items()):
  need(len(rows)==3,'STATUS_THREE_PER_JOURNAL:'+g)
  for i,(n,f)in enumerate(rows):
   last=i==2;need(f['lifetime']==9+k and f['sequence']==0 and f['bytes']==len(AJ)and f['head']==ZERO and f['configured']is False and f['authorityRestorable']and f['sourceSHA256']==source_sha,'STATUS_UNUSED_JOURNAL:'+n)
   need(f['journalClosed']is last and f['durablyDrained']is last and f['inputClosed']is last and f['workerTerminated']is last,'STATUS_CLOSE_ONLY_LAST:'+n)

def independent(tar_path,digest,head,receiver_raw,source_sha):
 """The owner's own archive/index receiver on the same raw, with the team's pinned head."""
 scan=native_tar(tar_path,digest,allow_empty_active=True)
 return verify_archive_index(scan,head,source_candidate=source_sha,archive_receivers={sha(receiver_raw):receiver_raw})

def evidence_ref(repo,rel,digest=None):
 p=Path(repo)/rel;need(p.is_file()and not any(x.is_symlink()for x in[p,*p.parents]),'EVIDENCE_REGULAR:'+rel);raw=p.read_bytes();need(digest is None or sha(raw)==digest,'EVIDENCE_SHA:'+rel)
 return raw,{'path':rel,'bytes':len(raw),'sha256':sha(raw)}

def verify(tar_path,digest,pin_path,pin_sha,*,repo=R):
 """Admit a raw private-files TAR as the pinned continuation state, or raise ContractError."""
 raw=Path(pin_path).read_bytes();need(sha(raw)==pin_sha,'PIN_SHA');pin=json.loads(raw);need(raw==canonical(pin)and pin.get('format')==FORMAT and pin.get('version')==1,'PIN_FORMAT')
 entries,data=read_tar(tar_path,digest);checks=['RAW_SHA','STRICT_TAR_PROFILE']
 want=pin['entries'];need(not set(want)-set(entries),'MISSING:'+','.join(sorted(set(want)-set(entries))[:3]));need(not set(entries)-set(want),'EXTRA:'+','.join(sorted(set(entries)-set(want))[:3]));checks.append('INDEX_EXACT_96')
 for n,e in want.items():
  got=entries[n];need(all(got[k]==e[k]for k in('type','mode','uid','gid')),'META:'+n);need(got['bytes']==e['bytes']and got['sha256']==e['sha256'],'BYTES:'+n);need(got['mtime']==e['mtime'],'MTIME:'+n)
 checks.append('ENTRY_TYPE_MODE_UID_GID_BYTES_SHA_MTIME')
 sem=semantics(entries,data);check_state(entries,data,sem);checks.append('STATE_SHAPE_87_9_GEN11_THREE_CLOSED_EMPTY_EIGHT_ARCHIVED')
 reg=pin['registry'];need(sem['head']==reg['head']and len(sem['rows'])==reg['rows']and sem['state']['counters']==reg['counters'],'REGISTRY_HEAD_ROWS_COUNTERS');checks.append('REGISTRY_HEAD_COUNTERS')
 index=data[REGISTRY]
 for p in reg['prefixes']:
  need(len(index)>=p['bytes']and sha(index[:p['bytes']])==p['sha256']and sem['rows'][p['rows']-1]['end']==p['bytes'],'REGISTRY_PREFIX:'+p['label'])
 checks.append('REGISTRY_APPEND_ONLY_PREFIXES')
 base=pin['conserved']
 for n,e in base['files'].items():need(n in entries and all(entries[n][k]==e[k]for k in META),'CONSERVED_FILE:'+n)
 for n,e in base['directories'].items():need(n in entries and all(entries[n][k]==e[k]for k in('type','mode','uid','gid')),'CONSERVED_DIRECTORY:'+n)
 need(any(n.startswith(WORKSPACE)for n in base['files']),'CONSERVED_WORKSPACE');checks.append('CONSERVED_M801_STATE_AND_WORKSPACE')
 groups=new_statuses(sem,data,pin['statusBaseline75']);need({g:[n for n,_ in v]for g,v in groups.items()}==pin['statuses'],'STATUS_SET');check_statuses(groups,pin['productSourceSHA256']);checks.append('STATUS_NINE_BOUND_TO_NEW_JOURNALS')
 receiver,_=evidence_ref(repo,pin['receiver']['path'],pin['receiver']['sha256']);src=sha(Path(__file__).read_bytes());ind=independent(tar_path,digest,reg['head'],receiver,src)
 need(ind['status']=='SOURCE_BOUND_ORIGINAL_ARCHIVE_INDEX_JOIN_VERIFIED'and ind['registryHead']==sem['head']and ind['counters']==sem['state']['counters']and ind['pendingTransactions']==0 and ind['activeJournals']==NEW and ind['archivedJournals']==8,'INDEPENDENT_RECEIVER_AGREES');checks.append('INDEPENDENT_OWNER_ARCHIVE_INDEX_RECEIVER')
 return{'format':PROOF,'version':1,'status':'TEAM_CONTINUATION_STATE_MATCHES_PIN_NOT_AUTHORITY_NOT_G1','pinSHA256':pin_sha,'tarSHA256':digest,'rawIdenticalToPinnedCapture':digest==pin['source']['sha256'],
  'contractSourceSHA256':src,'registryHead':sem['head'],'counters':sem['state']['counters'],'lifetimeGenerations':LIFETIME,'checks':checks,'independentReceiver':{k:ind[k]for k in('status','registryHead','counters','activeJournals','archivedJournals','pendingTransactions')},
  'authorityRestorable':False,'archiveOrResumeAuthorized':False,'G1AcceptanceClaimed':False,'flightAcceptance':False,'independentQA':False}
