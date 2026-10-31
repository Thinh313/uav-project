"""Explicit receiver04 closure -> diagnostic NOT_READY tar; no runtime/build/extraction."""
from pathlib import Path,PurePosixPath
import os,stat,json,hashlib,tarfile,io,subprocess,shutil,datetime,ast,types
R=Path(__file__).resolve().parents[2];SRC=R/'.local/simverify02/receiver04';OUT=R/'delivery/sim-verified02';E=R/'evidence/simverify02';LIMIT=512*2**20
assert shutil.disk_usage(R).free>=20*2**30,'DISK20_REQUIRED'
OUT.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def safe(n):
 p=PurePosixPath(n)
 assert n and not p.is_absolute()and p.as_posix()==n and all(x not in['','..','.']for x in p.parts),'UNSAFE_NAME'
 assert '\\'not in n and '\0'not in n
 return n
source_bytes=(SRC/'bundle-manifest.json').read_bytes();source=json.loads(source_bytes);source_sha=sha(source_bytes)
source_checksum=(SRC/'bundle-manifest.sha256').read_text().strip();assert source_sha==source_checksum,'PARENT_MANIFEST_SHA'
entries={};source_fingerprints={}
for n,m in source['files'].items():
 safe(n);p=SRC/n
 for parent in [p,*p.parents]:
  if parent==SRC.parent:break
  assert not parent.is_symlink(),'SOURCE_SYMLINK'
 st=p.lstat();assert stat.S_ISREG(st.st_mode)and not p.is_symlink(),'SOURCE_REGULAR_ONLY'
 b=p.read_bytes();assert len(b)==m['bytes']and sha(b)==m['sha256']and stat.S_IMODE(st.st_mode)==m['mode'],n
 assert m['mode']in[0o644,0o755],'SOURCE_MODE'
 entries[n]={'path':p,'sha256':m['sha256'],'bytes':m['bytes'],'mode':m['mode']};source_fingerprints[n]=(m['sha256'],m['bytes'],m['mode'])
assert 'runtime/sitl/arducopter'not in entries
notes='''# NOT_READY: diagnostic engineering handoff, packaging attempt02

Attempt01 is rejected for included-parser incompatibility: its manifest checksum used a conventional filename suffix instead of the required 64-hex-plus-newline format. Attempt01 remains retained, immutable and superseded. Attempt02 corrects that wire format and lists the structural mountpoint in the regenerated dependency closure. The original dependencies JSON is retained in lineage; original receiver04 source/assets/APK bytes remain unchanged. No runtime/source correction or functional requalification is performed.\n\nThis archive is a diagnostic source/dependency handoff. It is not a qualified flight simulator release, Beta acceptance, production APK or Hera flight-control release. Do not use it to control a physical aircraft.\n\nThe payload preserves the exact receiver04 manifest closure and existing engineering APK, with these packaging-only additions: an empty regular `runtime/sitl/arducopter` Docker mountpoint, lineage manifest, this notice and qualification metadata. The empty file is a structural bind-mount target, not firmware and not an executable replacement. The actual pinned AP artifact remains at its existing runtime build path. No runtime was started to qualify this new archive.\n\nUnresolved acceptance gates:\n\n- A usable, fresh simulator/AP control link and recovery after a dead link remain unqualified.\n- A complete manual takeoff, neutral acquisition, bounded pitch/yaw, release/background/stale revocation, LAND and observed ground/disarm sequence did not pass end to end.\n- Recipient policy advertises apSeconds300 while the projected runtime fallback is210; the server countdown starts before admission. This known duration-policy mismatch is not repaired by this diagnostic package.
- Real-time factor, clock/frame correctness and sustained behavior under the operator/UI load have not been accepted for this recipient build.\n- Durable closed review and full raw evidence reconstruction have not been accepted. Metadata or externally referenced raw paths do not establish full raw verification.\n- Android public SAF export/import, restart persistence and receiver roundtrip have not been accepted. Import never restores control authority.\n- RPM-based synthesized audio is not Hera acoustic calibration; audible output and stale/end mute acceptance remain unverified.\n- Physical Xiaomi/Hera/HeraHub/SDK acceptance, AUTO missions and broader weather/collision/training validity are not established. Features marked unsupported remain unsupported.\n\nThe included 3D assets and input/audio code do not prove functional readiness or subjective visual/training quality. Structural archive verification proves byte/membership integrity only. Existing `sourceIDs` describe lineage, not a certification or software signature.\n\nThe engineering APK is unchanged. Use only an explicitly selected Android USB serial; never root a physical phone, choose an arbitrary connected device or use another app's data. The supported host is the declared macOS/ARM dependency set, not an asserted Windows/Linux port. Existing 20 GiB admission and 10 GiB plus reserve runtime guards remain in the source. Start/doctor scripts do not override this NOT_READY qualification.\n\nBefore any authorized future test: extract into a new empty directory, verify the archive SHA and manifest, inspect `QUALIFICATION-NOT-READY.json`, then follow `planning/simhand01/README.md`. A doctor or clean process exit is not functional acceptance.\n'''
qualification={'format':'aeris-simverified02-diagnostic-qualification','version':1,'status':'NOT_READY','engineeringOnly':True,'productionSignature':False,'functionalQualification':False,'originalArchiveAndReceiver04Immutable':True,'packagingAttempt':2,'supersedesRejectedPackagingAttempt':{'archive':'AERIS-SIM-VERIFY02-DIAGNOSTIC-NOT-READY.tar.gz','sha256':'7046c2b37a92b2b747d344a4d5d3d765fa5b7588fd674b1f8158e8b7fa5405ad','reason':'INCLUDED_CHECKSUM_PARSER_REJECTS_FILENAME_SUFFIX'},'knownDurationPolicyGap':'recipient apSeconds300 vs projected fallback210; countdown begins before admission','parentManifestSha256':source_sha,'parentEngineeringRevision':source.get('engineeringRevision'),'sourceIDs':source.get('sourceIDs'),'addedStructuralMountpoint':{'path':'runtime/sitl/arducopter','bytes':0,'mode':0o644,'sha256':sha(b''),'purpose':'EMPTY_REGULAR_DOCKER_BIND_TARGET_NOT_FIRMWARE'},'unchangedAPK':next({'path':n,**m}for n,m in source['files'].items()if n.endswith('.apk')),'remainingAcceptance':['usableFreshAPLinkAndDeadLinkRecovery','completeManualFlightAndNeutralAuthorityLifecycle','realTimeFactorClockAndFullFrameIntegrityUnderLoad','durableReviewAndFullRawVerification','AndroidSAFExportImportRestartReceiverRoundtrip','audibleRPMSynthesisAndStaleMute','physicalXiaomiHeraSDK','AUTOAndBroaderWeatherCollisionTrainingValidity'],'archiveIntegrity':'SEE_EXTERNAL_PACKAGING_RECEIPT; NOT_FUNCTIONAL_ACCEPTANCE'}
new_bytes={'runtime/sitl/arducopter':b'','RELEASE-NOTES-NOT-READY.md':notes.encode(),'QUALIFICATION-NOT-READY.json':(json.dumps(qualification,ensure_ascii=False,indent=2)+'\n').encode(),'lineage/receiver04-bundle-manifest.json':source_bytes,'lineage/receiver04-dependencies.json':(SRC/'planning/simhand01/dependencies.json').read_bytes()}
for n,b in new_bytes.items():safe(n);assert n not in entries;entries[n]={'data':b,'sha256':sha(b),'bytes':len(b),'mode':0o644}
dep_name='planning/simhand01/dependencies.json';old_dep=entries[dep_name];dependencies=json.loads((SRC/dep_name).read_text());dependencies['files']={n:{k:v for k,v in m.items()if k in['sha256','bytes','mode']}for n,m in sorted(entries.items())if n!=dep_name};dependencies['uncompressedBytes']=sum(v['bytes']for v in dependencies['files'].values());dependencies['qualificationStatus']='NOT_READY';dependencies['packagingRevision']='SIMVERIFY02-DIAGNOSTIC02';dep_bytes=(json.dumps(dependencies,ensure_ascii=False,indent=2)+'\n').encode();entries[dep_name]={'data':dep_bytes,'sha256':sha(dep_bytes),'bytes':len(dep_bytes),'mode':0o644}
manifest={**source,'files':{n:{k:v for k,v in entries[n].items()if k in['sha256','bytes','mode']}for n in sorted(entries)},'uncompressedBytes':sum(m['bytes']for m in entries.values()),'qualificationStatus':'NOT_READY','engineeringRevision':{'id':'SIMVERIFY02-DIAGNOSTIC-PACKAGE02','parentManifestSHA256':source_sha,'parentEngineeringRevision':source.get('engineeringRevision'),'changes':['checksum wire format64hex+LF exact included-parser compatibility','structural mountpoint included in dependency closure','NOT_READY release qualification and original dependencies/manifest lineage','attempt01 explicitly rejected and superseded'],'productionSignature':False},'functionalQualification':False}
manifest_bytes=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();manifest_sha=sha(manifest_bytes);checksum=(manifest_sha+'\n').encode();assert len(checksum)==65
for n,b in [('bundle-manifest.json',manifest_bytes),('bundle-manifest.sha256',checksum)]:entries[n]={'data':b,'bytes':len(b),'sha256':sha(b),'mode':0o644}
assert sum(m['bytes']for m in entries.values())<LIMIT,'UNCOMPRESSED512MIB'
archive=OUT/'AERIS-SIM-VERIFY02-DIAGNOSTIC02-NOT-READY.tar.gz'
with tarfile.open(archive,'x:gz',format=tarfile.USTAR_FORMAT,compresslevel=6)as t:
 for n in sorted(entries):
  m=entries[n];info=tarfile.TarInfo(safe(n));info.size=m['bytes'];info.mode=m['mode'];info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  if 'path'in m:
   with m['path'].open('rb')as f:t.addfile(info,f)
  else:t.addfile(info,io.BytesIO(m['data']))
assert archive.stat().st_size<LIMIT
# First verifier: raw tar member headers + every complete decompressed body.
with tarfile.open(archive,'r:gz')as t:
 members=t.getmembers();assert len(members)==len(entries)and len({m.name for m in members})==len(members)
 assert set(m.name for m in members)==set(entries)
 for m in members:
  safe(m.name);assert m.isfile()and not m.linkname and not m.pax_headers and m.mode==entries[m.name]['mode']
  b=t.extractfile(m).read();assert len(b)==entries[m.name]['bytes']and sha(b)==entries[m.name]['sha256']
# Independent parser: BSD tar listing and one concatenated stdout body stream.
listing=subprocess.run(['/usr/bin/tar','-tzf',str(archive)],capture_output=True,check=True,timeout=30).stdout.decode().splitlines()
assert listing==sorted(entries)and len(listing)==len(set(listing))
p=subprocess.Popen(['/usr/bin/tar','-xOf',str(archive)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
bsd=[]
try:
 for n in listing:
  left=entries[n]['bytes'];h=hashlib.sha256();count=0
  while left:
   b=p.stdout.read(min(left,1024*1024));assert b,'BSD_TAR_SHORT_BODY';h.update(b);count+=len(b);left-=len(b)
  assert h.hexdigest()==entries[n]['sha256'];bsd.append({'path':n,'bytes':count,'sha256':h.hexdigest()})
 assert p.stdout.read(1)==b'','BSD_TAR_EXTRA_BODY'
 stderr=p.stderr.read();assert p.wait(timeout=30)==0,stderr.decode(errors='replace')
finally:
 if p.poll()is None:p.kill();p.wait(timeout=5)
# Recheck original parent bytes and every original member after streaming.
assert (SRC/'bundle-manifest.json').read_bytes()==source_bytes
for n,(h,b,mode)in source_fingerprints.items():
 p=SRC/n;assert sha(p.read_bytes())==h and p.stat().st_size==b and stat.S_IMODE(p.stat().st_mode)==mode

# Invoke exact included Python parser functions over an archive-backed readonly FS.
# The function bodies are compiled unchanged from the included support.py AST.
with tarfile.open(archive,'r:gz')as t:virtual={m.name:t.extractfile(m).read()for m in t.getmembers()}
class VFile:
 def __init__(self,name=''):self.name=str(name)
 def __truediv__(self,n):return VFile((PurePosixPath(self.name)/str(n)).as_posix())
 def read_bytes(self):return virtual[self.name]
 def read_text(self):return self.read_bytes().decode()
 def is_file(self):return self.name in virtual
 def is_symlink(self):return False
 def stat(self):return types.SimpleNamespace(st_size=len(self.read_bytes()))
 def open(self,mode='r'):
  assert mode in['r','rb'];return io.BytesIO(self.read_bytes())if mode=='rb'else io.StringIO(self.read_text())
def path_adapter(p):return p if isinstance(p,VFile)else Path(p)
tree=ast.parse(virtual['planning/simhand01/support.py'].decode());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in['sha','verify_manifest']];doctor=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='doctor');closure=next(n for n in doctor.body if isinstance(n,ast.FunctionDef)and n.name=='closure');namespace={'Path':path_adapter,'ROOT':VFile(),'hashlib':hashlib,'json':json,'deps':VFile('planning/simhand01/dependencies.json')};exec(compile(ast.Module(body=nodes+[closure],type_ignores=[]),'INCLUDED_support.py_exact_functions','exec'),namespace);python_digest=namespace['verify_manifest'](VFile());assert python_digest==manifest_sha;dependency_result=namespace['closure']();assert dependency_result['verifiedFiles']==len(dependencies['files']);assert dependencies['files']['runtime/sitl/arducopter']['sha256']==sha(b'')
correct_checksum=virtual['bundle-manifest.sha256'];virtual['bundle-manifest.sha256']=(manifest_sha+'  bundle-manifest.json\n').encode();old_wire_rejected=False
try:namespace['verify_manifest'](VFile())
except RuntimeError as err:old_wire_rejected=str(err)=='BUNDLE_MANIFEST_SHA'
assert old_wire_rejected;virtual['bundle-manifest.sha256']=correct_checksum
node=subprocess.run(['node','--experimental-vm-modules',str(R/'planning/simverify02/verify-diagnostic-parsers.mjs'),str(archive)],capture_output=True,text=True,timeout=45);assert node.returncode==0,node.stderr;node_parser=json.loads(node.stdout);assert node_parser['status']=='PASS'
parser_results={'status':'PASS','checksumBytes':len(checksum),'exactIncludedPythonVerifyManifest':'ACCEPTED','exactIncludedPythonDoctorDependencyClosure':dependency_result,'negativeConventional87ByteChecksum':'REJECTED_BUNDLE_MANIFEST_SHA','exactIncludedNodeBudgetResolver':node_parser,'scope':'UNMODIFIED_INCLUDED_FUNCTION_BODIES_WITH_READONLY_ARCHIVE_VIRTUAL_FS; NO_EXTRACTION_OR_RUNTIME_START; NOT_FULL_EXTERNAL_HARDWARE_DOCTOR'}

archive_sha=sha(archive.read_bytes())
def put(name,b):
 aliases={'bundle-manifest.json':'bundle-manifest-diagnostic02.json','bundle-manifest.sha256':'bundle-manifest-diagnostic02.sha256','RELEASE-NOTES-NOT-READY.md':'RELEASE-NOTES-DIAGNOSTIC02-NOT-READY.md','QUALIFICATION-NOT-READY.json':'QUALIFICATION-DIAGNOSTIC02-NOT-READY.json'}
 p=OUT/aliases.get(name,name)
 with p.open('xb')as f:f.write(b)
for n,b in [('bundle-manifest.json',manifest_bytes),('bundle-manifest.sha256',checksum),('RELEASE-NOTES-NOT-READY.md',notes.encode()),('QUALIFICATION-NOT-READY.json',new_bytes['QUALIFICATION-NOT-READY.json']),('AERIS-SIM-VERIFY02-DIAGNOSTIC02-NOT-READY.tar.gz.sha256',(archive_sha+'  '+archive.name+'\n').encode())]:put(n,b)
receipt={'format':'aeris-simverify02-diagnostic-archive-verification','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(archive.relative_to(R)),'sha256':archive_sha,'compressedBytes':archive.stat().st_size,'uncompressedMemberBytes':sum(m['bytes']for m in entries.values()),'members':len(entries),'manifestPayloadFiles':len(manifest['files']),'parentFilesPreserved':len(source_fingerprints),'exactOriginalPayloadAtSamePath':len(source_fingerprints)-1,'originalDependencyBytesCopiedToLineage':True,'includedParserCompatibility':parser_results,'parentManifestSha256':source_sha,'manifestSha256':manifest_sha,'originalAPK':qualification['unchangedAPK'],'structuralMountpoint':qualification['addedStructuralMountpoint'],'verification':{'pythonTarHeadersAndAllSHA':'PASS','independentBSDTarListingAndAllRawBodies':'PASS','uniqueExplicitRegularSafeMembers':'PASS','sourceReceiver04UnchangedAfterAssembly':'PASS','symlinks':0,'hardlinks':0,'unlistedFiles':0,'filesystemExtractionPerformed':False},'functionalStatus':'NOT_READY','functionalQualification':False,'packagingAttempt':2,'supersededFailedArchive':'delivery/sim-verified02/AERIS-SIM-VERIFY02-DIAGNOSTIC-NOT-READY.tar.gz','runtimeStarted':False,'newBuildOrSignature':False,'newScratchOutsideRepository':False,'allMemberVerification':bsd}
with (E/'diagnostic-archive-verification02.json').open('x')as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
with (E/'diagnostic-archive-attempt01-rejected.json').open('x')as f:json.dump({'status':'REJECTED_PARSER_COMPATIBILITY','immutablePriorArchive':'delivery/sim-verified02/AERIS-SIM-VERIFY02-DIAGNOSTIC-NOT-READY.tar.gz','sha256':'7046c2b37a92b2b747d344a4d5d3d765fa5b7588fd674b1f8158e8b7fa5405ad','reason':'87byte conventional checksum filename suffix rejected by exact included Python/Node parsers','supersededBy':receipt['archive'],'replacementSHA256':archive_sha,'functionalQualification':False},f,indent=2);f.write('\n')
with (OUT/'LATEST-DIAGNOSTIC.json').open('x')as f:json.dump({'selectedArchive':archive.name,'sha256':archive_sha,'packagingAttempt':2,'parserCompatibility':'PASS_INCLUDED_PYTHON_AND_NODE','functionalStatus':'NOT_READY','doNotUseArchiveAttempt01':'AERIS-SIM-VERIFY02-DIAGNOSTIC-NOT-READY.tar.gz','reasonAttempt01Rejected':'INCLUDED_PARSER_CHECKSUM_WIRE_FORMAT'},f,indent=2);f.write('\n')
print(json.dumps({k:receipt[k]for k in['archive','sha256','compressedBytes','uncompressedMemberBytes','members','manifestPayloadFiles','parentFilesPreserved','manifestSha256','functionalStatus']},indent=2))
