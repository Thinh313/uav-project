"""Root-only, split explicit UI setup. Importing never executes ADB or creates evidence.
No AP/STAGE/CONNECT/grant, installation, seeding, clearing, AX/CDP or bridge evaluation.
"""
from pathlib import Path
import argparse,hashlib,json,math,os,re,struct,subprocess,sys,time,uuid
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(R))
from importlib import import_module
allocated_metadata=import_module('planning.betaintegrated01.cockpit05-entry10.full.metadata').allocated_metadata
HELPERS=R/'planning/betaintegrated01/cockpit05-soak/android'
sys.path.insert(0,str(HELPERS))
from cockpit05_root_operator import RootOperator
from cockpit05_android_operator import PACKAGE,OperatorError,exclusive as helper_exclusive,utc
E=R/'evidence/betaintegrated01-cockpit05-entry10-flight'
SETUP=E/'android-setup01'
ACCEPTED=R/'evidence/betaintegrated01-cockpit05-native/android/restart-recovery.json'
SELECTED_BUILD=R/'evidence/betaintegrated01-cockpit05-native/build-02.json'
NAME='SITL30min_Manual_Assisted'
RUN='UI_SETUP_NO_SESSION';GENERATION='UI_SETUP_NO_AUTHORITY'
NAV={'survey':[17,254,79,318],'preflight':[17,318,79,382],'fly':[17,382,79,446],'review':[17,446,79,510]}
FIELD=(280,246);SAVE=(275,616)

def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def read(path):return json.loads(Path(path).read_text())
def require(value,reason):
 if not value:raise OperatorError(reason)
GUARD=E/'emulator01';GUARD_SOURCE=R/'planning/betaintegrated01/cockpit05-entry10/full/android_guardian.py'
META_PLANNING=R/'planning/betaintegrated01/cockpit05-entry10/full';META_CAP=64*2**20;PER_COMMAND_RESERVE=2**20

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

def expected_baseline():
 accepted=read(ACCEPTED);result=sha_map(accepted['afterSHA256Map'])
 require(len(result)==8,'ACCEPTED_MAP_NOT_EIGHT');require(accepted['state']['workspace']['draft']['revision']==5,'ACCEPTED_DRAFT_NOT_R5');return accepted,result

def native_empty(state,layout,view=None):
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

def verify_r6(before_state,after_state,before_map,after_map,new_name=NAME):
 before=before_state['workspace']['draft'];after=after_state['workspace']['draft'];require(before['revision']==5 and after['revision']==6,'EXPECTED_EXACT_R5_TO_R6')
 require(after['name']==new_name,'ACTUAL_SAVED_NAME_MISMATCH')
 for key in ('id','kind','datum','altitudeDatum','units','geometry','altitudeM','corridorWidthM','trainingOnly'):
  require(after.get(key)==before.get(key),'UNINTENDED_DRAFT_CHANGE:'+key)
 require(after.get('altitudeM')==3,'QUALIFIED_3M_GEOMETRY_REQUIRED');old_files_preserved(before_map,after_map)
 added=set(after_map)-set(before_map);require(len(after_map)==9 and len(added)==1,'EXACTLY_ONE_R6_FILE_REQUIRED');path=next(iter(added));digest=after_state['workspace']['draftSHA256'];require(re.fullmatch(r'files/workspace03/draft-000006-[a-f0-9]{64}\.json',path)is not None and after_map[path]==digest,'R6_CANONICAL_SHA_LINK')
 return {'path':path,'sha256':digest,'revision':6,'oldEightSHAUnchanged':True}

class Setup:
 def __init__(self):
  guard_ready();SETUP.mkdir(parents=True,exist_ok=True);logs=SETUP/'operator'
  self.op=RootOperator.resume(logs,RUN,GENERATION)if logs.exists()else RootOperator(logs,RUN,GENERATION)
 def bytes(self,args,timeout=3):
  guard_ready(mutation=args[:2]==['shell','input']);raw=self.op.command(args,timeout=timeout)[0];require(len(raw)<=PER_COMMAND_RESERVE,'COMMAND_OUTPUT_OVER1M');return raw
 def json_file(self,path):
  raw=self.bytes(['shell','run-as',PACKAGE,'cat',path]);require(len(raw)<=131072,'PRIVATE_JSON_BOUND');return json.loads(raw)
 def state(self):return self.json_file('files/workspace-state.json')
 def layout(self):
  guard_ready();return self.op.layout()
 def workspace_map(self):
  names_raw=self.bytes(['shell','run-as',PACKAGE,'ls','-1','files/workspace03']);require(len(names_raw)<=65536,'WORKSPACE_LIST_BOUND');names=names_raw.decode().splitlines();require(1<=len(names)<=256 and len(set(names))==len(names),'WORKSPACE_LIST_COUNT')
  for name in names:require(re.fullmatch(r'(?:draft-[0-9]{6}|review-[A-Za-z0-9_.:-]{1,128})-[a-f0-9]{64}\.json',name)is not None,'WORKSPACE_PENDING_OR_FOREIGN_PATH')
  raw=self.bytes(['shell','run-as',PACKAGE,'sha256sum',*['files/workspace03/'+name for name in sorted(names)]]);require(len(raw)<=131072,'MAP_BYTES_BOUND');return sha_map(raw.decode())
 def settled(self,view=None,seconds=5):
  deadline=time.monotonic()+seconds;last=None
  while True:
   s=self.state();l=self.layout()
   try:native_empty(s,l,view);return s,l
   except OperatorError as error:last=str(error)
   if time.monotonic()>=deadline:raise OperatorError('SETTLED_NOT_OBSERVED:'+str(last))
   time.sleep(.1)
 def observe(self,label='observe',view=None):
  guard_ready();self.op.focus();s,l=self.settled(view);guard_ready();screen=self.op.screenshot();raw=screen.read_bytes();require(raw[:8]==b'\x89PNG\r\n\x1a\n'and 24<=len(raw)<=512*1024,'SCREEN_PNG_REQUIRED');width,height=struct.unpack('>II',raw[16:24]);require((width,height)==(1280,800),'EXACT_QUALIFIED_VIEWPORT_REQUIRED')
  result={'atUTC':utc(),'label':label,'package':PACKAGE,'screen':str(screen.relative_to(R)),'screenSHA256':sha(raw),'width':width,'height':height,'state':s,'layout':l,'workspaceSHA256Map':self.workspace_map(),'hostMonotonicNs':time.monotonic_ns(),'RootVisualApproval':False,'noAuthority':True};out=SETUP/(label+'-'+uuid.uuid4().hex+'.json');exclusive(out,result);print(json.dumps({'observation':str(out.relative_to(R)),'screen':result['screen'],'screenSHA256':result['screenSHA256'],'view':s['chosenView']}));return result
 def reviewed(self,args,view):
  require(args.reviewed_current_screen_sha is not None and re.fullmatch('[a-f0-9]{64}',args.reviewed_current_screen_sha)is not None,'EXPLICIT_ROOT_REVIEWED_SCREEN_SHA_REQUIRED')
  current=self.observe('before-'+args.step,view);require(current['screenSHA256']==args.reviewed_current_screen_sha,'FRESH_SCREEN_BYTES_DIFFER_FROM_ROOT_REVIEWED_SHA_NO_ACTION')
  exclusive(SETUP/('review-consent-'+uuid.uuid4().hex+'.json'),{'atUTC':utc(),'step':args.step,'reviewedSHA256':args.reviewed_current_screen_sha,'freshScreen':current['screen'],'nativeViewEpoch':current['state']['viewEpoch'],'basis':'ROOT_EXPLICIT_SHA_FOR_THIS_EXACT_CURRENT_FRAME','noAutomaticRetry':True});return current
 def baseline(self):
  require(not(E/'initial-workspace-SHA.json').exists(),'INITIAL_BASELINE_ALREADY_EXISTS')
  current=self.observe('baseline','survey');accepted,expected=expected_baseline();require(current['workspaceSHA256Map']==expected,'ACTUAL_WORKSPACE_DIFFERS_FROM_ACCEPTED_EIGHT')
  require(current['state']['workspace']==accepted['state']['workspace'],'ACTUAL_WORKSPACE_DIFFERS_FROM_ACCEPTED_R5_MOCK_HISTORY')
  require(current['state']['workspace']['draftSHA256']==accepted['state']['workspace']['draftSHA256'],'ACTUAL_R5_SHA_MISMATCH')
  build=read(SELECTED_BUILD);exclusive(E/'initial-workspace-SHA.json',expected);exclusive(E/'initial-workspace-state.json',current['state']);exclusive(SETUP/'baseline-proof.json',{'atUTC':utc(),'acceptedReceipt':str(ACCEPTED.relative_to(R)),'acceptedReceiptSHA256':sha(ACCEPTED.read_bytes()),'selectedAPK':build['apk'],'selectedAPK_SHA256':build['sha256'],'layout':current['layout'],'screen':current['screen'],'screenSHA256':current['screenSHA256'],'RootBeforeGenuineUIR6Save':True,'noSeedClearInstallOrGrant':True});return current
 def before_r6(self,current):
  baseline={'workspaceSHA256Map':read(E/'initial-workspace-SHA.json'),'state':read(E/'initial-workspace-state.json')};require(current['workspaceSHA256Map']==baseline['workspaceSHA256Map'],'WORKSPACE_CHANGED_SINCE_BASELINE');require(current['state']['workspace']==baseline['state']['workspace'],'WORKSPACE_STATE_CHANGED_SINCE_BASELINE');return baseline
 def prepare(self,args):
  require(not(SETUP/'prepared-r6.json').exists(),'PREPARE_ALREADY_ATTEMPTED_NO_AUTORETRY');current=self.reviewed(args,'survey');baseline=self.before_r6(current)
  exclusive(SETUP/'prepare-r6-intent.json',{'atUTC':utc(),'field':FIELD,'name':NAME,'RootReviewedSHA256':current['screenSHA256'],'noSave':True,'noAutomaticRetry':True})
  for command in (['shell','input','tap',*FIELD],['shell','input','keycombination','113','29'],['shell','input','keyevent','67'],['shell','input','text',NAME],['shell','input','keyevent','4'],['shell','input','tap',260,150]):self.bytes(command)
  time.sleep(.35);after=self.observe('prepared-r6','survey');self.before_r6(after);exclusive(SETUP/'prepared-r6.json',{'atUTC':utc(),'name':NAME,'beforeState':baseline['state'],'beforeMap':baseline['workspaceSHA256Map'],'preparedObservation':after,'textMustBeVisuallyVerifiedByRootBeforeSave':True,'saveSent':False});return after
 def save(self,args):
  require(not(SETUP/'save-r6-intent.json').exists(),'SAVE_ALREADY_ATTEMPTED_NO_AUTORETRY');prepared=read(SETUP/'prepared-r6.json');current=self.reviewed(args,'survey');self.before_r6(current);require(current['screenSHA256']==prepared['preparedObservation']['screenSHA256'],'PREPARED_NAME_SCREEN_CHANGED_NO_SAVE')
  exclusive(SETUP/'save-r6-intent.json',{'atUTC':utc(),'coordinate':SAVE,'nameVisuallyApprovedByRoot':NAME,'RootReviewedSHA256':current['screenSHA256'],'noAutomaticRetry':True});self.bytes(['shell','input','tap',*SAVE]);deadline=time.monotonic()+5
  while True:
   state,layout=self.settled('survey');draft=state['workspace']['draft']
   if draft.get('revision')==6:break
   require(draft.get('revision')==5,'UNEXPECTED_DRAFT_REVISION_AFTER_SAVE')
   if time.monotonic()>=deadline:raise OperatorError('R6_SAVE_NOT_OBSERVED_NO_RETRY')
   time.sleep(.1)
  after_map=self.workspace_map();verified=verify_r6(prepared['beforeState'],state,prepared['beforeMap'],after_map);raw=self.bytes(['shell','run-as',PACKAGE,'cat',verified['path']]);require(sha(raw)==verified['sha256']and json.loads(raw)==state['workspace']['draft'],'R6_REAL_FILE_BYTES_OR_CONTENT_MISMATCH')
  after=self.observe('saved-r6','survey');exclusive(SETUP/'saved-r6.json',{'atUTC':utc(),'state':state,'layout':layout,'workspaceSHA256Map':after_map,'verifiedR6':verified,'observation':after,'noAuthority':True});return after
 def preflight(self,args):
  require(not(SETUP/'preflight-intent.json').exists(),'PREFLIGHT_NAV_ALREADY_ATTEMPTED_NO_AUTORETRY');saved=read(SETUP/'saved-r6.json');current=self.reviewed(args,'survey');require(current['workspaceSHA256Map']==saved['workspaceSHA256Map'],'WORKSPACE_CHANGED_AFTER_R6');require(current['state']['workspace']['draft']['revision']==6,'ACTUAL_R6_REQUIRED')
  exclusive(SETUP/'preflight-intent.json',{'atUTC':utc(),'bounds':NAV['preflight'],'RootReviewedSHA256':current['screenSHA256'],'noStageOrConnect':True});l,t,r,b=NAV['preflight'];self.bytes(['shell','input','tap',(l+r)//2,(t+b)//2]);after=self.observe('preflight','preflight');require(after['workspaceSHA256Map']==saved['workspaceSHA256Map'],'NAV_CHANGED_WORKSPACE');connect=after['layout']['buttons']['control01-connect'];require(connect['visible']and connect['enabled']is False,'CONNECT_MUST_REMAIN_DISABLED_UNSTAGED')
  exclusive(SETUP/'ui-geometry.json',{'atUTC':utc(),'package':PACKAGE,'viewport':[1280,800],'navGeometry':NAV,'basis':'ROOT_APPROVED_FRESH_SCREEN_SHA_MATCH_AND_LAYOUT_VIEWPORT_NOT_AX_MEASUREMENT','RootReviewedSHA256':current['screenSHA256'],'observedPreflightScreen':after['screen'],'preflightState':after['state'],'preflightLayout':after['layout'],'actualR6':saved['verifiedR6'],'ownerActive':False,'bindingStagedSHA256':None,'noStageConnectOrGrant':True});return after

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('step',choices=['observe','baseline','prepare-r6','save-r6','preflight']);parser.add_argument('--reviewed-current-screen-sha');args=parser.parse_args();setup=Setup()
 if args.step=='observe':setup.observe()
 elif args.step=='baseline':setup.baseline()
 elif args.step=='prepare-r6':setup.prepare(args)
 elif args.step=='save-r6':setup.save(args)
 else:setup.preflight(args)
if __name__=='__main__':main()
