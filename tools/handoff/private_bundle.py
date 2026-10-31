#!/usr/bin/env python3
"""Portable private intake. Digest integrity is not identity or flight admission."""
import argparse,gzip,io,hashlib,json,os,posixpath,re,shutil,stat,tarfile,unicodedata,zipfile
from pathlib import Path
CHUNK=1048576; FLOOR=10*2**30+256*2**20; MAX=2*2**30
COUNTS=(12532,334,2976,2037,5,9)
NAMES=('PUBLIC-SOURCE.tar.gz','PUBLIC-SOURCE-MANIFEST.json','PRIVATE-CONTEXT.zip','export-manifest-private.json','ENGINEERING-REPLAY-KIT.tar.gz','ENGINEERING-REPLAY-KIT.manifest.json','SITL-LINUX-ARM64-IMAGE.tar.gz','SITL-IMAGE.manifest.json','UAV-PROJECT-HANDOVER.pdf','README-PRIVATE.md','FINAL-HANDOFF-VERIFICATION.json','private-archive-QA.json','public-receiver-QA.json','PDF-QA.json','source-state.json','npm-test01.stdout.txt','npm-test01.stderr.txt','npm-test01.json','fixture-recheck01.json','fixture-recheck02.json','fixture-recheck03.json','public-mock-check01.json','publication-review.json','SHA256SUMS.txt')
KEEP=('SITL-LINUX-ARM64-IMAGE.tar.gz','SITL-IMAGE.manifest.json','PUBLIC-SOURCE-MANIFEST.json','export-manifest-private.json','ENGINEERING-REPLAY-KIT.manifest.json','README-PRIVATE.md'); ART='private-handoff-artifacts'
AUTHORING_HISTORY={'README.md':'docs/HISTORY-README-2026-10-31.md','GIT-REPOSITORY.md':'docs/HISTORY-GIT-REPOSITORY-2026-10-31.md'}
IGNORE_SUFFIX=b"\n# Public handoff: sensitive context and host artifacts are supplied separately.\n/handoff-private/\n/PRIVATE-CONTEXT.zip\n/ENGINEERING-REPLAY-KIT.tar.gz\n/SITL-LINUX-ARM64-IMAGE.tar.gz\n/tmp/\n!/evidence/workbench01/\n!/evidence/workbench01/handoff-manifest.json\n\n!/evidence/handoff09/\n!/evidence/handoff09/completed.aeris-handoff.json\n"
class Refused(ValueError):pass
def need(v,code):
 if not v:raise Refused(code)
def digest(f):
 h=hashlib.sha256();n=0
 while b:=f.read(CHUNK):h.update(b);n+=len(b);need(n<=MAX,'STREAM_BOUND')
 return h.hexdigest(),n
def safe(s):
 need(type(s)is str and 0<len(s)<=1024 and '\\'not in s and '\0'not in s and not s.startswith('/'),'PATH_SHAPE');parts=s.split('/');need(all(p not in('','.','..')and p.casefold()!='.git' for p in parts),'PATH_COMPONENT');return s
def unique(rows,key='path'):
 out={};fold=set()
 for r in rows:
  n=safe(r[key]);f=unicodedata.normalize('NFC',n).casefold();need(n not in out and f not in fold,'DUPLICATE_PATH');out[n]=r;fold.add(f)
 return out
def small(f,limit=8*CHUNK):
 out=[];n=0
 while b:=f.read(min(CHUNK,limit+1-n)):out.append(b);n+=len(b);need(n<=limit,'SMALL_READ_BOUND')
 return b''.join(out)
def parsed(b):
 def pairs(items):
  d={}
  for k,v in items:need(k not in d,'DUPLICATE_JSON_KEY');d[k]=v
  return d
 return json.loads(b,object_pairs_hook=pairs)
class Bounded:
 def __init__(self,f,limit=MAX):self.f=f;self.limit=limit
 def read(self,n):need(0<=n<=CHUNK,'ARCHIVE_HEADER_READ_BOUND');b=self.f.read(n);need(self.f.tell()<=self.limit,'ARCHIVE_EXPANDED_BOUND');return b
 def seek(self,n,w=0):need(w==0 and 0<=n<=self.limit,'ARCHIVE_SEEK_BOUND');return self.f.seek(n,w)
 def tell(self):return self.f.tell()
 def seekable(self):return True
def scan_tar(file,kind,consume=None,expected=None,capture=None,capture_names=None):
 gz=gzip.GzipFile(fileobj=file);stream=Bounded(gz);rows={};dirs={};fold=set();total=0
 with tarfile.open(fileobj=stream,mode='r:')as t:
  for m in t:
   need(len(rows)+len(dirs)<20000,'TAR_COUNT_BOUND');n=safe(m.name.rstrip('/')if m.isdir()else m.name)
   if kind=='source':need(n=='uav-project'or n.startswith('uav-project/'),'SOURCE_PREFIX');n=n[len('uav-project/'): ]if n!='uav-project'else''
   if not n:need(m.isdir(),'SOURCE_ROOT_KIND');continue
   f=unicodedata.normalize('NFC',n).casefold();need(f not in fold,'DUPLICATE_TAR_PATH');fold.add(f);need(m.mode&~0o777==0,'UNSAFE_MODE')
   if m.isdir():dirs[n]=m.mode;continue
   need(m.type in(tarfile.REGTYPE,tarfile.AREGTYPE,tarfile.SYMTYPE,tarfile.LNKTYPE)and m.sparse is None,'UNSAFE_TAR_KIND');need(0<=m.size<=256*CHUNK,'MEMBER_BOUND');total+=m.size;need(total<=MAX,'TAR_EXPANDED_BOUND');row={'kind':'file','bytes':m.size,'mode':m.mode}
   if m.issym():
    need(kind=='source','SYMLINK_KIND');target=m.linkname;need(target and not target.startswith('/')and '\\'not in target and '\0'not in target,'SYMLINK_TARGET');resolved=posixpath.normpath(posixpath.join(posixpath.dirname(n),target));safe(resolved);row.update(kind='symlink',link=target,target=resolved,bytes=len(target.encode()),sha256=hashlib.sha256(target.encode()).hexdigest())
   elif m.islnk():
    need(kind=='engineering','HARDLINK_KIND');target=safe(m.linkname);need(target in rows and rows[target]['kind']=='file','HARDLINK_PRIOR_REGULAR_TARGET');row.update(kind='hardlink',target=target,sha256=rows[target]['sha256'],bytes=rows[target]['bytes']);need(m.mode==rows[target]['mode'],'HARDLINK_MODE')
   else:
    body=t.extractfile(m)
    if expected is not None:
     need(n in expected and expected[n]['kind']=='file','PREPARE_EXACT_MEMBER');row['sha256']=expected[n]['sha256'];need(row==expected[n],'PREPARE_EXACT_HEADER');used=[False]
     def opener():used[0]=True;return body
     consume(n,row,opener)
     if not used[0]:need(digest(body)==(row['sha256'],row['bytes']),'SKIPPED_SOURCE_SHA')
    elif capture is not None and m.size<=CHUNK and(capture_names is None or n in capture_names):
     raw=small(body,CHUNK);need(sum(map(len,capture.values()))+len(raw)<=8*CHUNK,'IMAGE_METADATA_BOUND');capture[n]=raw;row['sha256']=hashlib.sha256(raw).hexdigest();need(len(raw)==m.size,'TAR_MEMBER_TRUNCATED')
    else:row['sha256'],length=digest(body);need(length==m.size,'TAR_MEMBER_TRUNCATED')
    body.close()
   if expected is not None:need(n in expected and row==expected[n],'PREPARE_EXACT_MEMBER_METADATA')
   rows[n]=row
   if consume and not m.isfile():consume(n,row,lambda:None)
 # Drain gzip completely to enforce CRC/trailer; tar padding must contain only zeroes.
 while tail:=stream.read(CHUNK):need(not any(tail),'TRAILING_TAR_DATA')
 gz.close()
 for n in set(rows)|set(dirs):
  need(not any('/'.join(n.split('/')[:i])in rows for i in range(1,len(n.split('/')))),'MEMBER_THROUGH_FILE')
 for row in rows.values():
  if row['kind']=='symlink':need(row['target']in rows and rows[row['target']]['kind']=='file','SYMLINK_CONTAINED_REGULAR_TARGET')
 if expected is not None:need(set(rows)==set(expected),'PREPARE_EXACT_MEMBER_SET')
 return rows,dirs
def export_binding(public_rows,final_manifest,captured):
 changes=[]
 for n,row in public_rows.items():
  final=final_manifest.get(n);need(final is not None,'EXPORT_PUBLIC_MANIFEST_BINDING')
  if(row['sha256'],row['bytes'])==(final['sha256'],final['bytes']):continue
  need(final['kind']=='file','AUTHORING_FINAL_KIND');entry={'path':n,'exportSHA256':row['sha256'],'exportBytes':row['bytes'],'finalSHA256':final['sha256'],'finalBytes':final['bytes']}
  if n in AUTHORING_HISTORY:
   history=final_manifest.get(AUTHORING_HISTORY[n]);need(history is not None and history['kind']=='file'and(history['sha256'],history['bytes'])==(row['sha256'],row['bytes']),'AUTHORING_HISTORY_PROOF');entry.update(proof='EXACT_ORIGINAL_PRESERVED_AS_HISTORY',historyPath=AUTHORING_HISTORY[n],historySHA256=history['sha256'])
  elif n=='.gitignore':
   raw=captured.get(n);need(raw is not None and type(row['bytes'])is int and 0<=row['bytes']<=65536,'AUTHORING_IGNORE_PREFIX_BOUND');prefix=raw[:row['bytes']];need(hashlib.sha256(prefix).hexdigest()==row['sha256']and raw[row['bytes']:]==IGNORE_SUFFIX and len(IGNORE_SUFFIX)==330,'AUTHORING_IGNORE_EXACT_PREFIX_APPEND');entry.update(proof='EXACT_ORIGINAL_PREFIX_AND_DECLARED_APPEND',appendBytes=len(IGNORE_SUFFIX),appendSHA256=hashlib.sha256(IGNORE_SUFFIX).hexdigest())
  else:raise Refused('EXPORT_UNKNOWN_SOURCE_REPLACEMENT')
  changes.append(entry)
 return changes
class Bundle:
 def __init__(self,path,expected,counts=COUNTS):self.path=Path(path);self.expected=expected;self.counts=counts;self.fp=None;self.tar=None
 def __enter__(self):
  try:return self.enter()
  except BaseException:self.__exit__();raise
 def enter(self):
  need(re.fullmatch('[0-9a-f]{64}',self.expected or'')is not None,'EXTERNAL_DIGEST_REQUIRED');need(not self.path.is_symlink()and self.path.is_file(),'BUNDLE_REGULAR');self.fp=self.path.open('rb');self.initial=os.fstat(self.fp.fileno());need(1024<=self.initial.st_size<=512*CHUNK and self.initial.st_size%512==0,'OUTER_SIZE_BOUND');self.fp.seek(self.initial.st_size-1024);need(self.fp.read(1024)==b'\0'*1024,'OUTER_END_MARKERS');self.fp.seek(0);actual,n=digest(self.fp);need(actual==self.expected,'OUTER_SHA256');self.fp.seek(0);self.tar=tarfile.open(fileobj=Bounded(self.fp,512*CHUNK),mode='r:');self.outer={}
  for m in self.tar:
   need(m.type in(tarfile.REGTYPE,tarfile.AREGTYPE)and m.sparse is None and m.name.startswith('uav-project-private/'),'OUTER_MEMBER_KIND');n=safe(m.name[len('uav-project-private/'):]);need(n in NAMES and n not in self.outer,'OUTER_EXACT_NAMES');need(0<=m.size<=256*CHUNK,'OUTER_MEMBER_BOUND');self.outer[n]=m
  need(set(self.outer)==set(NAMES),'OUTER_EXACT_MEMBERS')
  while tail:=self.fp.read(CHUNK):need(not any(tail),'OUTER_TRAILING_DATA')
  sums=small(self.open('SHA256SUMS.txt'),16384).decode();checks={}
  for line in sums.splitlines():
   match=re.fullmatch(r'([a-f0-9]{64})  ([A-Za-z0-9_.-]+)',line);need(match is not None,'SUMS_LINE');h,n=match.groups();need(n in NAMES and n!='SHA256SUMS.txt'and n not in checks,'SUMS_EXACT_NAMES');checks[n]=h
  need(set(checks)==set(NAMES)-{'SHA256SUMS.txt'},'SUMS_COMPLETE')
  for n,h in checks.items():need(digest(self.open(n))[0]==h,'INNER_ARCHIVE_SHA256')
  self.checks=checks;return self
 def __exit__(self,*exc):
  if self.tar:self.tar.close()
  if self.fp:self.fp.close()
 def open(self,n):return self.tar.extractfile(self.outer[n])
 def document(self,n):return parsed(small(self.open(n)))
 def unchanged(self):
  s=os.fstat(self.fp.fileno());need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(self.initial.st_dev,self.initial.st_ino,self.initial.st_size,self.initial.st_mtime_ns,self.initial.st_ctime_ns),'BUNDLE_CHANGED_DURING_READ')
 def verify(self):
  public=self.document('PUBLIC-SOURCE-MANIFEST.json');export=self.document('export-manifest-private.json');eng=self.document('ENGINEERING-REPLAY-KIT.manifest.json');image=self.document('SITL-IMAGE.manifest.json')
  need(public.get('format')=='uav-project-public-source-manifest'and public.get('version')==1,'PUBLIC_MANIFEST_SCHEMA');pm=unique(public['files']);captured={};sm,sd=scan_tar(self.open('PUBLIC-SOURCE.tar.gz'),'source',capture=captured,capture_names={'.gitignore'});need(set(sm)==set(pm)|{'handoff/SOURCE-MANIFEST.json'},'SOURCE_EXACT_MANIFEST');need(sm['handoff/SOURCE-MANIFEST.json']['sha256']==self.checks['PUBLIC-SOURCE-MANIFEST.json'],'MANIFEST_SELF_BYTES')
  for n,r in pm.items():need(r['kind']==sm[n]['kind']and r['sha256']==sm[n]['sha256']and r['bytes']==sm[n]['bytes'],'SOURCE_FILE_SHA_KIND_SIZE')
  need(export.get('format')=='uav-project-source-export'and not export.get('secretPatternFilesHeldBack'),'CONTEXT_SCHEMA');restricted=unique(export['restricted']);anonym=unique(export['anonymized']);public_rows=unique(export['publicFiles']);authoring=export_binding(public_rows,pm,captured);need(self.counts!=COUNTS or len(authoring)==3,'EXPECTED_AUTHORING_METADATA_REPLACEMENTS');need(not(set(restricted)&set(anonym)),'CONTEXT_OVERLAY_COLLISION');context={n:r['sha256']for n,r in restricted.items()}
  for n,r in anonym.items():need(r.get('originalPrivateOverlay')is True and n in pm and pm[n]['kind']=='file'and pm[n]['sha256']==r['publicSHA256'],'OVERLAY_EXPECTED_PUBLIC_SHA');context[n]=r['originalSHA256']
  cm={};zipbytes=0
  with zipfile.ZipFile(io.BytesIO(small(self.open('PRIVATE-CONTEXT.zip'),32*CHUNK)))as z:
   need(len(z.infolist())<=1000,'ZIP_COUNT_BOUND');unique([{'path':m.filename}for m in z.infolist()]);need(set(z.namelist())==set(context),'CONTEXT_EXACT_NAMES')
   for m in z.infolist():
    mode=m.external_attr>>16;need(not m.is_dir()and stat.S_IFMT(mode)in(0,stat.S_IFREG)and mode&0o7000==0 and not(m.flag_bits&1),'ZIP_UNSAFE_KIND');need(0<=m.file_size<=128*CHUNK,'ZIP_MEMBER_BOUND');zipbytes+=m.file_size;need(zipbytes<=512*CHUNK,'ZIP_EXPANDED_BOUND');h,n=digest(z.open(m));need(h==context[m.filename]and n==m.file_size,'CONTEXT_SHA_SIZE');need(m.filename not in restricted or'bytes'not in restricted[m.filename]or n==restricted[m.filename]['bytes'],'CONTEXT_DECLARED_SIZE');cm[m.filename]={'kind':'file','bytes':n,'sha256':h,'mode':mode&0o777 or 0o600}
  need(eng.get('format')=='uav-project-engineering-replay-kit'and eng.get('archiveSHA256')==self.checks['ENGINEERING-REPLAY-KIT.tar.gz'],'ENGINEERING_SCHEMA_SHA');em=unique(eng['files']);er,ed=scan_tar(self.open('ENGINEERING-REPLAY-KIT.tar.gz'),'engineering');need(set(em)==set(er),'ENGINEERING_EXACT_MANIFEST')
  for n,r in em.items():need((r['sha256'],r['bytes'],r['mode'])==(er[n]['sha256'],er[n]['bytes'],er[n]['mode']),'ENGINEERING_SHA_SIZE_MODE')
  need((len(sm),len(cm),len(er),sum(r['kind']=='hardlink'for r in er.values()),sum(r['kind']=='symlink'for r in sm.values()),len(anonym))==self.counts,'EXPECTED_BUNDLE_COUNTS')
  im={};ir,_=scan_tar(self.open('SITL-LINUX-ARM64-IMAGE.tar.gz'),'image',capture=im)
  for n,r in ir.items():need(n in('index.json','manifest.json','oci-layout')or re.fullmatch('blobs/sha256/[a-f0-9]{64}',n),'IMAGE_MEMBER_PATH');need(r['kind']=='file','IMAGE_REGULAR_ONLY');need(not n.startswith('blobs/')or r['sha256']==n.split('/')[-1],'IMAGE_BLOB_SHA')
  need(image['archiveSHA256']==self.checks['SITL-LINUX-ARM64-IMAGE.tar.gz']and image['archiveBytes']==self.outer['SITL-LINUX-ARM64-IMAGE.tar.gz'].size,'IMAGE_ARCHIVE_IDENTITY');index=parsed(im['index.json']);root=index['manifests'][0];need(root['digest']==image['imageID'],'IMAGE_INDEX_IDENTITY');rootpath='blobs/sha256/'+root['digest'].split(':')[1];need(ir[rootpath]['bytes']==root['size'],'IMAGE_ROOT_SIZE');nested=parsed(im[rootpath]);selected=next(x for x in nested['manifests']if x.get('platform',{}).get('os')==image['os']and x.get('platform',{}).get('architecture')==image['architecture']);manifest=parsed(im['blobs/sha256/'+selected['digest'].split(':')[1]]);config='blobs/sha256/'+manifest['config']['digest'].split(':')[1];cfg=parsed(im[config]);docker=parsed(im['manifest.json']);need(len(docker)==1 and docker[0]['Config']==config and cfg['os']==image['os']and cfg['architecture']==image['architecture'],'IMAGE_CONFIG_IDENTITY')
  need(docker[0]['Layers']==['blobs/sha256/'+x['digest'].split(':')[1]for x in manifest['layers']],'IMAGE_LAYER_IDENTITY')
  for d in[manifest['config'],*manifest['layers']]:need(ir['blobs/sha256/'+d['digest'].split(':')[1]]['bytes']==d['size'],'IMAGE_DESCRIPTOR_SIZE')
  # Derived plan replaces only the nine approved anonymized source entries.
  final=dict(sm)
  for n,r in cm.items():need(n not in final or n in anonym or(final[n]['kind']=='file'and final[n]['sha256']==r['sha256']),'CONTEXT_UNAPPROVED_OVERWRITE');final[n]=r
  for n,r in er.items():need(n not in final or(final[n]['kind']=='file'and final[n]['sha256']==r['sha256']),'ENGINEERING_UNAPPROVED_OVERWRITE');final[n]=r
  need(not any(n==ART or n.startswith(ART+'/')for n in final),'RESERVED_ARTIFACT_NAMESPACE')
  for n in KEEP:final[ART+'/'+n]={'kind':'file','bytes':self.outer[n].size,'sha256':self.checks[n],'mode':0o600}
  unique([{'path':n}for n in final]);need(all('/'.join(n.split('/')[:i])not in final for n in final for i in range(1,len(n.split('/')))),'DERIVED_PATH_THROUGH_FILE');need(not(set(final)&(set(sd)|set(ed))),'DERIVED_FILE_DIRECTORY_COLLISION')
  directories=set(sd)|set(ed)|{ART}
  for n in final:
   for p in Path(n).parents:
    if str(p)!='.':directories.add(p.as_posix())
  allocation=sum(((r['bytes']+4095)//4096)*4096 if r['kind']=='file'else 4096 for r in final.values())+len(directories)*8192+16*CHUNK
  self.plan={'authoring':authoring,'source':sm,'sourceDirs':sd,'context':cm,'engineering':er,'engineeringDirs':ed,'overlays':set(anonym),'final':final,'allocation':allocation}
  self.unchanged();return{'status':'VERIFIED_PRIVATE_BUNDLE_INTEGRITY_ONLY','sourceEntries':len(sm),'publicAuthoringChanges':authoring,'contextEntries':len(cm),'engineeringEntries':len(er),'engineeringHardlinks':self.counts[3],'sourceSymlinks':self.counts[4],'originalOverlays':len(anonym),'imageIdentity':'VERIFIED_ARCHIVE_OCI_INDEX_CHAIN_AND_CONFIG_NOT_LOADED','positiveWorkspaceAllocationBytes':allocation,'floorPlusReserveBytes':FLOOR,'betaOrFlightAcceptance':False}
 def prepare(self,destination):
  dest=Path(destination).absolute();new_destination(dest);need(self.plan['allocation']<=768*CHUNK,'WORKSPACE_ALLOCATION_CAP');need(shutil.disk_usage(dest.parent).free>=FLOOR+self.plan['allocation'],'DISK_ADMISSION');self.unchanged();dest.mkdir(mode=0o700);start={'format':'uav-private-preparation-start','status':'STARTED_NOT_ADMISSION','expectedBundleSHA256':self.expected};write_file(dest/ART/'PREPARATION-START.json',json_bytes(start),0o600)
  def guard(n=8192):need(shutil.disk_usage(dest).free>=FLOOR+n+65536,'DISK_RUNTIME_FLOOR')
  def put(n,r,opener):
   guard();out=dest/n;parents(out.parent,dest,guard)
   if out.exists()or out.is_symlink():need(out.is_file()and not out.is_symlink()and hash_path(out)[0]==r['sha256'],'DUPLICATE_EXISTING_BYTES');os.chmod(out,r['mode']);return
   if r['kind']=='symlink':os.symlink(r['link'],out)
   elif r['kind']=='hardlink':need((dest/r['target']).is_file()and not(dest/r['target']).is_symlink(),'HARDLINK_DESTINATION');os.link(dest/r['target'],out)
   else:
    with opener()as f:write_file(out,f,r['mode'],r['sha256'],r['bytes'],guard)
  scan_tar(self.open('PUBLIC-SOURCE.tar.gz'),'source',lambda n,r,f:put(n,r,f)if n not in self.plan['overlays']else None,expected=self.plan['source'])
  with zipfile.ZipFile(io.BytesIO(small(self.open('PRIVATE-CONTEXT.zip'),32*CHUNK)))as z:
   for n,r in self.plan['context'].items():put(n,r,lambda n=n:z.open(n))
  scan_tar(self.open('ENGINEERING-REPLAY-KIT.tar.gz'),'engineering',put,expected=self.plan['engineering'])
  for n in KEEP:put(ART+'/'+n,self.plan['final'][ART+'/'+n],lambda n=n:self.open(n))
  for n,mode in{**self.plan['sourceDirs'],**self.plan['engineeringDirs']}.items():
   p=dest/n;parents(p,dest,guard);os.chmod(p,mode)
  found=set()
  for base,dirs,files in os.walk(dest,followlinks=False):
   need(not any((Path(base)/n).is_symlink()for n in dirs),'DERIVED_DIRECTORY_SYMLINK')
   for name in files:
    p=Path(base)/name;n=p.relative_to(dest).as_posix()
    if n==ART+'/PREPARATION-START.json':continue
    need(n in self.plan['final'],'DERIVED_EXTRA_FILE');r=self.plan['final'][n];found.add(n)
    if r['kind']=='symlink':need(p.is_symlink()and os.readlink(p)==r['link'],'DERIVED_SYMLINK')
    else:
     need(not p.is_symlink()and p.is_file()and hash_path(p)==(r['sha256'],r['bytes'])and stat.S_IMODE(p.stat().st_mode)==r['mode'],'DERIVED_FILE_SHA_MODE')
     if r['kind']=='hardlink':need(p.stat().st_ino==(dest/r['target']).stat().st_ino and p.stat().st_dev==(dest/r['target']).stat().st_dev,'DERIVED_HARDLINK')
  need(found==set(self.plan['final']),'DERIVED_MISSING_FILE');self.unchanged();need(shutil.disk_usage(dest).free>=FLOOR,'FINAL_DISK_FLOOR');result={'status':'PRIVATE_DERIVED_NOT_PUBLIC_SNAPSHOT','verifiedFinalFiles':len(found),'publicAuthoringChanges':self.plan['authoring'],'originalOverlays':len(self.plan['overlays']),'engineeringHardlinksPreserved':self.counts[3],'gitRemotePresent':False,'operationalAdmission':False,'receiptSelfExcluded':True,'expectedBundleSHA256':self.expected};write_file(dest/ART/'PREPARATION-RECEIPT.json',json_bytes(result),0o600);return result

def parents(path,root,guard=lambda n:None):
 if path==root:return
 need(path.is_relative_to(root),'DESTINATION_ESCAPE');parents(path.parent,root,guard)
 if path.exists():need(path.is_dir()and not path.is_symlink(),'DESTINATION_PARENT_KIND')
 else:guard(8192);path.mkdir(mode=0o700)
def hash_path(p):
 with p.open('rb')as f:return digest(f)
def new_destination(dest):
 need(not os.path.lexists(dest)and dest.parent.is_dir(),'NEW_DESTINATION_REQUIRED')
 for p in[dest.parent,*dest.parent.parents]:need(not p.is_symlink()and not(p/'.git').exists(),'NON_GIT_NO_SYMLINK_DESTINATION')
def write_file(path,data,mode,expected=None,size=None,guard=lambda n:None):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600),'wb')as out:
  h=hashlib.sha256();n=0
  if isinstance(data,bytes):data=__import__('io').BytesIO(data)
  while b:=data.read(CHUNK):guard(len(b)+4096);out.write(b);h.update(b);n+=len(b);need(n<=MAX,'WRITE_BOUND')
  need(expected is None or(h.hexdigest()==expected and n==size),'WRITE_ORIGINAL_SHA_SIZE');os.fchmod(out.fileno(),mode);out.flush();os.fsync(out.fileno())
def json_bytes(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('verify','prepare'));p.add_argument('bundle');s=p.add_mutually_exclusive_group(required=True);s.add_argument('--expected-sha');s.add_argument('--sha-file');p.add_argument('--destination');p.add_argument('--report');a=p.parse_args();expected=a.expected_sha;report_allowed=False
 try:
  if a.sha_file:
   rows=Path(a.sha_file).read_text().splitlines();need(len(rows)==1,'EXTERNAL_SHA_FILE_ONE_LINE');m=re.fullmatch(r'([a-f0-9]{64}) [ *](.+)',rows[0]);need(m is not None and m[2]==Path(a.bundle).name,'EXTERNAL_SHA_FILE_NAME');expected=m[1]
  need((a.action=='prepare')==bool(a.destination),'DESTINATION_ACTION_SCOPE')
  if a.report:new_destination(Path(a.report).absolute());report_allowed=True
  with Bundle(a.bundle,expected)as bundle:
   result=bundle.verify()
   if a.action=='prepare':result=bundle.prepare(a.destination)
  if a.report:write_file(a.report,json_bytes(result),0o600)
  print(json.dumps(result,sort_keys=True));return 0
 except Exception as e:
  result={'status':'REFUSED_NOT_ADMISSION','reason':str(e)if isinstance(e,Refused)else type(e).__name__,'privateFilenamesPrinted':False,'partialPreparationMustNotBeUsed':a.action=='prepare'}
  if a.report and report_allowed:
   try:write_file(a.report,json_bytes(result),0o600)
   except OSError:pass
  print(json.dumps(result,sort_keys=True));return 2
if __name__=='__main__':raise SystemExit(main())
