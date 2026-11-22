"""One explicit guest filesystem barrier, not adb file-transfer sync or proof of persistence."""
import time
from pathlib import Path
from .metadata_budget import capture_command,encoded

def guardian_sync(adb,budget,root,check):
 argv=[str(adb),'-s','emulator-5582','shell','sync'];start=time.monotonic_ns();deadline=start+2_000_000_000;value=None;failure=None
 with budget.operation({'guardian':64+128+12288}):
  try:
   value=capture_command(budget,'guardian',argv,deadline_ns=deadline,stdout_limit=64,stderr_limit=128,check_live=check)
   failure=value['failure']
   if failure is None and(not value['captureComplete']or type(value['exit'])is not int or value['exit']!=0 or value['stdout']or value['stderr']):failure=RuntimeError('GUEST_SYNC_EXACT_EMPTY_SUCCESS_REQUIRED')
  except BaseException as error:failure=error
  row={'format':'aeris-h4-guarded-guest-sync','version':1,'argv':argv,'startedHostNs':start,'finishedHostNs':time.monotonic_ns(),'deadlineHostNs':deadline,'exit':None if value is None else value['exit'],'captureComplete':False if value is None else value['captureComplete'],'stdoutHex':None if value is None else value['stdout'].hex(),'stderrHex':None if value is None else value['stderr'].hex(),'failure':None if failure is None else type(failure).__name__+':'+str(failure)[:512],'status':'BARRIER_OBSERVED_NOT_STORAGE_CERTIFICATION'if failure is None else'UNKNOWN_BARRIER_NOT_ACCEPTANCE','flightAcceptance':False,'freshBootQualificationStillRequired':True}
  budget.write('guardian',Path(root)/'guest-sync-h4.json',encoded(row),closing=failure is not None)
  if failure is not None:raise failure
  return row

def device_sync(device):
 need=lambda v:None if v else(_ for _ in()).throw(ValueError('H4_GUEST_SYNC_EXACT_ONCE_EMPTY_RESULT'))
 need(not getattr(device,'_guest_sync_h4_attempted',False));device._guest_sync_h4_attempted=True
 result=device.command(['shell','sync'],deadline_ns=device.now()+2_000_000_000,maximum_bytes=64);need(result==b'');return device.last_command_ref
