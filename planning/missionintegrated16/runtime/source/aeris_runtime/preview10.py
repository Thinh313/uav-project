"""Pure original-domain admission arithmetic BEFORE slot/ledger construction."""
from pathlib import Path
import hashlib,json,os,shutil,time
from .paths import repository
from .candidate import CAP as ARTIFACT_CAP,artifact_cap_admitted
from .inventory import Inventory,avd_allocations
from .metadata_budget import observer_envelope,encoded,CAP,BLOCK
from .policy import case_budget
from .input_roles10 import inputs

def _artifact_admitted(value):return artifact_cap_admitted(value)

def preview(candidate,digest,evidence,planning,spec,*,validate_candidate=True,seconds=180):
 from .mission16 import nominal_duration
 seconds=nominal_duration(Path(evidence).name,seconds)
 repo=repository();candidate=Path(candidate).resolve();evidence=Path(evidence).resolve();planning=Path(planning).resolve()
 if candidate.parent!=repo/'evidence/missionintegrated16/candidates'or evidence.parent!=repo/'evidence/missionintegrated16'or evidence.name not in('s01','s02','l01')or evidence.exists()or planning!=repo/'planning/missionintegrated16':raise ValueError('IPC10_FIXED_PREVIEW_SCOPE')
 from .pipeline_contract import artifact_cap_contract
 artifact_cap_contract()
 if validate_candidate:
  from .candidate import load
  selected=load(candidate,digest);artifact_cap_contract(selected)
 inputs(verify_hashes=True);config=json.loads(Path(spec).read_bytes());avd=Path(config['AVD']);rows=avd_allocations(avd)
 baseline={'format':'aeris-runtime-avd-baseline','version':1,'path':str(avd.resolve()),'observedHostNs':time.monotonic_ns(),'allocatedBytes':sum(v['allocatedBytes']for v in rows.values()),'fileAllocations':rows,'growthPolicy':'SUM_POSITIVE_PER_PATH_DEVICE_INODE_NO_CONTRACTION_OFFSET'}
 if len(encoded(baseline))>131072:raise ValueError('BOOTSTRAP_AVD_BASELINE128KiB')
 inv=Inventory(evidence,planning,avd,baseline,artifact_root=candidate.parent,preview=True)();forecast=case_budget(shutil.disk_usage(repo).free,seconds);baseline_charge=((len(encoded(baseline))+BLOCK-1)//BLOCK)*BLOCK+8192;current=inv['metadataBytes']+baseline_charge;future=observer_envelope()['totalFutureBytes']
 old=repo/'evidence/betasim-integrated01/r08/avd-baseline.json';oldraw=old.read_bytes();prior=json.loads(oldraw);oldgrowth=sum(max(0,row['allocatedBytes']-prior['fileAllocations'][n]['allocatedBytes'])if n in prior['fileAllocations']and all(row[k]==prior['fileAllocations'][n][k]for k in('device','inode'))else row['allocatedBytes']for n,row in rows.items())
 return {'format':'aeris-ipc10-readonly-admission-preview','version':1,'plannedSeconds':seconds,'slot':str(evidence),'slotCreated':False,'ledgerConstructed':False,'actorsStarted':False,'metadataCurrentBytes':current,'baselineAllocationUpperBound':baseline_charge,'metadataFutureIncludingClosureAndLedger':future,'metadataCap':CAP,'metadataAdmitted':current+future<=CAP,'metadataHeadroom':CAP-current-future,'artifactUnionBytes':inv['artifactBytes'],'artifactCap':ARTIFACT_CAP,'artifactAdmitted':_artifact_admitted(inv['artifactBytes']),'diskAdmitted':forecast['admitted'],'diskBudget':forecast,'inventory':inv,'avdBaselineSemantics':'UNCHANGED_ORIGINAL_PER_CAMPAIGN_FRESH_BASELINE_NOT_LIFETIME_RESET_OF_NATIVE_APP','oldR08BaselineRef':{'path':str(old.relative_to(repo)),'sha256':hashlib.sha256(oldraw).hexdigest(),'bytes':len(oldraw)},'retainedAVDActualAllocatedBytes':baseline['allocatedBytes'],'growthFromOldR08BaselineForDisclosureOnly':oldgrowth,'nativeLifetimeCounters':'NOT_RESET; genuine native admission still required after authorized boot','scope':'SOURCE_AND_RESOURCE_PREVIEW_NOT_NATIVE_OR_RUNTIME_ACCEPTANCE'}
