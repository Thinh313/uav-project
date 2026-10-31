"""Independent bounded receiver. Never extracts untrusted ZIP or restores control authority."""
from pathlib import Path
import json,zipfile,io,hashlib,base64,re,subprocess,sys,stat,os,datetime,math
R=Path(__file__).resolve().parents[2];MAX=24*2**20
sha=lambda b:hashlib.sha256(b).hexdigest()
def strict(raw):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('DUPLICATE_JSON_KEY')
   d[k]=v
  return d
 def bad(v):raise ValueError('NONFINITE')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def unzip(raw,max_bytes,max_members):
 if len(raw)>max_bytes:raise ValueError('ZIP_INPUT_BOUND')
 out={};total=0
 with zipfile.ZipFile(io.BytesIO(raw))as z:
  if len(z.infolist())>max_members:raise ValueError('MEMBER_BOUND')
  for item in z.infolist():
   n=item.filename
   if not n or n in out or n.startswith('/')or '\\'in n or any(x in ['','..','.']for x in n.split('/'))or item.is_dir()or item.flag_bits&1 or stat.S_ISLNK(item.external_attr>>16):raise ValueError('ZIP_PATH_DUPLICATE_TYPE')
   total+=item.file_size
   if item.file_size>max_bytes or total>max_bytes or item.compress_size and item.file_size/item.compress_size>300:raise ValueError('ZIP_EXPANDED_BOUND')
   with z.open(item)as f:b=f.read(max_bytes+1)
   if len(b)!=item.file_size:raise ValueError('ZIP_SIZE')
   out[n]=b
 return out

def trace(raw,session,allowed):
 if not raw or len(raw)>2**20 or not raw.endswith(b'\n'):raise ValueError('TRACE_BOUND_TORN')
 previous='';last=-1;lastframe={};frames={};phase={};source=None;count=0;references=[]
 for count,line in enumerate(raw.splitlines(),1):
  v=strict(line)
  if set(v)!={'n','elapsedMs','previous','payloadBase64','sha256'}or type(v['n'])is not int or v['n']!=count or count>512 or type(v['elapsedMs'])is not int or v['elapsedMs']<0 or v['elapsedMs']<last or v['previous']!=previous:raise ValueError('TRACE_CHAIN_ORDER_CLOCK')
  body={k:v[k]for k in ['n','elapsedMs','previous','payloadBase64']}
  if sha(json.dumps(body,separators=(',',':'),ensure_ascii=False).encode())!=v['sha256']:raise ValueError('TRACE_SHA')
  payload=base64.b64decode(v['payloadBase64'],validate=True)
  if not 0<len(payload)<=16384:raise ValueError('TRACE_PAYLOAD_BOUND')
  p=strict(payload)
  if set(p)!={'session','kind','data'}or p['session']!=session:raise ValueError('TRACE_SESSION')
  k=p['kind'];d=p['data'];s=d.get('snapshot',d);i=s.get('input');video=s.get('video')
  if count==1:
   if k!='SESSION'or d['source']!='SYNTHETIC_FIXTURE'or d['operational']is not False or d['authorityRestorable']is not False:raise ValueError('TRACE_SOURCE_SCOPE')
   source=d.get('sourceId')
   if source not in allowed:raise ValueError('UNKNOWN_SOURCE_ID')
  if i and(i['operational']is not False or i['physicalMappingVerified']is not False):raise ValueError('PHYSICAL_INPUT_CLAIM')
  if video and(video['actualImages']!=0 or video['source']!='SYNTHETIC_FIXTURE'or video['cameraAgeMs']is not None or video['cameraToDisplayLatencyMs']is not None or video['displayScanoutMeasured']is not False):raise ValueError('FALSE_CAMERA_PROVENANCE')
  if k=='VIDEO_PREPARE':phase[d['generation']]='PREPARING';frames[d['generation']]=0
  if k=='VIDEO_STARTED':
   g=d['generation']
   if phase.get(g)!='PREPARING'or not s['foreground']or not s['focused']:raise ValueError('VIDEO_START')
   phase[g]='PLAYING'
  if k=='FRAME_CALLBACK':
   g=d['generation'];pts=d['mediaTimeNs']
   if phase.get(g)!='PLAYING'or not s['foreground']or not s['focused']or pts<0 or pts<=lastframe.get(g,-1):raise ValueError('FRAME_GENERATION_TIMELINE')
   lastframe[g]=pts;frames[g]+=1
   if video['generation']!=g or video['frameCallbacks']!=frames[g]or video['producerTimestampNs']!=pts:raise ValueError('FRAME_COUNT')
  if k=='VIDEO_ENDED':
   g=d['generation']
   if phase.get(g)!='PLAYING'or frames[g]<1 or video['state']!='ENDED_WITH_CALLBACKS':raise ValueError('VIDEO_END')
   phase[g]='ENDED'
  if k in ['VIDEO_STOP','VIDEO_STALE','VIDEO_PREPARE_TIMEOUT','ACTIVITY_PAUSED','FOCUS_LOST']:
   for g in phase:phase[g]='STOPPED'
  if k in ['ACTIVITY_PAUSED','FOCUS_LOST','ACTIVITY_RESUMED_NO_RESTORE','FOCUS_GAINED_NO_RESTORE']and(i['mockOwned']or s['watchKeys']or video['state']in ['WAITING_RENDER_CALLBACK','RENDER_CALLBACK_OBSERVED']):raise ValueError('AUTHORITY_RESTORE_OR_LIFECYCLE')
  if k=='WORKSPACE_REVIEW_LINK':references.append(d['reference'])
  if k=='ANDROID_JOYSTICK_RAW_UNMAPPED':
   if d['physicalMappingVerified']is not False or not isinstance(d['axes'],list)or len(d['axes'])>16:raise ValueError('JOYSTICK_MAPPING_BOUND')
   for a in d['axes']:
    if type(a['axis'])is not int or type(a['raw'])not in[int,float]or not math.isfinite(a['raw']):raise ValueError('JOYSTICK_AXIS')
  if k=='ANDROID_KEY_UNATTESTED':
   delta=d['callbackUptimeMs']-d['eventUptimeMs']
   if d['clockDomain']!='ANDROID_UPTIME_MILLIS'or d['dispatchDelayMs']!=(delta if 0<=delta<=2000 else None)or d['noControlMapping']is not True:raise ValueError('KEY_CLOCK_OR_MAPPING')
  previous=v['sha256'];last=v['elapsedMs']
 return {'records':count,'head':previous,'sourceId':source,'extent':'COMMITTED_PREFIX','references':references,'actualImages':0,'authorityRestorable':False}

def workspace(raw,context):
 files=unzip(raw,8*2**20,132)
 if 'HEAD'not in files or 'MANIFEST'not in files:raise ValueError('WORKSPACE_HEAD')
 rows=files.pop('MANIFEST').decode('ascii').splitlines()
 if len(rows)!=len(files)+3 or rows[:3]!=['AERISARCHIVE83',context['workspaceHead'],'authority=false']:raise ValueError('WORKSPACE_MANIFEST')
 declared={}
 for line in rows[3:]:
  name,size,h=line.split(' ')
  if name in declared or name not in files or int(size)!=len(files[name])or sha(files[name])!=h:raise ValueError('WORKSPACE_MANIFEST_MEMBER')
  declared[name]=h
 if set(declared)!=set(files):raise ValueError('WORKSPACE_MANIFEST_INVENTORY')
 for n in files:
  if not re.fullmatch(r'(?:SITL-)?(?:HEAD|[0-9]{12}-[a-f0-9]{64}\.bin)',n):raise ValueError('WORKSPACE_ENTRY')
 bodies=[]
 for prefix,expected in [('',context['workspaceHead']),('SITL-',context['sitlHead'])]:
  headname=prefix+'HEAD'
  if expected=='ROOT':
   if any(n.startswith(prefix)for n in files)and prefix=='SITL-':raise ValueError('UNDECLARED_SITL')
   continue
  if files.get(headname,b'').decode().strip()!=expected:raise ValueError('WORKSPACE_HEAD_MISMATCH')
  rows={}
  for n,b in files.items():
   if not n.startswith(prefix)or prefix==''and n.startswith('SITL-')or not n.endswith('.bin'):continue
   h=b.split(b'\n',6)
   if len(h)!=7 or h[0]!=b'AERISWORKSPACE33' or h[5]!=b'1' or not re.fullmatch(rb'[1-9][0-9]{0,11}',h[1])or n[len(prefix):len(prefix)+12]!=('%012d'%int(h[1]))or not re.fullmatch(rb'ROOT|[a-f0-9]{64}',h[2]) or sha(b)!=n[len(prefix)+13:-4]or int(h[4])!=len(h[6])or sha(h[6])!=h[3].decode():raise ValueError('WORKSPACE_RECORD_SHA_FORMAT')
   rows[sha(b)]={'previous':h[2].decode(),'revision':int(h[1]),'body':h[6]}
  at=expected;seen=set();last_revision=None
  while at!='ROOT':
   if at not in rows or at in seen:raise ValueError('WORKSPACE_CHAIN_MISSING_CYCLE')
   r=rows[at]
   if last_revision is not None and r['revision']>=last_revision:raise ValueError('WORKSPACE_REVISION')
   seen.add(at);last_revision=r['revision'];at=r['previous']
  # Retained orphans may exist, but every .bin above is independently hash checked.
  bodies.append({'kind':'workspace'if prefix==''else'sitl','body':rows[expected]['body'].decode('utf-8')})
 p=subprocess.run(['node','native/native91/receiver_workflow91.mjs'],input=json.dumps(bodies),text=True,cwd=R,capture_output=True,timeout=30)
 if p.returncode:raise ValueError('WORKSPACE_SEMANTIC_REPLAY:'+p.stderr[-500:])
 return strict(p.stdout)

def verify(raw,receiver,nonce,allowed):
 files=unzip(raw,MAX,26)
 if 'manifest.json'not in files or len(files['manifest.json'])>65536:raise ValueError('MANIFEST_MISSING_BOUND')
 m=strict(files['manifest.json'])
 if set(m)!={'format','version','sourceAuthenticated','authorityRestorable','actualImages','context','files'}or m['format']!='aeris-diagnostic91'or m['version']!=1 or m['sourceAuthenticated']is not False or m['authorityRestorable']is not False or m['actualImages']!=0:raise ValueError('MANIFEST_SCOPE')
 c=m['context']
 if c['receiver']!=receiver or c['nonce']!=nonce:raise ValueError('RECEIVER_NONCE')
 if c['authorityRestorable']is not False or c['sourceId']not in allowed or c['sourceMode']not in ['mock','sitl']:raise ValueError('CONTEXT_SCOPE')
 entries=m['files'];names=[e['name']for e in entries]
 if len(names)!=len(set(names))or set(files)!={'manifest.json',*names}or 'workspace.zip'not in names:raise ValueError('INVENTORY_MISMATCH')
 traces={}
 for e in entries:
  name=e['name'];b=files[name]
  if type(e['bytes'])is not int or e['bytes']!=len(b)or e['sha256']!=sha(b):raise ValueError('MEMBER_SHA_SIZE')
  if name=='workspace.zip':continue
  if not re.fullmatch(r'diagnostics/[a-f0-9-]{36}\.jsonl',name)or e['extent']!='COMMITTED_PREFIX':raise ValueError('TRACE_NAME_EXTENT')
  v=trace(b,Path(name).stem,allowed)
  if e['head']!=v['head']or e['records']!=v['records']:raise ValueError('PREFIX_HEAD_COUNT')
  traces[name]=v
 if not traces:raise ValueError('NO_TRACE')
 semantic=workspace(files['workspace.zip'],c);resolved=0;historical=0
 for t in traces.values():
  for ref in t['references']:
   expected=c['sitlHead']if ref.get('phase')=='CLOSED_SITL'else c['workspaceHead']
   if ref.get('workspace')!=c['workspace']or ref.get('head')!=expected:historical+=1;continue
   row=next((x for x in semantic if x['kind']==('sitl-review'if ref.get('phase')=='CLOSED_SITL'else'workspace')),None)
   if row is None or ref.get('missionSha256')!=row.get('missionSha256')or ref.get('phase')=='CLOSED_SITL'and ref.get('reviewAccepted')!=row.get('accepted'):raise ValueError('REVIEW_LINK_MISSION_MISMATCH')
   resolved+=1
 return {'status':'PASS_LOCAL_INTEGRITY_AND_SEMANTICS','packageSha256':sha(raw),'manifestSha256':sha(files['manifest.json']),'receiver':receiver,'nonce':nonce,'context':c,'traces':traces,'workspaceSemantic':semantic,'currentHeadReferencesVerified':resolved,'historicalReferencesOutsideCapturedHead':historical,'sourceAuthenticated':False,'authorityRestored':False,'actualImages':0,'prefixIsNotCompleteSession':True}
def receive(path,receiver,nonce,receipt,allowed):
 if path.is_symlink()or not path.is_file()or path.stat().st_size>MAX or receipt.exists()or receipt.is_symlink()or receipt.parent.is_symlink():raise ValueError('INPUT_OR_RECEIPT_BOUND')
 result=verify(path.read_bytes(),receiver,nonce,allowed);marker=receipt.parent/('.receive91-'+sha((receiver+'\0'+nonce).encode())+'.lock');fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:os.write(fd,json.dumps({'packageSha256':result['packageSha256'],'receipt':receipt.name,'state':'RECEIPT_COMMIT_INTENT'}).encode());os.fsync(fd)
 finally:os.close(fd)
 with receipt.open('x')as f:json.dump(result,f,indent=2);f.flush();os.fsync(f.fileno())
 fd=os.open(receipt.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return result
if __name__=='__main__':
 result=receive(Path(sys.argv[1]),sys.argv[2],sys.argv[3],Path(sys.argv[4]),set(sys.argv[5:]));print(json.dumps({'status':result['status'],'traces':len(result['traces']),'sha256':result['packageSha256']}))
