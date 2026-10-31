"""Actual selected Inventory implementation; tiny owned fixture, no actors/SDK."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys,json,time,hashlib
R=Path(__file__).resolve().parents[4];sys.path[:0]=[str(R/'planning/vidlife12/runtime/source'),str(R)]
from aeris_runtime.inventory import Inventory
from aeris_runtime import inventory,input_roles10,candidate
checks=0
with TemporaryDirectory(prefix='.inventory-prelude03-',dir=Path(__file__).parent)as scratch:
 root=Path(scratch).resolve();evidence=root/'evidence/vidlife12/s01';evidence.mkdir(parents=True);planning=root/'planning/vidlife12';planning.mkdir(parents=True);avd=root/'avd';avd.mkdir()
 for name in('aeris_runtime','native/mission-runtime','native/betasim-integrated01','native/betasim-application09'):(root/name).mkdir(parents=True,exist_ok=True)
 baseline={'format':'aeris-runtime-avd-baseline','version':1,'path':str(avd),'allocatedBytes':0,'observedHostNs':time.monotonic_ns(),'growthPolicy':'SUM_POSITIVE_PER_PATH_DEVICE_INODE_NO_CONTRACTION_OFFSET','fileAllocations':{}}
 with patch.object(inventory,'repository',return_value=root),patch.object(candidate,'repository',return_value=root),patch.object(input_roles10,'inputs',return_value=[]):
  inv=Inventory(evidence,planning,avd,baseline);prior=inv();before=evidence.parent/'before-hold02';before.mkdir();retained=before/'original-before-image.mjs';retained.write_bytes(b'ORIGINAL-EVIDENCE\n'*400);charged=retained.stat().st_blocks*512;after=inv();assert after['metadataBytes']-prior['metadataBytes']==charged;checks+=1
  assert after['artifactBytes']==prior['artifactBytes']and after['explicitRawExclusionCount']==0;checks+=1
  bad=evidence.parent/'undeclared-directory';bad.mkdir()
  try:inv()
  except ValueError as e:assert str(e)=='HOSTDIAG11_UNDECLARED_PRELUDE_ROOT:undeclared-directory';checks+=1
  else:raise AssertionError('undeclared directory accepted')
  bad.rmdir();link=evidence.parent/'untrusted-symlink';link.symlink_to(before,target_is_directory=True)
  try:inv()
  except ValueError as e:assert str(e)=='HOSTDIAG11_PRELUDE_SYMLINK';checks+=1
  else:raise AssertionError('symlink accepted')
  link.unlink();nested=before/'nested-symlink';nested.symlink_to(retained)
  try:inv()
  except ValueError as e:assert str(e)=='ALLOCATION_LEDGER_SYMLINK';checks+=1
  else:raise AssertionError('nested beforeimage symlink accepted')
  nested.unlink();assert inv()['metadataBytes']==after['metadataBytes'];checks+=1
p=R/'planning/vidlife12/runtime/source/aeris_runtime/inventory.py'
print(json.dumps({'format':'aeris-vidlife12-inventory-prelude03-mock','status':'PASS','checks':checks,'selectedSourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'retainedBeforeImageChargedAs':'METADATA','fixtureAllocatedBytesCharged':charged,'undeclaredDirectoryRefused':True,'symlinksRefused':True,'fixtureRemoved':not root.exists(),'SDKOrActorsStarted':False,'functionalVideoAccepted':False}))
