"""CLI: independent combined qualification from one closed original recording.
Usage: python3 -B .../actual_combined_cold.py <actual-combined01>
No services, extraction or duplicatedhostraw. Root external anchors required.
"""
from pathlib import Path
import base64,hashlib,json,sys,tarfile,importlib.util,datetime,resource
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from pilot.betaintegrated01.cockpit04.revision02.oracles import verify_case_long
from pilot.betaintegrated01.cockpit04.revision02.confirmation import descriptor_sha256,_closed_native
from pilot.betaintegrated01.cockpit04.revision02.native_release import native_wire_evidence
from combined_oracle import assisted_window,cleanup_witness,qualify_facts,raw_clock_model_window
from native_authority02 import audit

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def restart_ui_matches(prior,current,draft_sha,run):
 before=prior['workspace'];after=current['workspace']
 assert after.get('error')is None and before.get('error')is None
 assert before['draftSHA256']==after['draftSHA256']==draft_sha
 ids=lambda w:{x.get('run',x.get('id'))for x in w['reviews']}
 assert ids(before)==ids(after)and run in ids(after)
 return True
def restart_workspace(C,descriptor,binding,anchor,source_sha):
 before=json.loads((C/'private-before-restart-SHA.json').read_text());recovery=json.loads((C/'restart-recovery.json').read_text());assert recovery['files']==before
 current=recovery['currentUI'];layout=recovery['layout'];assert current['native']['phase']=='NO_SESSION'and current['ownerActive']is False and layout['bindingStagedSHA256']is None
 prior=json.loads((C/'workspace-before-restart.json').read_text());epoch_before=recovery.get('beforeViewEpoch');epoch_after=current['viewEpoch'];assert type(epoch_before)is int and type(epoch_after)is int and epoch_before!=epoch_after
 location=json.loads((C/'native-export-location.json').read_text());assert digest(location['path'])==location['sha256'];assert str(Path(location['path']).resolve())==str(Path(descriptor['nativeTarPath']).resolve());run=binding['run'];table={};observed={};count=0
 with tarfile.open(location['path'],'r:')as t:
  for member in t:
   if not member.isfile():continue
   count+=1;assert count<=2048
   if member.name not in before:raise ValueError('EXPORT_FOREIGN_FILE:'+member.name)
   h=hashlib.sha256();chunks=[];small=member.name.startswith(('files/workspace03/','files/review-links/'))
   if small:assert member.size<=131072
   f=t.extractfile(member)
   for raw in iter(lambda:f.read(65536),b''):
    h.update(raw)
    if small:chunks.append(raw)
   assert member.name not in observed;observed[member.name]=h.hexdigest();assert observed[member.name]==before[member.name]
   if small:table[member.name]=b''.join(chunks)
 assert observed==before
 drafts={};reviews={};import re
 for name,raw in table.items():
  base=Path(name).name
  if name.startswith('files/workspace03/'):
   m=re.fullmatch(r'(draft-(\d{6})|review-([A-Za-z0-9_.:-]{1,128}))-([a-f0-9]{64})\.json',base);assert m and m[4]==hashlib.sha256(raw).hexdigest();o=json.loads(raw)
   if m[2]:assert int(m[2])==o['revision']and o['trainingOnly']is True;drafts[o['revision']]=(m[4],o)
   else:assert m[3]==o['run'];reviews[o['run']]=o
 assert set(drafts)==set(range(1,len(drafts)+1));review=reviews[run];link=json.loads(table['files/review-links/'+run+'.json']);assert review['preflightContext']==link
 for k in('run','epoch','boot','generation','operator','profileId','configSHA256'):assert link[k]==binding[k]
 assert link['APSHA256']==binding['binarySHA256']and link['modelSHA256']==binding['modelSHA256']and link['sourceSHA256']==source_sha and link['sourceIdentity']['sourceSHA256']==source_sha;assert drafts[link['surveyRevision']][0]==link['surveySHA256']==review['surveySHA256'];assert restart_ui_matches(prior,current,link['surveySHA256'],run);assert review['nativeTerminalSHA256']==anchor and review['status']=='FAILED'and review['completionClaim']is False and review['authorityRestorable']is False and review['coverageClaim']is False and review['actualImages']==0 and review['groundDistinctFreshGroups']==0
 return dict(exactSHA=True,immutableFiles=len(before),NO_SESSION=True,ownerActive=False,bindingStagedSHA256=None,newViewEpoch=True,beforeViewEpoch=epoch_before,afterViewEpoch=epoch_after,reviewStatus='FAILED_PRESERVED_NATIVE_DID_NOT_OBSERVE_POSTCUT_LANDING',nativeGroundGroups=0,hostGroundSeparate=True,draftRevision=link['surveyRevision'],draftSHA256=link['surveySHA256'],nativeTerminalSHA256=anchor,sourceSHA256=source_sha)

def power_guard(C,start,cut):
 closure=json.loads((C/'root-guard-closure.json').read_text());assert not closure['faults'];previous=-1;first=last=None;count=0
 for line in(C/'guard.jsonl').read_text().splitlines():
  r=json.loads(line);at=r['hostNs'];assert type(at)is int and at>previous;previous=at;first=at if first is None else first;last=at;count+=1;assert abs(r['wallMonoGapSeconds'])<=2 and r['freeBytes']>=10*2**30+256*2**20
  if r['AC']is not True:assert type(r['batteryPercent'])is int and r['batteryPercent']>20
 assert first<=start<=cut<=last;driver=json.loads((C/'closure.json').read_text());assert driver['failure']is None and not driver['guardFailures']
 return dict(status='PASS_ROOT_GUARD_OBSERVATIONS',samples=count,observedStartHostNs=first,observedEndHostNs=last,noObservedWallMonotonicStepAbove2s=True,actualDfFloorReserveMaintained=True)

def main(case):
 E=R/'evidence/betaintegrated01-m1cockpit04';B=E/case;C=B/'control';O=E/'qa'/('combined-cold-'+case);O.mkdir();A=json.loads((C/'external-anchors.json').read_text());D=json.loads((C/'native-confirmation-descriptor.json').read_text());DA=json.loads((C/'native-confirmation-external-anchor.json').read_text());assert descriptor_sha256(D)==DA['canonicalSHA256'];cfg=json.loads((B/'raw/run-config.json').read_text());binding=json.loads((C/'launch-binding.json').read_text());build=json.loads((E/'native/build-02.json').read_text());assert all(digest(R/p)==s for p,s in build['sourcePins'].items());ap=json.loads((C/'container-control-stdout.txt').read_text().splitlines()[-1]);ctx=[cfg[k]for k in('run','epoch','boot')];assert cfg['requestedSpeedup']==1 and cfg['capMs']==500 and cfg['maximumSeconds']==1960
 base=verify_case_long(B/'raw',*ctx,host_anchor=A['liveParentBackend']['commitAnchor'],AP_anchor=ap['terminalSHA256'],transport_anchor=A['liveParentBackend']['transportCommitAnchor'],scenario='loss',native_confirmation=D,confirmedHomeReceiptAnchor=DA['canonicalSHA256'])
 native=audit(D['nativeTarPath'],D['prefix'],D['nativeExternalAnchor'],binding,scenario='assisted-hold-loss');_,rows=_closed_native(D['nativeTarPath'],D['prefix'],D['nativeExternalAnchor']);tx,hb=native_wire_evidence(rows);wire=base['wireAudit'];cleanup=cleanup_witness(wire,tx,hb);start=json.loads((C/'assisted-window-start.json').read_text())['hostNs'];cut=wire['cutClosedHostNs'];window=assisted_window(wire['passiveTimeline'],start,cut);clocks=raw_clock_model_window(B/'raw/journal',start,cut,cfg);restart=restart_workspace(C,D,binding,D['nativeExternalAnchor'],build['sourceSHA256']);guard=power_guard(C,start,cut);combined=qualify_facts(base,wire,native,window,clocks,cleanup,restart=restart)
 final=dict(atUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='READY_COMBINED_30MIN_SIMULATION_SCOPE_ONLY'if combined['status'].startswith('COMBINED_FACTS_PASS')else'NOT_READY',scenario=combined['scenario'],actualQualificationFromClosedRawOnly=True,wholeBetaAccepted=False,combined=combined,fullFrameModelAP=base['fullFrameModelAP'],originalHeldForwardLossResult=dict(status=base['status'],criteria=base['control']['criteria']),geography=base['geography'],HomeConfirmation=base['confirmedHome'],cleanup=cleanup,nativeAuthority=native,window=window,clocks=clocks,restart=restart,powerGuard=guard,selectedAPK_SHA256=build['sha256'],selectedSourceSHA256=build['sourceSHA256'],externalAnchorsSHA256=digest(C/'external-anchors.json'),allRootBeforeAfterAndExportSHAMatch=True,hostRawCopies=0,sourceAuthenticity='LOCAL_PINNED_ORCHESTRATION_NOT_REMOTE_AUTHENTICATION',physicalControllerOrHeraClaim=False,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 (O/'results.json').open('x').write(json.dumps(final,indent=2)+'\n');print(json.dumps(dict(status=final['status'],frames=base['fullFrameModelAP']['frames'],nativeRows=native['records'],failed=combined['failed'])))
if __name__=='__main__':main(sys.argv[1])
