"""Bounded concrete Android public bridge transport. No install/clear/private write API."""
from pathlib import Path
import contextlib,json,os,re,selectors,subprocess,time
from .candidate import put
from pilot.betaintegrated01.runtime.ap_stage import canonical
class AndroidDevice:
 def __init__(self,adb,serial,evidence,*,now=time.monotonic_ns):
  self.adb=str(Path(adb).resolve());self.serial=serial;self.root=Path(evidence);self.now=now;self.sequence=0;self.root.mkdir(parents=True,exist_ok=True)
  if not re.fullmatch('emulator-[0-9]+',serial):raise ValueError('EXPLICIT_OWNED_EMULATOR_ONLY')
 def command(self,args,*,deadline_ns,maximum_bytes=131072):
  self.sequence+=1;start=self.now();remaining=(deadline_ns-start)/1e9
  if remaining<=0:raise TimeoutError('ANDROID_COMMAND_DEADLINE')
  argv=[self.adb,'-s',self.serial,*args]
  try:p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=remaining)
  except subprocess.TimeoutExpired as e:
   value={'argv':argv,'startedHostNs':start,'endedHostNs':self.now(),'timeout':True,'stdoutHex':(e.stdout or b'')[:maximum_bytes].hex(),'stderrHex':(e.stderr or b'')[:maximum_bytes].hex()};put(self.root/('command-%05d.json'%self.sequence),canonical(value)+b'\n');raise
  value={'argv':argv,'startedHostNs':start,'endedHostNs':self.now(),'exit':p.returncode,'stdoutHex':p.stdout[:maximum_bytes].hex(),'stderrHex':p.stderr[:maximum_bytes].hex(),'truncated':len(p.stdout)>maximum_bytes or len(p.stderr)>maximum_bytes};put(self.root/('command-%05d.json'%self.sequence),canonical(value)+b'\n')
  if p.returncode or value['truncated']:raise RuntimeError('ANDROID_COMMAND_FAILED_OR_BOUND:'+str(self.sequence))
  return p.stdout
 def intent(self,component,extras,*,deadline_ns):
  if component!='vn.rtr.aeris.mission/.CockpitActivity' or set(extras)!={'missionAction','missionRequestBase64'} or extras['missionAction'] not in ('STATUS','BOOTSTRAP') or not re.fullmatch(r'[A-Za-z0-9_=\-]{1,43692}',extras['missionRequestBase64']):raise ValueError('PUBLIC_INTENT_ALLOWLIST')
  return self.command(['shell','am','start','-n',component,'--es','missionAction',extras['missionAction'],'--es','missionRequestBase64',extras['missionRequestBase64']],deadline_ns=deadline_ns)
 def pid(self,package,*,deadline_ns):
  if package!='vn.rtr.aeris.mission':raise ValueError('PACKAGE_ALLOWLIST')
  raw=self.command(['shell','pidof',package],deadline_ns=deadline_ns).decode().strip()
  if re.fullmatch('[1-9][0-9]*',raw)is None:raise ValueError('EXACT_ACTUAL_PROCESS_REQUIRED')
  return int(raw)
 def read_private(self,package,path,*,maximum_bytes,deadline_ns):
  if package!='vn.rtr.aeris.mission' or path not in ('files/runtime/response.json','files/runtime/current.json') or maximum_bytes!=131072:raise ValueError('COHERENT_READ_ONLY_ALLOWLIST')
  return self.command(['shell','run-as',package,'cat',path],deadline_ns=deadline_ns,maximum_bytes=maximum_bytes)
 @contextlib.contextmanager
 def live_log(self,tag,*,deadline_ns):
  if tag!='AERIS_MISSION':raise ValueError('LIVE_LOG_TAG')
  self.sequence+=1;seq=self.sequence;start=self.now();argv=[self.adb,'-s',self.serial,'logcat','-v','raw','AERIS_MISSION:I','*:S'];out=self.root/('live-%05d.jsonl'%seq);err=self.root/('live-%05d.stderr'%seq);ef=err.open('xb');p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=ef);selector=selectors.DefaultSelector();selector.register(p.stdout,selectors.EVENT_READ);os.set_blocking(p.stdout.fileno(),False);pending=b'';count=0
  def rows():
   nonlocal pending,count
   with out.open('xb') as f:
    while self.now()<=deadline_ns:
     if p.poll() is not None:raise RuntimeError('ANDROID_LIVE_LOG_EXIT')
     for key,mask in selector.select(min(.05,max(0,(deadline_ns-self.now())/1e9))):
      raw=os.read(p.stdout.fileno(),65536)
      if not raw:raise RuntimeError('ANDROID_LIVE_LOG_EOF')
      count+=len(raw)
      if count>4*2**20 or len(pending)+len(raw)>262144:raise RuntimeError('LIVE_LOG_BOUND')
      f.write(raw);f.flush();pending+=raw
      while b'\n' in pending:
       line,pending=pending.split(b'\n',1)
       if not line.startswith(b'{'):continue
       if len(line)>16384:raise RuntimeError('LIVE_ACK_LINE_BOUND')
       value=json.loads(line)
       if type(value)is not dict:raise ValueError('LIVE_ACK_OBJECT')
       yield value
    raise TimeoutError('ANDROID_PUBLIC_LIVE_ACK10S')
  try:yield rows()
  finally:
   if p.poll() is None:p.terminate()
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
   selector.close();p.stdout.close();ef.flush();os.fsync(ef.fileno());ef.close();put(self.root/('live-%05d-receipt.json'%seq),canonical({'argv':argv,'startedHostNs':start,'closedHostNs':self.now(),'bytes':count,'exit':p.returncode,'subscriptionBeforeIntent':True,'logCleared':False})+b'\n')
 def export_private(self,run,target,*,deadline_ns,metadata_only=False,maximum_bytes=168*2**20):
  if re.fullmatch('[A-Za-z0-9_-]{1,64}',run)is None:raise ValueError('EXPORT_RUN')
  target=Path(target);paths=['files/checkpoint14','files/latest-state.json','files/workspace03','files/review-links','files/runtime']
  if not metadata_only:paths.insert(0,'files/control-runs/'+run)
  if type(maximum_bytes)is not int or not 0<maximum_bytes<=(64*2**20 if metadata_only else 168*2**20):raise ValueError('EXPORT_ORIGINAL_CAP')
  argv=[self.adb,'-s',self.serial,'exec-out','run-as','vn.rtr.aeris.mission','tar','-cf','-',*paths];started=self.now();err=target.with_suffix('.stderr');ef=err.open('xb');p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=ef);sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);os.set_blocking(p.stdout.fileno(),False);count=0
  try:
   with target.open('xb') as f:
    while True:
     if self.now()>deadline_ns:raise TimeoutError('NATIVE_EXPORT_DEADLINE')
     for key,mask in sel.select(.05):
      raw=os.read(p.stdout.fileno(),65536)
      if not raw:sel.unregister(p.stdout);break
      count+=len(raw)
      if count>maximum_bytes:raise RuntimeError('NATIVE_TAR168MiB_CAP')
      f.write(raw)
     if not sel.get_map():break
    code=p.wait(timeout=max(.01,(deadline_ns-self.now())/1e9));f.flush();os.fsync(f.fileno())
   if code:raise RuntimeError('NATIVE_EXPORT_FAILED:'+str(code))
   from .candidate import sha
   return {'path':str(target),'sha256':sha(target),'bytes':count,'startedHostNs':started,'finishedHostNs':self.now(),'argv':argv,'exit':code,'selectedRun':run,'readOnlyExport':True}
  finally:
   if p.poll() is None:p.terminate()
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
   sel.close();p.stdout.close();ef.flush();os.fsync(ef.fileno());ef.close()
 def prepare_normal(self,expected_apk_sha,*,deadline_ns):
  """Cold resource preparation only; genuine source-bound READY follows public API."""
  import xml.etree.ElementTree as ET
  started=self.now();package='vn.rtr.aeris.mission';raw=self.command(['shell','pm','path',package],deadline_ns=deadline_ns).decode().strip()
  if not raw.startswith('package:/') or '\n' in raw:raise ValueError('ONE_INSTALLED_DEVELOPMENT_PACKAGE')
  actual=self.command(['shell','sha256sum',raw[8:]],deadline_ns=deadline_ns).decode().split()[0]
  if actual!=expected_apk_sha:raise ValueError('ACTUAL_INSTALLED_APK_SHA')
  self.command(['shell','am','start','-n',package+'/.CockpitActivity'],deadline_ns=deadline_ns)
  while self.now()<=deadline_ns:
   activity=self.command(['shell','dumpsys','activity','activities'],deadline_ns=deadline_ns,maximum_bytes=131072).decode()
   focused=any(package in line and ('mResumedActivity' in line or 'topResumedActivity' in line) for line in activity.splitlines())
   xml=self.command(['shell','uiautomator','dump','/dev/tty'],deadline_ns=deadline_ns).decode();start=xml.find('<?xml');end=xml.rfind('</hierarchy>')
   if start>=0 and end>=start:
    tree=ET.fromstring(xml[start:end+12]);nodes=list(tree.iter('node'));web=any(n.get('class')=='android.webkit.WebView' and n.get('package')==package for n in nodes);controls=any(n.get('package')==package and (n.get('content-desc') in ('AERIS khảo sát và huấn luyện SITL','Real-time Robotics AERIS') or n.get('text')=='Khảo sát') for n in nodes)
    if focused and web and controls:return {'status':'NATIVE_RESOURCES_PREPARED_NOT_PROTOCOL_READY','startedHostNs':started,'observedHostNs':self.now(),'installedAPKSHA256':actual,'actualPID':self.pid(package,deadline_ns=deadline_ns),'plainLaunchNoMissionExtras':True,'focusedVisibleUIObserved':True,'protocolREADYClaimed':False}
   time.sleep(.1)
  raise TimeoutError('NATIVE_RESOURCE_PREPARATION60S')

 def restart_normal(self,expected_apk_sha,*,deadline_ns):
  self.command(['shell','am','force-stop','vn.rtr.aeris.mission'],deadline_ns=deadline_ns)
  # pidof returns1 when absent: use a bounded shell predicate and retain original receipt.
  gone=self.command(['shell','sh','-c','if pidof vn.rtr.aeris.mission >/dev/null; then echo RUNNING; else echo ABSENT; fi'],deadline_ns=deadline_ns).decode().strip()
  if gone!='ABSENT':raise RuntimeError('RESTART_OLD_PROCESS_NOT_GONE')
  return self.prepare_normal(expected_apk_sha,deadline_ns=deadline_ns)
