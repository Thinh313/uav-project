"""07+08 cumulative finite caps. Prior retained bytes are not new disk reservations."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[4]
E=R/'evidence/betaintegrated01-cockpit05-clockorder08'
PRIOR=R/'evidence/betaintegrated01-cockpit05-nativeio07'
PRIOR_PLAN=R/'planning/betaintegrated01/cockpit05-nativeio07/flight'
PLAN=Path(__file__).parent
MIB=2**20
LEDGER=E/'prior07-ledger01.json'
def allocated(root):return sum(p.lstat().st_blocks*512 for p in Path(root).rglob('*')if p.is_file()and not p.is_symlink())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prior():
 v=json.loads(LEDGER.read_text())
 if v.get('format')!='aeris-clockorder08-prior07-cumulative-ledger'or type(v.get('version'))is not int or v['version']!=1:raise ValueError('PRIOR_LEDGER_SCHEMA')
 for k in('priorEvidenceAllocatedBytes','priorPlanningAllocatedBytes','priorMetadataAllocatedBytes','cumulativeAVDOriginalBaseline','closed07AVDAllocatedBytes','priorPositiveAVDGrowthBytes','priorExportBytes'):
  if type(v.get(k))is not int or v[k]<0:raise ValueError('PRIOR_LEDGER_TYPED_COUNTS')
 if v['priorEvidenceRoot']!=str(PRIOR)or v['priorPlanningRoot']!=str(PRIOR_PLAN)or v['globalExportCapBytes']!=192*MIB or v['globalMetadataCapBytes']!=64*MIB or v['cumulativeAVDGrowthCapBytes']!=512*MIB or v['cumulativeAVDOriginalBaseline']!=752848896:raise ValueError('PRIOR_LEDGER_SCOPE')
 if sha(v['prior07HandoffPath'])!=v['prior07HandoffSHA256']or v['prior07HandoffSHA256']!='4b81c329ac33490d03ce1113641232c32c3995a240a544dd706e89e19a0d0138':raise ValueError('PRIOR_SEAL_ANCHOR')
 paths=v['priorExportPaths']
 if len(paths)!=2 or sum(p['bytes']for p in paths)!=v['priorExportBytes']:raise ValueError('PRIOR_EXPORT_SUM')
 for p in paths:
  path=R/p['path']
  if not path.is_relative_to(PRIOR)or not path.is_file()or path.is_symlink()or path.stat().st_size!=p['bytes']:raise ValueError('PRIOR_EXPORT_PATH_SIZE')
 return v

def verify_prior_allocation():
 v=prior()
 if allocated(PRIOR)!=v['priorEvidenceAllocatedBytes']or allocated(PRIOR_PLAN)!=v['priorPlanningAllocatedBytes']:raise ValueError('SEALED_PRIOR_ALLOCATION_CHANGED')
 return v

def metadata_total():
 from .metadata import allocated_metadata
 return allocated_metadata(PRIOR)+allocated(PRIOR_PLAN)+allocated_metadata(E)+allocated(PLAN)
def avd_growth(current):return max(0,current-prior()['cumulativeAVDOriginalBaseline'])
def retained_prior_allocation():
 v=prior();return v['priorEvidenceAllocatedBytes']+v['priorPlanningAllocatedBytes']
def short_tar_cap():
 # Preserve long tar167.75MiB and two08 diagnostic slots; prior07 is actual debit.
 return min(int(23.75*MIB),192*MIB-prior()['priorExportBytes']-int(167.75*MIB)-2*256*1024)
def assert_shared_caps(current_avd):
 v=verify_prior_allocation()
 if metadata_total()>64*MIB:raise ValueError('CUMULATIVE07_08_METADATA64MiB_CAP')
 if avd_growth(current_avd)>512*MIB:raise ValueError('CUMULATIVE07_08_AVD512MiB_CAP')
 if short_tar_cap()<=0:raise ValueError('NO_REMAINING_SHORT_EXPORT_CAP')
 return v

def cold_caps(control):
 from .export_native import exports
 v=verify_prior_allocation();admission=json.loads((E/'emulator01/admission.json').read_text())
 if admission.get('prior07LedgerSHA256')!=sha(LEDGER)or admission.get('cumulativeAVDOriginalBaseline')!=v['cumulativeAVDOriginalBaseline']:raise ValueError('GUARD_CUMULATIVE_LEDGER_BINDING')
 total=sum(p.stat().st_size for p in exports())
 if total>192*MIB or metadata_total()>64*MIB:raise ValueError('COLD_CUMULATIVE_EXPORT_OR_METADATA_CAP')
 return dict(prior07LedgerSHA256=sha(LEDGER),priorExportBytes=v['priorExportBytes'],cumulativeExportBytes=total,globalExportCapBytes=192*MIB,cumulativeMetadataBytes=metadata_total(),globalMetadataCapBytes=64*MIB,cumulativeAVDOriginalBaseline=v['cumulativeAVDOriginalBaseline'],shortTarCapBytes=short_tar_cap(),longTarCapBytes=int(167.75*MIB),old07NotPromoted=True)
