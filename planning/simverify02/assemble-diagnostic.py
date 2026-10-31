"""Explicit receiver04 closure -> diagnostic NOT_READY tar; no runtime/build/extraction."""
from pathlib import Path,PurePosixPath
import os,stat,json,hashlib,tarfile,io,subprocess,shutil,datetime
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
source_checksum=(SRC/'bundle-manifest.sha256').read_text().split()[0];assert source_sha==source_checksum,'PARENT_MANIFEST_SHA'
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
notes='''# NOT_READY: diagnostic engineering handoff\n\nThis archive is a diagnostic source/dependency handoff. It is not a qualified flight simulator release, Beta acceptance, production APK or Hera flight-control release. Do not use it to control a physical aircraft.\n\nThe payload preserves the exact receiver04 manifest closure and existing engineering APK, with these packaging-only additions: an empty regular `runtime/sitl/arducopter` Docker mountpoint, lineage manifest, this notice and qualification metadata. The empty file is a structural bind-mount target, not firmware and not an executable replacement. The actual pinned AP artifact remains at its existing runtime build path. No runtime was started to qualify this new archive.\n\nUnresolved acceptance gates:\n\n- A usable, fresh simulator/AP control link and recovery after a dead link remain unqualified.\n- A complete manual takeoff, neutral acquisition, bounded pitch/yaw, release/background/stale revocation, LAND and observed ground/disarm sequence did not pass end to end.\n- Real-time factor, clock/frame correctness and sustained behavior under the operator/UI load have not been accepted for this recipient build.\n- Durable closed review and full raw evidence reconstruction have not been accepted. Metadata or externally referenced raw paths do not establish full raw verification.\n- Android public SAF export/import, restart persistence and receiver roundtrip have not been accepted. Import never restores control authority.\n- RPM-based synthesized audio is not Hera acoustic calibration; audible output and stale/end mute acceptance remain unverified.\n- Physical Xiaomi/Hera/HeraHub/SDK acceptance, AUTO missions and broader weather/collision/training validity are not established. Features marked unsupported remain unsupported.\n\nThe included 3D assets and input/audio code do not prove functional readiness or subjective visual/training quality. Structural archive verification proves byte/membership integrity only. Existing `sourceIDs` describe lineage, not a certification or software signature.\n\nThe engineering APK is unchanged. Use only an explicitly selected Android USB serial; never root a physical phone, choose an arbitrary connected device or use another app's data. The supported host is the declared macOS/ARM dependency set, not an asserted Windows/Linux port. Existing 20 GiB admission and 10 GiB plus reserve runtime guards remain in the source. Start/doctor scripts do not override this NOT_READY qualification.\n\nBefore any authorized future test: extract into a new empty directory, verify the archive SHA and manifest, inspect `QUALIFICATION-NOT-READY.json`, then follow `planning/simhand01/README.md`. A doctor or clean process exit is not functional acceptance.\n'''
qualification={'format':'aeris-simverified02-diagnostic-qualification','version':1,'status':'NOT_READY','engineeringOnly':True,'productionSignature':False,'functionalQualification':False,'originalArchiveAndReceiver04Immutable':True,'parentManifestSha256':source_sha,'parentEngineeringRevision':source.get('engineeringRevision'),'sourceIDs':source.get('sourceIDs'),'addedStructuralMountpoint':{'path':'runtime/sitl/arducopter','bytes':0,'mode':0o644,'sha256':sha(b''),'purpose':'EMPTY_REGULAR_DOCKER_BIND_TARGET_NOT_FIRMWARE'},'unchangedAPK':next({'path':n,**m}for n,m in source['files'].items()if n.endswith('.apk')),'remainingAcceptance':['usableFreshAPLinkAndDeadLinkRecovery','completeManualFlightAndNeutralAuthorityLifecycle','realTimeFactorClockAndFullFrameIntegrityUnderLoad','durableReviewAndFullRawVerification','AndroidSAFExportImportRestartReceiverRoundtrip','audibleRPMSynthesisAndStaleMute','physicalXiaomiHeraSDK','AUTOAndBroaderWeatherCollisionTrainingValidity'],'archiveIntegrity':'SEE_EXTERNAL_PACKAGING_RECEIPT; NOT_FUNCTIONAL_ACCEPTANCE'}
new_bytes={'runtime/sitl/arducopter':b'','RELEASE-NOTES-NOT-READY.md':notes.encode(),'QUALIFICATION-NOT-READY.json':(json.dumps(qualification,ensure_ascii=False,indent=2)+'\n').encode(),'lineage/receiver04-bundle-manifest.json':source_bytes}
for n,b in new_bytes.items():safe(n);assert n not in entries;entries[n]={'data':b,'sha256':sha(b),'bytes':len(b),'mode':0o644}
manifest={**source,'files':{n:{k:v for k,v in entries[n].items()if k in['sha256','bytes','mode']}for n in sorted(entries)},'uncompressedBytes':sum(m['bytes']for m in entries.values()),'qualificationStatus':'NOT_READY','engineeringRevision':{'id':'SIMVERIFY02-DIAGNOSTIC-PACKAGE01','parentManifestSHA256':source_sha,'parentEngineeringRevision':source.get('engineeringRevision'),'changes':['packaging-only empty regular Docker bind mountpoint','NOT_READY release qualification and exact parent manifest lineage'],'productionSignature':False},'functionalQualification':False}
manifest_bytes=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();manifest_sha=sha(manifest_bytes);checksum=(manifest_sha+'  bundle-manifest.json\n').encode()
for n,b in [('bundle-manifest.json',manifest_bytes),('bundle-manifest.sha256',checksum)]:entries[n]={'data':b,'bytes':len(b),'sha256':sha(b),'mode':0o644}
assert sum(m['bytes']for m in entries.values())<LIMIT,'UNCOMPRESSED512MIB'
archive=OUT/'AERIS-SIM-VERIFY02-DIAGNOSTIC-NOT-READY.tar.gz'
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
archive_sha=sha(archive.read_bytes())
def put(name,b):
 p=OUT/name
 with p.open('xb')as f:f.write(b)
for n,b in [('bundle-manifest.json',manifest_bytes),('bundle-manifest.sha256',checksum),('RELEASE-NOTES-NOT-READY.md',notes.encode()),('QUALIFICATION-NOT-READY.json',new_bytes['QUALIFICATION-NOT-READY.json']),('AERIS-SIM-VERIFY02-DIAGNOSTIC-NOT-READY.tar.gz.sha256',(archive_sha+'  '+archive.name+'\n').encode())]:put(n,b)
receipt={'format':'aeris-simverify02-diagnostic-archive-verification','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(archive.relative_to(R)),'sha256':archive_sha,'compressedBytes':archive.stat().st_size,'uncompressedMemberBytes':sum(m['bytes']for m in entries.values()),'members':len(entries),'manifestPayloadFiles':len(manifest['files']),'parentFilesPreserved':len(source_fingerprints),'parentManifestSha256':source_sha,'manifestSha256':manifest_sha,'originalAPK':qualification['unchangedAPK'],'structuralMountpoint':qualification['addedStructuralMountpoint'],'verification':{'pythonTarHeadersAndAllSHA':'PASS','independentBSDTarListingAndAllRawBodies':'PASS','uniqueExplicitRegularSafeMembers':'PASS','sourceReceiver04UnchangedAfterAssembly':'PASS','symlinks':0,'hardlinks':0,'unlistedFiles':0,'filesystemExtractionPerformed':False},'functionalStatus':'NOT_READY','functionalQualification':False,'runtimeStarted':False,'newBuildOrSignature':False,'newScratchOutsideRepository':False,'allMemberVerification':bsd}
with (E/'diagnostic-archive-verification01.json').open('x')as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:receipt[k]for k in['archive','sha256','compressedBytes','uncompressedMemberBytes','members','manifestPayloadFiles','parentFilesPreserved','manifestSha256','functionalStatus']},indent=2))
