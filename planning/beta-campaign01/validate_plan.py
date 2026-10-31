"""Validate planning consistency only; never launches a simulator or marks product PASS."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,ast,re,datetime,subprocess
R=Path(__file__).resolve().parents[2];P=R/'planning/beta-campaign01';D=R/'delivery';E=R/'evidence/beta-campaign01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((P/'campaign.json').read_text());assert q['status']=='PLAN_NOT_EXECUTED'
def ids(items):
 a=[i['id']for i in items];assert len(a)==len(set(a));return set(a)
M=ids(q['milestones']);T=ids(q['taskGraph']);REQ=ids(q['requirements']);C=ids(q['cases']);K=ids(q['metrics']);S=ids(q['sources'])
def dag(items):
 graph={i['id']:i['dependsOn']for i in items};seen=set();active=set()
 def visit(n):
  assert n in graph and n not in active,('DEPENDENCY_CYCLE_OR_MISSING',n)
  if n in seen:return
  active.add(n)
  for p in graph[n]:visit(p)
  active.remove(n);seen.add(n)
 for n in graph:visit(n)
 return len(seen)
dag(q['milestones']);dag(q['taskGraph'])
for r in q['requirements']:assert r['milestone']in M and r['priority']=='MUST'and r['state']=='NOT_CHECKED_NEW_CAMPAIGN'and r['acceptance']
covered=set()
for c in q['cases']:
 assert c['state']=='PLANNED_NOT_EXECUTED'and c['requirements']and set(c['requirements'])<=REQ and isinstance(c['repeats'],int)and c['repeats']>=1;covered.update(c['requirements'])
assert covered==REQ,('UNCOVERED_REQUIREMENTS',sorted(REQ-covered))
for k in q['metrics']:assert k['requirement']in REQ and k['target']and k['method']and k['state']=='NOT_MEASURED_NEW_CAMPAIGN'
F=[f['featureID']for f in q['featureMapping']];assert len(F)==len(set(F))==48 and set(F)=={'F'+str(n).zfill(2)for n in range(1,49)}
for f in q['featureMapping']:assert f['requirementIDs']and set(f['requirementIDs'])<=REQ and f['scope']and f['qualification']=='NOT_CHECKED_NEW_CAMPAIGN'
for t in q['taskGraph']:assert t['milestone']in M and t['state']=='NOT_STARTED'and t['requiresTIPBeforeImplementation']
for c in q['customerTraceability']:assert c['requirements']and set(c['requirements'])<=REQ
assert set(q['releaseGate']['requiredRequirementIDs'])==REQ and q['releaseGate']['openP0P1Allowed']==0 and q['releaseGate']['requiredNotCheckedAllowed']==0
for s in q['sources']:assert urlsplit(s['url']).scheme=='https'and s['provenance']=='OFFICIAL_DOCUMENT_OR_PUBLISHER_CLAIM_NOT_AERIS_TEST'
for i in q['localInputs']:assert sha(R/i['path'])==i['sha256']and (R/i['path']).stat().st_size==i['bytes'],('INPUT_DRIFT',i['path'])
pol=q['executionPolicy'];assert pol['diskAdmissionGiB']==20 and pol['diskRuntimeFloorGiB']==10 and pol['reserveMiB']==256 and pol['forecastSeconds']==15
assert pol['physicsSpeedup']==1 and pol['pacingCapMs']==500 and pol['fsyncBeforeSensor']and not pol['frameDropForPerformance']and not pol['planLaunchesRuntime']and not pol['productionSigning']and not pol['physicalFlightCommands']and not pol['automaticEvidenceDeletion']
nominal=[c for c in q['cases']if c['id']in ['N04','N05','N06','N07','N08','N09']];assert len(nominal)==6 and sum(c['repeats']for c in nominal)==18
assert [sum(m['estimatedPersonDays'][j]for m in q['milestones'])for j in range(2)]==q['scheduling']['totalEstimatedPersonDays']
for p in P.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
class H(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[];self.titleCount=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.append(a['id'])
  if 'href'in a:self.links.append(a['href'])
  if tag=='h1':self.titleCount+=1
h=H();hp=D/'PLAN-BETA-CAMPAIGN01.html';h.feed(hp.read_text());assert len(h.ids)==len(set(h.ids))and h.titleCount==1
local=[]
for l in h.links:
 if l.startswith('#'):assert l[1:]in h.ids
 elif not urlsplit(l).scheme:
  p=(hp.parent/unquote(l.split('#')[0])).resolve()
  # PLAN-VALIDATION is this script's exclusive output and will be created below.
  assert p.is_file()or p==P/'PLAN-VALIDATION.json',('BROKEN_LOCAL_LINK',l);local.append(l)
baselineStatus=subprocess.check_output(['git','status','--porcelain=v1'],cwd=R).decode().splitlines();trackedChanges=[s for s in baselineStatus if not s.startswith('?? ')];assert len(trackedChanges)==97 and all(s.startswith(' D ')for s in trackedChanges),'UNEXPECTED_TRACKED_SOURCE_CHANGE'
files=[p for p in P.iterdir()if p.is_file()and p.name!='PLAN-VALIDATION.json']+[hp]
report={'format':'aeris-beta-campaign-plan-consistency','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PLAN_STRUCTURE_VALIDATED_NOT_PRODUCT_ACCEPTANCE','reviewer':'Sameassistant architectural/self-review; no independent human/agent flight review','counts':{'milestones':len(M),'requirements':len(REQ),'metrics':len(K),'featureGroups':len(F),'scenarioDesigns':len(C),'taskPackages':len(T),'customerNeeds':len(q['customerTraceability']),'localInputsSHAchecked':len(q['localInputs']),'polygonCorridorNominalRepetitions':18},'checks':['unique IDs','acyclic milestone and task dependencies','all MUST requirements covered by case designs','48 feature groups mapped with explicit scope','release gate matches all MUST and disallows required NOT_CHECKED','customer traceability','metric target/method links','historical input SHA preservation','20/10GiB and frame/fsync/speedup/cap invariants','Python AST','HTML IDs/anchors/local links','97 preexisting missing paths unchanged; no tracked source modifications'],'localLinksChecked':local,'files':{str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':sha(p)}for p in files},'runtimeTestsRun':False,'browserVisualQA':'NOT_RUN; planHTML structurally checked only','hardwareFlightOrSigning':False,'planningCompleted':True,'campaignExecuted':False,'productStatus':'NOT_READY_BETA_UNTIL_GATES_EXECUTED'}
(P/'PLAN-VALIDATION.json').open('x').write(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(E/'plan-validation01.json').open('x').write(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','counts','runtimeTestsRun','campaignExecuted']},indent=2))
