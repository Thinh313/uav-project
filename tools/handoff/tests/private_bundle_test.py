#!/usr/bin/env python3
"""Tiny generated adversarial fixtures; no production-package extraction."""
import argparse,hashlib,importlib.util,io,json,os,stat,tarfile,tempfile,zipfile
from pathlib import Path
from unittest.mock import patch
S=Path(__file__).resolve().parents[1]/'private_bundle.py';spec=importlib.util.spec_from_file_location('private_intake_under_test',S);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
H=lambda b:hashlib.sha256(b).hexdigest();J=lambda v:json.dumps(v,sort_keys=True).encode();C=(5,2,3,1,1,1)
def archive(entries,zipped=True):
 out=io.BytesIO()
 with tarfile.open(fileobj=out,mode='w:gz'if zipped else'w:',format=tarfile.PAX_FORMAT)as t:
  for name,data,kind,mode in entries:
   r=tarfile.TarInfo(name);r.mode=mode;r.type=kind
   if kind in(tarfile.LNKTYPE,tarfile.SYMTYPE):r.linkname=data;r.size=0;t.addfile(r)
   else:r.size=len(data);t.addfile(r,io.BytesIO(data))
 return out.getvalue()
def fixture(fault=None):
 data={n:b'fixture metadata\n'for n in m.NAMES};public={'README.md':b'public fixture\n','docs/overlay.md':b'anonymous','bin/run':b'echo fixture\n'};export_public=dict(public)
 if fault and fault.startswith('authoring'):
  export_public.update({'GIT-REPOSITORY.md':b'old git guide','.gitignore':b'old-ignore\n'});public.update({'README.md':b'new handoff guide','GIT-REPOSITORY.md':b'new git guide','.gitignore':export_public['.gitignore']+m.IGNORE_SUFFIX,'docs/HISTORY-README-2026-10-31.md':export_public['README.md'],'docs/HISTORY-GIT-REPOSITORY-2026-10-31.md':export_public['GIT-REPOSITORY.md']})
  if fault=='authoring-history':public['docs/HISTORY-README-2026-10-31.md']=b'tampered history'
  if fault=='authoring-prefix':public['.gitignore']=b'bad-ignore\n'+m.IGNORE_SUFFIX
  if fault=='authoring-append':public['.gitignore']+=b'bad append'
  if fault=='authoring-unknown':public['bin/run']=b'unknown product replacement'
 pub=[{'path':n,'kind':'file','bytes':len(b),'sha256':H(b)}for n,b in public.items()];pub.append({'path':'bin/link','kind':'symlink','bytes':3,'sha256':H(b'run')});export_rows=[{'path':n,'sha256':H(b),'bytes':len(b)}for n,b in export_public.items()]+[{'path':'bin/link','sha256':H(b'run'),'bytes':3}]
 pm={'format':'uav-project-public-source-manifest','version':1,'files':pub};data['PUBLIC-SOURCE-MANIFEST.json']=J(pm)
 pe=[('uav-project/'+n,b,tarfile.REGTYPE,0o755 if n=='bin/run'else 0o644)for n,b in public.items()]+[('uav-project/bin/link','run',tarfile.SYMTYPE,0o777),('uav-project/handoff/SOURCE-MANIFEST.json',J(pm),tarfile.REGTYPE,0o644)]
 if fault=='escape':pe.append(('uav-project/../escape',b'x',tarfile.REGTYPE,0o644))
 if fault=='absolute':pe.append(('/absolute',b'x',tarfile.REGTYPE,0o644))
 if fault=='duplicate':pe.append(pe[0])
 if fault=='git':pe.append(('uav-project/.git/config',b'x',tarfile.REGTYPE,0o644))
 if fault=='source-sha':pe[0]=(pe[0][0],b'changed',tarfile.REGTYPE,0o644)
 if fault=='symlink-escape':pe[3]=(pe[3][0],'../../../escape',tarfile.SYMTYPE,0o777)
 if fault=='special':pe.append(('uav-project/fifo',b'',tarfile.FIFOTYPE,0o600))
 data['PUBLIC-SOURCE.tar.gz']=archive(pe)
 if fault=='gzip-truncated':data['PUBLIC-SOURCE.tar.gz']=data['PUBLIC-SOURCE.tar.gz'][:-8]
 original=b'private original';restricted=b'private fixture';export={'format':'uav-project-source-export','publicFiles':export_rows,'restricted':[{'path':'private/notes.md','sha256':H(restricted),'bytes':len(restricted)}],'anonymized':[{'path':'docs/overlay.md','originalSHA256':H(original),'publicSHA256':H(public['docs/overlay.md']),'originalPrivateOverlay':True}],'secretPatternFilesHeldBack':[]}
 if fault=='overlay':export['anonymized'][0]['publicSHA256']='0'*64
 data['export-manifest-private.json']=J(export);out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED)as z:
  for n,b in[('private/notes.md',restricted),('docs/overlay.md',original)]:
   r=zipfile.ZipInfo(n);r.create_system=3;r.external_attr=(stat.S_IFLNK|0o777 if fault=='zip-symlink'else 0o600)<<16;z.writestr(r,b'wrong'if fault=='context-sha'else b)
  if fault=='context-extra':z.writestr('private/extra',b'x')
 data['PRIVATE-CONTEXT.zip']=out.getvalue();engineering=b'engineering fixture';ee=[('evidence/one',engineering,tarfile.REGTYPE,0o444),('evidence/link','evidence/one',tarfile.LNKTYPE,0o444),('README.md',public['README.md'],tarfile.REGTYPE,0o644)]
 if fault=='hardlink-escape':ee[1]=(ee[1][0],'../escape',tarfile.LNKTYPE,0o444)
 if fault=='hardlink-forward':ee[0],ee[1]=ee[1],ee[0]
 data['ENGINEERING-REPLAY-KIT.tar.gz']=archive(ee);em={'format':'uav-project-engineering-replay-kit','archiveSHA256':H(data['ENGINEERING-REPLAY-KIT.tar.gz']),'files':[{'path':n,'bytes':len(engineering)if n.startswith('evidence/')else len(public['README.md']),'sha256':H(engineering)if n.startswith('evidence/')else H(public['README.md']),'mode':0o444 if n.startswith('evidence/')else 0o644}for n,_,_,_ in ee]}
 if fault=='engineering-mode':em['files'][0]['mode']=0o600
 data['ENGINEERING-REPLAY-KIT.manifest.json']=J(em)
 blobs={};blob=lambda b:blobs.setdefault(H(b),b)and H(b)
 cfg=blob(J({'os':'linux','architecture':'arm64'}));layer=blob(b'layer');manifest=blob(J({'config':{'digest':'sha256:'+cfg,'size':len(blobs[cfg])},'layers':[{'digest':'sha256:'+layer,'size':len(blobs[layer])}]}));root=blob(J({'manifests':[{'digest':'sha256:'+manifest,'size':len(blobs[manifest]),'platform':{'os':'linux','architecture':'arm64'}}]}))
 ie=[('blobs/sha256/'+h,b,tarfile.REGTYPE,0o644)for h,b in blobs.items()]+[('index.json',J({'manifests':[{'digest':'sha256:'+root,'size':len(blobs[root])}]}),tarfile.REGTYPE,0o644),('manifest.json',J([{'Config':'blobs/sha256/'+cfg,'Layers':['blobs/sha256/'+layer]}]),tarfile.REGTYPE,0o644),('oci-layout',J({'imageLayoutVersion':'1.0.0'}),tarfile.REGTYPE,0o644)]
 data['SITL-LINUX-ARM64-IMAGE.tar.gz']=archive(ie);data['SITL-IMAGE.manifest.json']=J({'archiveSHA256':H(data['SITL-LINUX-ARM64-IMAGE.tar.gz']),'archiveBytes':len(data['SITL-LINUX-ARM64-IMAGE.tar.gz']),'imageID':'sha256:'+root,'os':'linux','architecture':'arm64'})
 if fault=='image-id':q=json.loads(data['SITL-IMAGE.manifest.json']);q['imageID']='sha256:'+'0'*64;data['SITL-IMAGE.manifest.json']=J(q)
 data['SHA256SUMS.txt']=''.join(H(b)+'  '+n+'\n'for n,b in data.items()if n!='SHA256SUMS.txt').encode()
 if fault=='checksum':data['README-PRIVATE.md']=b'altered after checksum'
 outer=archive([('uav-project-private/'+n,b,tarfile.REGTYPE,0o600)for n,b in data.items()],False)
 if fault=='outer-truncated':outer=outer[:-16000]
 return outer

def run(parent):
 removed=[];checks=[]
 with tempfile.TemporaryDirectory(prefix='codex-tmp-intake01-20261031-',dir=parent)as scratch:
  root=Path(scratch);removed.append(str(root));bundle=root/'tiny-bundle.tar';bundle.write_bytes(fixture());expected=H(bundle.read_bytes())
  with m.Bundle(bundle,expected,C)as b:
   verified=b.verify();assert verified['sourceEntries']==5 and verified['imageIdentity'].startswith('VERIFIED_');checks.append('valid_nested_and_image_identity')
   with patch.object(m.shutil,'disk_usage',return_value=type('D',(),{'free':m.FLOOR+b.plan['allocation']-1})()):
    try:b.prepare(root/'insufficient')
    except m.Refused as e:assert str(e)=='DISK_ADMISSION'
    else:raise AssertionError('disk refusal missing')
   assert not(root/'insufficient').exists();checks.append('disk_admission_has_no_destination_side_effect')
   with patch.object(m.shutil,'disk_usage',return_value=type('D',(),{'free':100*2**30})()):result=b.prepare(root/'prepared')
   assert result['status']=='PRIVATE_DERIVED_NOT_PUBLIC_SNAPSHOT';dest=root/'prepared';assert(dest/'docs/overlay.md').read_bytes()==b'private original';assert(dest/'evidence/one').stat().st_ino==(dest/'evidence/link').stat().st_ino;assert stat.S_IMODE((dest/'evidence/one').stat().st_mode)==0o444;assert os.readlink(dest/'bin/link')=='run';assert not(dest/'.git').exists();assert(dest/'private-handoff-artifacts/SITL-LINUX-ARM64-IMAGE.tar.gz').is_file();checks+=['derived_original_overlay','hardlink_and_readonly_mode','safe_source_symlink','image_retained_without_load','nonGit_destination']
   for name in['prepared']:
    try:b.prepare(root/name)
    except m.Refused:checks.append('existing_destination_refused')
    else:raise AssertionError('existing accepted')
   git=root/'public-git';git.mkdir();(git/'.git').mkdir()
   try:b.prepare(git/'not-private')
   except m.Refused:checks.append('Git_destination_refused')
   else:raise AssertionError('Git accepted')
   link=root/'linked-parent';link.symlink_to(git,target_is_directory=True)
   try:b.prepare(link/'not-private')
   except m.Refused:checks.append('symlink_parent_refused')
   else:raise AssertionError('symlink parent accepted')
  raw=fixture('authoring');bundle.write_bytes(raw)
  with m.Bundle(bundle,H(raw),(9,2,3,1,1,1))as b:
   verified=b.verify();assert len(verified['publicAuthoringChanges'])==3
   with patch.object(m.shutil,'disk_usage',return_value=type('D',(),{'free':100*2**30})()):prepared=b.prepare(root/'authored-prepared')
   assert len(prepared['publicAuthoringChanges'])==3;checks+=['metadata_authoring_exact_history_and_prefix_append','metadata_authoring_recorded_in_derived_receipt']
  for fault,code in[('authoring-history','AUTHORING_HISTORY_PROOF'),('authoring-prefix','AUTHORING_IGNORE_EXACT_PREFIX_APPEND'),('authoring-append','AUTHORING_IGNORE_EXACT_PREFIX_APPEND'),('authoring-unknown','EXPORT_UNKNOWN_SOURCE_REPLACEMENT')]:
   raw=fixture(fault);bundle.write_bytes(raw)
   try:
    with m.Bundle(bundle,H(raw),(9,2,3,1,1,1))as b:b.verify()
   except m.Refused as e:assert str(e)==code;checks.append(fault+'_refused')
   else:raise AssertionError('accepted '+fault)
  for fault in['escape','absolute','duplicate','git','source-sha','symlink-escape','special','gzip-truncated','overlay','zip-symlink','context-sha','context-extra','hardlink-escape','hardlink-forward','engineering-mode','image-id','checksum','outer-truncated']:
   raw=fixture(fault);bundle.write_bytes(raw)
   try:
    with m.Bundle(bundle,H(raw),C)as b:b.verify()
   except Exception as e:
    expected_codes={'escape':'PATH_COMPONENT','absolute':'PATH_SHAPE','duplicate':'DUPLICATE_TAR_PATH','git':'PATH_COMPONENT','source-sha':'SOURCE_FILE_SHA_KIND_SIZE','symlink-escape':'PATH_COMPONENT','special':'UNSAFE_TAR_KIND','gzip-truncated':'EOFError','overlay':'OVERLAY_EXPECTED_PUBLIC_SHA','zip-symlink':'ZIP_UNSAFE_KIND','context-sha':'CONTEXT_SHA_SIZE','context-extra':'CONTEXT_EXACT_NAMES','hardlink-escape':'PATH_COMPONENT','hardlink-forward':'HARDLINK_PRIOR_REGULAR_TARGET','engineering-mode':'ENGINEERING_SHA_SIZE_MODE','image-id':'IMAGE_INDEX_IDENTITY','checksum':'INNER_ARCHIVE_SHA256','outer-truncated':'OUTER_SIZE_BOUND'}
    code=str(e)if isinstance(e,m.Refused)else type(e).__name__;assert code==expected_codes[fault],(fault,code);checks.append(fault+'_refused')
   else:raise AssertionError('accepted '+fault)
  bundle.write_bytes(fixture())
  try:
   with m.Bundle(bundle,'0'*64,C)as b:b.verify()
  except m.Refused as e:assert str(e)=='OUTER_SHA256';checks.append('external_digest_refused')
  else:raise AssertionError('wrong external digest accepted')
  with m.Bundle(bundle,H(bundle.read_bytes()),C)as b:
   b.verify();bundle.write_bytes(bundle.read_bytes()+b'changed')
   try:
    with patch.object(m.shutil,'disk_usage',return_value=type('D',(),{'free':100*2**30})()):b.prepare(root/'changed-bundle')
   except m.Refused as e:assert str(e)=='BUNDLE_CHANGED_DURING_READ';checks.append('bundle_change_before_prepare_refused')
   else:raise AssertionError('changed bundle prepared')
 assert all(not Path(p).exists()for p in removed)
 return{'format':'uav-private-intake-adversarial-mock','status':'PASS','checks':len(checks),'cases':checks,'productionPackageExtracted':False,'actorsSDKDockerOrNetworkUsed':False,'scratchRemoved':removed,'fixtureBytesMaximum':len(fixture()),'diskProbeMockedForTinySuccess':True,'originalPackageChanged':False,'testCountsNotProductionAcceptance':True}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--scratch-parent',required=True);a=p.parse_args();print(json.dumps(run(Path(a.scratch_parent)),sort_keys=True))
