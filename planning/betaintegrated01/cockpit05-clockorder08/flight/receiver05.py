"""Test-only read-only adapters for05, frozen160MiB readers and external receipts.

Package05 identity is a separately retained Root observation, not inferable from
shared control journal bytes. No ADB, launcher, command sender or socket exists.
"""
from pathlib import Path
import base64,hashlib,json,re
from pilot.betaintegrated01.cockpit04.revision02.confirmation import create_confirmation_descriptor_long,verify_confirmation,launch_context
from .native_stream import closed_native
from .native_wire import native_wire_evidence
from .contract import PACKAGE,SOURCE_SHA256,APK_SHA256,expected_context
SHA=re.compile(r'[0-9a-f]{64}')


def package_observation(value,context):
    launch_context(context)
    if type(value)is not dict or value.get('package')!=PACKAGE or value.get('sourceSHA256')!=SOURCE_SHA256 or value.get('apkSHA256')!=APK_SHA256:raise ValueError('EXPECTED_SELECTED05_PACKAGE_OBSERVATION')
    if any(value.get(k)!=context[k]for k in('run','epoch','boot','generation')):raise ValueError('PACKAGE_OBSERVATION_CONTEXT')
    if type(value.get('observedHostNs'))is not int or value['observedHostNs']<0 or type(value.get('observationEvidenceSHA256'))is not str or SHA.fullmatch(value['observationEvidenceSHA256'])is None:raise ValueError('ROOT_PACKAGE_OBSERVATION_EVIDENCE')
    path=value.get('observationEvidencePath')
    if type(path)is not str or not 1<=len(path)<=4096 or '\0'in path:raise ValueError('ROOT_PACKAGE_OBSERVATION_PATH')
    p=Path(path)
    if not p.is_file()or p.stat().st_size>262144:raise ValueError('ROOT_PACKAGE_OBSERVATION_FILE_BOUND')
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=value['observationEvidenceSHA256']:raise ValueError('ROOT_PACKAGE_OBSERVATION_FILE_SHA')
    evidence=json.loads(raw)
    if evidence.get('package')!=PACKAGE or evidence.get('installedAPK_SHA256')!=APK_SHA256 or evidence.get('selectedAPKSourceSHA256')!=SOURCE_SHA256:raise ValueError('ROOT_PACKAGE_OBSERVATION_FILE_BINDING')
    return value


def selected_context(context):
    launch_context(context)
    if context['run']not in('cockpit05-clockorder08-short-01','cockpit05-clockorder08-combined-01'):raise ValueError('ONLY_NEW_SELECTED05_RUN_NOT_PRIOR_MOCK_OR_OLD_ACTUAL')
    if context['profileId']not in('M1-COCKPIT04-NOMINAL','M1-COCKPIT04-LOSS'):raise ValueError('SELECTED_SHARED04_PROVIDER_ID_REQUIRED')
    variant='nominal'if context['profileId'].endswith('-NOMINAL')else'loss'
    expected=expected_context(context['run'],context['epoch'],context['boot'],context['generation'],context['operator'],variant)
    if context!=expected:raise ValueError('SELECTED05_PROFILE_CONFIG_OR_AP_IDENTITY')
    return context


def make_confirmation(nativeTarPath,prefix,nativeExternalAnchor,bracket,launchContext,*,packageObservation):
    selected_context(launchContext);package_observation(packageObservation,launchContext)
    descriptor,anchor=create_confirmation_descriptor_long(nativeTarPath,prefix,nativeExternalAnchor,bracket,launchContext)
    # Verify causality too; creating a descriptor alone does not validate Home.
    verify_confirmation(descriptor,anchor,launchContext['run'],launchContext['epoch'],launchContext['boot'])
    return descriptor,anchor


def verify_selected_run(nativeTarPath,prefix,nativeExternalAnchor,context,*,packageObservation):
    selected_context(context);package_observation(packageObservation,context)
    if prefix!='files/control-runs/'+context['run']+'/':raise ValueError('SELECTED05_RUN_PREFIX_REQUIRED')
    cold,rows=closed_native(nativeTarPath,prefix,nativeExternalAnchor);opened=provider=0;count=0
    if any(cold[k]!=context[k]for k in('run','epoch')):raise ValueError('SELECTED_NATIVE_SESSION_CONTEXT')
    def checked():
        nonlocal opened,provider,count
        for row in rows:
            count+=1
            if row['kind']=='LIFECYCLE':
                item=json.loads(base64.b64decode(row['base64'],validate=True))
                if item.get('kind')=='OPENED':
                    opened+=1
                    if opened!=1 or any(item.get(k)!=context[k]for k in('run','epoch','boot','generation','operator','profileId','binarySHA256')):raise ValueError('NATIVE_OPENED_CONTEXT')
            if row['kind']=='CONTROL_PROVIDER':
                item=json.loads(base64.b64decode(row['base64'],validate=True));provider+=1
                if provider!=1 or opened!=1 or any(item.get(k)!=context[k]for k in('run','epoch','boot','generation','binarySHA256','configSHA256')):raise ValueError('NATIVE_PROVIDER_CONTEXT')
            yield row
    tx,hb=native_wire_evidence(checked())
    if opened!=1 or provider!=1 or count!=cold['records']:raise ValueError('UNIQUE_FULL_NATIVE_EPISODE_REQUIRED')
    return {'status':'CLOSED_FAILED_NATIVE_FORENSICS_ONLY'if cold.get('forensicOnly')else'SELECTED07_NATIVE_BYTES_AND_LOCAL_WIRE_PASS_NOT_AUTHORITY_OR_FLIGHT_ACCEPTANCE','preSocketRefusals':cold.get('preSocketRefusals',[]),'successfulFlightQualified':False,'integrity':cold,'decodedOwnHeartbeats':len(hb),'nativeWrittenWireGroups':sum(len(v)for v in tx.values()),'packageObservation':packageObservation,'packageIdentityProvenByNativeRawAlone':False,'fullAuthorityConsentAndCombinedGroundAudit':'REQUIRED_SEPARATELY','priorMOCKReviewsPromoted':False}


def capture_outside_anchors(hostReceipt,APReceipt,nativeCheckpoint,context,*,packageObservation):
    """Pure binding of receipts captured by Root outside the raw package.

    Passing JSON found inside a tar does not establish this trust boundary.
    Root must retain the live stdout/checkpoint commands and their hashes.
    """
    selected_context(context);package_observation(packageObservation,context)
    for item in(hostReceipt,APReceipt,nativeCheckpoint):
        if type(item)is not dict or any(item.get(k)!=context[k]for k in('run','epoch','boot')):raise ValueError('OUTSIDE_RECEIPT_CONTEXT')
    if hostReceipt.get('status')!='HOST_CAPTURE_CLOSED_NOT_FLIGHT_ACCEPTANCE'or hostReceipt.get('error')is not None:raise ValueError('HOST_NOT_CLOSED')
    for key in('commitAnchor','transportCommitAnchor','clockCommitAnchor'):
        if type(hostReceipt.get(key))is not dict or any(hostReceipt[key].get(k)!=context[k]for k in('run','epoch')):raise ValueError('HOST_OUTSIDE_COMMIT_MISSING')
    if APReceipt.get('parentDrainFinished')is not True or APReceipt.get('error')is not None or type(APReceipt.get('terminalSHA256'))is not str or SHA.fullmatch(APReceipt['terminalSHA256'])is None:raise ValueError('AP_OUTSIDE_TERMINAL_MISSING')
    j=nativeCheckpoint.get('journal',{});authority=nativeCheckpoint.get('input',{})
    if nativeCheckpoint.get('generation')!=context['generation']or nativeCheckpoint.get('closed')is not True or nativeCheckpoint.get('authorityRestorable')is not False or j.get('closed')is not True or type(j.get('commitAnchor'))is not str or SHA.fullmatch(j['commitAnchor'])is None:raise ValueError('NATIVE_OUTSIDE_CLOSED_ANCHOR_MISSING')
    if authority.get('consent')is not False or authority.get('leaseId')is not None:raise ValueError('NATIVE_AUTHORITY_NOT_REVOKED')
    return {'liveParentBackend':hostReceipt,'liveParentAP':APReceipt,'nativeClosedCheckpoint':nativeCheckpoint,'RootSelectedPackageObservation':packageObservation,'scope':'LIVE_ROOT_CHANNEL_LOCAL_ORCHESTRATION_BINDING_NOT_REMOTE_AUTHENTICATION','APExitNeverProvesGround':True,'groundOrFlightAccepted':False,'priorMOCKReviewsPromoted':False}
