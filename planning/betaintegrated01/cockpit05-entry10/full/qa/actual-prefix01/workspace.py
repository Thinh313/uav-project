from pathlib import Path
import sys,json,hashlib,tarfile,importlib,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[6];sys.path.insert(0,str(R));E=R/'evidence/betaintegrated01-cockpit05-entry10-flight';C=E/'actual-combined01/control';A=R/'evidence/betaintegrated01-cockpit05-closure01/native-private02.tar';O=E/'qa/actual-prefix01'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
selected=json.loads((E/'host/input-contract01.json').read_text());assert all(sha(R/p)==s for p,s in selected['sourceSHA256'].items());binding=json.loads((C/'launch-binding.json').read_text());stage=json.loads((C/'staging-gate-before-AP.json').read_text());assert stage['APStarted']is False and stage['noWriterAtStage']is True and stage['layout']['bindingStagedSHA256']==stage['rootBindingSHA256']==sha(C/'launch-binding.json');assert stage['layout']['view']==stage['layout']['presentedView']=='preflight'and stage['layout']['viewReady']is True and stage['layout']['ownerActive']is False;button=stage['layout']['buttons']['control01-connect'];assert button['visible']is True and button['enabled']is True and button['bounds']==[99,634,310,690]
cold=importlib.import_module('planning.betaintegrated01.cockpit05-entry10.full.actual_combined_cold');package=cold.installed_package_proof(C,binding)
initial=json.loads((C/'initial-workspace-SHA.json').read_text());initialstate=json.loads((C/'initial-workspace-state.json').read_text());r6=json.loads((C/'workspace-r6-before-actual.json').read_text());recovery=json.loads((C/'restart-recovery-supplement01.json').read_text());before=json.loads((C/'private-before-restart-SHA.json').read_text());after=recovery['files'];assert before==after and len(after)==134 and all(after.get(p)==s for p,s in initial.items());assert len(initial)==8
state=recovery['currentUI'];assert state['native']['phase']=='NO_SESSION'and state['ownerActive']is False and state['native']['authorityRestorable']is False and recovery['layout']['bindingStagedSHA256']is None;assert recovery['beforeViewEpoch']!=recovery['afterViewEpoch']==state['viewEpoch'];assert state['workspace']['draftSHA256']==r6['workspaceState']['workspace']['draftSHA256']=='c3a2edd63398ba80943b46b548c32bfeb8bba3562523c532104d4ce7757f27e6';assert state['workspace']['draft']['revision']==6
oldreviews={x['id']:x for x in initialstate['workspace']['reviews']};newreviews={x['id']:x for x in state['workspace']['reviews']};assert len(oldreviews)==3 and all(newreviews[k]==v for k,v in oldreviews.items());assert binding['run']in newreviews;current=newreviews[binding['run']];assert current['status']=='PENDING_NATIVE_TERMINAL_OR_VERIFICATION'and current['completionClaim']is False and current['authorityRestorable']is False
actual={};small={}
with tarfile.open(A,'r:')as t:
 for item in t:
  if item.isdir():continue
  assert item.isfile()and item.name in before and item.name not in actual and '..'not in Path(item.name).parts
  h=hashlib.sha256();rawsmall=[];f=t.extractfile(item)
  for b in iter(lambda:f.read(65536),b''):
   h.update(b)
   if item.name.startswith(('files/workspace03/','files/review-links/')):rawsmall.append(b)
  actual[item.name]=h.hexdigest();assert actual[item.name]==before[item.name]
  if rawsmall:small[item.name]=b''.join(rawsmall)
assert actual==before
link=json.loads(small['files/review-links/'+binding['run']+'.json']);assert link['sourceSHA256']==link['sourceIdentity']['sourceSHA256']=='4fe53ee61afd133a9075c7e1736e09406fb4449afc7ce2c01c0c45c9a3926c23'and link['surveyRevision']==6 and link['surveySHA256']==state['workspace']['draftSHA256'];assert all(link[k]==binding[k]for k in['run','epoch','boot','generation','operator','profileId','configSHA256']);assert link['APSHA256']==binding['binarySHA256']and link['modelSHA256']==binding['modelSHA256'];live=json.loads((C/'live-AP.json').read_text());assert live['actualExeSHA256']==binding['binarySHA256'];assert not(E/'actual-combined01/raw/cut-request.json').exists()
review=json.loads((C/'post-restart-review-observed01.json').read_text());assert review['selectedRunSummary']['id']==binding['run']and review['selectedRunSummary']['status']==current['status']
result={'status':'ACTUAL_R6_STAGE_PACKAGE_AND_RESTART_BYTES_VERIFIED_FAILED_CASE_ONLY','source178PinsZeroDrift':True,'actualPackage':package,'APLiveBinarySHA256':live['actualExeSHA256'],'R6SHA256':state['workspace']['draftSHA256'],'prior8SHAUnchanged':True,'prior3MOCKSummariesUnchanged':True,'currentRunArchiveSHA256':sha(A),'archiveAll134MemberSHAMatches':True,'restartNewEpoch':True,'restartNOSESSION':True,'authorityRestored':False,'reviewStatus':current['status'],'reviewCompleted':False,'nativeArchiveClosedBytesSeparateFromPendingUIReview':True,'intentionalCutRequestExists':False,'postLANDGroundProven':False,'flightOrThirtyMinuteAccepted':False,'notes':['Originalinertpreflightlayoutstaleincident recoveredbyRootactualAX; freshstageBeforeAPbindingcheckpointverified, oldincidentnotrewritten','OriginalrestartKeyErrorphase receipt preserved; supplementisreadonlyreobservation afteralreadyrequestedrestart, notadditionalrestart','Original120s44.8MBpartialexportpreserved; independent02preservationarchivevalid62.3MB, noflightpromotion']};(O/'workspace-stage-restart.json').open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],len(actual))
