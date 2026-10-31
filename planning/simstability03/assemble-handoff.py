"""Stream an explicit pinned recipient closure into a new qualified engineering handoff.
No runtime, build, extraction, project copy, dependency installation or source edits.
Assembly is disabled until Contractor supplies a final, digest-bound authorization JSON.
"""
from pathlib import Path,PurePosixPath
import argparse,ast,datetime,hashlib,io,json,os,shutil,stat,subprocess,tarfile,types
R=Path(__file__).resolve().parents[2];LIMIT=512*2**20;APK_SHA='8f1767933059b719d0bfb260df751678d24bd6d0a345397a5d52815cf7f2aec1'
sha=lambda b:hashlib.sha256(b).hexdigest()
def safe(n):
 p=PurePosixPath(n)
 if not n or p.is_absolute()or p.as_posix()!=n or any(x in['','.','..']for x in p.parts)or'\\'in n or'\0'in n:raise ValueError('UNSAFE_NAME')
 return n
def checksum(raw):return (sha(raw)+'\n').encode()
def validate_authorization(q,digest):
 assert q.get('assemblyAuthorized')is True,'FINAL_ASSEMBLY_NOT_AUTHORIZED'
 assert q.get('sourceManifestSHA256')==digest,'QUALIFICATION_SOURCE_BINDING'
 assert isinstance(q.get('runtimeAcceptance'),str)and q['runtimeAcceptance']not in['PENDING','RUNNING','RUNNING_NOT_FINAL']and len(q['runtimeAcceptance'])<=100,'FINAL_RUNTIME_STATUS_REQUIRED'
 assert isinstance(q.get('status'),str)and 1<=len(q['status'])<=100 and '\n'not in q['status']and q['status']not in['PENDING','RUNNING','RUNNING_NOT_FINAL'],'FINAL_STATUS_REQUIRED'
 for k in ['verifiedOutcomes','remainingGates']:
  assert isinstance(q.get(k),list)and len(q[k])<=32 and all(isinstance(x,str)and 1<=len(x)<=800 for x in q[k]),'QUALIFICATION_LIST_BOUND'
 return q
NOTES='''# AERIS SIM-STABILITY03: {status}

Engineering handoff for the declared macOS ARM host and the unchanged development APK. This is reference-quad simulation, not calibrated Hera performance or authorization to control a physical aircraft. The current qualification is `QUALIFICATION-SIM-STABILITY03.json`; retained older NOT_READY notes/qualification/source IDs describe lineage only and do not override it. No production signature or private signing key is included.

## Verified outcomes within the declared scope
{verified}

## Remaining gates and unsupported capabilities
{gates}

Physical Xiaomi/Hera/HeraHub/payload/SDK acceptance is NOT_CHECKED. AUTO mission capability is unsupported in this slice. The PBR scene is a licensed visual representation driven by reference physics; synthesized RPM audio is not calibrated Hera acoustics. No unmeasured photon latency, general training validity, zero frame loss, full source-image delivery or broader environmental accuracy is asserted. Large raw captures are retained on the original evidence host and are NOT embedded in exported SAF metadata packages or this engineering archive.

## Host prerequisites and installation

Use macOS ARM with the cached Python3.14.6, declared Node runtime and existing Docker image digest from the manifest. These prerequisites are external; no download, native rebuild or Windows/Linux compatibility is implied. Check the archive SHA, exact 65-byte `bundle-manifest.sha256` (64 lowercase hex characters and LF), payload manifest and dependency closure before following `planning/simhand01/README.md`. Extract only into a new empty directory. The empty regular `runtime/sitl/arducopter` is a structural Docker bind target; the actual AP binary remains at the pinned runtime build path.

Keep admission20GiB and runtime10GiB plus256MiB reserve guards. The recipient policy remains2GiB; internal engineering runtime accounting does not change recipient guards. AP300s is a wall upper bound, not proof that the immutable AP recorder supports an accepted300s capture. Land and close bounded tests before recorder exhaustion.

The engineering APK is unchanged (SHA256 `{apk}`). Select an explicit USB serial for every Android action; never select an arbitrary attached device, root a physical phone, or treat an emulator result as Xiaomi/Hera acceptance. Native SAF imports are historical records only and never restore authority. Restart requires explicit new session, preflight and neutral acquisition. A doctor, archive hash or clean process exit alone does not prove a successful flight.
'''
def source_entries(src,expected):
 raw=(src/'bundle-manifest.json').read_bytes();digest=sha(raw);assert digest==expected,'PINNED_SOURCE_MANIFEST';assert (src/'bundle-manifest.sha256').read_bytes()==checksum(raw),'SOURCE_CHECKSUM65'
 source=json.loads(raw);assert len(source['files'])==110,'EXPLICIT110_SOURCE_CLOSURE';entries={};fingerprints={}
 for n,m in source['files'].items():
  safe(n);assert not n.startswith(('.local/','.git/'))and(not n.startswith('evidence/')or n in['evidence/sim32/source-final/pilot/sim32/physics.py','evidence/simhand01/source-baseline01.json'])and Path(n).suffix.lower()not in['.pem','.key','.jks','.keystore','.p12','.pfx'],'SECRET_OR_RAW_NOT_ALLOWED'
  p=src/n
  for parent in [p,*p.parents]:
   if parent==src.parent:break
   assert not parent.is_symlink(),'SOURCE_SYMLINK'
  st=p.lstat();assert stat.S_ISREG(st.st_mode)and stat.S_IMODE(st.st_mode)==m['mode']and m['mode']in[0o644,0o755],'SOURCE_TYPE_MODE'
  b=p.read_bytes();assert len(b)==m['bytes']and sha(b)==m['sha256'],('PINNED_SOURCE_FILE',n)
  entries[n]={'path':p,**m};fingerprints[n]=(m['sha256'],m['bytes'],m['mode'])
 apk=[(n,m)for n,m in source['files'].items()if n.endswith('.apk')];assert len(apk)==1 and apk[0][1]['sha256']==APK_SHA,'EXACT_DEVELOPMENT_APK'
 assert entries['runtime/sitl/arducopter']['bytes']==0,'STRUCTURAL_MOUNTPOINT'
 return raw,digest,source,entries,fingerprints,apk[0]
def exact_python_parser(virtual):
 class VFile:
  def __init__(self,name=''):self.name=str(name)
  def __truediv__(self,n):return VFile((PurePosixPath(self.name)/str(n)).as_posix())
  def read_bytes(self):return virtual[self.name]
  def read_text(self):return self.read_bytes().decode()
  def is_file(self):return self.name in virtual
  def is_symlink(self):return False
  def stat(self):return types.SimpleNamespace(st_size=len(self.read_bytes()))
  def open(self,mode='r'):assert mode in['r','rb'];return io.BytesIO(self.read_bytes())if mode=='rb'else io.StringIO(self.read_text())
 tree=ast.parse(virtual['planning/simhand01/support.py'].decode());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in['sha','verify_manifest']];doctor=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='doctor');closure=next(n for n in doctor.body if isinstance(n,ast.FunctionDef)and n.name=='closure');ns={'Path':lambda p:p if isinstance(p,VFile)else Path(p),'ROOT':VFile(),'hashlib':hashlib,'json':json,'deps':VFile('planning/simhand01/dependencies.json')};exec(compile(ast.Module(body=nodes+[closure],type_ignores=[]),'EXACT_INCLUDED_PARSER','exec'),ns);digest=ns['verify_manifest'](VFile());deps=ns['closure']();correct=virtual['bundle-manifest.sha256'];virtual['bundle-manifest.sha256']=(digest+'  bundle-manifest.json\n').encode()
 try:ns['verify_manifest'](VFile());raise AssertionError('CONVENTIONAL_CHECKSUM_ACCEPTED')
 except RuntimeError as e:assert str(e)=='BUNDLE_MANIFEST_SHA'
 finally:virtual['bundle-manifest.sha256']=correct
 return {'manifestSHA256':digest,'dependencyClosure':deps,'negativeFilenameSuffixChecksum':'REJECTED'}
def assemble(args):
 assert shutil.disk_usage(R).free>=20*2**30,'ADMISSION20_GIB_REQUIRED';src=Path(args.source).resolve();assert src==R/'.local/simstability03/receiver03','SOURCE_SCOPE';raw,digest,source,entries,fingerprints,apk=source_entries(src,args.source_sha);q=validate_authorization(json.loads(Path(args.qualification).read_text()),digest)
 out=R/'delivery/sim-stability03';out.mkdir(exist_ok=True);assert Path(args.name).name==args.name and args.name.endswith('.tar.gz'),'OUTPUT_NAME';archive=out/args.name;assert not archive.exists(),'EXCLUSIVE_ARCHIVE_REQUIRED'
 qualification={**q,'format':'aeris-simstability03-engineering-qualification','version':1,'engineeringOnly':True,'productionSignature':False,'sourceIDs':source.get('sourceIDs'),'sourceLineageManifestSHA256':digest,'rawEvidenceEmbedded':False,'unchangedAPK':{'path':apk[0],**apk[1]},'physicalXiaomiHeraSDK':'NOT_CHECKED','authorityRestorable':False,'runtimeStartedByPackaging':False,'recipientEvidenceQuotaBytes':2*2**30}
 notes=NOTES.format(status=q['status'],verified='\n'.join('- '+x for x in q['verifiedOutcomes']),gates='\n'.join('- '+x for x in q['remainingGates']),apk=APK_SHA).encode();new={'RELEASE-NOTES-SIM-STABILITY03.md':notes,'QUALIFICATION-SIM-STABILITY03.json':(json.dumps(qualification,ensure_ascii=False,indent=2)+'\n').encode(),'lineage/receiver03-bundle-manifest.json':raw,'lineage/receiver03-dependencies.json':(src/'planning/simhand01/dependencies.json').read_bytes()}
 for n,b in new.items():safe(n);assert n not in entries;entries[n]={'data':b,'bytes':len(b),'sha256':sha(b),'mode':0o644}
 dep='planning/simhand01/dependencies.json';dependencies=json.loads((src/dep).read_text());dependencies.update(files={n:{k:m[k]for k in['bytes','sha256','mode']}for n,m in sorted(entries.items())if n!=dep},qualificationStatus=q['status'],packagingRevision='SIM-STABILITY03-ENGINEERING-HANDOFF');dependencies['uncompressedBytes']=sum(m['bytes']for m in dependencies['files'].values());b=(json.dumps(dependencies,indent=2)+'\n').encode();entries[dep]={'data':b,'bytes':len(b),'sha256':sha(b),'mode':0o644}
 manifest={**source,'files':{n:{k:m[k]for k in['bytes','sha256','mode']}for n,m in sorted(entries.items())},'uncompressedBytes':sum(m['bytes']for m in entries.values()),'qualificationStatus':q['status'],'qualificationFile':'QUALIFICATION-SIM-STABILITY03.json','releaseNotesFile':'RELEASE-NOTES-SIM-STABILITY03.md','engineeringRevision':{'id':'SIM-STABILITY03-ENGINEERING-HANDOFF','parentManifestSHA256':digest,'sourceRevision':source.get('engineeringRevision'),'sourceIDsAreLineageOnly':True,'productionSignature':False},'simstability03':{**source.get('simstability03',{}),'status':q['runtimeAcceptance'],'qualificationFile':'QUALIFICATION-SIM-STABILITY03.json'}}
 mb=(json.dumps(manifest,indent=2)+'\n').encode();ms=sha(mb)
 for n,b in [('bundle-manifest.json',mb),('bundle-manifest.sha256',checksum(mb))]:entries[n]={'data':b,'bytes':len(b),'sha256':sha(b),'mode':0o644}
 assert entries['bundle-manifest.sha256']['bytes']==65 and sum(m['bytes']for m in entries.values())<=LIMIT,'ARCHIVE_BOUND'
 with tarfile.open(archive,'x:gz',format=tarfile.USTAR_FORMAT,compresslevel=6)as t:
  for n,m in sorted(entries.items()):
   assert shutil.disk_usage(R).free>=10*2**30+256*2**20,'RUNTIME10_GIB_RESERVE';info=tarfile.TarInfo(safe(n));info.size=m['bytes'];info.mode=m['mode'];info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   if'path'in m:
    with m['path'].open('rb')as f:t.addfile(info,f)
   else:t.addfile(info,io.BytesIO(m['data']))
 assert archive.stat().st_size<=LIMIT
 virtual={}
 with tarfile.open(archive,'r:gz')as t:
  members=t.getmembers();assert len(members)==len(entries)and len({m.name for m in members})==len(entries)and {m.name for m in members}==set(entries)
  for m in members:
   safe(m.name);assert m.isfile()and not m.linkname and not m.pax_headers and m.mode==entries[m.name]['mode'];b=t.extractfile(m).read();assert len(b)==entries[m.name]['bytes']and sha(b)==entries[m.name]['sha256'];virtual[m.name]=b
 python=exact_python_parser(virtual);assert python['manifestSHA256']==ms
 listing=subprocess.check_output(['/usr/bin/tar','-tzf',str(archive)],timeout=30).decode().splitlines();assert listing==sorted(entries);proc=subprocess.Popen(['/usr/bin/tar','-xOf',str(archive)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  for n in listing:
   left=entries[n]['bytes'];h=hashlib.sha256()
   while left:
    b=proc.stdout.read(min(1048576,left));assert b,'BSD_TAR_SHORT';h.update(b);left-=len(b)
   assert h.hexdigest()==entries[n]['sha256'],'BSD_TAR_SHA'
  assert proc.stdout.read(1)==b'';stderr=proc.stderr.read();assert proc.wait(timeout=30)==0,stderr
 finally:
  if proc.poll()is None:proc.kill();proc.wait()
 node=subprocess.run(['node','--experimental-vm-modules',str(R/'planning/simverify02/verify-diagnostic-parsers.mjs'),str(archive)],capture_output=True,text=True,timeout=45);assert node.returncode==0,node.stderr;node_result=json.loads(node.stdout);assert node_result['status']=='PASS'
 assert (src/'bundle-manifest.json').read_bytes()==raw
 for n,(h,size,mode)in fingerprints.items():p=src/n;assert sha(p.read_bytes())==h and p.stat().st_size==size and stat.S_IMODE(p.stat().st_mode)==mode
 receipt={'format':'aeris-simstability03-engineering-archive-verification','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(archive.relative_to(R)),'archiveSHA256':sha(archive.read_bytes()),'compressedBytes':archive.stat().st_size,'members':len(entries),'manifestPayloadFiles':len(manifest['files']),'uncompressedBytes':sum(m['bytes']for m in entries.values()),'sourceManifestSHA256':digest,'manifestSHA256':ms,'source110Unchanged':True,'originalAPKUnchanged':True,'newBuildOrSignature':False,'extractionPerformed':False,'runtimeStarted':False,'qualification':qualification,'verification':{'allSafeRegularUniqueExplicitMembers':'PASS','allMemberByteSHAAndMode':'PASS','independentBSDTarAllRawBodies':'PASS','exactIncludedPythonParser':python,'exactIncludedNodeParser':node_result,'sourcePreservation':'PASS','unlistedMembers':0,'symlinks':0,'hardlinks':0}}
 external={archive.name+'.sha256':(receipt['archiveSHA256']+'  '+archive.name+'\n').encode(),'bundle-manifest.json':mb,'bundle-manifest.sha256':checksum(mb),**{k:v for k,v in new.items()if not k.startswith('lineage/')}}
 for n,b in external.items():
  with(out/n).open('xb')as f:f.write(b)
 with(out/'PACKAGING-VERIFICATION.json').open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
 with(out/'LATEST.json').open('x')as f:json.dump({'archive':archive.name,'sha256':receipt['archiveSHA256'],'qualification':q['status'],'runtimeAcceptance':q['runtimeAcceptance'],'manifestSHA256':ms,'productionSignature':False},f,indent=2);f.write('\n')
 print(json.dumps({k:receipt[k]for k in['archive','archiveSHA256','compressedBytes','members','manifestPayloadFiles','sourceManifestSHA256','manifestSHA256']},indent=2))
def main():
 a=argparse.ArgumentParser();a.add_argument('--source',default=str(R/'.local/simstability03/receiver03'));a.add_argument('--source-sha',default='df3eb4ec961e2fc83116440ec017796593b36847f2e1a601e7dd0a8b11ec5c8f');a.add_argument('--qualification',required=True);a.add_argument('--name',default='AERIS-SIM-STABILITY03-ENGINEERING.tar.gz');assemble(a.parse_args())
if __name__=='__main__':main()
