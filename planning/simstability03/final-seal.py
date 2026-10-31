"""Contractor cold verification, link check and digest seal after archive assembly."""
from pathlib import Path,PurePosixPath
import json,hashlib,tarfile,stat,datetime,re,urllib.parse,socket
from html.parser import HTMLParser
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03';D=R/'delivery';P=D/'sim-stability03'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
receipt=json.loads((P/'PACKAGING-VERIFICATION.json').read_text());arc=R/receipt['archive'];assert sha(arc)==receipt['archiveSHA256']
with tarfile.open(arc,'r:gz')as t:
 members=t.getmembers();names=[m.name for m in members];assert len(set(names))==len(names)==116
 assert all(m.isfile()and not m.linkname and PurePosixPath(m.name).as_posix()==m.name and not PurePosixPath(m.name).is_absolute()and '..'not in PurePosixPath(m.name).parts for m in members)
 manifest=t.extractfile('bundle-manifest.json').read();digest=hashlib.sha256(manifest).hexdigest();assert t.extractfile('bundle-manifest.sha256').read()==(digest+'\n').encode();assert digest==receipt['manifestSHA256']
 q=json.loads(manifest);assert set(names)==set(q['files'])|{'bundle-manifest.json','bundle-manifest.sha256'}
 for n,v in q['files'].items():
  m=t.getmember(n);b=t.extractfile(m).read();assert len(b)==v['bytes']and hashlib.sha256(b).hexdigest()==v['sha256']and m.mode==v['mode']
 qualification=json.load(t.extractfile('QUALIFICATION-SIM-STABILITY03.json'));assert qualification['status']=='NOT READY'and qualification['productionSignature']is False
class Links(HTMLParser):
 def __init__(self):super().__init__();self.paths=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src']:self.paths.append(v)
hp=D/'COMPLETION-SIM-STABILITY03.html';parser=Links();parser.feed(hp.read_text());links=[]
for target in parser.paths:
 if urllib.parse.urlsplit(target).scheme or target.startswith('#'):continue
 p=(hp.parent/urllib.parse.unquote(target.split('#')[0])).resolve();assert p.is_file(),('REPORT_BROKEN_LINK',target);links.append({'link':target,'bytes':p.stat().st_size})
for port in [8896,5582,5583]:
 with socket.socket()as s:assert s.connect_ex(('127.0.0.1',port))!=0
lockChecks={}
for tag in ['01','02','03']:
 lock=R/('.local/simstability03/receiver'+tag)/'.local/simhand01/active';lockChecks[tag]=not lock.exists();assert not lock.exists()
scopes=[R/'planning/simstability03',E,P,D/'COMPLETION-SIM-STABILITY03.md',hp,*[R/('.local/simstability03/receiver'+t)for t in ['01','02','03']]]
inventory={}
for scope in scopes:
 for p in sorted(scope.rglob('*')if scope.is_dir()else[scope]):
  if p==E/'handoff-final01.json'or not p.is_file()or '__pycache__'in p.parts:continue
  assert not p.is_symlink(),('NEW_SCOPE_SYMLINK',p)
  inventory[str(p.relative_to(R))]={'bytes':p.stat().st_size,'sha256':sha(p),'mode':stat.S_IMODE(p.stat().st_mode)}
out={'format':'aeris-simstability03-contractor-final-seal','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'overallStatus':'NOT READY','manualScope':'ACTUAL_ANDROID_SITL_PASS_SEE_RAW_NOT_GENERAL_PRODUCT_ACCEPTANCE','archiveSHA256':receipt['archiveSHA256'],'manifestSHA256':digest,'archiveMembersChecked':len(members),'reportLocalLinksChecked':links,'reportVisualQA':'NOT_RUN_DESKTOP_BROWSER; STRUCTURAL_AND_LINK_QA_ONLY; ACTUAL_ANDROID_SCREENSHOTS_RETAINED','ownedLocksAbsent':lockChecks,'ownedRuntimePortsClosed':True,'entries':len(inventory),'bytes':sum(v['bytes']for v in inventory.values()),'inventory':inventory,'preservationReceiptSHA256':sha(E/'preservation-final01.json'),'qualificationSHA256':sha(E/'qualification-final01.json'),'runtimeAcceptance':'NOT_INFERRED_FROM_ARCHIVE_OR_SEAL','continuityClaim':False,'ENDUREAcceptanceClaim':False,'restorationAttempted':False}
(E/'handoff-final01.json').open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['inventory','reportLocalLinksChecked']},indent=2))
