"""Finite source-qualified QA read-only commands. Not a release Device amendment."""
from pathlib import Path
import os,selectors,subprocess
from aeris_runtime.native17 import AndroidDomain17
from aeris_runtime.android import _capture_cleanup,_stop_capture_process
from pilot.betaintegrated01.runtime.ap_stage import canonical
PACKAGE='vn.rtr.aeris.betasim09'
PRIVATE='/data/user/0/'+PACKAGE
OLD_APK='/data/app/~~Va6nx-HHfoMTNy8IOwleEg==/vn.rtr.aeris.betasim09-6j4RNlDBOXdTOAE-0yN3xg==/base.apk'
COLD='if pidof '+PACKAGE+' >/dev/null; then echo RUNNING; else echo ABSENT; fi'
STAT='if [ -d '+PRIVATE+' ]; then stat -c "%F %u %g %i" '+PRIVATE+'; else echo PRIVATE_ABSENT; fi'
READ_COMMANDS={
 ('shell','getprop','sys.boot_completed'):256,
 ('shell','am','get-current-user'):256,
 ('shell','pm','list','users'):4096,
 ('shell','cmd','user','is-user-unlocked','0'):256,
 ('shell','pm','path','--user','0',PACKAGE):4096,
 ('shell','pm','list','packages','-u','--user','0',PACKAGE):4096,
 ('shell','dumpsys','package',PACKAGE):65536,
 ('shell','sh','-c',STAT):1024,
 ('shell','sh','-c',COLD):256,
 ('shell','ls','-ld',OLD_APK):2048,
 ('shell','sha256sum',OLD_APK):2048,
}
def need(value,label):
 if not value:raise ValueError('PACKAGE_QA_'+label)
def private_export_eligible(stat_row,stat_bytes,cold_row,cold_bytes,preparation):
 def positive(row):return row.get('status')=='OBSERVED_EXIT0_EMPTY_STDERR'and type(row.get('exit'))is int and row['exit']==0 and row.get('error')is None and type(row.get('stderrBytes'))is int and row['stderrBytes']==0
 root=preparation.get('format')=='aeris-owned-emulator-content-reader-preparation'and preparation.get('version')==2 and preparation.get('serial')=='emulator-5582'and preparation.get('actualUID0')is True and preparation.get('confirmation')=='READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED'
 return positive(stat_row)and positive(cold_row)and stat_bytes.startswith(b'directory ')and cold_bytes==b'ABSENT\n'and root

class ReadOnlyPackageDevice(AndroidDomain17):
 def _command_bound(self,args):
  need(self.serial=='emulator-5582'and self.observer is not None and self.observer.tag=='AERIS_PRODUCT_STATUS','OWNED_DEVICE_TAG')
  if tuple(args)in READ_COMMANDS:return READ_COMMANDS[tuple(args)]
  # Only frozen OS-readiness/content-reader grammar remains available. Never
  # delegate arbitrary original am/install/authority controls from this adapter.
  from aeris_runtime.android import ANDROID_READY_SCRIPT
  if args in(["wait-for-device"],["root"],["shell","id","-u"],["shell","cat","/proc/sys/kernel/random/boot_id"],["shell","sh","-c",ANDROID_READY_SCRIPT]):return super()._command_bound(args)
  raise ValueError('PACKAGE_QA_NOT_FIXED_READ_COMMAND')
 def export_root_private(self,*,deadline_ns):
  self._check_budget_actor();need(getattr(self,'diagnostic_root_cold_private',False)is True,'GENUINE_UID0_COLD_PRIVATE_REQUIRED');run=self.root.parent.name;target=self.root.parent/'native-restart-metadata.tar';maximum_bytes=64*2**20;metadata_only=True;full_original=False;product_full_closed=True
  need(not target.exists()and target.parent.resolve()==self.root.parent.resolve()and not any(p.is_symlink()for p in[target,*target.parents]),'EXCLUSIVE_FIXED_EXPORT')
  with self.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):return self._root_tar(target,run,maximum_bytes,metadata_only,full_original,product_full_closed,deadline_ns)
 def _root_tar(self,target,run,maximum_bytes,metadata_only,full_original,product_full_closed,deadline_ns):
  prior=sum(p.stat().st_size for p in target.parent.glob('native-*.tar')if p.is_file());maximum_bytes=min(maximum_bytes,192*2**20-prior)
  if maximum_bytes<=0:raise ValueError('EXPORT_ORIGINAL192MiB_AGGREGATE')
  self.budget.ensure('commands',16385+8192);self.budget.reserve_export(target,maximum_bytes);argv=[self.adb,'-s',self.serial,'exec-out','tar','-C',PRIVATE,'-cf','-','files'];argv_ref=self.store.command_bytes(canonical(argv));started=self.now();p=None;sel=selectors.DefaultSelector();count=0;seen=0;stderr=bytearray();failure=None;complete=False;result=None;file=None;cleanup_errors=[];retained=0
  try:
   file=target.open('xb');p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   for name,stream in [('stdout',p.stdout),('stderr',p.stderr)]:os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ,name)
   while sel.get_map():
    if self.live_check is not None:self.live_check()
    if self.now()>deadline_ns:raise TimeoutError('NATIVE_EXPORT_DEADLINE')
    for key,_ in sel.select(.05):
     name=key.data;limit=min(65536,maximum_bytes+1-seen)if name=='stdout'else min(65536,16385-len(stderr));raw=os.read(key.fileobj.fileno(),limit)
     if not raw:sel.unregister(key.fileobj);continue
     if name=='stderr':
      stderr.extend(raw)
      if len(stderr)>16384:raise ValueError('NATIVE_EXPORT_STDERR16KiB_PREFIX_INCOMPLETE')
     else:
      accepted=raw[:max(0,maximum_bytes-count)]
      if accepted:
       wrote=file.write(accepted)
       if wrote!=len(accepted):raise OSError('NATIVE_EXPORT_SHORT_WRITE')
       count+=wrote
      seen+=len(raw)
      if seen>maximum_bytes:raise RuntimeError('NATIVE_EXPORT_CAP_PREFIX_INCOMPLETE')
   code=p.wait(timeout=max(.01,(deadline_ns-self.now())/1e9))
   if code:raise RuntimeError('NATIVE_EXPORT_FAILED:'+str(code))
   if stderr:raise RuntimeError('ROOT_PRIVATE_EXPORT_STDERR_PREFIX_RETAINED')
   file.flush();os.fsync(file.fileno());complete=True
   from aeris_runtime.candidate import sha
   result={'path':str(target),'sha256':sha(target),'bytes':count,'startedHostNs':started,'finishedHostNs':self.now(),'argv':argv,'exit':code,'selectedRun':run,'readOnlyExport':True,'captureComplete':True}
  except BaseException as primary:failure=primary
  finally:
   operations=[]
   if p is not None:operations.append(('export-process-stop',lambda:_stop_capture_process(p)))
   operations.append(('export-selector-close',sel.close))
   if p is not None:operations.extend([('export-stdout-close',p.stdout.close),('export-stderr-close',p.stderr.close)])
   if file is not None:operations.extend([('export-file-flush',file.flush),('export-file-fsync',lambda:os.fsync(file.fileno())),('export-file-close',file.close)])
   failure=_capture_cleanup(failure,operations,cleanup_errors)
   if cleanup_errors:complete=False
   reservation_retained=file is None or bool(cleanup_errors)
   try:
    if file is not None:retained=target.stat().st_size
    if file is not None and not cleanup_errors:self.budget.finish_export(target)
    err_ref=self.store.command_bytes(stderr);receipt={'format':'aeris-native-export','version':1,'argvRef':argv_ref,'fullOriginalFiles':full_original or product_full_closed,'path':str(target),'bytesRetained':retained,'bytesAcceptedByWriter':count,'bytesObservedLowerBound':seen,'stderrRef':err_ref,'startedHostNs':started,'finishedHostNs':self.now(),'exit':None if p is None else p.poll(),'captureComplete':complete and failure is None,'failure':None if failure is None else type(failure).__name__+':'+str(failure)[:512],'cleanupErrors':cleanup_errors,'exportReservationRetained':reservation_retained,'flightAcceptance':False}
    ref=self.store.receipt('export-metadata.json'if metadata_only else'export-full.json',receipt,closing=failure is not None)
    if result is not None:result.update(stderrRef=err_ref,captureReceiptRef=ref,captureComplete=complete and failure is None)
   except BaseException as secondary:
    if failure is None:failure=secondary
    else:failure.add_note('EXPORT_PERSISTENCE_SECONDARY:'+str(secondary)[:256])
  if failure is not None:raise failure
  return result
