"""Explicit frozen-leaf repository mapping, separate from candidate code location."""
from pathlib import Path
import os
def repository():
 explicit=os.environ.get('AERIS_REPOSITORY_ROOT')
 if os.environ.get('AERIS_CANDIDATE_DIR') and not explicit:raise ValueError('CANDIDATE_REAL_REPOSITORY_EXPLICIT_REQUIRED')
 p=Path(explicit or str(Path(__file__).resolve().parents[1])).resolve()
 if not p.is_dir() or not (p/'pilot/betaintegrated01/runtime/ap_stage.py').is_file() or not (p/'native/mission-runtime').is_dir():raise ValueError('RUNTIME_REPOSITORY_REQUIRED')
 return p
PACKAGE_ROOT=Path(__file__).resolve().parent
