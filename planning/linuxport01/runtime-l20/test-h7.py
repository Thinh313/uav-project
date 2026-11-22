"""H7 finite coupled mocks; no ADB/AP/emulator. Synthetic archive is not G103 evidence."""
from pathlib import Path
import ast,base64,copy,gzip,hashlib,io,json,os,stat,sys,tarfile,tempfile,time,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime import reconcile_h7 as h
from aeris_runtime.native17 import AndroidDomain17,admin,sha,PACKAGE
from aeris_runtime.metadata_budget import MetadataBudget,encoded
from aeris_runtime.once_reader import read_ref,read_receipts
from aeris_runtime.status15_reader import journal
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.monitor import ResourceMonitor,host_power
class Child:
 calls=[];body=b''
 def __init__(self,argv,**kw):
  self.pid=os.getpid();self.args=argv;self.returncode=0;type(self).calls.append(argv);remote=__import__('shlex').split(argv[4])if len(argv)==5 and argv[3]=='shell'else argv[3:];body=type(self).body if remote[:3]==['run-as',PACKAGE,'cat']else b'Broadcast completed: result=0\n'
  for n,raw in [('stdout',body),('stderr',b'')]:
   r,w=os.pipe();os.write(w,raw);os.close(w);setattr(self,n,os.fdopen(r,'rb'))
 def poll(self):return self.returncode
 def wait(self,timeout=None):return self.returncode
 def send_signal(self,s):self.returncode=-s
 def terminate(self):self.returncode=-15
 def kill(self):self.returncode=-9

def synthetic(base):
 o=h.originals();nonce=o['ack']['requestNonce'];plan=sha(o['plan']);rp=o['receiver'];members=rp['originals'];records=[];head='0'*64
 def emit(kind,fields):
  nonlocal head
  raw=(str(len(records)+1)+'\t'+head+'\t'+kind+'\t'+base64.b64encode('\t'.join(fields).encode()).decode()).encode();head=sha(raw);records.append(raw+b'\t'+head.encode()+b'\n');return head
 def group(prefix):return prefix+[x for q in members for x in[q['generation'],str(q['bytes']),q['sha256'],q['disposition'],q['proofSHA256']]]
 enroll=emit('ENROLL_BEGIN',group([rp['backupSHA256'],sha(o['report']),rp['coldProofSHA256'],'8']));emit('ENROLL_COMMIT',[enroll]+[x for q in members for x in[q['generation'],'0','1']]);req=emit('REQUEST_RESERVE',[nonce,'APPLY','1']);ticket=emit('ARCHIVE_BEGIN',group([plan,'8']));commit=('AERIS_JOURNAL17_COMMITTED\t'+plan+'\t'+sha(o['report'])+'\n').encode();emit('ARCHIVE_COMMIT',[ticket,'product-input-archives17/'+plan,'intent-0.record',plan,str(len(o['plan'])),'commit-0.record',sha(commit),str(len(commit))]);receipt=encoded({'format':'aeris-native-journal17-administrative-receipt','version':1,'requestNonce':nonce,'operation':'APPLY','package':PACKAGE,'status':'ARCHIVED_VERIFIED_NO_AUTHORITY','planSHA256':plan,'independentReceiverSHA256':sha(o['report']),'backupTARSHA256':o['beforeSHA256'],'sourceSHA256':rp['newSourceSHA256'],'coldAbsenceProofSHA256':rp['coldProofSHA256'],'authorityRestorable':False,'flightAuthorityGranted':False,'actualImages':0,'snapshotBeforeOwnReceiptCommit':True,'processEpoch':'SYNTHETIC_MOCK_ONLY','pid':1,'observedElapsedNs':1,'journalLifecycle':{'registryPending':1,'registryHead':'NOT_FINAL_SNAPSHOT'}});emit('REQUEST_RECEIPT',[req,nonce,'product-input-lifecycle17/request-'+nonce+'.json',str(len(receipt)),sha(receipt)]);ack=dict(o['ack'],bytes=len(receipt),sha256=sha(receipt),registryHead=head);o=dict(o,ack=ack)
 rows={};dirs={}
 with tarfile.open(o['before'],'r:')as t:
  for m in t:
   m=copy.copy(m);m.mtime=0
   if m.isdir():dirs[m.name.rstrip('/')]=m
   else:
    name=m.name
    if name.startswith('files/product-input01/'):m.name='files/product-input-archives17/'+plan+'/'+name.rsplit('/',1)[1]
    rows[m.name]=(m,t.extractfile(name).read())
 for name in['files/product-input-registry17','files/product-input-lifecycle17','files/product-input-archives17','files/product-input-archives17/'+plan]:
  m=tarfile.TarInfo(name);m.type=tarfile.DIRTYPE;m.mode=0o700;m.uid=m.gid=10141;dirs[name]=m
 for name,data in {'files/product-input-registry17/highwater.aj17':b'AERIS_JOURNAL_REGISTRY17_V1\n'+b''.join(records),'files/product-input-lifecycle17/guard.lock':b'',ack['path']:receipt,'files/product-input-archives17/'+plan+'/intent-0.record':o['plan'],'files/product-input-archives17/'+plan+'/commit-0.record':commit}.items():
  m=tarfile.TarInfo(name);m.size=len(data);m.mode=0o600;m.uid=m.gid=10141;rows[name]=(m,data)
 out=Path(base)/'current.tar'
 def write(rows=rows,dirs=dirs,path=out):
  with tarfile.open(path,'w',format=tarfile.USTAR_FORMAT)as t:
   for m in dirs.values():t.addfile(m)
   for m,data in rows.values():t.addfile(m,io.BytesIO(data))
  return path
 return o,write(),rows,dirs,write
# Reuse inert fixture methods only; imports resolve selected H7, not priorruntime.
mt=ast.parse((R/'planning/betarc01/runtime/test-maintenance-close02.py').read_bytes());mc=next(n for n in mt.body if isinstance(n,ast.ClassDef)and n.name=='MaintenanceClose');mc.body=[n for n in mc.body if isinstance(n,ast.FunctionDef)and n.name=='fixture'];[setattr(n,'value','m701')for n in ast.walk(mc)if isinstance(n,ast.Constant)and n.value=='m101'];ns=dict(globals(),HERE=B);exec(compile(ast.Module(body=[mc],type_ignores=[]),'inert_H7_monitor_fixture','exec'),ns)
ht=ast.parse((R/'planning/betarc01/runtime-h5/test-h5.py').read_bytes());hc=next(n for n in ht.body if isinstance(n,ast.ClassDef)and n.name=='H5');hc.body=[n for n in hc.body if isinstance(n,ast.FunctionDef)and n.name=='fixture'];[setattr(n,'value','sdkOnlyH7')for n in ast.walk(hc)if isinstance(n,ast.Constant)and n.value=='sdkOnlyH5'];ns.update(ns=ns);exec(compile(ast.Module(body=[hc],type_ignores=[]),'inert_H7_current_raw_fixture','exec'),ns)
def append_row(root,kind,value):
 p=Path(root)/'receipts'/(kind+'.jsonl');p.parent.mkdir(parents=True,exist_ok=True);offset=p.stat().st_size if p.exists()else 0;raw=encoded(value)
 with p.open('ab')as f:f.write(raw)
 return {'format':'aeris-original-byte-ref','version':3,'path':str(p.relative_to(root)),'offset':offset,'bytes':len(raw),'sha256':sha(raw)}
def command_row(root,remote,out,clock):
 p=Path(root)/'command-stream.raw';offset=p.stat().st_size if p.exists()else 0;argv=encoded(['/mock/adb','-s','emulator-5582',*remote]);data=out+argv
 with p.open('ab')as f:f.write(data)
 def ref(start,raw):return {'format':'aeris-original-byte-ref','version':3,'path':'command-stream.raw','offset':start,'bytes':len(raw),'sha256':sha(raw)}
 row={'format':'aeris-command','version':3,'sequence':999,'startedHostNs':clock,'endedHostNs':clock+1,'captureComplete':True,'failure':None,'exit':0,'argvRef':ref(offset+len(out),argv),'stdoutRef':ref(offset,out),'stderrRef':ref(offset,b'')};return append_row(root,'command',row)
class H7(unittest.TestCase):
 def test_actual_g103_originals_source_join(self):
  o=h.originals();self.assertEqual(o['ack']['requestNonce'],'1183e55d5512dc4e021b4e84cdf0d0a6');self.assertEqual(o['ack']['bytes'],1401);self.assertEqual(o['priorKernelBootUUID'],'b8b8e188-0efa-4338-8fc0-47da9b055e99')
 def device(self,tmp):
  root=Path(tmp)/'g104';root.mkdir();budget=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);budget.admit();d=AndroidDomain17('/mock/adb','emulator-5582',root/'sessions/mock/android-api',budget=budget,observer_tag='AERIS_PRODUCT_STATUS');return d
 def test_actual_admin_to_bound_and_capture_original_ack_unknown_no_retry(self):
  with tempfile.TemporaryDirectory(prefix='h7-',dir=B)as tmp,patch('aeris_runtime.android.subprocess.Popen',Child):
   d=self.device(tmp);o=h.originals();ack=o['ack'];Child.body=b'X'*ack['bytes'];Child.calls=[]
   from contextlib import contextmanager
   @contextmanager
   def logs(*args,**kw):yield iter([ack])
   d.live_log=logs;d.observer.last_ref={'mockOriginalACK':True};owner=types.SimpleNamespace(manifest={'native':{'sourceSHA256':o['receiver']['newSourceSHA256']}},write=lambda *a:None);case={'device':d,'adoption17':{},'receiver17':{'plan':o['plan'],'planSHA256':sha(o['plan']),'reportSHA256':sha(o['report'])},'backup17':{'sha256':o['beforeSHA256']}}
   with patch('aeris_runtime.native17.secrets.token_hex',return_value=ack['requestNonce']),self.assertRaisesRegex(ValueError,'ORIGINAL_ADMIN_ACK_RECEIPT_SHA'):admin(owner,case,'APPLY',deadline_ns=time.monotonic_ns()+10_000_000_000)
   self.assertEqual(len(Child.calls),2);self.assertEqual(d.sequence,2);self.assertTrue(d.last_command['captureComplete']);self.assertIsNone(d._admin_receipt_read17);before=len(Child.calls)
   with self.assertRaises(ValueError):admin(owner,case,'APPLY',deadline_ns=time.monotonic_ns()+10_000_000_000)
   with self.assertRaises(ValueError):d.read_admin_receipt17(ack,ack['requestNonce'],deadline_ns=time.monotonic_ns()+10_000_000_000)
   self.assertEqual(len(Child.calls),before)
 def test_ack_reader_synthetic_success_and_finite_refusals(self):
  with tempfile.TemporaryDirectory(prefix='h7-',dir=B)as tmp,patch('aeris_runtime.android.subprocess.Popen',Child):
   d=self.device(tmp);d.command(['shell','id','-u'],deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=64);ack=dict(h.originals()['ack']);Child.body=b'SYNTHETIC_RECEIPT_ONLY';ack.update(bytes=len(Child.body),sha256=sha(Child.body));self.assertEqual(d.read_admin_receipt17(ack,ack['requestNonce'],deadline_ns=time.monotonic_ns()+10_000_000_000),Child.body)
   for args in[['shell','run-as',PACKAGE,'cat','files/product-input-lifecycle17/request-'+'0'*32+'.json'],['shell','run-as','foreign','cat',ack['path']],['shell','run-as',PACKAGE,'cat','files/../secret']]:
    with self.assertRaises(ValueError):d._command_bound(args)
 def test_full_index_and_conservation_synthetic_not_actual_receipt(self):
  with tempfile.TemporaryDirectory(prefix='h7-',dir=B)as tmp:
   o,p,rows,dirs,write=synthetic(tmp)
   with patch.object(h,'originals',return_value=o):r=h.reconcile(p,sha(p.read_bytes()),source_candidate='a'*64,native_apk_sha=o['retained']['binding']['selectedNewAPKSHA256'],native_source_sha=o['receiver']['newSourceSHA256'])
   self.assertEqual(r['pendingTransactions'],0);self.assertEqual(r['registryProof']['activeJournals'],0);self.assertEqual(r['registryProof']['archivedJournals'],8)
   for mode in['wrongHead','missingOriginal','extraFile','metadata','receipt','workspace','directory']:
    q=copy.deepcopy(rows);ds=copy.deepcopy(dirs);oo=copy.deepcopy(o)
    if mode=='wrongHead':oo['ack']['registryHead']='f'*64
    elif mode=='missingOriginal':q.pop(next(n for n in q if n.endswith('.aj02')))
    elif mode=='extraFile':m=tarfile.TarInfo('files/UNKNOWN');m.size=1;q[m.name]=(m,b'X')
    elif mode=='metadata':q[next(n for n in q if n.endswith('.aj02'))][0].uid+=1
    elif mode=='receipt':m,data=q[o['ack']['path']];q[o['ack']['path']]=(m,b'X'*len(data))
    elif mode=='workspace':name=next(n for n in q if n.startswith('files/betasim-workspace01/')and not n.endswith('/HEAD'));m,data=q[name];q[name]=(m,b'X'*len(data))
    else:ds['files'].mode^=1
    path=Path(tmp)/(mode+'.tar');write(q,ds,path)
    with patch.object(h,'originals',return_value=oo),self.subTest(mode=mode),self.assertRaises(Exception):h.reconcile(path,sha(path.read_bytes()),source_candidate='a'*64,native_apk_sha=o['retained']['binding']['selectedNewAPKSHA256'],native_source_sha=o['receiver']['newSourceSHA256'])
 def sdk_fixture(self,tmp):
  o,m,b=ns['H5']().fixture(tmp);data,path,rows,dirs,write=synthetic(tmp);v=o.case['maintenanceRC01']['sdkOnlyH7'];root=o.case['device'].root;target=Path(v['rootPrivateBackup']['path']);target.unlink();os.link(path,target);backup=v['rootPrivateBackup'];cap=json.loads(read_ref(root,backup['captureReceiptRef']));backup.update(bytes=target.stat().st_size,sha256=sha(target.read_bytes()));cap.update(bytesRetained=target.stat().st_size,bytesAcceptedByWriter=target.stat().st_size,bytesObservedLowerBound=target.stat().st_size);backup['captureReceiptRef']=append_row(root,'diagnostic',cap);o.manifest['native']['sourceSHA256']=data['receiver']['newSourceSHA256'];
  with patch.object(h,'originals',return_value=data):v['tarProfileObservation']={'observation':h.reconcile(target,sha(target.read_bytes()),source_candidate=o.digest,native_apk_sha=o.manifest['native']['APK_SHA256'],native_source_sha=o.manifest['native']['sourceSHA256'])['tarTransportProfile'],'originalCaptureRef':backup['captureReceiptRef']}
  return o,m,b,data
 def test_actual_sdk_close_reaches_full_tar_argv_and_semantic_verifier(self):
  with tempfile.TemporaryDirectory(prefix='h7-',dir=B)as tmp:
   o,m,b,data=self.sdk_fixture(tmp)
   with patch.object(h,'originals',return_value=data):proof=h.verify_sdk(o,o.case['maintenanceRC01']);closed=o.close_sdk_only()
   self.assertEqual(proof['pendingTransactions'],0);self.assertFalse(closed['flightAcceptance']);self.assertFalse(closed['monitorDurableDrainClaimed']);self.assertTrue(o.case['closed'])
   del o.write;o.write('coldboot-h7.json',{'mockObservation':True});b.write('guardian',o.root/'guardian/closure.json',encoded({'mockOnly':True}));b.write('external_task',o.root/'diagnostics/guardian-process/close.json',encoded({'mockOnly':True}));tree=ast.parse((R/'planning/betarc01/runtime-h9/root-reconcile-h9.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='terminal_summary');env={'hashlib':hashlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_H7_terminal_summary','exec'),env);call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='write'and n.args and isinstance(n.args[0],ast.Constant)and n.args[0].value=='owner-terminal.json');eval(compile(ast.Expression(body=call),'actual_H7_terminal_write','eval'),dict(env,owner=o));self.assertLessEqual((o.root/'reports/owner-terminal.json').stat().st_size,4096)
 def test_actual_application_original_resume_route_and_raw_forgeries(self):
  from aeris_runtime.product_native09 import verify_application_original
  with tempfile.TemporaryDirectory(prefix='h7-',dir=B)as tmp:
   o,m,b,data=self.sdk_fixture(tmp);root=o.case['device'].root;v=o.case['maintenanceRC01']['sdkOnlyH7'];cap=json.loads(read_ref(root,v['rootPrivateBackup']['captureReceiptRef']));rawargv=encoded([o.case['device'].adb,'-s','emulator-5582','exec-out','run-as',PACKAGE,'tar','-cf','-','files']);stream=root/'command-stream.raw';offset=stream.stat().st_size
   with stream.open('ab')as f:f.write(rawargv)
   cap['argvRef']={'format':'aeris-original-byte-ref','version':3,'path':'command-stream.raw','offset':offset,'bytes':len(rawargv),'sha256':sha(rawargv)};v['rootPrivateBackup']['captureReceiptRef']=append_row(root,'diagnostic',cap);o.digest=sha(encoded(o.manifest).rstrip(b'\n'));samples=v['samples'];proof={'format':'aeris-h7-enrolled-readonly-resume','candidateSHA256':o.digest,'APKSHA256':o.manifest['native']['APK_SHA256'],'nativeSourceSHA256':o.manifest['native']['sourceSHA256'],'installOrAdminDispatched':False,'authorityRestorable':False,'coldBeforeRef':samples[0]['commandRefs']['cold'],'installedPathRef':samples[0]['commandRefs']['path'],'installedSHARef':samples[0]['commandRefs']['sha'],'coldAfterRef':v['afterBackupColdRef'],'backup':v['rootPrivateBackup']};auth=append_row(root,'diagnostic',proof);pwd=command_row(root,['run-as',PACKAGE,'pwd','-P'],('/data/user/0/'+PACKAGE+'\n').encode(),10**13)
   legacy=root.parent/'android-api-retained';legacy.mkdir();du=command_row(legacy,['run-as','vn.rtr.aeris.mission','du','-k','-s','files'],b'4\tfiles\n',10**13);old=root.parent/'native-original-before-quarantine.tar'
   with tarfile.open(old,'w',format=tarfile.USTAR_FORMAT)as t:
    d=tarfile.TarInfo('files');d.type=tarfile.DIRTYPE;d.mode=0o700;t.addfile(d);f=tarfile.TarInfo('files/old');f.size=3;t.addfile(f,io.BytesIO(b'old'))
   retained={'format':'aeris-retained-old-application-private-inventory','package':'vn.rtr.aeris.mission','sourceStopped':True,'notNewDeviceGrowthCredit':True,'sourceDUCommandRef':du,'allocatedBytes':4096,'sourceOriginalTAR':{'path':str(old),'sha256':sha(old.read_bytes())},'plaintextFileLengthBytes':3,'entries':2};rref=append_row(root,'diagnostic',retained);domain={'format':'aeris-root-observed-development-application-domain','version':1,'nativeLifecycleResumeH7':True,'applicationId':PACKAGE,'serial':'emulator-5582','privateFilesDirectory':'/data/user/0/'+PACKAGE+'/files','sourceSHA256':o.manifest['native']['sourceSHA256'],'APKSHA256':o.manifest['native']['APK_SHA256'],'candidateSHA256':o.digest,'authorizationRef':auth,'actualPrivateDirectoryCommandRef':pwd,'retainedInventoryRef':rref,'oldApplicationOriginalsRetained':True,'noAuthorityRestore':True,'nativeReportedApplicationId':False};ref=append_row(root,'diagnostic',domain)
   with patch.object(h,'originals',return_value=data):self.assertEqual(verify_application_original(root,ref,o.manifest),domain)
   for key in['candidateSHA256','retainedInventoryRef','authorizationRef','actualPrivateDirectoryCommandRef']:
    bad=copy.deepcopy(domain)
    if isinstance(bad[key],dict):bad[key]['sha256']='0'*64
    else:bad[key]='0'*64
    rr=append_row(root,'diagnostic',bad)
    with patch.object(h,'originals',return_value=data),self.subTest(key=key),self.assertRaises(Exception):verify_application_original(root,rr,o.manifest)
 def test_actual_m501_GNU_raw_through_original_SDK_close_not_m501_acceptance(self):
  with tempfile.TemporaryDirectory(prefix='h7-',dir=B)as tmp:
   o,m,b,_=self.sdk_fixture(tmp);v=o.case['maintenanceRC01']['sdkOnlyH7'];root=o.case['device'].root;backup=v['rootPrivateBackup'];target=Path(backup['path']);target.unlink();actual=R/'evidence/betarc01/m501/sessions/beta-rc01-sdk-reconcile01/native-restart-metadata.tar';os.link(actual,target);cap=json.loads(read_ref(root,backup['captureReceiptRef']));backup.update(bytes=target.stat().st_size,sha256=sha(target.read_bytes()));cap.update(bytesRetained=target.stat().st_size,bytesAcceptedByWriter=target.stat().st_size,bytesObservedLowerBound=target.stat().st_size);backup['captureReceiptRef']=append_row(root,'diagnostic',cap);v['tarProfileObservation']={'observation':h.reconcile(target,backup['sha256'],source_candidate=o.digest,native_apk_sha=o.manifest['native']['APK_SHA256'],native_source_sha=o.manifest['native']['sourceSHA256'])['tarTransportProfile'],'originalCaptureRef':backup['captureReceiptRef']};proof=h.verify_sdk(o,o.case['maintenanceRC01']);self.assertEqual(proof['pendingTransactions'],0);self.assertEqual(proof['reconciliation']['registryProof']['archivedJournals'],8);self.assertFalse(o.close_sdk_only()['flightAcceptance'])
 def test_preserved_h6_all_bytes_modes_and_no_guard_delta(self):
  baseline=json.loads(gzip.decompress((B/'H6-DERIVATION-BASELINE.json.gz').read_bytes()))
  for v in baseline['files'].values():
   p=R/v['oldPath'];st=p.stat();self.assertEqual((sha(p.read_bytes()),stat.S_IMODE(st.st_mode),st.st_ino,st.st_dev),(v['sha256'],v['mode'],v['inode'],v['device']))
  for n in['android.py','emulator.py','guest_sync_h4.py','inventory.py']:self.assertEqual((B/'source/aeris_runtime'/n).read_bytes(),(R/'planning/betarc01/runtime-h6/source/aeris_runtime'/n).read_bytes())
if __name__=='__main__':
 result=unittest.main(verbosity=2,exit=False).result;print(json.dumps({'format':'aeris-h7-actual-mock-module-origins','modules':{n:{'path':str(Path(m.__file__).resolve()),'sha256':sha(Path(m.__file__).read_bytes())}for n,m in sys.modules.items()if(n=='aeris_runtime'or n.startswith('aeris_runtime.'))and getattr(m,'__file__',None)},'actorsStarted':False}));raise SystemExit(0 if result.wasSuccessful()else 1)
