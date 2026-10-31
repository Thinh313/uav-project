"""Exact authoritative Node quota admission; Python memory remains campaign authority."""
from pathlib import Path
import importlib.util,sys
_clock_path=Path(__file__).resolve().parents[2]/'pilot/beta06g17/clock_basis.py'
if 'aeris_g17_clock' in sys.modules:
 host_clock=sys.modules['aeris_g17_clock']
 if Path(host_clock.__file__).resolve()!=_clock_path:raise RuntimeError('EXACT_G17_CLOCK_MODULE_IDENTITY_REQUIRED')
else:
 _clock_spec=importlib.util.spec_from_file_location('aeris_g17_clock',_clock_path);host_clock=importlib.util.module_from_spec(_clock_spec);sys.modules[_clock_spec.name]=host_clock;_clock_spec.loader.exec_module(host_clock)
import json,subprocess,hashlib,fcntl,os
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation17';P=Path(__file__).with_name('quota-policy.json')
def load_policy():return json.loads(P.read_bytes())
def admit(phase,*,remaining_ap,remaining_hosts,closed_runs,claim_id,cancel_event=None):
 assert phase in ['before-host','before-connect','guard','runtime','closure']and isinstance(claim_id,str)and 1<=len(claim_id)<=128,'EXPLICIT_ADMISSION_CONTEXT'
 value={'phase':phase,'remaining_ap':remaining_ap,'remaining_hosts':remaining_hosts,'closed_runs':closed_runs,'verifyHashes':phase in ['before-host','closure'],'closure':phase=='closure'}
 deadline=host_clock.now_s()+15
 proc=subprocess.Popen(['node',str(Path(__file__).with_name('quota.mjs')),json.dumps(value)],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  while True:
   if cancel_event is not None and cancel_event.is_set():raise RuntimeError('QUOTA_READ_CANCELLED_ON_OWNED_CLOSE')
   if host_clock.now_s()>deadline:raise RuntimeError('QUOTA_READ_DEADLINE')
   try:out,err=proc.communicate(timeout=.25);break
   except subprocess.TimeoutExpired:pass
  assert len(out.encode())<=256*1024 and len(err.encode())<=64*1024,'QUOTA_RESPONSE_BOUND'
  if proc.returncode:raise RuntimeError('SHARED_QUOTA_REFUSED:'+err[-2048:])
  result=json.loads(out);assert result['status']=='ADMITTED';result['claimId']=claim_id;return result
 finally:
  if proc.poll()is None:
   proc.terminate()
   try:proc.communicate(timeout=2)
   except subprocess.TimeoutExpired:proc.kill();proc.communicate(timeout=1)
def _regular_fd(p,flags,mode=0o600):
 current=p.parent
 while current!=R:
  assert current.is_relative_to(R)and current.is_dir()and not current.is_symlink(),'REGULAR_QUOTA_ANCESTOR';current=current.parent
 fd=os.open(p,flags|os.O_NOFOLLOW,mode);assert __import__('stat').S_ISREG(os.fstat(fd).st_mode),'REGULAR_QUOTA_FILE';return fd
def reserve_write(*,category,entries,bytes,claim_id,closure=False):
 host_clock.now_ns() # Unsupported provider cannot reach a ledger writer.
 p=load_policy();assert category in ['native','screenshots','hostOther']and type(entries)is int and entries>=0 and type(bytes)is int and bytes>=0 and isinstance(claim_id,str)and 0<len(claim_id)<=160 and type(closure)is bool,'EXACT_WRITE_RESERVATION'
 assert not closure or category!='screenshots'and claim_id.startswith('closure:'),'EXACT_CLOSURE_CLAIM_KIND'
 lock=E/'quota-native-ledger.lock';ledger=E/'quota-native-ledger.jsonl';E.mkdir(exist_ok=True);lfd=_regular_fd(lock,os.O_RDWR|os.O_CREAT)
 try:
  fcntl.flock(lfd,fcntl.LOCK_EX);fd=_regular_fd(ledger,os.O_RDWR|os.O_CREAT);raw=os.read(fd,p['categories']['native']['ledgerBytes']+1)
  try:
   assert len(raw)<=p['categories']['native']['ledgerBytes']and(not raw or raw.endswith(b'\n')),'BOUNDED_COMPLETE_NATIVE_LEDGER';rows=[json.loads(x)for x in raw.splitlines()];assert len(rows)<p['categories']['native']['ledgerRows'],'LEDGER_ROW_QUOTA'
   used={k:{'entries':0,'bytes':0,'normalEntries':0,'normalBytes':0}for k in ['native','screenshots','hostOther']};used['native']['entries']=2;used['native']['normalEntries']=2;seen=set();previous='';policy_sha=hashlib.sha256(P.read_bytes()).hexdigest()
   rows=_validated_rows(raw,p)
   for row in rows:
    previous=row['hash'];seen.add(row['claimId']);v=used[row['category']];v['entries']+=row['entries'];v['bytes']+=row['bytes']
    if not row['closure']:v['normalEntries']+=row['entries'];v['normalBytes']+=row['bytes']
   assert claim_id not in seen,'UNIQUE_WRITE_CLAIM'
   if category=='screenshots':
    kind=claim_id.split(':',1)[0].removeprefix('png-');assert kind in ['dispatch','prepare','direct'],'PNG_SUBCOUNT';assert sum(x['category']=='screenshots'and x['claimId'].startswith('png-'+kind+':')for x in rows)<p['categories']['screenshots'][kind],'PNG_SUBCOUNT_QUOTA';assert bytes<=p['categories']['screenshots']['perFileBytes'],'UNCHANGED_PNG5MIB'
   body={'claimId':claim_id,'category':category,'entries':entries,'bytes':bytes,'closure':closure,'policySha256':policy_sha,'seq':len(rows)+1,'previous':previous};row={**body,'hash':hashlib.sha256(json.dumps(body,separators=(',',':'),sort_keys=True).encode()).hexdigest()};line=json.dumps(row,separators=(',',':')).encode()+b'\n';v=used[category];v['entries']+=entries;v['bytes']+=bytes
   if not closure:v['normalEntries']+=entries;v['normalBytes']+=bytes
   used['native']['bytes']+=len(raw)+len(line);used['native']['normalBytes']+=sum(len(rawline)+1 for rawline,oldrow in zip(raw.splitlines(),rows)if not oldrow['closure'])+(len(line)if not closure else 0)
   if not closure and category=='native':assert used['native']['normalEntries']<=p['categories']['native']['normalFiles']+2,'NATIVE_NORMAL_FILE_DIRECTORY_BOUND'
   for k,v in used.items():
    cap=p['categories'][k];assert v['entries']<=cap['entries']and v['bytes']<=cap['bytes']and v['normalEntries']<=cap['entries']-cap.get('closureEntries',0)and v['normalBytes']<=cap['bytes']-cap.get('closureBytes',0),'CATEGORY_WRITE_QUOTA:'+k
   assert len(raw)+len(line)<=p['categories']['native']['ledgerBytes'],'LEDGER_BYTE_QUOTA';os.lseek(fd,0,os.SEEK_END);n=os.write(fd,line);assert n==len(line),'QUOTA_LEDGER_SHORT_WRITE';os.fsync(fd);return row
  finally:os.close(fd)
 finally:os.close(lfd)

def _validated_rows(raw,p):
 assert len(raw)<=p['categories']['native']['ledgerBytes']and(not raw or raw.endswith(b'\n')),'BOUNDED_COMPLETE_NATIVE_LEDGER'
 rows=[json.loads(x)for x in raw.splitlines()];assert len(rows)<=p['categories']['native']['ledgerRows'],'LEDGER_ROW_QUOTA';seen=set();previous='';policy_sha=hashlib.sha256(P.read_bytes()).hexdigest()
 for i,row in enumerate(rows):
  assert set(row)=={'claimId','category','entries','bytes','closure','policySha256','seq','previous','hash'}and row['category']in ['native','screenshots','hostOther']and type(row['entries'])is int and row['entries']>=0 and type(row['bytes'])is int and row['bytes']>=0 and type(row['closure'])is bool and isinstance(row['claimId'],str)and 0<len(row['claimId'])<=160 and row['claimId']not in seen and row['policySha256']==policy_sha and type(row['seq'])is int and row['seq']==i+1 and row['previous']==previous,'EXACT_LEDGER_ROW'
  assert not row['closure']or row['category']!='screenshots'and row['claimId'].startswith('closure:'),'EXACT_CLOSURE_CLAIM_KIND'
  if row['category']=='screenshots':
   kind=row['claimId'].split(':',1)[0].removeprefix('png-');assert kind in p['futureRecipe']['pngSubtypes']and row['entries']==1 and row['bytes']<=p['categories']['screenshots']['perFileBytes'],'EXACT_PNG_LEDGER_CLAIM'
  body={k:v for k,v in row.items()if k!='hash'};assert hashlib.sha256(json.dumps(body,separators=(',',':'),sort_keys=True).encode()).hexdigest()==row['hash'],'LEDGER_HASH_CHAIN';previous=row['hash'];seen.add(row['claimId']);
 return rows

def check_native_future(remaining_ap,remaining_hosts):
 assert type(remaining_ap)is int and 0<=remaining_ap<=4 and type(remaining_hosts)is int and 0<=remaining_hosts<=2,'TRUSTED_FINITE_COUNTERS_REQUIRED'
 p=load_policy();ledger=E/'quota-native-ledger.jsonl';lock=E/'quota-native-ledger.lock'
 if ledger.exists():
  assert lock.exists(),'NATIVE_LEDGER_LOCK_REQUIRED';lfd=_regular_fd(lock,os.O_RDONLY)
  try:
   fcntl.flock(lfd,fcntl.LOCK_SH);fd=_regular_fd(ledger,os.O_RDONLY)
   try:rows=_validated_rows(os.read(fd,p['categories']['native']['ledgerBytes']+1),p)
   finally:os.close(fd)
  finally:os.close(lfd)
 else:
  assert not ledger.is_symlink()and not lock.is_symlink(),'REGULAR_QUOTA_FILE';rows=[]
 normal_files=sum(x['entries']for x in rows if x['category']=='native'and not x['closure']);coeff=p['futureRecipe']['nativeFiles'];future_files=coeff[0]*remaining_ap+coeff[1]*remaining_hosts+coeff[2];assert normal_files+future_files<=p['categories']['native']['normalFiles'],'NATIVE_FUTURE512FILE_HEADROOM'
 result={'normalFiles':{'used':normal_files,'future':future_files,'cap':p['categories']['native']['normalFiles']}}
 for kind,coeff in p['futureRecipe']['pngSubtypes'].items():
  used=sum(x['category']=='screenshots'and x['claimId'].startswith('png-'+kind+':')for x in rows);future=coeff[0]*remaining_ap+coeff[1]*remaining_hosts+coeff[2];assert used+future<=p['categories']['screenshots'][kind],'PNG_FUTURE_SUBTYPE_HEADROOM:'+kind;result[kind]={'used':used,'future':future,'cap':p['categories']['screenshots'][kind]}
 return result

check_png_future=check_native_future
