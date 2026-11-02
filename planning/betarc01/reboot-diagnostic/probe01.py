"""Finite read-only reboot evidence, never installer or flight acceptance."""
from pathlib import Path
import json,re,time
from aeris_runtime.android import ANDROID_READY_SCRIPT
from aeris_runtime.once_reader import read_ref
from planning.betarc01.diagnostics.package_device01 import ReadOnlyPackageDevice,private_export_eligible,PACKAGE,PRIVATE,COLD,STAT,need
SAMPLE_OFFSETS=(0,30,60)
SAMPLE_COMMANDS=(('shell','getprop','sys.boot_completed'),('shell','cat','/proc/sys/kernel/random/boot_id'),('shell','dumpsys','user'),('shell','pm','path','--user','0',PACKAGE),('shell','dumpsys','package',PACKAGE))
FIXED_COMMANDS=(('shell','cat','/proc/mounts'),('shell','df','-k','/data'),('shell','getprop','ro.crypto.state'),('shell','getprop','init.svc.vold'),('shell','getprop','sys.user.0.ce_available'),('shell','logcat','-d','-b','all','-v','threadtime','-t','120','PackageManager:V','PackageManagerService:V','PackageInstaller:V','installd:V','vold:V','StorageManagerService:V','*:S'))
class RebootReadOnlyDevice(ReadOnlyPackageDevice):
 def bind_path(self,base):
  need(type(base)is str and re.fullmatch(r'/data/app/~~[A-Za-z0-9_=-]{1,96}/vn[.]rtr[.]aeris[.]betasim09-[A-Za-z0-9_=-]{1,96}/base[.]apk',base)is not None,'SAFE_M201_ORIGINAL_CODE_PATH');self.current_base=base
 def _command_bound(self,args):
  need(self.serial=='emulator-5582'and self.observer.tag=='AERIS_PRODUCT_STATUS','EXACT_DIAGNOSTIC_DEVICE')
  if tuple(args)in SAMPLE_COMMANDS or tuple(args)in FIXED_COMMANDS:return 65536
  if args in(['shell','stat','-c','%F %u %g %s',self.current_base],['shell','sha256sum',self.current_base],['shell','sh','-c',STAT],['shell','sh','-c',COLD],['shell','id','-u']):return 4096
  if args in(['wait-for-device'],['root'],['shell','cat','/proc/sys/kernel/random/boot_id'],['shell','sh','-c',ANDROID_READY_SCRIPT]):return super()._command_bound(args)
  raise ValueError('REBOOT_DIAGNOSTIC_READONLY_FINITE_GRAMMAR')
def observe(device,args):
 args=list(args);before=device.sequence;error=None
 try:device.command(args,deadline_ns=device.now()+10_000_000_000,maximum_bytes=device._command_bound(args))
 except RuntimeError as exc:
  row=device.last_command;need(device.sequence==before+1 and row is not None and row.get('sequence')==device.sequence and row.get('captureComplete')is True and row.get('failure')in('RuntimeError:ANDROID_COMMAND_EXIT:'+str(row.get('exit')),'RuntimeError:ANDROID_COMMAND_STDERR_PREFIX_RETAINED_FAILURE'),'COMPLETE_ORIGINAL_FAILED_READ_ONLY');error=str(exc)
 row=device.last_command;out=read_ref(device.root,row['stdoutRef']);err=read_ref(device.root,row['stderrRef']);return {'command':args,'commandReceiptRef':device.last_command_ref,'status':'OBSERVED_EXIT0_EMPTY_STDERR'if error is None else'UNKNOWN_NONZERO_OR_STDERR_ORIGINAL_PRESERVED','exit':row['exit'],'error':error,'stderrBytes':len(err),'startedHostNs':row['startedHostNs'],'endedHostNs':row['endedHostNs']},out

def sample_series(device,check,ready_ns,emit,*,now=time.monotonic_ns,sleep=time.sleep):
 samples=[]
 for offset in SAMPLE_OFFSETS:
  target=ready_ns+offset*1_000_000_000
  while now()<target:
   check();remaining=target-now()
   if remaining>0:sleep(min(.1,remaining/1e9))
  check();started=now();rows=[];boot=None
  for args in SAMPLE_COMMANDS:
   row,out=observe(device,args);rows.append(row)
   if args==('shell','cat','/proc/sys/kernel/random/boot_id')and row['status']=='OBSERVED_EXIT0_EMPTY_STDERR':boot=out.decode('ascii').strip()
  stat,out=observe(device,['shell','stat','-c','%F %u %g %s',device.current_base]);rows.append(stat)
  if stat['status']=='OBSERVED_EXIT0_EMPTY_STDERR'and out.startswith(b'regular file '):row,_=observe(device,['shell','sha256sum',device.current_base]);rows.append(row)
  value={'offsetSeconds':offset,'targetHostNs':target,'startedHostNs':started,'finishedHostNs':now(),'actualOffsetSeconds':(started-ready_ns)/1e9,'kernelBootUUID':boot,'observations':rows};emit(value);samples.append(value)
 return samples
