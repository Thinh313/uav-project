"""Finite RC case contracts; no receipt alone grants flight or storage authority."""
from pathlib import Path
import hashlib,json,re,time
from .paths import repository
from .metadata_budget import encoded
from .mission16 import SLOTS,common_bindings

KINDS={'g109':'native','g108':'native','g107':'native','g106':'native','g105':'native','g104':'native','g103':'native','g101':'native','g102':'native','g201':'polygon','g202':'polygon','g203':'corridor','g204':'corridor','g301':'link-loss','g302':'ap-reboot','g303':'native-restart','g304':'native-restart','g401':'integrated','g402':'integrated'}
# Maximum new direct generations before each case can finish. The two G1
# sessions, nominal restart and interrupted native restart are all charged.
GENERATIONS={k:2 if v in('native','polygon','corridor','integrated','native-restart') else 1 for k,v in KINDS.items()}
# No caller can lower the remaining requirement. Archive boundaries are
# future gates, never a credit before the original cold proof exists.
REMAINING={'g109':0,'g108':0,'g107':0,'g106':0,'g105':0,'g104':0,'g103':0,'g101':0,'g102':0,'g201':2,'g202':2,'g203':0,'g204':0,'g301':5,'g302':4,'g303':2,'g304':2,'g401':0,'g402':0}
REPAIR_RESERVE=2
ARCHIVE_BOUNDARY={k:('G1_UNUSED_BEFORE_G2'if k.startswith('g1')else'G2_CLOSED_BEFORE_FAULTS'if k.startswith('g2')else'NO_ARCHIVE_AFTER_POSSIBLY_UNRESOLVED_NATIVE_FAULT')for k in KINDS}

ARCHIVE_BOUNDARY['g104']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'
ARCHIVE_BOUNDARY['g105']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'
ARCHIVE_BOUNDARY['g106']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'
ARCHIVE_BOUNDARY['g107']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'
ARCHIVE_BOUNDARY['g108']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'
ARCHIVE_BOUNDARY['g109']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'

def need(v,n):
 if not v:raise ValueError('RC01_'+n)
def ref_file(ref,*,maximum=262144):
 need(type(ref)is dict and set(ref)=={'path','bytes','sha256'},'REFERENCE_SCHEMA');p=Path(ref['path']).absolute();repo=repository();need(p.is_relative_to(repo/'evidence')and not any(x.is_symlink()for x in[p,*p.parents])and p.is_file()and p.stat().st_nlink==1 and type(ref['bytes'])is int and 0<ref['bytes']<=maximum and p.stat().st_size==ref['bytes']and re.fullmatch('[a-f0-9]{64}',ref['sha256']),'REFERENCE_SCOPE_BOUND');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256'],'REFERENCE_SHA');return p,raw

def storage_anchor(path,digest,manifest):
 p=Path(path).absolute();need(p.is_relative_to(repository()/'evidence/betarc01')or p.is_relative_to(repository()/'evidence/nativejournal17'),'STORAGE_ANCHOR_SCOPE');need(p.is_file()and not any(x.is_symlink()for x in[p,*p.parents])and p.stat().st_size<=32768,'STORAGE_ANCHOR_BOUND');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==digest,'STORAGE_ANCHOR_SHA');v=json.loads(raw);need(v.get('format')=='aeris-betarc01-root-native-storage-anchor'and v.get('version')==1 and v.get('authorityRestorable')is False and v.get('APKSHA256')==manifest['native']['APK_SHA256']and v.get('nativeSourceSHA256')==manifest['native']['sourceSHA256']and re.fullmatch('[a-f0-9]{64}',v.get('registryHead',''))and v['registryHead']!='0'*64,'STORAGE_ANCHOR_IDENTITY');need(type(v.get('archiveReceivers'))is list and 1<=len(v['archiveReceivers'])<=8 and type(v.get('approvedSources'))is list and len(v['approvedSources'])<=8,'STORAGE_ANCHOR_FINITE_SOURCES');return v

def generation_forecast(active,slot,*,remaining_generations):
 need(type(active)is int and 0<=active<=8 and slot in GENERATIONS and type(remaining_generations)is int and remaining_generations>=0,'GENERATION_FORECAST_TYPES');need(remaining_generations==REMAINING[slot],'SOURCE_HELD_REMAINING_PLAN_NO_CALLER_DISCOUNT');required=GENERATIONS[slot];need(active+required+remaining_generations+REPAIR_RESERVE<=8,'ACTIVE8_FULL_CAMPAIGN_FORECAST_REFUSED_NO_START');return {'activeObserved':active,'currentCaseMaximumNew':required,'remainingPlannedNew':remaining_generations,'repairReserve':REPAIR_RESERVE,'projectedMaximumActive':active+required+remaining_generations+REPAIR_RESERVE,'nextExplicitArchiveBoundary':ARCHIVE_BOUNDARY[slot],'activeLimit':8,'refundOrReset':False,'unresolvedGenerationMayNotRotate':True}

def qualify_existing(owner,case,anchor_path,anchor_sha,node,*,remaining_generations):
 """PRESENT-only package observation, complete cold data replay before Activity."""
 need(not getattr(case['device'],'migration17_verified',False),'QUALIFY_ONCE_BEFORE_ACTIVITY');a=storage_anchor(anchor_path,anchor_sha,owner.manifest);case['native'].install_selected(owner.candidate,owner.digest,deadline_ns=time.monotonic_ns()+90_000_000_000)
 d=case['device'];auth=json.loads(__import__('aeris_runtime.once_reader',fromlist=['read_ref']).read_ref(d.root,case['native'].application_domain['authorizationRef']));backup=auth['existingNewDomainBackup'];need(auth['targetPackagePresenceClassification']=='PRESENT'and auth['noClearWipeRenameOrDelete']is True and auth['counterResetOrCreditRefund']is False,'GENUINE_PRESENT_WITHOUT_INSTALL')
 from planning.betarc01.tar_profile_h7.archive import verify_storage
 proof=verify_storage(backup['path'],backup['sha256'],a['registryHead'],source_candidate=owner.digest,archive_receivers=a['archiveReceivers'],approved_sources=a['approvedSources'],node=node)
 need(proof['pendingTransactions']==0 and proof['allArchiveReceiversVerified']is True,'ACTUAL_COLD_REGISTRY_COMPLETE');active=sum(x.startswith('files/product-input01/')and x.endswith('.aj02')for x in proof['originalInputFiles']);forecast=generation_forecast(active,owner.root.name,remaining_generations=remaining_generations)
 # The exact observed index head is an external anchor, never a claimed
 # current clock/authority. Activity is admitted only after full-byte replay.
 case['storageAnchorRC01']=a;case['storageProofBeforeRC01']=proof;case['generationForecastRC01']=forecast;case['device'].migration17_verified=True;case['native'].continuation_storage_anchor=a
 owner.write('native-storage-before-rc01.json',{'format':'aeris-betarc01-prelaunch-native-storage-proof','version':1,'candidateSHA256':owner.digest,'nativeTARSHA256':backup['sha256'],'proof':proof,'generationForecast':forecast,'authorityRestorable':False});return proof

def qualify_closed(owner,case,node):
 """Current originals are checked against all archive receipts before crypto."""
 a=case['storageAnchorRC01'];export=case['native'].closed_export['export']
 from planning.betarc01.tar_profile_h7.archive import verify_storage
 selected=[x['snapshot']['input']['journal']['generation']for x in case['native'].archived_lifecycles]+[case['native'].closed_snapshot['input']['journal']['generation']]
 proof=verify_storage(export['path'],export['sha256'],case['storageProofBeforeRC01']['registryHead'],source_candidate=owner.digest,archive_receivers=a['archiveReceivers'],approved_sources=a['approvedSources'],node=node,require_selected_closed=selected)
 raw=encoded(proof);need(len(raw)<=65536,'CLOSED_REGISTRY_PROOF64K');path=owner.root/'reports/native-journal17-archive-proof.json';ref=owner.budget.write('external_task',path,raw);case['archiveProofRef17']={'path':str(path),'bytes':len(raw),'sha256':ref['sha256']};return proof
