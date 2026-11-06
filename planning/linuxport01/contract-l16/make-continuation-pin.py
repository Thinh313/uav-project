#!/usr/bin/env python3
"""Prepare-only: write the team m803 continuation pin from the team's own evidence.

Run from the tree root (the bind-mounted work tree). Reads only team evidence:
  evidence/betarc01/m803   read-only forensic capture after g107 attempt 1 (the state that is pinned; attempt 6)
  evidence/linuxport01/failed/m803-attempt0{1..5}   the earlier m803 attempts (1-4 emulator -6/-11 on shutdown
                           with the same TAR bytes; 5 failed before the emulator started, no TAR)
  evidence/betarc01/m802   the previous pinned state, re-admitted here by contract-l12 and its pin
  evidence/betarc01/g107   the run that made this state: its object store holds the new status file bytes
  evidence/betarc01/g105, m801   harness captures whose registries are earlier byte prefixes
  evidence/betarc01/g103   the receiver report the archive plan names
Every property is checked before anything is written. The pin is created exclusively
and never overwritten. There is no owner counterpart of this state, so every m802-state
entry is paired with its m803 entry.
"""
from pathlib import Path
import argparse,importlib.util,json
B=Path(__file__).resolve().parent
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('continuation_l16',B/'continuation_l16.py');c12=module('continuation_l12',B.parent/'contract-l12/continuation_l12.py')
need,sha=c.need,c.sha
RUN='beta-rc01-forensic-capture03'
M803='evidence/betarc01/m803/sessions/'+RUN+'/native-restart-metadata.tar'
CAPTURE='evidence/betarc01/m803/reports/forensic-capture-h10.json'
CLOSURE='evidence/betarc01/m803/guardian/closure.json'
PROCESS='evidence/betarc01/m803/diagnostics/guardian-process/close.json'
FAILED='evidence/linuxport01/failed/m803-attempt%02d'
M802='evidence/betarc01/m802/sessions/beta-rc01-forensic-capture02/native-restart-metadata.tar'
M802_PIN='planning/linuxport01/contract-l12/m802-continuation-pin.json';M802_PIN_SHA='4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45'
G107_OBJECTS='evidence/betarc01/g107/sessions/beta-rc01-native03/android-api/objects/'
BASELINE='evidence/betarc01/g105/sessions/beta-rc01-native01/native-restart-metadata.tar'
SESSION1='evidence/betarc01/g105/sessions/beta-rc01-native01/native-journal17-after-first-close.tar'
M801='evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar'
RECEIVER='evidence/betarc01/g103/reports/native17-receiver-original.json'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
 R=Path.cwd();out=Path(a.out);need(not out.exists(),'PIN_EXISTS_NO_OVERWRITE')
 # The pinned state: shape from content, and a normal SDK close of the capture (emulator and guardian process exit 0).
 _,m_ref=c.evidence_ref(R,M803);te,td=c.read_tar(R/M803,m_ref['sha256']);ts=c.semantics(te,td);c.check_state(te,td,ts)
 cap=json.loads((R/CAPTURE).read_bytes());clo=json.loads((R/CLOSURE).read_bytes());proc=json.loads((R/PROCESS).read_bytes())
 need(cap['status']=='COMPLETE_ORIGINAL_CAPTURE_AWAITING_GENUINE_SDK_CLOSE_AND_INDEPENDENT_SEMANTICS'and cap['rootPrivateBackup']['sha256']==m_ref['sha256'],'M803_CAPTURE_REPORT')
 need(type(clo['exit'])is int and clo['exit']==0 and clo['failure']is None and clo['exceptionalPhysicalDisposal']is False and clo['cleanupNotes']==[]and clo['durablyDrained']is True and proc['exit']==0,'M803_NORMAL_SDK_CLOSE')
 attempts=[]
 for n in range(1,6):
  f=R/(FAILED%n);fc=json.loads((f/'guardian/closure.json').read_bytes());t=f/'sessions'/RUN/'native-restart-metadata.tar'
  if t.is_file():
   _,r=c.evidence_ref(R,str(t.relative_to(R)));need(r['sha256']==m_ref['sha256']and fc['exit']in(-6,-11),'M803_ATTEMPT_SAME_BYTES:%d'%n);attempts.append({'attempt':n,'tar':r,'emulatorExit':fc['exit'],'usableAsContractBase':False})
  else:need(fc['exit']is None and fc['failure']=='TimeoutError:HOST_AUDIT_DURABILITY_BARRIER','M803_ATTEMPT5_NO_TAR');attempts.append({'attempt':n,'tar':None,'emulatorExit':None,'guardianFailure':fc['failure'],'usableAsContractBase':False})
 attempts.append({'attempt':6,'tar':m_ref,'emulatorExit':clo['exit'],'usableAsContractBase':True})
 # The previous state is the pinned m802, admitted by contract-l12 with its own pin.
 _,p_ref=c.evidence_ref(R,M802_PIN,M802_PIN_SHA);_,o_ref=c.evidence_ref(R,M802)
 prior=c12.verify(R/M802,o_ref['sha256'],R/M802_PIN,M802_PIN_SHA,repo=R);need(prior['status']=='TEAM_CONTINUATION_STATE_MATCHES_PIN_NOT_AUTHORITY_NOT_G1'and prior['rawIdenticalToPinnedCapture'],'M802_ADMITTED_BY_CONTRACT_L12')
 oe,od=c.read_tar(R/M802,o_ref['sha256']);os_=c.semantics(oe,od);m802pin=json.loads((R/M802_PIN).read_bytes())
 # Conservation: every m802 file but the registry unchanged (type, mode, UID, GID, mtime, size, SHA); directories keep type/mode/owner.
 cfiles={n:e for n,e in oe.items()if e['type']=='regular'and n!=c.REGISTRY};cdirs={n:e for n,e in oe.items()if e['type']=='directory'}
 need(len(cfiles)==86 and len(cdirs)==9,'M802_86_FILES_9_DIRS')
 for n,e in cfiles.items():need(te.get(n)==e,'M802_FILE_CONSERVED:'+n)
 for n,e in cdirs.items():need(n in te and all(te[n][k]==e[k]for k in('type','mode','uid','gid')),'M802_DIRECTORY_CONSERVED:'+n)
 need(set(m802pin['conserved']['files'])<=set(cfiles),'M801_STATE_INSIDE_M802_STATE')
 added=sorted(set(te)-set(oe));last=ts['state']['new'][-1]
 need(ts['state']['new'][:3]==os_['state']['new']and added[0]==c.ACTIVE+last+'.aj02'and len(added)==2 and added[1].startswith(c.STATUS),'ADDED_EXACT_ONE_JOURNAL_ONE_STATUS')
 # The new status file is byte-identical to the STATUS reply g107 attempt 1 kept in its own object store.
 status=td[added[1]];_,g_ref=c.evidence_ref(R,G107_OBJECTS+sha(status),sha(status))
 need(json.loads(status)['input']['journal']['generation']==last,'STATUS_NAMES_OPEN_JOURNAL')
 # Append-only registry: four earlier registries are byte prefixes.
 prefixes=[]
 for label,rel in(('post-g103 75-file baseline (g105 pre-run capture)',BASELINE),('after g105 native session 1',SESSION1),('team m801 capture (contract-l10 pinned state)',M801),('team m802 capture (contract-l12 pinned state)',M802)):
  _,r=c.evidence_ref(R,rel);_,d=c.read_tar(R/rel,r['sha256']);idx=d[c.REGISTRY];rows,_=c.replay(idx);need(td[c.REGISTRY].startswith(idx),'REGISTRY_PREFIX:'+label)
  prefixes.append({'label':label,'source':r,'rows':len(rows),'bytes':len(idx),'sha256':sha(idx)})
 need([p['rows']for p in prefixes]==[6,9,12,15],'PREFIX_ROWS_6_9_12_15')
 for p,q in zip(prefixes[:3],m802pin['registry']['prefixes']):need({k:p[k]for k in('rows','bytes','sha256')}=={k:q[k]for k in('rows','bytes','sha256')},'SAME_EARLIER_PREFIXES_AS_M802_PIN')
 base75=m802pin['statusBaseline75']
 groups=c.new_statuses(ts,td,base75);src={f['sourceSHA256']for v in groups.values()for _,f in v};need(len(src)==1,'ONE_PRODUCT_SOURCE');src=src.pop()
 need(src==m802pin['productSourceSHA256'],'SAME_PRODUCT_SOURCE_AS_M802');c.check_statuses(groups,src)
 need({g:[n for n,_ in v]for g,v in list(groups.items())[:3]}==m802pin['statuses'],'M802_STATUSES_UNCHANGED_GROUPS')
 recv,r_ref=c.evidence_ref(R,RECEIVER);need(r_ref==m802pin['receiver'],'SAME_RECEIVER_AS_M802')
 ind=c.independent(R/M803,m_ref['sha256'],ts['head'],recv,sha((B/'continuation_l16.py').read_bytes()))
 need(ind['registryHead']==ts['head']and ind['counters']==ts['state']['counters']and ind['activeJournals']==4 and ind['archivedJournals']==8 and ind['pendingTransactions']==0,'INDEPENDENT_RECEIVER_AGREES')
 _,cap_ref=c.evidence_ref(R,CAPTURE);_,clo_ref=c.evidence_ref(R,CLOSURE)
 pin={'format':c.FORMAT,'version':1,'status':'TEAM_PINNED_OBSERVED_M803_STATE_NOT_AUTHORITY_NOT_G1',
  'decision':'research team decision 2026-11-07 (LINUXPORT01, after g107 attempt 1): keep the changed state, including the open journal, as history and pin it; owner strictness, team values; not the project owner',
  'source':{**m_ref,'captureReport':cap_ref,'guardianClosure':clo_ref,'slot':'m803','run':RUN,'attempt':6,'captureAttempts':attempts},
  'origin':{'run':'g107 attempt 1 (beta-rc01-native03), failed at the start of native session 1; the AERIS app started','statusObject':g_ref,'openJournal':last,'openJournalClosedOrRepaired':False},
  'previousPinnedState':{'pin':p_ref,'tar':o_ref,'admittedByContractL12':True},
  'entries':te,'counts':{'files':c.FILES,'directories':9,'perDirectory':{d:sum(1 for n in ts['files']if n.startswith(d+'/')and n.count('/')==d.count('/')+1)for d in sorted(ts['dirs'])}},
  'registry':{'head':ts['head'],'rows':len(ts['rows']),'rowTypes':c.ROW_TYPES,'counters':ts['state']['counters'],'lifetimeGenerations':c.LIFETIME,'newGenerations':ts['state']['new'],'openGenerations':[last],'prefixes':prefixes},
  'conserved':{'source':o_ref,'files':cfiles,'directories':cdirs},'statusBaseline75':base75,'statuses':{g:[n for n,_ in v]for g,v in groups.items()},'productSourceSHA256':src,
  'receiver':r_ref,'addedSinceM802':added,
  'authorityRestorable':False,'archiveOrResumeAuthorized':False,'G1AcceptanceClaimed':False,'flightAcceptance':False,'independentQA':False}
 raw=c.canonical(pin);need(len(raw)<=262144,'PIN256K')
 with open(out,'xb')as f:f.write(raw)
 proof=c.verify(R/M803,m_ref['sha256'],out,sha(raw),repo=R)
 print(json.dumps({'pin':str(out),'pinSHA256':sha(raw),'pinBytes':len(raw),'selfVerify':proof['status'],'checks':len(proof['checks']),'registryHead':ts['head'],'rows':len(ts['rows']),'added':added}))
if __name__=='__main__':main()
