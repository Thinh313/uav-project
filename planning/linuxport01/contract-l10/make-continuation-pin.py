#!/usr/bin/env python3
"""Prepare-only: write the team m801 continuation pin from the team's own evidence.

Run from the tree root (the bind-mounted work tree). Reads only:
  evidence/betarc01/m801   team read-only forensic capture (the state that is pinned)
  evidence/betarc01/g105   harness captures before g105 (75-file baseline) and after its session 1
  evidence/betarc01/g103   the receiver report the archive plan names
and the owner's m801 raw (--owner-m801), only to build the table of differences.
Every property the owner lists for step 2 is checked before anything is written,
and every difference from the owner's m801 must fall in a named class, or nothing
is written. The pin is created exclusively and never overwritten.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
B=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('continuation_l10',B/'continuation_l10.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
need,sha=c.need,c.sha
M801='evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar'
CAPTURE='evidence/betarc01/m801/reports/forensic-capture-h10.json'
BASELINE='evidence/betarc01/g105/sessions/beta-rc01-native01/native-restart-metadata.tar'
SESSION1='evidence/betarc01/g105/sessions/beta-rc01-native01/native-journal17-after-first-close.tar'
RECEIVER='evidence/betarc01/g103/reports/native17-receiver-original.json'

# Every field allowed to differ from the owner's m801, by registry row type and field index,
# and by JSON leaf path. Anything else stops the build.
def registry_class(kind,i):
 if kind=='ENROLL_COMMIT'and i>=1 and(i-1)%3 in(1,2):return'DEVICE_INODE'
 if kind=='GEN_COMMIT'and i in(4,5):return'DEVICE_INODE'
 if(kind,i)in{('REQUEST_RESERVE',0),('REQUEST_RECEIPT',1),('REQUEST_RECEIPT',2)}:return'RANDOM_REQUEST_NONCE'
 if(kind,i)in{('GEN_BEGIN',0),('GEN_COMMIT',1),('CLOSE',0)}:return'RANDOM_GENERATION_ID'
 if(kind,i)in{('ARCHIVE_COMMIT',0),('REQUEST_RECEIPT',0),('GEN_COMMIT',0)}:return'ROW_BACK_REFERENCE'
 if(kind,i)==('REQUEST_RECEIPT',4):return'PER_RUN_REQUEST_RECEIPT_SHA'
 return None
REQUEST_KEYS={'/requestNonce':'RANDOM_REQUEST_NONCE','/pid':'PID','/processEpoch':'PROCESS_EPOCH','/observedElapsedNs':'TIME','/journalLifecycle/registryHead':'REGISTRY_HEAD_OF_THIS_RUN'}
STATUS_KEYS={'/input/journal/generation':'RANDOM_GENERATION_ID','/requestNonce':'RANDOM_STATUS_NONCE','/pid':'PID','/processEpoch':'PROCESS_EPOCH','/input/processEpoch':'PROCESS_EPOCH','/webGeometry/processEpoch':'PROCESS_EPOCH',
 '/observedElapsedNs':'TIME','/webGeometry/observedElapsedNs':'TIME','/webGeometry/viewEpoch':'VIEW_EPOCH','/input/producerKeyId':'PER_SESSION_KEY','/input/producerPublicKeyX509Base64':'PER_SESSION_KEY',
 '/inventory/logicalBytes':'LOGICAL_BYTES_FROM_EARLIER_STATUS_SIZES'}

def leaves(v,p=''):
 if isinstance(v,dict):
  for k,x in v.items():yield from leaves(x,p+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from leaves(x,p+'/%d'%i)
 else:yield p,v
def json_diff(a,b,allowed,label):
 x=dict(leaves(json.loads(a)));y=dict(leaves(json.loads(b)));d=sorted(k for k in set(x)|set(y)if x.get(k,'<absent>')!=y.get(k,'<absent>'))
 need(all(k in allowed for k in d),'OWNER_DIFF_UNCLASSIFIED_JSON:'+label+':'+','.join(k for k in d if k not in allowed));return{k:allowed[k]for k in d}
def ref(entries,n):return{'path':n,'bytes':entries[n]['bytes'],'sha256':entries[n]['sha256']}

def owner_differences(te,td,ts,oe,od,os_,baseline):
 """Pair every non-identical entry with its owner counterpart and name why it differs."""
 same=lambda n:n in oe and all(te[n][k]==oe[n][k]for k in('type','mode','uid','gid','bytes','sha256'))
 identical=sorted(n for n in te if same(n));differ_same_path=sorted(n for n in te if n in oe and not same(n))
 need(differ_same_path==[c.REGISTRY],'OWNER_DIFF_ONLY_REGISTRY_SAME_PATH');rows=[]
 # Registry: same row types and field counts; differing fields only in named classes; chain diverges only after a differing row.
 tr,orr=ts['rows'],os_['rows'];need([r['type']for r in tr]==[r['type']for r in orr],'OWNER_DIFF_ROW_TYPES');classes={};diverged=False;per_row=[]
 for a,b in zip(tr,orr):
  need(len(a['fields'])==len(b['fields']),'OWNER_DIFF_FIELD_COUNT');prev_same=(tr[a['sequence']-2]['hash']==orr[b['sequence']-2]['hash'])if a['sequence']>1 else True
  need(prev_same or diverged,'OWNER_DIFF_CHAIN_WITHOUT_CAUSE');d=[i for i,(x,y)in enumerate(zip(a['fields'],b['fields']))if x!=y]
  for i in d:k=registry_class(a['type'],i);need(k is not None,'OWNER_DIFF_UNCLASSIFIED_REGISTRY_FIELD:%d:%s:%d'%(a['sequence'],a['type'],i));classes[k]=classes.get(k,0)+1
  diverged=diverged or bool(d);per_row.append({'row':a['sequence'],'type':a['type'],'differingFields':d,'previousHeadDiffers':not prev_same})
 tq,oq=[next(iter(s['state']['requests'].values()))['receipt']for s in(ts,os_)]
 need(tq['sha256']==sha(td[tq['path']])and oq['sha256']==sha(od[oq['path']]),'OWNER_DIFF_RECEIPT_SHA_IS_FILE_SHA')
 rows.append({'category':'REGISTRY_DEVICE_INODE_AND_RANDOM_IDS','team':ref(te,c.REGISTRY),'owner':ref(oe,c.REGISTRY),'sameBytesLength':te[c.REGISTRY]['bytes']==oe[c.REGISTRY]['bytes'],
  'differingByteCount':sum(1 for a,b in zip(td[c.REGISTRY],od[c.REGISTRY])if a!=b),'fieldClasses':classes,'rows':per_row,'rowHashesDifferBecause':'each row hash covers the previous head and its own fields'})
 # Request lifecycle receipt.
 tn,on=tq['path'],oq['path'];rows.append({'category':'REQUEST_RECEIPT_RANDOM_NAME_PER_RUN_VALUES','team':ref(te,tn),'owner':ref(oe,on),'differingFields':json_diff(td[tn],od[on],REQUEST_KEYS,'request')})
 # Two new journals, paired by creation order: random names, identical bytes.
 for g,h in zip(ts['state']['new'],os_['state']['new']):
  a,b=c.ACTIVE+g+'.aj02',c.ACTIVE+h+'.aj02';need(td[a]==od[b]==c.AJ,'OWNER_DIFF_NEW_JOURNAL_BYTES');rows.append({'category':'NEW_JOURNAL_RANDOM_NAME_SAME_BYTES','team':ref(te,a),'owner':ref(oe,b),'contentIdentical':True})
 # Six status DTOs, paired by journal and observed order; logicalBytes difference must equal the earlier size differences.
 tg,og=c.new_statuses(ts,td,baseline),c.new_statuses(os_,od,[n for n in baseline]);drift=0
 for (g,trs),(h,ors) in zip(tg.items(),og.items()):
  for (a,fa),(b,fb) in zip(trs,ors):
   d=json_diff(td[a],od[b],STATUS_KEYS,'status');need(fa['generation']==g and fb['generation']==h,'OWNER_DIFF_STATUS_GENERATION')
   lt,lo=json.loads(td[a])['inventory']['logicalBytes'],json.loads(od[b])['inventory']['logicalBytes'];need(lt-lo==drift,'OWNER_DIFF_LOGICAL_BYTES_ARITHMETIC');drift+=len(td[a])-len(od[b])
   rows.append({'category':'STATUS_RANDOM_NAME_PER_RUN_VALUES','team':ref(te,a),'owner':ref(oe,b),'differingFields':d,'logicalBytesDifference':lt-lo,'sizeDifference':len(td[a])-len(od[b])})
 paired={r['team']['path']for r in rows};need(paired|set(identical)==set(te)and len(rows)==10 and len(identical)==82,'OWNER_DIFF_EXACT_82_PLUS_10')
 need({r['owner']['path']for r in rows}|set(identical)==set(oe),'OWNER_DIFF_OWNER_SIDE_COMPLETE')
 return{'identicalEntries':82,'differingEntries':10,'mtimeCompared':False,'rows':rows}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--owner-m801',required=True);ap.add_argument('--owner-m801-sha',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 R=Path.cwd();out=Path(a.out);need(not out.exists(),'PIN_EXISTS_NO_OVERWRITE')
 m_raw,m_ref=c.evidence_ref(R,M801);te,td=c.read_tar(R/M801,m_ref['sha256']);ts=c.semantics(te,td);c.check_state(te,td,ts)
 _,b_ref=c.evidence_ref(R,BASELINE);be,bd=c.read_tar(R/BASELINE,b_ref['sha256'])
 bfiles={n:e for n,e in be.items()if e['type']=='regular'and n!=c.REGISTRY};bdirs={n:e for n,e in be.items()if e['type']=='directory'}
 need(len(bfiles)+1==75 and len(bdirs)==9,'BASELINE_75_FILES_9_DIRS')
 for n,e in bfiles.items():need(n in te and te[n]==e,'BASELINE_FILE_CONSERVED:'+n)
 for n,e in bdirs.items():need(n in te and all(te[n][k]==e[k]for k in('type','mode','uid','gid')),'BASELINE_DIRECTORY_CONSERVED:'+n)
 added=sorted(set(ts['files'])-set(be));need(len(added)==8 and sum(n.startswith(c.ACTIVE)for n in added)==2 and sum(n.startswith(c.STATUS)for n in added)==6,'ADDED_EXACT_TWO_JOURNALS_SIX_STATUS')
 prefixes=[]
 for label,rel in(('post-g103 75-file baseline (g105 pre-run capture)',BASELINE),('after g105 native session 1',SESSION1)):
  _,r=c.evidence_ref(R,rel);_,d=c.read_tar(R/rel,r['sha256']);idx=d[c.REGISTRY];rows,_=c.replay(idx);need(td[c.REGISTRY].startswith(idx),'REGISTRY_PREFIX:'+label)
  prefixes.append({'label':label,'source':r,'rows':len(rows),'bytes':len(idx),'sha256':sha(idx)})
 groups=c.new_statuses(ts,td,bfiles);src={f['sourceSHA256']for v in groups.values()for _,f in v};need(len(src)==1,'ONE_PRODUCT_SOURCE');src=src.pop();c.check_statuses(groups,src)
 recv,r_ref=c.evidence_ref(R,RECEIVER);ind=c.independent(R/M801,m_ref['sha256'],ts['head'],recv,sha((B/'continuation_l10.py').read_bytes()))
 need(ind['registryHead']==ts['head']and ind['counters']==ts['state']['counters'],'INDEPENDENT_RECEIVER_AGREES')
 oe,od=c.read_tar(a.owner_m801,a.owner_m801_sha);os_=c.semantics(oe,od);c.check_state(oe,od,os_)
 table=owner_differences(te,td,ts,oe,od,os_,bfiles);_,cap=c.evidence_ref(R,CAPTURE)
 pin={'format':c.FORMAT,'version':1,'status':'TEAM_PINNED_OBSERVED_M801_STATE_NOT_AUTHORITY_NOT_G1',
  'decision':'research team decision 2026-11-06 (LINUXPORT01): owner strictness, team values; not the project owner',
  'source':{**m_ref,'captureReport':cap,'slot':'m801','run':'beta-rc01-forensic-capture01'},
  'entries':te,'counts':{'files':83,'directories':9,'perDirectory':{d:sum(1 for n in ts['files']if n.startswith(d+'/')and n.count('/')==d.count('/')+1)for d in sorted(ts['dirs'])}},
  'registry':{'head':ts['head'],'rows':len(ts['rows']),'rowTypes':c.ROW_TYPES,'counters':ts['state']['counters'],'lifetimeGenerations':10,'newGenerations':ts['state']['new'],'prefixes':prefixes},
  'conserved':{'source':b_ref,'files':bfiles,'directories':bdirs},'statuses':{g:[n for n,_ in v]for g,v in groups.items()},'productSourceSHA256':src,
  'receiver':r_ref,'differencesFromOwnerM801':{'owner':{'path':'evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar (owner tree)','sha256':a.owner_m801_sha},**table},
  'authorityRestorable':False,'archiveOrResumeAuthorized':False,'G1AcceptanceClaimed':False,'flightAcceptance':False,'independentQA':False}
 raw=c.canonical(pin);need(len(raw)<=262144,'PIN256K')
 with open(out,'xb')as f:f.write(raw)
 proof=c.verify(R/M801,m_ref['sha256'],out,sha(raw),repo=R)
 print(json.dumps({'pin':str(out),'pinSHA256':sha(raw),'pinBytes':len(raw),'selfVerify':proof['status'],'checks':len(proof['checks']),'registryHead':ts['head'],'differences':[r['category']for r in table['rows']]}))
if __name__=='__main__':main()
