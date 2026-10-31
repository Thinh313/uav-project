"""Read-only COCKPIT05 soak identity contract. No launch, ADB or network calls."""
from pathlib import Path
import hashlib,json,zipfile
from pilot.betaintegrated01.cockpit04.revision02.capacity import task_budget
from pilot.betaintegrated01.cockpit04.revision02.confirmation import launch_context
from planning.betaintegrated01.m1cockpit04.host.launch_fixture import build_config as old_build_config
ROOT=Path(__file__).resolve().parents[4]
PACKAGE='vn.rtr.aeris.cockpit05'
ACTIVITY=PACKAGE+'/.CockpitActivity'
APK_SHA256='c76669fa97326232c6129d0f93d3b12751a424a0ce724669ff51e29f6db958c3'
SOURCE_SHA256='4fe53ee61afd133a9075c7e1736e09406fb4449afc7ce2c01c0c45c9a3926c23'
EVIDENCE='evidence/betaintegrated01-cockpit05-soak'
BUILD='evidence/betaintegrated01-cockpit05-native/build-02.json'
MANIFEST='evidence/betaintegrated01-m1cockpit04/host/module-manifest02.json'
MANIFEST_SHA256='df581d0713ca6a1caa334c69a54400836d9e93b59ed804b73fa34be456b6bfa3'
PROVIDERS='planning/betaintegrated01/m1cockpit04/native/expected-providers01.json'


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb')as f:
        for block in iter(lambda:f.read(2**20),b''):digest.update(block)
    return digest.hexdigest()


def build_input_contract(repository=ROOT):
    r=Path(repository);receipt=json.loads((r/BUILD).read_text());prior=json.loads((r/MANIFEST).read_text())
    if sha(r/MANIFEST)!=MANIFEST_SHA256:raise ValueError('FROZEN_RUNTIME_MANIFEST_IDENTITY')
    if receipt['sha256']!=APK_SHA256 or receipt['sourceSHA256']!=SOURCE_SHA256 or len(receipt['sourcePins'])!=37:raise ValueError('SELECTED_APK02_BUILD_IDENTITY')
    if len(prior['sourceSHA256'])!=107:raise ValueError('ORIGINAL_107_RUNTIME_INPUTS_REQUIRED')
    sources=dict(prior['sourceSHA256'])
    for name,h in receipt['sourcePins'].items():
        if name in sources and sources[name]!=h:raise ValueError('SHARED_SOURCE_DISAGREEMENT')
        sources[name]=h
    drift=[name for name,h in sources.items()if sha(r/name)!=h]
    if drift:raise ValueError({'FROZEN_INPUT_DRIFT':drift})
    apk=r/receipt['apk'];bundle=json.loads((r/PROVIDERS).read_text())
    if sha(apk)!=APK_SHA256:raise ValueError('SELECTED_APK02_BYTES')
    profile_proofs={}
    with zipfile.ZipFile(apk)as archive:
        if len(archive.namelist())!=len(set(archive.namelist())):raise ValueError('APK_DUPLICATE_MEMBERS')
        if archive.read('assets/expected-providers.json')!=(r/PROVIDERS).read_bytes():raise ValueError('PACKAGED_PROVIDER04_NOT_PINNED')
        if json.loads(archive.read('assets/source-identity.json'))['sourceSHA256']!=SOURCE_SHA256:raise ValueError('PACKAGED_SOURCE_IDENTITY')
        dex=archive.read('classes.dex')
        if b'Lvn/rtr/aeris/cockpit05/CockpitActivity;'not in dex or b'Lvn/rtr/aeris/cockpit04/'in dex:raise ValueError('INSTALLED_PACKAGE04_DEPENDENCY')
        for variant in ('nominal','loss'):
            base=r/'pilot/betaintegrated01/cockpit04/profiles'/variant;profile=json.loads((base/'run-profile02.json').read_text());typed=json.loads((base/'typed-profile01.json').read_text());provider=bundle['profiles'][profile['id']]
            if provider['configSHA256']!=sha(base/'run-profile02.json')or provider['typedSHA256']!=sha(base/'typed-profile01.json'):raise ValueError('PROVIDER_CONFIG_TYPED_IDENTITY')
            if provider['binarySHA256']!=profile['APSHA256']or provider['modelSHA256']!=profile['modelSHA256']:raise ValueError('PROVIDER_PHYSICAL_IDENTITY')
            if archive.read('assets/'+provider['typedAsset'])!=(base/'typed-profile01.json').read_bytes()or len(typed['parameters'])!=39:raise ValueError('PACKAGED_39_TYPED_BITS')
            old=json.loads((r/'runtime/betaintegrated01/control01'/variant/'typed-profile.json').read_text())
            if typed['parameters']!=old['parameters']:raise ValueError('PHYSICAL_PARAMETER_BITS_CHANGED')
            if profile['requestedSpeedup']!=1 or profile['capMs']!=500 or provider['durationSeconds']!=2000:raise ValueError('PACER_NATIVE_LIFETIME_CHANGED')
            for name,h in profile['parameterSHA256'].items():
                p=base/name if name=='control.parm'else r/'runtime/betaintegrated01/dist'/name
                if sha(p)!=h:raise ValueError('PARAMETER_FILE_DRIFT')
            if sha(r/'runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03')!=provider['binarySHA256']or sha(r/'pilot/betaintegrated01/runtime/physics.py')!=provider['modelSHA256']:raise ValueError('AP_MODEL_DRIFT')
            profile_proofs[variant]={'profileId':profile['id'],'configSHA256':provider['configSHA256'],'typedSHA256':provider['typedSHA256'],'APSHA256':provider['binarySHA256'],'modelSHA256':provider['modelSHA256'],'parameters':39,'parameterTreesExactOriginal':True}
    activity=(r/'native/betaintegrated01/cockpit05/src/vn/rtr/aeris/cockpit05/CockpitActivity.java').read_text()
    if 'vn.rtr.aeris.cockpit04'in activity or 'new WorkspaceStore(new File(getFilesDir(),"workspace03")'not in activity:raise ValueError('PRIVATE_PACKAGE_NAMESPACE')
    metadata={name:sha(r/name)for name in(BUILD,MANIFEST,PROVIDERS,'evidence/betaintegrated01-cockpit05-native/qa/apk-closure02.json','planning/betaintegrated01/cockpit05-native/RUNNER02.md')}
    return {'format':'aeris-cockpit05-soak-input-contract','version':1,'status':'STATIC_INPUT_CLOSURE_ONLY_NOT_RUNTIME_ACCEPTANCE','package':PACKAGE,'activity':ACTIVITY,'apk':receipt['apk'],'apkSHA256':APK_SHA256,'APKSourceSHA256':SOURCE_SHA256,'priorRuntimeManifestSHA256':MANIFEST_SHA256,'originalRuntimeInputs':107,'selectedAPKInputs':37,'sourceSHA256':sources,'metadataSHA256':metadata,'profiles':profile_proofs,'capacity':task_budget(),'newEvidenceRoot':EVIDENCE,'privatePaths':{'binding':'files/launch-binding.json','workspace':'files/workspace03','selectedRun':'files/control-runs/<newRun>/'},'installedCockpit04PackageRequired':False,'shared04CompiledSourcesAndProviderIDsIntentional':True,'priorMOCKReviews':'KEEP_EXACT_BYTES_NONAUTHORITATIVE','priorDraftRevisions':[1,2,3,4,5],'newActualDraftRevision':6,'runtimeStartsByBuilder':0,'productionSigning':False,'actualThirtyMinuteAccepted':False}


def expected_context(run,epoch,boot,generation,operator,variant='nominal',repository=ROOT):
    if variant not in('nominal','loss'):raise ValueError('PROFILE_VARIANT')
    bundle=json.loads((Path(repository)/PROVIDERS).read_text());p=bundle['profiles']['M1-COCKPIT04-'+variant.upper()]
    return launch_context({'run':run,'epoch':epoch,'boot':boot,'generation':generation,'operator':operator,'profileId':p['profileId'],'binarySHA256':p['binarySHA256'],'configSHA256':p['configSHA256']})


def build_config(repository,variant,run,epoch,boot,evidence,case_id,*,maximum_seconds=1960,wipe_state=True,state_reuse=None):
    if type(maximum_seconds)is not int or maximum_seconds!=1960:raise ValueError('ONE_COMBINED_1960_ONLY')
    result=old_build_config(repository,variant,run,epoch,boot,evidence,case_id,maximum_seconds=1960,wipe_state=wipe_state,state_reuse=state_reuse)
    # Attach as explicit Root test metadata; expected physical configSHA stays the
    # frozen run-profile02 bytes. The runtime does not consume these labels.
    result['selectedTestPackage']=PACKAGE;result['selectedTestAPKSourceSHA256']=SOURCE_SHA256
    result['externalResourcePolicy']=task_budget();result['legacyProfile02ResourceLabelsSuperseded']=True
    return result
