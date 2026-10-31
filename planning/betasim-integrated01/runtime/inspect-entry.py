#!/usr/bin/env python3
"""Read-only pre-HOLD entry/config/native-artifact inspection; starts no actors."""
from pathlib import Path
import ast,hashlib,json,os,sys
P=Path(__file__).resolve();R=P.parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(P.parent/'source'),str(R)]
from aeris_runtime import policy,candidate
from aeris_runtime.entry import module_origin_receipt
bpath=R/'evidence/betasim-integrated01/product/native-build01.json';b=json.loads(bpath.read_bytes());apk=(R/b['apk']).read_bytes();archive=(R/b['inputArchive']).read_bytes();candidate._native_verify(b,archive,apk)
params=json.loads((P.parent/'source/aeris_runtime/assets/workbench-profiles/nominal/typed-profile.json').read_bytes());assert params['id']=='WORKBENCH_SIM_V1'and len(params['parameters'])==39 and params['parameters']['FS_OPTIONS']['value']==0 and params['parameters']['FS_GCS_ENABLE']['value']==5
configs=[]
for seconds in(180,760):
 c=policy.build_config('workbench','source-inspect','a'*32,'b'*32,R/'evidence/betasim-integrated01/runtime/never-started-raw','nominal',maximum_seconds=seconds);policy.validate_recording_policy(c);assert c['requestedSpeedup']==1 and c['capMs']==500 and c['providerKind']=='WORKBENCH_SIM_V1'and c['rateHz']==1200;configs.append({'seconds':seconds,'configSHA256':c['expectedConfigSHA256'],'budget':policy.case_budget(maximum_seconds=seconds),'actorStarted':False})
origins=module_origin_receipt(P.parent);parses=[]
for p in(P.parent/'source/aeris_runtime').rglob('*.py'):ast.parse(p.read_bytes(),str(p));parses.append(str(p.relative_to(R)))
old=R/'evidence/runtime-transport15-atomic-prep/reports/cached-image-preflight01.json';cached=json.loads(old.read_bytes());assert cached['exit']==0 and cached['containerStarted']is False
report={'format':'aeris-source-entry-inspection','version':1,'status':'PASS_SOURCE_ONLY_NOT_ADMISSION_OR_RUNTIME','runtimeRoot':str(P.parent),'sourceOrigins':origins,'parsedSourceFiles':len(parses),'typedProfileSHA256':candidate.sha(P.parent/'source/aeris_runtime/assets/workbench-profiles/nominal/typed-profile.json'),'typedProfile':'WORKBENCH_SIM_V1','typedParameters':39,'controlParmSHA256':candidate.sha(P.parent/'source/aeris_runtime/assets/workbench-profiles/nominal/control.parm'),'nativeAPK_SHA256':b['sha256'],'nativeReceiptSHA256':candidate.sha(bpath),'nativeSourceSHA256':b['sourceSHA256'],'sourceConfigChecks':configs,'spec':str(R/'evidence/runtime-observe04/emulator-spec.json'),'image':cached['stdout'].strip(),'imageOriginalReadOnlyReference':{'path':str(old.relative_to(R)),'sha256':candidate.sha(old)},'liveImageOrAdmissionVerified':False,'newCandidateFrozen':False,'actorsStarted':False,'scope':'source entry imports/config/typed/native archive checks only; no SDK/emulator/AP/browser/clock acceptance'}
p=R/'evidence/betasim-integrated01/runtime/source-entry-inspection.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('status','parsedSourceFiles','typedParameters','nativeAPK_SHA256','image','actorsStarted')}))
