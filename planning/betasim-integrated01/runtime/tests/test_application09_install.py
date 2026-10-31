"""Causal new-domain install ordering on tiny original-byte TAR fixtures.
No SDK, ADB, APK install or genuine device claim.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager
import copy,hashlib,io,json,sys,tarfile,shutil
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.application09 import AndroidDomain09,PACKAGE
from aeris_runtime.product_native09 import ProductNativeProbe09
from aeris_runtime.metadata_budget import encoded
LAB=R/'evidence/betasim-integrated01/runtime/.application09-install'
APK='8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1';SOURCE='b62de0407ac3913a62b6e073a18f9d2937d30545e911a6cf552c871adaabb64a';M={'native':{'package':PACKAGE,'productKind':'BETASIM_INTEGRATED','APK_SHA256':APK,'sourceSHA256':SOURCE}}
class Budget:
 @contextmanager
 def operation(self,*a):yield
class Store:
 def __init__(self):self.rows=[]
 def receipt(self,n,v,**kw):self.rows.append((n,v));return {'mockRef':n}
class Legacy:
 fault=None;du=b'8\tfiles\n';duplicate=False;pax=False;events=[]
 def __init__(self,*a,**kw):self.root=Path(a[2]);self.last_command_ref={'mock':'legacy-command'};self.last_command={'stdoutRef':{'mock':'du-stdout'},'argvRef':{'mock':'du-argv'}}
 def command(self,args,**kw):self.events.append(('old-command',args));return self.du if'du'in args else b''
 def _cold_absence(self,*a):self.events.append(('old-cold',));return {'mock':'cold'}
 def _installed_sha(self,*a):return {'mock':'path'},{'mock':'sha'}
 def _export_private(self,run,target,**kw):
  assert target.parent.resolve()==self.root.parent.resolve();self.events.append(('old-backup-start',))
  if self.fault:raise self.fault
  with tarfile.open(target,'w',format=tarfile.PAX_FORMAT if self.pax else tarfile.USTAR_FORMAT)as t:
   q=tarfile.TarInfo('files');q.type=tarfile.DIRTYPE;t.addfile(q)
   for _ in range(2 if self.duplicate else 1):
    q=tarfile.TarInfo('files/original.bin');q.size=3
    if self.pax:q.pax_headers={'comment':'original-extra'}
    t.addfile(q,io.BytesIO(b'old'))
  raw=target.read_bytes();self.events.append(('old-backup-complete',));return {'path':str(target),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'captureComplete':True}
def device(name,*,fresh=True):
 root=LAB/name;root.mkdir();d=AndroidDomain09.__new__(AndroidDomain09);d.root=root/'android-api';d.root.mkdir();d.adb='/fake/adb';d.serial='emulator-5582';d.budget=Budget();d.observer=SimpleNamespace(process=None,tag='AERIS_PRODUCT_STATUS');d._android_ready={};d.live_check=lambda:None;d.store=Store();d._check_budget_actor=lambda:None;d.installed=not fresh;d.commands=[];d.private=('/data/user/0/'+PACKAGE+'\n').encode()
 def command(args,**kw):
  d.commands.append(args);d.last_command_ref={'mock':'new-command-'+str(len(d.commands))};d.last_command={'stdoutRef':{'mock':'stdout'},'stderrRef':{'mock':'stderr'},'exit':0,'captureComplete':True}
  if args==['shell','pm','list','packages','--user','0',PACKAGE]:return b''if not d.installed else('package:'+PACKAGE+'\n').encode()
  if args[:2]==['shell','pm']:return b''if not d.installed else b'package:/new.apk\n'
  if args[:1]==['install']:assert('old-backup-complete',)in Legacy.events;assert d._fresh_domain_install_authorization;d.installed=True;return b'Success\n'
  if'pwd'in args:return d.private
  return b''
 d.command=command;d._cold_absence=lambda *a:{'mock':'new-cold'};d._installed_sha=lambda *a:({'mock':'new-path'},{'mock':'new-sha'});return d

def main():
 assert not LAB.exists();LAB.mkdir();groups=[]
 try:
  with patch('aeris_runtime.android.AndroidDevice',Legacy),patch('aeris_runtime.candidate.load',return_value=M):
   Legacy.events=[];d=device('good');p=ProductNativeProbe09(d,M);p.install_selected(LAB/'candidate','a'*64,deadline_ns=2**63-1);assert sum(a[0]=='install'for a in d.commands)==1 and p.retained_inventory['allocatedBytes']==8192 and p.retained_inventory['plaintextFileLengthBytes']==3;assert p.application_domain['applicationId']==PACKAGE and p.application_domain['nativeReportedApplicationId']is False;groups.append('actual-selected-install-method-old-stopped-full-TAR-and-du-before-one-fresh-install-actualnew-privatepath-sourceproof')
   for n,kind in enumerate(('backupEIO','duplicate','pax','duunknown','privateforeign')):
    Legacy.events=[];Legacy.fault=OSError('OLD_BACKUP_EIO')if kind=='backupEIO'else None;Legacy.duplicate=kind=='duplicate';Legacy.pax=kind=='pax';Legacy.du=b'UNKNOWN\n'if kind=='duunknown'else b'8\tfiles\n';d=device('bad'+str(n));p=ProductNativeProbe09(d,M)
    if kind=='privateforeign':d.private=b'/data/user/0/foreign\n'
    try:p.install_selected(LAB/'candidate','a'*64,deadline_ns=2**63-1)
    except Exception:pass
    else:raise AssertionError('expected refusal '+kind)
    assert not hasattr(p,'application_domain_ref')
    if kind!='privateforeign':assert not any(a[0]=='install'for a in d.commands)
   groups.append('original-backup-EIO-duplicate-PAX-unknown-oldallocation-refuse-before-install-foreignprivatepath-never-domainready')
   Legacy.fault=None;Legacy.duplicate=Legacy.pax=False;Legacy.du=b'8\tfiles\n';Legacy.events=[];d=device('reuse',fresh=False);d._export_private=lambda *a,**kw:{'captureComplete':True};p=ProductNativeProbe09(d,M);p.install_selected(LAB/'candidate','a'*64,deadline_ns=2**63-1);assert not any(a[0]=='install'for a in d.commands);groups.append('existing-selected-new-domain-reuse-requires-ownbackup-no-secondinstall-no-clear-or-datareset')
  # Invoke the ACTUAL original exporter path guards, stop at reservation before
  # any Popen/file write. This catches a mock that ignores root/name/mode ABI.
  from aeris_runtime.android import AndroidDevice as Base
  d=device('export-boundary');d.include_quarantine=False;d.budget.ensure=lambda *a:None
  class BoundaryReached(Exception):pass
  def reserve(*a):raise BoundaryReached('VALIDATED_EXPORT_BOUNDARY_BEFORE_POPEN')
  d.budget.reserve_export=reserve
  try:Base._export_private(d,'run',d.root.parent/'native-restart-metadata.tar',deadline_ns=2**63-1,metadata_only=True,maximum_bytes=64*2**20,product_full_closed=True)
  except BoundaryReached:pass
  else:raise AssertionError('did not reach reservation boundary')
  try:Base._export_private(d,'run',d.root/'native-restart-metadata.tar',deadline_ns=2**63-1,metadata_only=True,maximum_bytes=64*2**20,product_full_closed=True)
  except ValueError as e:assert 'EXACT_ORIGINAL_EXPORT_DOMAIN'in str(e)
  else:raise AssertionError('wrong parent accepted')
  groups.append('actual-exporter-fixed-root-parent-new-reuse64MiB-full-files-mode-validated-before-reservation-no-Popen')
  out=R/'evidence/betasim-integrated01/runtime/application09-install-mock03.json';assert not out.exists();report={'format':'aeris-application09-selected-source-install-order','status':'PASS_CAUSAL_MEMORY_ADB_AND_REAL_TINY_TAR_NO_DEVICE_EXECUTION','groups':groups,'sourceSHA256':hashlib.sha256((T/'source/aeris_runtime/product_native09.py').read_bytes()).hexdigest(),'actorsStarted':False,'genuineSDKPrivateIdentityAccepted':False,'allOriginalsUnchanged':True,'scratchRemoved':str(LAB.relative_to(R))};out.write_bytes(encoded(report));print(json.dumps(report))
 finally:shutil.rmtree(LAB)
if __name__=='__main__':main()
