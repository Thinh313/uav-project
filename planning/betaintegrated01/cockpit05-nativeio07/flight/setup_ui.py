"""Root-only, split explicit UI setup. Importing never executes ADB or creates evidence.
No AP/STAGE/CONNECT/grant, installation, seeding, clearing, AX/CDP or bridge evaluation.
"""
from pathlib import Path
import argparse,hashlib,json,math,os,re,struct,subprocess,sys,time,uuid
import xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(R))
from importlib import import_module
allocated_metadata=import_module('planning.betaintegrated01.cockpit05-nativeio07.flight.metadata').allocated_metadata
HELPERS=Path(__file__).parent
sys.path.insert(0,str(HELPERS))
from cockpitio07_root_operator import RootOperator
from cockpitio07_android_operator import PACKAGE,OperatorError,exclusive as helper_exclusive,utc
E=R/'evidence/betaintegrated01-cockpit05-nativeio07'
SETUP=E/'android-setup01'
ACCEPTED=R/'evidence/betaintegrated01-cockpit05-entry10-flight/actual-combined01/control/restart-recovery-supplement01.json'
SELECTED_BUILD=R/'evidence/betaintegrated01-cockpit05-nativeio07/native/build-01.json'
NAME='SITL30min_Manual_Assisted'
RUN='UI_SETUP_NO_SESSION';GENERATION='UI_SETUP_NO_AUTHORITY'
NAV={'survey':[17,254,79,318],'preflight':[17,318,79,382],'fly':[17,382,79,446],'review':[17,446,79,510]}
FIELD=(280,246);SAVE=(275,616)

def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def read(path):return json.loads(Path(path).read_text())
def require(value,reason):
 if not value:raise OperatorError(reason)
GUARD=E/'emulator01';GUARD_SOURCE=R/'planning/betaintegrated01/cockpit05-nativeio07/flight/android_guardian.py'
META_PLANNING=R/'planning/betaintegrated01/cockpit05-nativeio07/flight';META_CAP=64*2**20;PER_COMMAND_RESERVE=2**20

def allocated(root):
 total=0
 if not root.exists():return 0
 for path in root.rglob('*'):
  if path.is_file()and not path.is_symlink():total+=path.stat().st_blocks*512
 return total

def ps_field(pid,field):
 require(type(pid)is int and pid>1,'GUARD_PID_TYPE')
 result=subprocess.run(['ps','-p',str(pid),'-o',field+'='],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=2)
 require(result.returncode==0 and len(result.stdout)<=4096,'GUARD_PID_OBSERVATION_FAILED');return result.stdout.decode().strip()

def elapsed_seconds(text):
 require(re.fullmatch(r'(?:[0-9]+-)?[0-9]{1,3}:[0-9]{2}(?::[0-9]{2})?',text)is not None,'GUARD_ELAPSED_FORMAT')
 days=0
 if '-'in text:day,text=text.split('-');days=int(day)
 parts=list(map(int,text.split(':')));parts=([0]+parts)if len(parts)==2 else parts
 require(parts[1]<60 and parts[2]<60,'GUARD_ELAPSED_RANGE');return days*86400+parts[0]*3600+parts[1]*60+parts[2]

def guard_ready(mutation=False):
 require(not(GUARD/'closure.json').exists()and not(GUARD/'failure.json').exists(),'GUARD_FAILED_OR_CLOSED')
 launch=read(GUARD/'launch.json');admission=read(GUARD/'admission.json')
 require(launch.get('scope')=='ANDROID_SITL_TEST'and launch.get('serial')=='emulator-5582'and launch.get('maximumSeconds')==5400,'GUARD_SCOPE_OR_DEADLINE')
 require(admission.get('scope')=='ANDROID_SITL_TEST'and admission.get('metadataBudgetBytes')==META_CAP and admission.get('maximumSeconds')==5400,'GUARD_ADMISSION_CONTRACT')
 budget=admission.get('fullBudget',{});required=budget.get('requiredFreeBytes');peak=budget.get('taskHardPeakBytes');actual=budget.get('actualFreeBytes')
 require(budget.get('admitted')is True and type(required)is int and type(peak)is int and type(actual)is int and required>=peak+10*2**30+256*2**20 and actual>=required,'FULL_WHOLE_CASE_ADMISSION_REQUIRED_NOT_ENTRY_ALONE')
 require(launch.get('guardianSourceSHA256')==sha(GUARD_SOURCE.read_bytes()),'GUARD_SOURCE_CHANGED')
 require(ps_field(launch.get('guardianPID'),'lstart')==launch.get('guardianProcessStart'),'GUARD_PID_START_MISMATCH')
 require(ps_field(launch.get('pid'),'lstart')==launch.get('processStart'),'EMULATOR_PID_START_MISMATCH')
 require(type(launch.get('processGroup'))is int and os.getpgid(launch['pid'])==launch['processGroup']==launch['pid'],'EMULATOR_PROCESS_GROUP_MISMATCH')
 elapsed=elapsed_seconds(ps_field(launch['guardianPID'],'etime'));require(elapsed<=5375,'GUARD_DEADLINE_HEADROOM_UNDER25S')
 with(GUARD/'guard.jsonl').open('rb')as stream:
  stream.seek(max(0,(GUARD/'guard.jsonl').stat().st_size-65536));tail=stream.read(65536)
 rows=tail.split(b'\n');require(len(rows)>=2,'GUARD_NO_COMPLETE_ROW');row=json.loads(rows[-2]);now=time.monotonic_ns()
 require(type(row.get('hostNs'))is int and 0<=now-row['hostNs']<=2000000000,'GUARD_ROW_STALE_OR_FUTURE')
 floor=10*2**30+256*2**20
 forecast=row.get('forecastFreeBytes');require(type(row.get('freeBytes'))is int and type(forecast)in(int,float)and math.isfinite(forecast)and min(row['freeBytes'],forecast)>=floor,'GUARD_FLOOR_OR_FORECAST_REFUSED')
 require(row.get('AC')is True or type(row.get('batteryPercent'))is int and row['batteryPercent']>20,'GUARD_POWER_REFUSED')
 require(allocated_metadata(E)+allocated(META_PLANNING)+PER_COMMAND_RESERVE<=META_CAP,'OWN_METADATA64M_MINUS_COMMAND_RESERVE')
 return {'guardianPID':launch['guardianPID'],'elapsedSeconds':elapsed,'rowHostNs':row['hostNs'],'floorReserveBytes':floor,'mutation':mutation}

def exclusive(path,value):
 guard_ready();return helper_exclusive(path,value)

def sha_map(text):
 require(isinstance(text,str)and len(text)<=131072,'WORKSPACE_MAP_BOUND')
 result={}
 for line in text.splitlines():
  match=re.fullmatch(r'([a-f0-9]{64})\s+(files/workspace03/(?:draft-[0-9]{6}|review-[A-Za-z0-9_.:-]{1,128})-[a-f0-9]{64}\.json)',line)
  require(match is not None,'WORKSPACE_MAP_LINE')
  digest,path=match.groups();require(path not in result,'WORKSPACE_DUPLICATE_PATH');require(path.endswith('-'+digest+'.json'),'WORKSPACE_FILENAME_SHA');result[path]=digest
 require(len(result)<=256,'WORKSPACE_MAP_COUNT');return result


def native_empty(state,layout,view=None):
 require(state.get('chosenView')in('survey','preflight','fly','review'),'KNOWN_NATIVE_VIEW_REQUIRED')
 require(state.get('native',{}).get('phase')=='NO_SESSION','NATIVE_SESSION_EXISTS')
 require(state.get('ownerActive')is False and layout.get('ownerActive')is False,'NATIVE_OWNER_EXISTS')
 require(state.get('native',{}).get('authorityRestorable')is False,'RESTORABLE_AUTHORITY')
 require(layout.get('bindingStagedSHA256')is None,'BINDING_ALREADY_STAGED')
 require(state.get('viewReady')is True and layout.get('viewReady')is True,'UI_NOT_SETTLED')
 require(state.get('chosenView')==state.get('presentedView')==layout.get('view')==layout.get('presentedView'),'PRESENTATION_DISAGREEMENT')
 if view is not None:require(state['chosenView']==view,'WRONG_UI_VIEW')
 require(type(state.get('viewEpoch'))is int and state['viewEpoch']>0,'CURRENT_EPOCH_INVALID')

def old_files_preserved(before,after):
 require(all(after.get(path)==digest for path,digest in before.items()),'OLD_WORKSPACE_SHA_CHANGED_OR_MISSING')


class Setup:
 def __init__(self):
  guard_ready();SETUP.mkdir(parents=True,exist_ok=True);logs=SETUP/'operator'
  self.op=RootOperator.resume(logs,RUN,GENERATION)if logs.exists()else RootOperator(logs,RUN,GENERATION)
 def bytes(self,args,timeout=3):
  guard_ready(mutation=args[:2]==['shell','input']);raw=self.op.command(args,timeout=timeout)[0];require(len(raw)<=PER_COMMAND_RESERVE,'COMMAND_OUTPUT_OVER1M');return raw
 def json_file(self,path):
  guard_ready();observed=self.op.command(['shell','run-as',PACKAGE,'cat',path],timeout=3,check=False);raw,err,code,_=observed;require(len(raw)+len(err)<=131072,'PRIVATE_JSON_BOUND')
  if code!=0:
   if b'No such file or directory'in raw+err:raise OperatorError('INITIAL_PRIVATE_STATE_ABSENT')
   raise OperatorError('PRIVATE_JSON_COMMAND_FAILED')
  return json.loads(raw)
 def state(self):return self.json_file('files/workspace-state.json')
 def layout(self):
  guard_ready();return self.json_file('files/native-controls-layout.json')
 def workspace_map(self):
  if self.state()['workspace']['draft']is None:return {}
  names_raw=self.bytes(['shell','run-as',PACKAGE,'ls','-1','files/workspace03']);require(len(names_raw)<=65536,'WORKSPACE_LIST_BOUND');names=names_raw.decode().splitlines();require(1<=len(names)<=256 and len(set(names))==len(names),'WORKSPACE_LIST_COUNT')
  for name in names:require(re.fullmatch(r'(?:draft-[0-9]{6}|review-[A-Za-z0-9_.:-]{1,128})-[a-f0-9]{64}\.json',name)is not None,'WORKSPACE_PENDING_OR_FOREIGN_PATH')
  raw=self.bytes(['shell','run-as',PACKAGE,'sha256sum',*['files/workspace03/'+name for name in sorted(names)]]);require(len(raw)<=131072,'MAP_BYTES_BOUND');return sha_map(raw.decode())
 def settled(self,view=None,seconds=5):
  deadline=time.monotonic()+seconds;last=None
  while True:
   try:
    s=self.state();l=self.layout();native_empty(s,l,view);return s,l
   except OperatorError as error:
    last=str(error)
    if last not in('INITIAL_PRIVATE_STATE_ABSENT',)and not last.startswith(('UI_NOT_SETTLED','PRESENTATION_DISAGREEMENT','WRONG_UI_VIEW','CURRENT_EPOCH_INVALID','NATIVE_SESSION_EXISTS','KNOWN_NATIVE_VIEW_REQUIRED')):raise
   if time.monotonic()>=deadline:raise OperatorError('SETTLED_NOT_OBSERVED:'+str(last))
   time.sleep(.1)
 def observe(self,label='observe',view=None):
  guard_ready();self.op.focus();s,l=self.settled(view);guard_ready();screen=self.op.screenshot();raw=screen.read_bytes();require(raw[:8]==b'\x89PNG\r\n\x1a\n'and 24<=len(raw)<=512*1024,'SCREEN_PNG_REQUIRED');width,height=struct.unpack('>II',raw[16:24]);require((width,height)==(1280,800),'EXACT_QUALIFIED_VIEWPORT_REQUIRED')
  result={'atUTC':utc(),'label':label,'package':PACKAGE,'screen':str(screen.relative_to(R)),'screenSHA256':sha(raw),'width':width,'height':height,'state':s,'layout':l,'workspaceSHA256Map':self.workspace_map(),'hostMonotonicNs':time.monotonic_ns(),'RootVisualApproval':False,'noAuthority':True};out=SETUP/(label+'-'+uuid.uuid4().hex+'.json');exclusive(out,result);print(json.dumps({'observation':str(out.relative_to(R)),'screen':result['screen'],'screenSHA256':result['screenSHA256'],'view':s['chosenView']}));return result
 def reviewed(self,args,view):
  require(args.reviewed_current_screen_sha is not None and re.fullmatch('[a-f0-9]{64}',args.reviewed_current_screen_sha)is not None,'EXPLICIT_ROOT_REVIEWED_SCREEN_SHA_REQUIRED')
  current=self.observe('before-'+args.step,view);require(current['screenSHA256']==args.reviewed_current_screen_sha,'FRESH_SCREEN_BYTES_DIFFER_FROM_ROOT_REVIEWED_SHA_NO_ACTION')
  exclusive(SETUP/('review-consent-'+uuid.uuid4().hex+'.json'),{'atUTC':utc(),'step':args.step,'reviewedSHA256':args.reviewed_current_screen_sha,'freshScreen':current['screen'],'nativeViewEpoch':current['state']['viewEpoch'],'basis':'ROOT_EXPLICIT_SHA_FOR_THIS_EXACT_CURRENT_FRAME','noAutomaticRetry':True});return current
 def private_map(self):
  raw=self.bytes(['exec-out','run-as',PACKAGE,'find','files/control-runs','files/workspace03','files/review-links','-type','f','-exec','sha256sum','{}','+'],timeout=20)
  values={}
  for line in raw.decode().splitlines():
   digest,name=line.split(None,1);name=name.strip()
   require(re.fullmatch('[0-9a-f]{64}',digest)and name.startswith(('files/control-runs/','files/workspace03/','files/review-links/'))and '..'not in Path(name).parts and name not in values,'PRIVATE_MAP_INVALID');values[name]=digest
  require(0<len(values)<=4096,'PRIVATE_MAP_BOUND');return values
 def empty_baseline(self):
  require(not(SETUP/'observed-empty-package.json').exists(),'EMPTY_ALREADY_OBSERVED')
  self.op.focus();state,layout=self.settled('survey');w=state['workspace']
  require(w['draft']is None and w['draftSHA256']is None and w['reviews']==[],'NEW_PACKAGE_MUST_START_EMPTY_NO_IMPORTED_HISTORY')
  exclusive(SETUP/'observed-empty-package.json',{'package':PACKAGE,'state':state,'layout':layout,'hostNs':time.monotonic_ns(),'noSeedOrImportedHistory':True})
  return state
 def keyboard_wait(self,shown):
  deadline=time.monotonic()+3;stable=0
  while True:
   guard_ready();window=self.op.command(['shell','dumpsys','input_method'],timeout=3)[0].decode(errors='replace')
   flags=re.findall(r'(?:mInputShown|isInputViewShown)\s*=\s*(true|false)',window)
   matched=bool(flags)and(any(v=='true'for v in flags)if shown else all(v=='false'for v in flags))
   stable=stable+1 if matched else 0
   if stable>=2:return
   require(time.monotonic()<deadline,'KEYBOARD_VISIBILITY_NOT_OBSERVED:'+str(shown));time.sleep(.1)
 def keyboard_settle(self):return self.keyboard_wait(False)
 def bootstrap_empty_dirs(self,args):
  require((SETUP/'observed-empty-package.json').is_file(),'OBSERVED_EMPTY_REQUIRED')
  require(not(SETUP/'empty-dir-bootstrap-intent.json').exists(),'EMPTY_DIR_BOOTSTRAP_ONE_ATTEMPT')
  current=self.reviewed(args,'survey');require(current['state']['workspace']['draft']is None,'BOOTSTRAP_BEFORE_UI_DRAFT')
  for d in('files/control-runs','files/review-links'):
   o=self.op.command(['shell','run-as',PACKAGE,'ls','-ld',d],check=False)
   require(o[2]!=0 and b'No such file or directory'in o[0]+o[1],'BOOTSTRAP_ONLY_EXPLICIT_ABSENT_DIR')
  exclusive(SETUP/'empty-dir-bootstrap-intent.json',{'directories':['files/control-runs','files/review-links'],'emptyOnly':True,'appFirstRunDirectoryInitializationTested':False,'noFlightJournalReviewWorkspaceOrAuthoritySeed':True})
  self.bytes(['shell','run-as',PACKAGE,'mkdir','files/control-runs','files/review-links'])
 def name_r1(self,args):
  require((SETUP/'observed-empty-package.json').is_file(),'OBSERVED_EMPTY_REQUIRED_BEFORE_NAME')
  require(not(SETUP/'name-r1-intent.json').exists(),'NAME_ONE_ATTEMPT_ONLY')
  self.keyboard_settle();current=self.reviewed(args,'survey');w=current['state']['workspace'];require(w['draft']is None and w['reviews']==[],'NEW_DRAFT_ALREADY_EXISTS')
  exclusive(SETUP/'name-r1-intent.json',{'hostNs':time.monotonic_ns(),'reviewedSHA256':current['screenSHA256'],'name':NAME,'referenceOrSaveNotTouched':True})
  self.keyboard_settle();self.bytes(['shell','input','tap',FIELD[0],FIELD[1]]);self.keyboard_wait(True)
  self.bytes(['shell','input','keyevent','KEYCODE_MOVE_END']);self.bytes(['shell','input','keyevent',*(['KEYCODE_DEL']*80)]);self.bytes(['shell','input','text',NAME])
  self.bytes(['shell','input','keyevent','KEYCODE_BACK']);self.keyboard_settle()
  self.bytes(['shell','input','tap',430,190]);self.keyboard_settle()
  return self.observe('name-r1','survey')
 def reference_r1(self,args):
  require((SETUP/'name-r1-intent.json').is_file(),'EXPLICIT_NAME_STAGE_REQUIRED')
  require(not(SETUP/'reference-r1-intent.json').exists(),'REFERENCE_ONE_ATTEMPT_ONLY')
  self.keyboard_settle();current=self.reviewed(args,'survey');require(current['state']['workspace']['draft']is None,'DRAFT_ALREADY_SAVED')
  exclusive(SETUP/'reference-r1-intent.json',{'hostNs':time.monotonic_ns(),'reviewedSHA256':current['screenSHA256'],'referenceQuadTouch':[270,547],'noSave':True})
  self.keyboard_settle();self.bytes(['shell','input','tap',270,547]);self.keyboard_settle()
  self.bytes(['shell','input','tap',430,190]);self.keyboard_settle()
  return self.observe('reference-r1','survey')
 def save_r1(self,args):
  require((SETUP/'reference-r1-intent.json').is_file(),'EXPLICIT_UI_PREPARE_REQUIRED_BEFORE_SAVE')
  require(not(SETUP/'save-r1-intent.json').exists(),'SAVE_ONE_ATTEMPT_ONLY')
  self.keyboard_settle();current=self.reviewed(args,'survey');w=current['state']['workspace'];require(w['draft']is None and w['reviews']==[],'NEW_DRAFT_ALREADY_EXISTS')
  self.keyboard_settle();exclusive(SETUP/'save-r1-intent.json',{'hostNs':time.monotonic_ns(),'reviewedSHA256':current['screenSHA256'],'name':NAME,'realTouchesOnly':True})
  self.bytes(['shell','input','tap',SAVE[0],SAVE[1]])
  deadline=time.monotonic()+5
  while True:
   state=self.state();d=state['workspace']['draft']
   if d is not None:break
   require(time.monotonic()<deadline,'R1_UI_SAVE_NOT_OBSERVED');time.sleep(.1)
  require(d['revision']==1 and d['kind']=='polygon'and d['altitudeM']==3 and len(d['geometry'])==4 and d['trainingOnly']is True and d['name']==NAME and state['workspace']['reviews']==[],'REAL_UI_R1_QUAD3M_REQUIRED')
  exclusive(SETUP/'save-r1-observed.json',{'state':state,'hostNs':time.monotonic_ns(),'realUI':True});return state
 def baseline(self):
  require(not(E/'initial-private-SHA.json').exists(),'INITIAL_BASELINE_ALREADY_EXISTS')
  require((SETUP/'save-r1-observed.json').is_file(),'REAL_UI_R1_SAVE_PROOF_REQUIRED')
  current=self.observe('baseline');d=current['state']['workspace']['draft'];actual=self.private_map()
  require(d['revision']==1 and d['altitudeM']==3 and d['kind']=='polygon'and len(d['geometry'])==4 and current['state']['workspace']['reviews']==[],'R1_EMPTY_HISTORY_BASELINE')
  require(len(actual)==1 and current['workspaceSHA256Map']==actual,'ONLY_REAL_R1_PRIVATE_FILE_REQUIRED')
  exclusive(E/'initial-private-SHA.json',actual);exclusive(E/'initial-workspace-SHA.json',current['workspaceSHA256Map']);exclusive(E/'initial-workspace-state.json',current['state']);return current

 def bootready(self):
  require(not(SETUP/'boot-ready-intent.json').exists(),'BOOTREADY_ALREADY_ATTEMPTED_NO_RETRY')
  exclusive(SETUP/'boot-ready-intent.json',{'atUTC':utc(),'maximumBootSeconds':90,'noStageConnectOrGrant':True});deadline=time.monotonic()+90
  while True:
   guard_ready();device=self.op.command(['get-state'],timeout=3,check=False)
   if device[2]==0 and device[0].strip()==b'device':break
   require(time.monotonic()<deadline,'OWNED_DEVICE_ONLINE90S_DEADLINE');time.sleep(.5)
  while self.bytes(['shell','getprop','sys.boot_completed']).strip()!=b'1':
   require(time.monotonic()<deadline,'OWNED_ANDROID_BOOT90S_DEADLINE');time.sleep(.5)
  paths=self.bytes(['shell','pm','path',PACKAGE]).decode().splitlines();require(len(paths)==1 and paths[0].startswith('package:/data/app/'),'CURRENT_INSTALLED_PACKAGE_PATH_REQUIRED');path=paths[0][8:];require(path.endswith('.apk')and '..'not in Path(path).parts and not any(c.isspace()for c in path),'INSTALLED_APK_PATH_INVALID')
  observed=self.bytes(['shell','sha256sum',path]).decode().split();build=read(SELECTED_BUILD);require(observed==[build['sha256'],path],'CURRENT_INSTALLED_APK_HASH_MISMATCH')
  self.bytes(['shell','am','start','-n',PACKAGE+'/.CockpitActivity'],timeout=10)
  state,layout=self.settled(seconds=10);exclusive(SETUP/'boot-ready.json',{'atUTC':utc(),'selectedAPK_SHA256':build['sha256'],'installedPath':path,'state':state,'layout':layout,'noInstallClearStageConnectOrGrant':True});return state
 def inactive_connect_visual(self,state,layout):
  # Known stale native layout cannot become a fabricated native measurement.
  native_empty(state,layout,'preflight');original=layout['buttons']['control01-connect'];require(original.get('enabled')is False,'UNSTAGED_CONNECT_MUST_BE_DISABLED')
  if original.get('visible')is True:return {'basis':'ACTUAL_NATIVE_LAYOUT','nativeOriginal':original}
  guard_ready();self.op.focus();xml,path=self.op.dump_ui(timeout=3);guard_ready();root=ET.fromstring(xml);nodes=[x for x in root.iter('node')if x.get('package')==PACKAGE and x.get('content-desc')=='control01-connect'];require(len(nodes)==1,'UNIQUE_CURRENT_INACTIVE_AX_CONNECT_REQUIRED');node=nodes[0]
  require(node.get('enabled')=='false'and node.get('visible-to-user','true')=='true','AX_UNSTAGED_CONNECT_NOT_DISABLED_VISIBLE');match=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''));require(match is not None,'AX_CONNECT_BOUNDS_INVALID');bounds=list(map(int,match.groups()));l,t,r,b=bounds;require(0<=l<r<=1280 and 0<=t<b<=800,'AX_CONNECT_OUT_OF_QUALIFIED_VIEWPORT')
  current=self.state();nowlayout=self.layout();native_empty(current,nowlayout,'preflight');require(current['viewEpoch']==state['viewEpoch'],'AX_VIEW_EPOCH_CHANGED')
  result={'basis':'FRESH_UIAUTOMATOR_DISABLED_CONNECT_ONLY_NOT_NATIVE_LAYOUT_OR_AUTHORITY','nativeOriginal':original,'AXBounds':bounds,'AXEnabled':False,'sourceXML':str(path),'sourceXML_SHA256':sha(xml),'nativeFlagsUnmodified':True}
  exclusive(SETUP/('inactive-connect-AX-'+uuid.uuid4().hex+'.json'),result);return result
 def preflight(self,args):
  suffix='-long'if args.next_case=='long'else'';marker='preflight'+suffix+'-intent.json'
  require(not(SETUP/marker).exists(),'PREFLIGHT_NAV_ALREADY_ATTEMPTED_NO_AUTORETRY');current=self.reviewed(args,None)
  expectedMap=read(E/'initial-private-SHA.json');expectedState=read(E/'initial-workspace-state.json')
  if args.next_case=='long':
   require(read(E/'qa/short-cold01/results.json').get('status')=='SHORT_PASS_CLOSED_RAW_ONLY','SHORT_COLD_GATE_REQUIRED')
   expectedMap=read(E/'actual-short01/control/all-private-after-restart-SHA.json');expectedState=read(E/'actual-short01/control/restart-recovery.json')['currentUI']
  require(self.private_map()==expectedMap,'PRIVATE_HISTORY_CHANGED_SINCE_BASELINE');require(current['state']['workspace']==expectedState['workspace'],'WORKSPACE_CHANGED_SINCE_BASELINE')
  exclusive(SETUP/marker,{'atUTC':utc(),'bounds':NAV['preflight'],'RootReviewedSHA256':current['screenSHA256'],'noStageOrConnect':True})
  if current['state']['chosenView']!='preflight':
   l,t,r,b=NAV['preflight'];self.bytes(['shell','input','tap',(l+r)//2,(t+b)//2])
  after=self.observe('preflight','preflight');require(self.private_map()==expectedMap,'NAV_CHANGED_PRIVATE_HISTORY');connectVisual=self.inactive_connect_visual(after['state'],after['layout'])
  exclusive(SETUP/('ui-geometry'+suffix+'.json'),{'atUTC':utc(),'package':PACKAGE,'viewport':[1280,800],'navGeometry':NAV,'basis':'ROOT_APPROVED_FRESH_SCREEN_SHA_MATCH_AND_LAYOUT_VIEWPORT_NOT_AX_MEASUREMENT','RootReviewedSHA256':current['screenSHA256'],'preflightState':after['state'],'preflightLayout':after['layout'],'inactiveConnectVisual':connectVisual,'actualR1Preserved':True,'priorPrivateFiles':1,'ownerActive':False,'bindingStagedSHA256':None,'noStageConnectOrGrant':True});return after

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('step',choices=['bootready','observe','empty','bootstrap-empty-dirs','name-r1','reference-r1','save-r1','baseline','preflight','preserve-old']);parser.add_argument('--reviewed-current-screen-sha');parser.add_argument('--next-case',choices=['short','long'],default='short');args=parser.parse_args();setup=Setup()
 if args.step=='preserve-old':
  import_module('planning.betaintegrated01.cockpit05-nativeio07.flight.preservation').observe(setup.op,SETUP/('old-package233-'+uuid.uuid4().hex+'.json'))
 elif args.step=='bootready':setup.bootready()
 elif args.step=='observe':setup.observe()
 elif args.step=='empty':setup.empty_baseline()
 elif args.step=='bootstrap-empty-dirs':setup.bootstrap_empty_dirs(args)
 elif args.step=='name-r1':setup.name_r1(args)
 elif args.step=='reference-r1':setup.reference_r1(args)
 elif args.step=='save-r1':setup.save_r1(args)
 elif args.step=='baseline':setup.baseline()
 else:setup.preflight(args)
if __name__=='__main__':main()
