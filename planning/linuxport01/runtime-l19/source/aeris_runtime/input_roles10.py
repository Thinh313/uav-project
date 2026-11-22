"""Finite original held input roles, with unchanged metadata safety domain.

Every new planning file is metadata. Only the exact held static resources in
this pinned152-path table use the original external-readonly resource domain.
"""
from pathlib import Path
import hashlib,json,stat
from .paths import repository,PACKAGE_ROOT
BASE='0d7d786666e502f9371860186eab5b98d7177dc31824d94bb3709fdc25e91f98'
APPROVED_ROWS_SHA256='d6d50e5fa1b6dcfa724a8ecea11bd89b1fcc93acce5a20e3d888392e18fbb6ab'
ROLES={'METADATA_SOURCE_TEXT','EXTERNAL_READONLY_BINARY','EXTERNAL_READONLY_VENDOR'}
def inputs(*,verify_hashes=True,deadline_check=None):
 repo=repository();value=json.loads((PACKAGE_ROOT/'assets/input-roles10.json').read_bytes());original=json.loads((repo/'evidence/betasim-integrated01/candidates'/BASE/'candidate.json').read_bytes())
 from .candidate import canonical
 if hashlib.sha256(canonical(original)).hexdigest()!=BASE or value.get('baseCandidate')!=BASE or value.get('format')!='aeris-fixed-ipc10-input-roles'or value.get('version')!=1:raise ValueError('IPC10_ORIGINAL_INPUT_ROLE_BINDING')
 rows=value.get('rows')
 if hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=APPROVED_ROWS_SHA256:raise ValueError('IPC10_EXACT_APPROVED_ROLE_TABLE')
 pins=original['productSourceSHA256']
 if type(rows)is not list or len(rows)!=152 or len({z.get('path')for z in rows})!=152:raise ValueError('IPC10_FINITE_INPUT_ROLES')
 counts={k:0 for k in ROLES}
 for row in rows:
  if deadline_check is not None:deadline_check()
  if set(row)!={'path','sha256','role'}or row['role']not in ROLES or pins.get(row['path'])!=row['sha256']:raise ValueError('IPC10_UNKNOWN_OR_CHANGED_INPUT_ROLE')
  counts[row['role']]+=1;path=repo/row['path']
  if any(p.is_symlink()for p in[path,*path.parents])or not stat.S_ISREG(path.lstat().st_mode):raise ValueError('IPC10_INPUT_REGULAR_NO_ALIAS')
  if verify_hashes:
   digest=hashlib.sha256()
   with path.open('rb')as stream:
    while True:
     if deadline_check is not None:deadline_check()
     chunk=stream.read(65536)
     if not chunk:break
     digest.update(chunk)
   if digest.hexdigest()!=row['sha256']:raise ValueError('IPC10_INPUT_SHA_DRIFT:'+row['path'])
 if counts!={'METADATA_SOURCE_TEXT':123,'EXTERNAL_READONLY_BINARY':11,'EXTERNAL_READONLY_VENDOR':18}:raise ValueError('IPC10_FIXED_ROLE_COUNTS')
 return rows
