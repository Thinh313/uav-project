"""CLI: independent combined qualification from one closed original recording.
Usage: python3 -B .../actual_combined_cold.py <actual-combined01>
No services, extraction or duplicatedhostraw. Root external anchors required.
"""
from pathlib import Path
import base64,hashlib,json,sys,tarfile,importlib.util,datetime,resource
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from importlib import import_module
verify_case_long=import_module('planning.betaintegrated01.cockpit05-compact10.flight.oracles').verify_case_long
_frozen_confirmation=import_module('planning.betaintegrated01.cockpit05-compact10.flight.confirmation')
descriptor_sha256=_frozen_confirmation.descriptor_sha256;_closed_native=_frozen_confirmation._closed_native
_frozen_native_wire=import_module('planning.betaintegrated01.cockpit05-compact10.flight.native_wire')
native_wire_evidence=_frozen_native_wire.native_wire_evidence
from planning.betaintegrated01.m1cockpit04.qa.combined_oracle import assisted_window,cleanup_witness,qualify_facts
_frozen_native_authority=import_module('planning.betaintegrated01.cockpit05-compact10.flight.native_authority')
audit=_frozen_native_authority.audit


def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def retained_adb_command(C,evidence,key,expected_argv):
 android=(C/'android').resolve();path=Path(evidence[key]).resolve()
 assert path.is_relative_to(android)and path.is_file()and path.stat().st_size<=65536
 assert digest(path)==evidence[key+'SHA256']
 receipt=json.loads(path.read_text());assert type(receipt.get('exit'))is int and receipt['exit']==0 and receipt.get('timedOut')is False and receipt['argv']==expected_argv
 data={}
 for stream in('stdout','stderr'):
  rawpath=path.parent/(stream+'.bin');assert rawpath.resolve().is_relative_to(android)and rawpath.is_file()and rawpath.stat().st_size<=65536
  raw=rawpath.read_bytes();assert type(receipt.get(stream+'Bytes'))is int and len(raw)==receipt[stream+'Bytes']and hashlib.sha256(raw).hexdigest()==receipt[stream+'SHA256'];data[stream]=raw
 return data['stdout']

def installed_package_proof(C,binding):
 #RootlocalADBobservation, notcryptographicauthentication byrawjournal.
 receiver=importlib.import_module('planning.betaintegrated01.cockpit05-observer11.flight.receiver05')
 value=json.loads((C/'installed-package-observation.json').read_text())
 context={k:binding[k]for k in('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')}
 receiver.selected_context(context);receiver.package_observation(value,context)
 evidence=Path(value.get('observationEvidencePath',C/'installed-package-observation-evidence.json'))
 if not evidence.is_absolute():evidence=C/evidence
 assert evidence.is_file()and digest(evidence)==value['observationEvidenceSHA256']
 data=json.loads(evidence.read_text());package='vn.rtr.aeris.cockpitio10';selected=import_module('planning.betaintegrated01.cockpit05-observer11.flight.contract').APK_SHA256
 assert data['expectedPackage']==data['package']==package and data['installedAPK_SHA256']==selected
 adb=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582']
 path_output=retained_adb_command(C,data,'APKPathReadCommandReceipt',adb+['shell','pm','path',package]).decode('ascii').splitlines()
 assert len(path_output)==1 and path_output[0].startswith('package:/data/app/')
 installed=path_output[0][8:];assert installed.endswith('.apk')and not any(c.isspace()for c in installed)and '..'not in Path(installed).parts
 hash_output=retained_adb_command(C,data,'APKHashReadCommandReceipt',adb+['shell','sha256sum',installed]).decode('ascii').splitlines()
 assert len(hash_output)==1 and hash_output[0].split()==[selected,installed]
 return dict(package=value['package'],apkSHA256=value['apkSHA256'],sourceSHA256=value['sourceSHA256'],observedHostNs=value['observedHostNs'],observationEvidenceSHA256=value['observationEvidenceSHA256'],scope='ROOT_ACTUAL_ADB_OBSERVATION_BOUND_TO_RETAINED_BYTES_NOT_RAW_PACKAGE_INFERENCE')

def restart_ui_matches(prior,current,draft_sha,run):
 before=prior['workspace'];after=current['workspace']
 assert after.get('error')is None and before.get('error')is None
 assert before['draftSHA256']==after['draftSHA256']==draft_sha
 ids=lambda w:{x.get('run',x.get('id'))for x in w['reviews']}
 assert ids(before)==ids(after)and run in ids(after)
 return True
def restart_workspace_base(C,descriptor,binding,anchor,source_sha,expected_status='FAILED'):
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
 assert link['APSHA256']==binding['binarySHA256']and link['modelSHA256']==binding['modelSHA256']and link['sourceSHA256']==source_sha and link['sourceIdentity']['sourceSHA256']==source_sha;assert drafts[link['surveyRevision']][0]==link['surveySHA256']==review['surveySHA256'];assert restart_ui_matches(prior,current,link['surveySHA256'],run);assert review['nativeTerminalSHA256']==anchor and review['status']==expected_status and review['completionClaim']is False and review['authorityRestorable']is False and review['coverageClaim']is False and review['actualImages']==0 and((expected_status=='FAILED'and review['groundDistinctFreshGroups']==0)or(expected_status!='FAILED'and review['groundDistinctFreshGroups']>=2))
 return dict(exactSHA=True,immutableFiles=len(before),NO_SESSION=True,ownerActive=False,bindingStagedSHA256=None,newViewEpoch=True,beforeViewEpoch=epoch_before,afterViewEpoch=epoch_after,reviewStatus=review['status'],nativeGroundGroups=review['groundDistinctFreshGroups'],hostGroundSeparate=True,draftRevision=link['surveyRevision'],draftSHA256=link['surveySHA256'],nativeTerminalSHA256=anchor,sourceSHA256=source_sha)

def restart_workspace(C,descriptor,binding,anchor,source_sha,expected_status='FAILED'):
 from .preservation import expected_old,verify_observation
 for name in('old-packages-before-case.json','old-packages-before-restart.json','old-packages-after-restart.json'):
  old=verify_observation(C/name);assert old['status']=='OLD_PACKAGES_EXACT307_PLUS_FOUR_DIAGNOSTICS_AND_EXISTING_R1_PRESERVED'
 # Original r1..6/MOCK/failed-run bytes are independently outside the selected-run tar.
 before=json.loads((C/'all-private-before-restart-SHA.json').read_text());after=json.loads((C/'all-private-after-restart-SHA.json').read_text());assert before==after
 initial=json.loads((C/'initial-private-SHA.json').read_text());assert len(initial)==1 and all(before.get(k)==h for k,h in initial.items())
 caseprior=json.loads((C/'all-private-before-case-SHA.json').read_text());assert all(before.get(k)==h for k,h in caseprior.items()),'CASE_PRIOR_PRIVATE_HISTORY_CHANGED'
 result=restart_workspace_base(C,descriptor,binding,anchor,source_sha,expected_status=expected_status)
 result.update(historicalPrivateFilesPreserved=len(initial),allPrivateBeforeAfterFiles=len(before),priorDraftRevisions=[1],priorMOCKPromoted=False)
 assert result['draftRevision']==1
 return result

def power_guard(C,start,cut):
 closure=json.loads((C/'root-guard-closure.json').read_text());assert not closure['faults'];previous=-1;first=last=None;count=0
 for line in(C/'guard.jsonl').read_text().splitlines():
  r=json.loads(line);at=r['hostNs'];assert type(at)is int and at>previous;previous=at;first=at if first is None else first;last=at;count+=1;assert abs(r['wallMonoGapSeconds'])<=2 and r['freeBytes']>=10*2**30+256*2**20
  if r['AC']is not True:assert type(r['batteryPercent'])is int and r['batteryPercent']>20
 assert first<=start<=cut<=last;driver=json.loads((C/'closure.json').read_text());assert driver['failure']is None and not driver['guardFailures']
 return dict(status='PASS_ROOT_GUARD_OBSERVATIONS',samples=count,observedStartHostNs=first,observedEndHostNs=last,noObservedWallMonotonicStepAbove2s=True,actualDfFloorReserveMaintained=True)

def main(case):
 import_module('planning.betaintegrated01.cockpit05-observer11.flight.contract').verify_full_inputs()
 assert case=='actual-combined01'
 import_module('planning.betaintegrated01.cockpit05-observer11.flight.ledger').cold_caps(None)
 E=R/'evidence/betaintegrated01-cockpit05-observer11';B=E/case;C=B/'control';O=E/'qa'/('combined-cold-'+case);O.mkdir();A=json.loads((C/'external-anchors.json').read_text());D=json.loads((C/'native-confirmation-descriptor.json').read_text());DA=json.loads((C/'native-confirmation-external-anchor.json').read_text());assert descriptor_sha256(D)==DA['canonicalSHA256'];cfg=json.loads((B/'raw/run-config.json').read_text());binding=json.loads((C/'launch-binding.json').read_text());build=import_module('planning.betaintegrated01.cockpit05-observer11.flight.contract').build_receipt();assert all(digest(R/p)==s for p,s in build['sourcePins'].items());ap=json.loads((C/'container-control-stdout.txt').read_text().splitlines()[-1]);ctx=[cfg[k]for k in('run','epoch','boot')];assert binding['run']=='cockpit05-observer11-combined-01' and cfg['run']==binding['run'];assert build['sha256']==import_module('planning.betaintegrated01.cockpit05-observer11.flight.contract').APK_SHA256;assert cfg['requestedSpeedup']==1 and cfg['capMs']==500 and cfg['maximumSeconds']==1960
 fullContract=importlib.import_module('planning.betaintegrated01.cockpit05-observer11.flight.contract');selected=fullContract.verify_full_inputs();policy=fullContract.policy();policy.validate_recording_policy(cfg);assert cfg['externalRecordingPolicy']==selected['externalRecordingPolicy'];import_module('planning.betaintegrated01.cockpit05-observer11.flight.contract').verify_observer_capture(B/'raw',B/'AP-state',cfg)
 packageProof=installed_package_proof(C,binding)
 hostProfile=import_module('planning.betaintegrated01.cockpit05-compact10.flight.host_profile').verify(B/'raw',A,cfg)
 diagnostic=import_module('planning.betaintegrated01.cockpit05-observer11.flight.diagnostic').verify(C,{k:binding[k]for k in('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')})
 base=verify_case_long(B/'raw',*ctx,host_anchor=A['liveParentBackend']['commitAnchor'],AP_anchor=ap['terminalSHA256'],transport_anchor=A['liveParentBackend']['transportCommitAnchor'],scenario='loss',native_confirmation=D,confirmedHomeReceiptAnchor=DA['canonicalSHA256'],clock_anchor=A['liveParentBackend']['clockCommitAnchor'],source_amendment=cfg['externalRecordingPolicy']['amendmentSHA256'],maximum_seconds=1960)
 nativeContext={**binding,'expectedViewEpoch':json.loads((C/'staging-gate-before-AP.json').read_text())['workspace']['viewEpoch']}
 native=audit(D['nativeTarPath'],D['prefix'],D['nativeExternalAnchor'],nativeContext,scenario='assisted-hold-loss');samplerDiagnostic=import_module('planning.betaintegrated01.cockpit05-observer11.flight.diagnostic').verify_sampler_binding(C,native['dedicatedSampler']);_,rows=_closed_native(D['nativeTarPath'],D['prefix'],D['nativeExternalAnchor']);tx,hb=native_wire_evidence(rows);wire=base['wireAudit'];cleanup=cleanup_witness(wire,tx,hb);start=json.loads((C/'assisted-window-start.json').read_text())['hostNs'];cut=wire['cutClosedHostNs'];window=assisted_window(wire['passiveTimeline'],start,cut);clocks=import_module('planning.betaintegrated01.cockpit05-compact10.flight.durations').raw_window(B/'raw',start,cut,cfg);restart=restart_workspace(C,D,binding,D['nativeExternalAnchor'],build['sourceSHA256']);guard=power_guard(C,start,cut);combined=qualify_facts(base,wire,native,window,clocks,cleanup,restart=restart)
 final=dict(atUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='READY_COMBINED_30MIN_SIMULATION_SCOPE_ONLY'if combined['status'].startswith('COMBINED_FACTS_PASS')else'NOT_READY',scenario=combined['scenario'],actualQualificationFromClosedRawOnly=True,wholeBetaAccepted=False,combined=combined,fullFrameModelAP=base['fullFrameModelAP'],originalHeldForwardLossResult=dict(status=base['status'],criteria=base['control']['criteria']),geography=base['geography'],HomeConfirmation=base['confirmedHome'],cleanup=cleanup,nativeAuthority=native,window=window,clocks=clocks,restart=restart,powerGuard=guard,selectedAPK_SHA256=build['sha256'],selectedSourceSHA256=build['sourceSHA256'],externalAnchorsSHA256=digest(C/'external-anchors.json'),allRootBeforeAfterAndExportSHAMatch=True,hostRawCopies=0,sourceAuthenticity='LOCAL_PINNED_ORCHESTRATION_NOT_REMOTE_AUTHENTICATION',selectedPackageObservation=packageProof,selectedNativePackage='vn.rtr.aeris.cockpitio10',historicalMOCKReviewsAreFlightEvidence=False,physicalControllerOrHeraClaim=False,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 (O/'results.json').open('x').write(json.dumps(final,indent=2)+'\n');print(json.dumps(dict(status=final['status'],frames=base['fullFrameModelAP']['frames'],nativeRows=native['records'],failed=combined['failed'])))
if __name__=='__main__':main(sys.argv[1])
