"""Fresh12 task resource baseline; all previous closed campaigns remain immutable."""
from pathlib import Path
import json,hashlib
from importlib import import_module
from . import contract
R=Path(__file__).resolve().parents[4];E=R/'evidence/betaintegrated01-cockpit05-release12';PLAN=contract.TASK_PLANNING;MIB=2**20
LEDGER=E/'avd-baseline.json'
def allocated(root):return sum(p.lstat().st_blocks*512 for p in Path(root).rglob('*')if p.is_file()and not p.is_symlink())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def baseline():
 v=json.loads(LEDGER.read_text());expected=R/'.local/betaintegrated01/android/avd/aeris-beta-m1.avd'
 if v.get('path')!=str(expected)or type(v.get('allocatedBytes'))is not int or v['allocatedBytes']<0:raise ValueError('FRESH12_ACTUAL_AVD_BASELINE_REQUIRED')
 return v

def metadata_total():
 _frozen_metadata=import_module('planning.betaintegrated01.cockpit05-compact10.flight.metadata')
 allocated_metadata=_frozen_metadata.allocated_metadata
 return allocated_metadata(E)+allocated(PLAN)
def avd_growth(current):return max(0,current-baseline()['allocatedBytes'])
def short_tar_cap():return int(23.75*MIB)
def assert_shared_caps(current_avd):
 if metadata_total()>64*MIB:raise ValueError('TASK12_METADATA64MiB_CAP')
 if avd_growth(current_avd)>512*MIB:raise ValueError('TASK12_AVD512MiB_CAP')
 return baseline()
def cold_caps(control):
 from .export_native import exports
 a=json.loads((contract.GUARDIAN/'admission.json').read_text());v=baseline()
 if a.get('task12AVDBaselineSHA256')!=sha(LEDGER)or a.get('task12AVDOriginalBaseline')!=v['allocatedBytes']:raise ValueError('GUARD_TASK12_BASELINE_BINDING')
 total=sum(p.stat().st_size for p in exports())
 if total>192*MIB or metadata_total()>64*MIB:raise ValueError('COLD12_EXPORT_OR_METADATA_CAP')
 return dict(task12AVDBaselineSHA256=sha(LEDGER),exportBytes=total,globalExportCapBytes=192*MIB,metadataBytes=metadata_total(),metadataCapBytes=64*MIB,shortTarCapBytes=short_tar_cap(),longTarCapBytes=int(167.75*MIB),oldCampaignsNotPromoted=True)
