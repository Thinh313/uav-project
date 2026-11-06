#!/usr/bin/env python3
"""Prepare-only: write the team m802 continuation pin from the team's own evidence.

Run from the tree root (the bind-mounted work tree). Reads only team evidence:
  evidence/betarc01/m802   read-only forensic capture after g106 attempt 1 (the state that is pinned)
  evidence/linuxport01/failed/m802-attempt01   the first m802 capture (emulator -11 on shutdown)
  evidence/betarc01/m801   the previous pinned state, re-admitted here by contract-l10 and its pin
  evidence/betarc01/g106   its export after native session 1 (the run that made this state)
  evidence/betarc01/g105   harness captures before g105 (75-file baseline) and after its session 1
  evidence/betarc01/g103   the receiver report the archive plan names
Every property is checked before anything is written. The pin is created exclusively
and never overwritten. There is no owner counterpart of this state, so instead of an
owner difference table every m801-state entry is paired with its m802 entry.
"""
from pathlib import Path
import argparse,importlib.util,json
B=Path(__file__).resolve().parent
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('continuation_l12',B/'continuation_l12.py');c10=module('continuation_l10',B.parent/'contract-l10/continuation_l10.py')
need,sha=c.need,c.sha
M802='evidence/betarc01/m802/sessions/beta-rc01-forensic-capture02/native-restart-metadata.tar'
CAPTURE='evidence/betarc01/m802/reports/forensic-capture-h10.json'
CLOSURE='evidence/betarc01/m802/guardian/closure.json'
ATTEMPT1='evidence/linuxport01/failed/m802-attempt01/sessions/beta-rc01-forensic-capture02/native-restart-metadata.tar'
M801='evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar'
M801_PIN='planning/linuxport01/contract-l10/m801-continuation-pin.json';M801_PIN_SHA='b5318c628ae0e1a2638988752baa18b2f3dcad682bb2c649e564dd06ef2c778d'
G106='evidence/betarc01/g106/sessions/beta-rc01-native02/native-journal17-after-first-close.tar'
BASELINE='evidence/betarc01/g105/sessions/beta-rc01-native01/native-restart-metadata.tar'
SESSION1='evidence/betarc01/g105/sessions/beta-rc01-native01/native-journal17-after-first-close.tar'
RECEIVER='evidence/betarc01/g103/reports/native17-receiver-original.json'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
 R=Path.cwd();out=Path(a.out);need(not out.exists(),'PIN_EXISTS_NO_OVERWRITE')
 # The pinned state: shape from content, and a normal SDK close of the capture.
 _,m_ref=c.evidence_ref(R,M802);te,td=c.read_tar(R/M802,m_ref['sha256']);ts=c.semantics(te,td);c.check_state(te,td,ts)
 cap=json.loads((R/CAPTURE).read_bytes());clo=json.loads((R/CLOSURE).read_bytes())
 need(cap['status']=='COMPLETE_ORIGINAL_CAPTURE_AWAITING_GENUINE_SDK_CLOSE_AND_INDEPENDENT_SEMANTICS'and cap['rootPrivateBackup']['sha256']==m_ref['sha256'],'M802_CAPTURE_REPORT')
 need(type(clo['exit'])is int and clo['exit']==0 and clo['failure']is None and clo['exceptionalPhysicalDisposal']is False and clo['cleanupNotes']==[]and clo['durablyDrained']is True,'M802_NORMAL_SDK_CLOSE')
 _,a1=c.evidence_ref(R,ATTEMPT1);need(a1['sha256']==m_ref['sha256'],'M802_ATTEMPT1_SAME_BYTES')
 # The previous state is the pinned m801, admitted by contract-l10 with its own pin.
 _,p_ref=c.evidence_ref(R,M801_PIN,M801_PIN_SHA);_,o_ref=c.evidence_ref(R,M801)
 prior=c10.verify(R/M801,o_ref['sha256'],R/M801_PIN,M801_PIN_SHA,repo=R);need(prior['status']=='TEAM_CONTINUATION_STATE_MATCHES_PIN_NOT_AUTHORITY_NOT_G1'and prior['rawIdenticalToPinnedCapture'],'M801_ADMITTED_BY_CONTRACT_L10')
 oe,od=c.read_tar(R/M801,o_ref['sha256']);os_=c.semantics(oe,od);m801pin=json.loads((R/M801_PIN).read_bytes())
 # Conservation: every m801 file but the registry unchanged (type, mode, UID, GID, mtime, size, SHA); directories keep type/mode/owner.
 cfiles={n:e for n,e in oe.items()if e['type']=='regular'and n!=c.REGISTRY};cdirs={n:e for n,e in oe.items()if e['type']=='directory'}
 need(len(cfiles)==82 and len(cdirs)==9,'M801_82_FILES_9_DIRS')
 for n,e in cfiles.items():need(te.get(n)==e,'M801_FILE_CONSERVED:'+n)
 for n,e in cdirs.items():need(n in te and all(te[n][k]==e[k]for k in('type','mode','uid','gid')),'M801_DIRECTORY_CONSERVED:'+n)
 need(set(m801pin['conserved']['files'])<=set(cfiles),'BASELINE75_INSIDE_M801_STATE')
 added=sorted(set(te)-set(oe));last=ts['state']['new'][-1]
 need(ts['state']['new'][:2]==os_['state']['new']and added[0]==c.ACTIVE+last+'.aj02'and len(added)==4 and all(n.startswith(c.STATUS)for n in added[1:]),'ADDED_EXACT_ONE_JOURNAL_THREE_STATUS')
 # The state is what g106 attempt 1 left after its first native session.
 _,g_ref=c.evidence_ref(R,G106);ge,_=c.read_tar(R/G106,g_ref['sha256']);need(ge==te,'SAME_ENTRIES_AS_G106_FIRST_CLOSE_EXPORT')
 # Append-only registry: three earlier registries are byte prefixes.
 prefixes=[]
 for label,rel in(('post-g103 75-file baseline (g105 pre-run capture)',BASELINE),('after g105 native session 1',SESSION1),('team m801 capture (contract-l10 pinned state)',M801)):
  _,r=c.evidence_ref(R,rel);_,d=c.read_tar(R/rel,r['sha256']);idx=d[c.REGISTRY];rows,_=c.replay(idx);need(td[c.REGISTRY].startswith(idx),'REGISTRY_PREFIX:'+label)
  prefixes.append({'label':label,'source':r,'rows':len(rows),'bytes':len(idx),'sha256':sha(idx)})
 need([p['rows']for p in prefixes]==[6,9,12],'PREFIX_ROWS_6_9_12')
 # Nine new status files relative to the 75-file baseline: three per new journal.
 base75=sorted(n for n in m801pin['conserved']['files']if n.startswith(c.STATUS))
 _,b_ref=c.evidence_ref(R,BASELINE);be,_=c.read_tar(R/BASELINE,b_ref['sha256']);need(base75==sorted(n for n in be if n.startswith(c.STATUS)),'STATUS_BASELINE75_FROM_G105_CAPTURE')
 groups=c.new_statuses(ts,td,base75);src={f['sourceSHA256']for v in groups.values()for _,f in v};need(len(src)==1,'ONE_PRODUCT_SOURCE');src=src.pop()
 need(src==m801pin['productSourceSHA256'],'SAME_PRODUCT_SOURCE_AS_M801');c.check_statuses(groups,src)
 need({g:[n for n,_ in v]for g,v in list(groups.items())[:2]}==m801pin['statuses'],'M801_STATUSES_UNCHANGED_GROUPS')
 recv,r_ref=c.evidence_ref(R,RECEIVER);need(r_ref==m801pin['receiver'],'SAME_RECEIVER_AS_M801')
 ind=c.independent(R/M802,m_ref['sha256'],ts['head'],recv,sha((B/'continuation_l12.py').read_bytes()))
 need(ind['registryHead']==ts['head']and ind['counters']==ts['state']['counters']and ind['activeJournals']==3 and ind['archivedJournals']==8 and ind['pendingTransactions']==0,'INDEPENDENT_RECEIVER_AGREES')
 _,cap_ref=c.evidence_ref(R,CAPTURE);_,clo_ref=c.evidence_ref(R,CLOSURE)
 pin={'format':c.FORMAT,'version':1,'status':'TEAM_PINNED_OBSERVED_M802_STATE_NOT_AUTHORITY_NOT_G1',
  'decision':'research team decision 2026-11-06 (LINUXPORT01, option 2 after g106 attempt 1): keep the changed state as history and pin it; owner strictness, team values; not the project owner',
  'source':{**m_ref,'captureReport':cap_ref,'guardianClosure':clo_ref,'slot':'m802','run':'beta-rc01-forensic-capture02','attempt':2,
   'captureAttempts':[{'attempt':1,'tar':a1,'emulatorExit':-11,'usableAsContractBase':False},{'attempt':2,'tar':m_ref,'emulatorExit':clo['exit'],'usableAsContractBase':True}]},
  'origin':{'run':'g106 attempt 1 (beta-rc01-native02), failed after native session 1','firstCloseExport':g_ref,'sameEntries':True},
  'previousPinnedState':{'pin':p_ref,'tar':o_ref,'admittedByContractL10':True},
  'entries':te,'counts':{'files':c.FILES,'directories':9,'perDirectory':{d:sum(1 for n in ts['files']if n.startswith(d+'/')and n.count('/')==d.count('/')+1)for d in sorted(ts['dirs'])}},
  'registry':{'head':ts['head'],'rows':len(ts['rows']),'rowTypes':c.ROW_TYPES,'counters':ts['state']['counters'],'lifetimeGenerations':c.LIFETIME,'newGenerations':ts['state']['new'],'prefixes':prefixes},
  'conserved':{'source':o_ref,'files':cfiles,'directories':cdirs},'statusBaseline75':base75,'statuses':{g:[n for n,_ in v]for g,v in groups.items()},'productSourceSHA256':src,
  'receiver':r_ref,'addedSinceM801':added,
  'authorityRestorable':False,'archiveOrResumeAuthorized':False,'G1AcceptanceClaimed':False,'flightAcceptance':False,'independentQA':False}
 raw=c.canonical(pin);need(len(raw)<=262144,'PIN256K')
 with open(out,'xb')as f:f.write(raw)
 proof=c.verify(R/M802,m_ref['sha256'],out,sha(raw),repo=R)
 print(json.dumps({'pin':str(out),'pinSHA256':sha(raw),'pinBytes':len(raw),'selfVerify':proof['status'],'checks':len(proof['checks']),'registryHead':ts['head'],'rows':len(ts['rows']),'added':added}))
if __name__=='__main__':main()
