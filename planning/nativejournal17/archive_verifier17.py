"""Independent readonly Registry17 + original archive/TAR byte joins.
No authority, device calls or native-only complete-filesystem rollback claim.
"""
import base64,hashlib,re,struct
from receiver17 import need,sha,aj02,MAGIC
INDEX_MAGIC=b'AERIS_JOURNAL_REGISTRY17_V1\n';ZERO='0'*64;ACTIVE='files/product-input01/';ARCHIVES='files/product-input-archives17/'
def num(s):
 need(type(s)is str and re.fullmatch('0|[1-9][0-9]{0,18}',s),'INDEX_INTEGER');n=int(s);need(n<2**63,'INDEX_INTEGER_BOUND');return n
def hash64(s):need(type(s)is str and re.fullmatch('[a-f0-9]{64}',s),'INDEX_HASH');return s
def gen32(s):need(type(s)is str and re.fullmatch('[a-f0-9]{32}',s),'INDEX_GENERATION');return s
def group(f,start):
 n=num(f[start]);need(1<=n<=8 and len(f)==start+1+n*5,'INDEX_ORIGINAL_GROUP');rows=[];seen=set()
 for i in range(n):
  g,nbytes,h,d,p=f[start+1+5*i:start+6+5*i];gen32(g);need(g not in seen,'INDEX_DUPLICATE_GENERATION');seen.add(g);nbytes=num(nbytes);need(len(MAGIC)<=nbytes<=32*2**20 and d in('UNUSED','CLOSED_VERIFIED'),'INDEX_ORIGINAL_SHAPE');rows.append(dict(generation=g,bytes=nbytes,sha256=hash64(h),disposition=d,proofSHA256=hash64(p)))
 return rows
def verify_archive_index(scan,expected_head,*,source_candidate,archive_receivers,require_selected_closed=()):
 hash64(source_candidate);originals=scan['inputOriginals'];index=originals.get('files/product-input-registry17/highwater.aj17');need(type(index)is bytes and index.startswith(INDEX_MAGIC)and len(index)<=8*2**20 and index.endswith(b'\n'),'EXACT_COMPLETE_REGISTRY_REQUIRED');head=ZERO;anchors=set();pending=None;enrolled=False;members={};batches={};counts=dict(reservedGenerations=0,committedGenerations=0,reservedRecords=0,committedRecords=0,reservedArchives=0,committedArchives=0,reservedRequests=0,committedReceipts=0);requests={};initial_unbound=False
 for ordinal,line in enumerate(index[len(INDEX_MAGIC):].splitlines(),1):
  need(len(line)+1<=4096 and b'\r'not in line,'INDEX_ROW_BOUND');v=line.decode('ascii').split('\t');need(len(v)==5 and num(v[0])==ordinal and v[1]==head and sha(b'\t'.join(x.encode('ascii')for x in v[:4]))==v[4],'INDEX_SEQUENCE_HASH');encoded=v[3];payload=base64.b64decode(encoded,validate=True);need(base64.b64encode(payload).decode()==encoded and all(9<=x<=126 and x not in(10,13)for x in payload),'INDEX_PAYLOAD_ENCODING');f=payload.decode('ascii').split('\t');kind=v[2];rowhash=hash64(v[4]);prior=pending
  if kind=='ENROLL_BEGIN':
   need(ordinal==1 and pending is None and not enrolled,'INDEX_ENROLL_ORDER');need(len(f)>=4,'INDEX_ENROLL_FIELDS');[hash64(x)for x in f[:3]];rows=group(f,3);need(len(rows)==8,'INDEX_ENROLL_EXACT8')
   for q in rows:need(q['disposition']=='UNUSED'and q['bytes']==len(MAGIC)and q['sha256']==sha(MAGIC),'INDEX_INITIAL_UNUSED');members[q['generation']]={**q,'location':ACTIVE+q['generation']+'.aj02','records':0,'head':ZERO,'closed':True,'outcome':False,'appends':[]}
   counts['reservedGenerations']+=8;counts['reservedRequests']=1;initial_unbound=True;pending=(kind,rowhash,f)
  elif kind=='ENROLL_COMMIT':
   need(prior is not None and prior[0]=='ENROLL_BEGIN'and len(f)==25 and f[0]==prior[1],'INDEX_ENROLL_COMMIT');seen=set()
   for at in range(1,25,3):need(f[at]in members and f[at]not in seen and num(f[at+1])>=0 and num(f[at+2])>0,'INDEX_ENROLL_IDENTITY');seen.add(f[at])
   counts['committedGenerations']+=8;enrolled=True;pending=None
  elif kind=='GEN_BEGIN':need(enrolled and pending is None and len(f)==1 and gen32(f[0])not in members,'INDEX_GEN_BEGIN');counts['reservedGenerations']+=1;pending=(kind,rowhash,f)
  elif kind=='GEN_COMMIT':
   need(prior is not None and prior[0]=='GEN_BEGIN'and len(f)==6 and f[0]==prior[1]and f[1]==prior[2][0]and num(f[2])==len(MAGIC)and f[3]==ZERO and num(f[4])>=0 and num(f[5])>0,'INDEX_GEN_COMMIT');g=f[1];members[g]=dict(generation=g,bytes=len(MAGIC),sha256=None,disposition='OPEN',proofSHA256=ZERO,location=ACTIVE+g+'.aj02',records=0,head=ZERO,closed=False,outcome=False,appends=[]);counts['committedGenerations']+=1;pending=None
  elif kind=='APPEND_BEGIN':
   need(enrolled and pending is None and len(f)==6 and f[0]in members,'INDEX_APPEND_BEGIN');m=members[f[0]];n,before,after=map(num,f[1:4]);need(not m['closed']and m['location'].startswith(ACTIVE)and n==m['records']+1 and n<=24576 and before==m['bytes']and before<after<=32*2**20 and after-before<=2585,'INDEX_APPEND_HIGHWATER');hash64(f[4]);hash64(f[5]);counts['reservedRecords']+=1;pending=(kind,rowhash,f)
  elif kind=='APPEND_COMMIT':
   need(prior is not None and prior[0]=='APPEND_BEGIN'and len(f)==3 and f[0]==prior[1]and f[2]in('0','1'),'INDEX_APPEND_COMMIT');a=prior[2];m=members[a[0]];elapsed=num(f[1]);m['appends'].append({'sequence':num(a[1]),'before':num(a[2]),'after':num(a[3]),'rowSHA':a[4],'head':a[5],'prior':m['head'],'elapsed':elapsed,'pending':f[2]=='1'});m.update(records=num(a[1]),bytes=num(a[3]),head=a[5],outcome=f[2]=='1',sha256=None);need(m['outcome']==(m['records']%2==1),'INDEX_PAIR_HIGHWATER');counts['committedRecords']+=1;pending=None
  elif kind=='REQUEST_RESERVE':
   need(enrolled and len(f)==3 and re.fullmatch('[a-f0-9]{32}',f[0])and f[1]in('PREVIEW','APPLY','RECOVER')and f[2]in('0','1')and f[0]not in requests,'INDEX_REQUEST_RESERVE')
   if f[2]=='1':need(initial_unbound and not requests and counts['reservedRequests']==1 and f[1]=='APPLY','INDEX_INITIAL_REQUEST_CREDIT');initial_unbound=False
   else:need(not initial_unbound and all(x.get('committed')for x in requests.values())and counts['reservedRequests']<32,'INDEX_REQUEST_NO_REFUND_OR_REPLAY');counts['reservedRequests']+=1
   requests[f[0]]={'id':rowhash,'operation':f[1],'committed':False}
  elif kind=='REQUEST_RECEIPT':
   need(enrolled and len(f)==5 and f[1]in requests,'INDEX_REQUEST_RECEIPT');q=requests[f[1]];need(not q['committed']and f[0]==q['id']and f[2]=='product-input-lifecycle17/request-'+f[1]+'.json'and 1<=num(f[3])<=4096,'INDEX_REQUEST_RECEIPT_BINDING');q.update(committed=True,path='files/'+f[2],bytes=num(f[3]),sha256=hash64(f[4]));counts['committedReceipts']+=1
  elif kind=='CLOSE':
   need(enrolled and pending is None and len(f)==7 and f[0]in members,'INDEX_CLOSE');m=members[f[0]];need(not m['closed']and num(f[1])==m['records']and num(f[2])==m['bytes']and f[3]==m['head']and f[4]in('UNUSED','CLOSED_VERIFIED','UNRESOLVED'),'INDEX_CLOSE_HIGHWATER');need(f[4]!='UNUSED'or m['records']==0,'INDEX_UNUSED_NOT_SUCCESS');need(f[4]!='CLOSED_VERIFIED'or(m['records']>0 and not m['outcome']),'INDEX_CLOSED_NOT_UNKNOWN');m.update(closed=True,disposition=f[4],sha256=hash64(f[5]),proofSHA256=hash64(f[6]))
  elif kind=='ARCHIVE_BEGIN':
   need(enrolled and pending is None and counts['reservedArchives']<8 and len(f)>1,'INDEX_ARCHIVE_BEGIN');hash64(f[0]);rows=group(f,1)
   for q in rows:
    need(q['disposition']=='UNUSED','ARCHIVED_USED_RAW_STATUS_P256_PROOF_DEFERRED');need(q['generation']in members,'INDEX_ARCHIVE_GENERATION');m=members[q['generation']];need(m['closed']and m['location'].startswith(ACTIVE)and not m['outcome']and m['bytes']==q['bytes']and m['sha256']==q['sha256']and m['disposition']==q['disposition'],'INDEX_ARCHIVE_ORIGINAL_BINDING')
   counts['reservedArchives']+=1;pending=(kind,rowhash,f)
  elif kind=='ARCHIVE_COMMIT':
   need(prior is not None and prior[0]=='ARCHIVE_BEGIN'and len(f)==8 and f[0]==prior[1],'INDEX_ARCHIVE_COMMIT');p=prior[2][0];need(f[1]=='product-input-archives17/'+p and re.fullmatch('intent-[0-7][.]record',f[2])and f[3]==p and re.fullmatch('commit-[0-7][.]record',f[5]),'INDEX_ARCHIVE_MANIFEST_BINDING');hash64(f[6]);need(200<=num(f[4])<=16384 and 1<=num(f[7])<=512,'INDEX_ARCHIVE_MANIFEST_BOUND');batches[p]={'fields':f,'originals':group(prior[2],1)}
   for q in batches[p]['originals']:members[q['generation']].update(location=ARCHIVES+p+'/'+q['generation']+'.aj02',proofSHA256=q['proofSHA256'])
   counts['committedArchives']+=1;pending=None
  else:need(False,'INDEX_UNKNOWN_TYPE')
  head=rowhash;anchors.add(head)
 need(enrolled and pending is None and not initial_unbound and all(x.get('committed')for x in requests.values()),'INDEX_PENDING_OR_UNENROLLED');need(re.fullmatch('[a-f0-9]{64}',expected_head or'')and expected_head in anchors,'EXTERNAL_HOST_HEAD_REQUIRED');need(len(members)<=72,'ALL_RETAINED_GENERATIONS72')
 for request in requests.values():need(request['path']in originals and len(originals[request['path']])==request['bytes']and sha(originals[request['path']])==request['sha256'],'COMMITTED_REQUEST_RECEIPT_MISSING_NO_REFUND')
 actual_requests={n for n in originals if re.fullmatch('files/product-input-lifecycle17/request-[a-f0-9]{32}[.]json',n)};need(actual_requests=={r['path']for r in requests.values()},'EXACT_REQUEST_RECEIPT_SET')
 for name,data in originals.items():
  if name.startswith(ACTIVE):need(re.fullmatch('files/product-input01/[a-f0-9]{32}[.]aj02',name),'INPUT_UNKNOWN_ACTIVE_FILE')
  elif name.startswith(ARCHIVES):need(re.fullmatch('files/product-input-archives17/[a-f0-9]{64}/([a-f0-9]{32}[.]aj02|(intent|commit)-[0-7][.]record)',name),'INPUT_UNKNOWN_ARCHIVE_FILE')
  elif name.startswith('files/product-input-registry17/'):need(name=='files/product-input-registry17/highwater.aj17','INPUT_UNKNOWN_INDEX_FILE')
  elif name.startswith('files/product-input-lifecycle17/'):need(name=='files/product-input-lifecycle17/guard.lock'and data==b''or name in actual_requests,'INPUT_UNKNOWN_CONTROL_FILE')
 need(type(require_selected_closed)in(list,tuple)and all(type(g)is str and re.fullmatch('[a-f0-9]{32}',g)for g in require_selected_closed)and len(set(require_selected_closed))==len(require_selected_closed)and set(require_selected_closed)<=set(members),'EXACT_SELECTED_CLOSE_GENERATIONS');actual_journals={name for name in originals if name.endswith('.aj02')};need(actual_journals=={m['location']for m in members.values()},'ALL_ORIGINAL_MEMBER_SET_NO_REFUND');active=0;archived=0
 for g,m in members.items():
  raw=originals[m['location']];decoded=aj02(raw);need(len(raw)==m['bytes']and decoded['records']==m['records']and decoded['head']==m['head']and bool(decoded['unresolvedIntent'])==m['outcome'],'EXACT_ORIGINAL_AJ02_HIGHWATER');need(m['sha256']is None or sha(raw)==m['sha256'],'ORIGINAL_SHA');active+=m['location'].startswith(ACTIVE);archived+=m['location'].startswith(ARCHIVES)
  for a in m['appends']:
   row=raw[a['before']:a['after']];need(len(row)==a['after']-a['before']and len(row)>=86 and sha(row)==a['rowSHA'],'APPEND_ORIGINAL_RANGE_SHA');n=struct.unpack_from('!I',row)[0];need(n+4==len(row),'APPEND_ORIGINAL_RANGE_LENGTH');body=row[4:-32];sequence,elapsed,kind=struct.unpack_from('!QQB',body);need(sequence==a['sequence']and elapsed==a['elapsed']and body[17:49].hex()==a['prior']and sha(body)==a['head']and row[-32:].hex()==a['head']and kind==(1 if a['pending']else 2),'APPEND_ORIGINAL_ROW_BINDING')
  if g in require_selected_closed:need(m['closed']and m['disposition']!='UNRESOLVED'and decoded['unresolvedIntent']is None,'SELECTED_ORIGINAL_CLOSE_REQUIRED')
 need(active<=8 and archived<=64 and len(batches)<=8,'BOUNDED_ACTIVE_ARCHIVES')
 actual_batches={name[len(ARCHIVES):].split('/')[0]for name in originals if name.startswith(ARCHIVES)};need(actual_batches==set(batches),'EXACT_ARCHIVE_BATCH_SET')
 for p,batch in batches.items():
  f=batch['fields'];base='files/'+f[1]+'/';plan=originals.get(base+f[2]);commit=originals.get(base+f[5]);need(type(plan)is bytes and sha(plan)==p and len(plan)==num(f[4])and type(commit)is bytes and sha(commit)==f[6]and len(commit)==num(f[7]),'ORIGINAL_ARCHIVE_MANIFEST_ANCHOR');need(plan.endswith(b'\n')and all(x==10 or x==9 or 32<=x<=126 for x in plan),'ORIGINAL_ARCHIVE_PLAN_ASCII_LF');lines=plan.decode('ascii').split('\n')[:-1];need(lines[0]=='AERIS_JOURNAL_LIFECYCLE17\t1'and lines[-1]=='end','ORIGINAL_ARCHIVE_PLAN');need(len(lines)==10+len(batch['originals'])and lines[1]=='package\tvn.rtr.aeris.betasim09','ORIGINAL_ARCHIVE_PLAN_SHAPE');plan_fields=[line.split('\t')for line in lines[2:9]];need([part[0]for part in plan_fields]==['oldAPK','oldSource','newSource','backup','receiver','cold','expectedHead']and all(len(part)==(3 if part[0]=='backup'else 2)for part in plan_fields),'ORIGINAL_ARCHIVE_PLAN_FIELDS');[hash64(part[1])for part in plan_fields[:-1]];need(1024<=num(plan_fields[3][2])<=192*2**20 and(plan_fields[-1][1]=='ROOT'or re.fullmatch('[a-f0-9]{64}',plan_fields[-1][1])),'ORIGINAL_ARCHIVE_PLAN_BACKUP_OR_HEAD');plan_members=[]
  for line in lines[9:-1]:
   part=line.split('\t');need(len(part)==6 and part[0]=='generation','ORIGINAL_ARCHIVE_PLAN_MEMBER');plan_members.append(dict(generation=gen32(part[1]),bytes=num(part[2]),sha256=hash64(part[3]),disposition=part[4],proofSHA256=hash64(part[5])))
  need(plan_members==batch['originals'],'ORIGINAL_ARCHIVE_PLAN_EXACT_MEMBER_JOIN');receiver=lines[6].split('\t');need(receiver[0]=='receiver'and len(receiver)==2 and commit==('AERIS_JOURNAL17_COMMITTED\t'+p+'\t'+receiver[1]+'\n').encode(),'ORIGINAL_ARCHIVE_COMMITTED_POINTER');report=archive_receivers.get(receiver[1]);need(type(report)is bytes and sha(report)==receiver[1],'ALL_ARCHIVE_RECEIVER_ORIGINALS_REQUIRED')
  from receiver17 import decode
  rp=decode(report);need(rp.get('format')=='aeris-journal17-independent-full-byte-receiver'and type(rp.get('version'))is int and rp['version']==1 and rp.get('package')=='vn.rtr.aeris.betasim09'and rp.get('oldAPKSHA256')==lines[2].split('\t')[1]and rp.get('oldSourceSHA256')==lines[3].split('\t')[1]and rp.get('newSourceSHA256')==lines[4].split('\t')[1]and rp.get('backupSHA256')==lines[5].split('\t')[1]and rp.get('backupBytes')==num(lines[5].split('\t')[2])and rp.get('coldProofSHA256')==lines[7].split('\t')[1]and rp.get('expectedHostRegistryHead')==lines[8].split('\t')[1],'ARCHIVE_RECEIVER_EXACT_PLAN_SOURCE')
  need(rp.get('status')=='COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT'and rp.get('authorityRestorable')is False,'ARCHIVE_RECEIVER_DISPOSITION');need(rp['originals']==[{**q,'records':members[q['generation']]['records'],'sourceClosedStatusBound':q['disposition']=='CLOSED_VERIFIED'}for q in batch['originals']],'ARCHIVE_RECEIVER_ALL_ORIGINALS')
 return {'format':'aeris-journal17-original-archive-index-proof','version':1,'status':'SOURCE_BOUND_ORIGINAL_ARCHIVE_INDEX_JOIN_VERIFIED','sourceCandidateSHA256':source_candidate,'nativeTARSHA256':scan['tarSHA256'],'registryHead':head,'pendingTransactions':0,'externalHostAnchorVerified':True,'allArchiveReceiversVerified':True,'originalClosedDispositionInferredFromEmpty':False,'originalInputFiles':{n:scan['files'][n]for n in originals},'totalInputArchiveIndexControlBytes':scan['inputBytes'],'activeJournals':active,'archivedJournals':archived,'counters':counts,'authorityRestorable':False,'flightAcceptance':False,'nativeOnlyCompleteFilesystemRollbackProof':False,'selectedClosedGenerations':list(require_selected_closed),'selectedCloseProofScope':'INDEX_CLOSE_AND_ORIGINAL_AJ02_ONLY_REQUIRES_SEPARATE_SIGNED_STATUS_PROOF'}

if __name__=='__main__':
 import argparse,json
 from pathlib import Path
 from receiver17 import native_tar,bounded
 p=argparse.ArgumentParser(description='Fresh complete archive/index original-byte proof; no device/runtime actors');p.add_argument('--backup',required=True);p.add_argument('--backup-sha',required=True);p.add_argument('--expected-head',required=True);p.add_argument('--candidate-sha',required=True);p.add_argument('--receiver',action='append',default=[]);p.add_argument('--selected-closed',action='append',default=[]);a=p.parse_args();reports={}
 for name in a.receiver:
  raw=bounded(name,32768);need(sha(raw)not in reports,'DUPLICATE_ARCHIVE_RECEIVER');reports[sha(raw)]=raw
 scan=native_tar(a.backup,a.backup_sha,allow_empty_active=True);proof=verify_archive_index(scan,a.expected_head,source_candidate=a.candidate_sha,archive_receivers=reports,require_selected_closed=a.selected_closed);proof['sourceVerifierSHA256']=sha(Path(__file__).read_bytes());proof['sourceTarVerifierSHA256']=sha(Path(__file__).with_name('receiver17.py').read_bytes());raw=(json.dumps(proof,sort_keys=True,separators=(',',':'))+'\n').encode();need(len(raw)<=65536,'ARCHIVE_PROOF64K');__import__('sys').stdout.buffer.write(raw)
