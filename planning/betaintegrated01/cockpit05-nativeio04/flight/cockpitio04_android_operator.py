"""Test-only owned-emulator UI helper. Importing performs no ADB or flight action.

Every mutation is one explicit caller method, never a scenario/autoflight/retry.
Cached geometry is permitted only by the caller, with fresh focus/state/screenshot.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

ADB = '/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
SERIAL = 'emulator-5582'
PACKAGE = 'vn.rtr.aeris.cockpitio04'
ACTIVITY = PACKAGE + '/.CockpitActivity'
BUTTONS = {'consent','guided','arm','confirm-home','takeoff','loiter','hold','land','close','connect'}
STICKS = {'control01-left-stick','control01-right-stick'}


class OperatorError(RuntimeError):
    pass


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def raw(value):
    if value is None:
        return b''
    return value if isinstance(value,bytes) else value.encode()


def exclusive(path, value):
    with Path(path).open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def node_bounds(node):
    match = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
    if not match:
        raise OperatorError('UI bounds missing or malformed')
    left,top,right,bottom = map(int,match.groups())
    if right<=left or bottom<=top or right>8192 or bottom>8192:
        raise OperatorError('UI bounds outside declared positive viewport bound')
    return left,top,right,bottom


def unique_node(xml, description, require_enabled=True, require_clickable=False):
    root = ET.fromstring(xml)
    matches = [x for x in root.iter('node') if x.get('content-desc')==description and x.get('package')==PACKAGE]
    if len(matches)!=1:
        raise OperatorError(f'Expected unique current-package node {description}, found {len(matches)}')
    node = matches[0]
    if require_enabled and node.get('enabled')!='true':
        raise OperatorError(f'Current UI node disabled: {description}')
    if require_clickable and node.get('clickable')!='true':
        raise OperatorError(f'Current UI node not clickable: {description}')
    return node_bounds(node)


@dataclass(frozen=True)
class Inspection:
    description: str
    screenshot: str
    screenshot_sha256: str
    created_mono_ns: int
    bounds: tuple[int,int,int,int]
    run: str
    generation: str
    state_sha256: str


def load_inspection(path):
    data=json.loads(Path(path).read_text())
    ticket=data.get('ticket',data)
    ticket['bounds']=tuple(ticket['bounds'])
    return Inspection(**ticket)


class Gesture:
    """Caller-owned asynchronous ADB gesture. PID return is not gesture success."""
    def __init__(self, op, argv, directory):
        self.op,self.argv,self.directory = op,argv,directory
        self.started_ns = time.monotonic_ns()
        self.out=(directory/'stdout.bin').open('xb');self.err=(directory/'stderr.bin').open('xb')
        try:
            self.process=subprocess.Popen(argv,stdout=self.out,stderr=self.err)
        except OSError as e:
            self.out.close();self.err.write(str(e).encode());self.err.close()
            exclusive(directory/'receipt-start-failed.json',{'atUTC':utc(),'argv':argv,'status':'EXEC_FAILED_NO_PID','error':str(e),'elapsedHostNs':time.monotonic_ns()-self.started_ns,'noRetry':True})
            raise OperatorError('Gesture client did not start; attempt and stderr retained')from e
        self.finished=False
        exclusive(directory/'receipt-start.json',{'atUTC':utc(),'argv':argv,'PID':self.process.pid,'startedHostMonoNs':self.started_ns,'status':'RUNNING_NOT_FINAL','scope':'UI_GESTURE_NO_MAVLINK_NO_AUTOMATIC_RETRY'})

    def wait(self, timeout=15):
        if self.finished:
            raise OperatorError('Gesture receipt already finalized')
        try:
            code=self.process.wait(timeout=timeout);status='EXITED'
        except subprocess.TimeoutExpired:
            exclusive(self.directory/f'timeout-{uuid.uuid4().hex}.json',{'atUTC':utc(),'PID':self.process.pid,'status':'GESTURE_CLIENT_TIMEOUT_NOT_CANCELLED','timeoutSeconds':timeout,'remoteGestureOutcome':'UNKNOWN','noRetry':True})
            raise OperatorError('Gesture client timed out; remote gesture is UNKNOWN, not retried/cancelled')
        self.out.close();self.err.close();self.finished=True
        result={'atUTC':utc(),'argv':self.argv,'exit':code,'status':status,'elapsedHostNs':time.monotonic_ns()-self.started_ns,
                'stdoutSHA256':sha((self.directory/'stdout.bin').read_bytes()),'stderrSHA256':sha((self.directory/'stderr.bin').read_bytes()),'noRetry':True}
        exclusive(self.directory/'receipt-final.json',result)
        if code:
            raise OperatorError(f'Gesture adb client exited {code}; see {self.directory}')
        return result


class AndroidOperator:
    def __init__(self, evidence_dir, expected_run, expected_generation):
        self.root=Path(evidence_dir);self.root.mkdir(parents=True,exist_ok=False)
        self.run,self.generation=expected_run,expected_generation
        if not all(re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',x)for x in (expected_run,expected_generation)):
            raise ValueError('Exact expected run/generation identifiers required')
        self.number=0;self.geometry={};self.geometry_source=None
        exclusive(self.root/'entry.json',{'atUTC':utc(),'serial':SERIAL,'package':PACKAGE,'expectedRun':self.run,'expectedGeneration':self.generation,
                  'helperSourceSHA256':sha(Path(__file__).read_bytes()),'contract':'EXPLICIT_CALLER_ACTIONS_ONLY_NO_MAVLINK_NO_SCENARIOS_NO_RETRIES','geometryPolicy':'INITIAL_UIAUTOMATOR_GEOMETRY_ONLY; never cached enabled/readiness state'})

    @classmethod
    def resume(cls, evidence_dir, expected_run, expected_generation):
        """Resume helper logging only, never resume a native session/authority."""
        root=Path(evidence_dir);entry=json.loads((root/'entry.json').read_text())
        if entry.get('expectedRun')!=expected_run or entry.get('expectedGeneration')!=expected_generation or entry.get('helperSourceSHA256')!=sha(Path(__file__).read_bytes()):
            raise OperatorError('Helper evidence/context/source mismatch')
        op=cls.__new__(cls);op.root=root;op.run=expected_run;op.generation=expected_generation
        op.number=max([int(p.name[:4])for p in root.iterdir()if p.is_dir()and re.match(r'^\d{4}-',p.name)]+[0]);op.geometry={};op.geometry_source=None
        cache=root/'initial-geometry.json'
        if cache.is_file():
            data=json.loads(cache.read_text());op.geometry={name:tuple(bounds)for name,bounds in data['geometry'].items()};op.geometry_source=data['sourceXML']
        exclusive(root/f'helper-resume-{uuid.uuid4().hex}.json',{'atUTC':utc(),'scope':'LOGGING_AND_GEOMETRY_ONLY_NO_DEVICE_ACTION_OR_AUTHORITY_RESTORE'})
        return op

    def _directory(self, label):
        self.number+=1
        p=self.root/f'{self.number:04d}-{label}-{uuid.uuid4().hex[:8]}'
        p.mkdir();return p

    def command(self, args, timeout=5, check=True):
        argv=[ADB,'-s',SERIAL,*map(str,args)];directory=self._directory('adb');started=time.monotonic_ns();at=utc()
        timed_out=False
        try:
            p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
            out,err,code=p.stdout,p.stderr,p.returncode
        except subprocess.TimeoutExpired as e:
            out,err,code=raw(e.stdout),raw(e.stderr),None;timed_out=True
        except OSError as e:
            out,err,code=b'',str(e).encode(),None;timed_out=False
        (directory/'stdout.bin').open('xb').write(out);(directory/'stderr.bin').open('xb').write(err)
        result={'atUTC':at,'argv':argv,'exit':code,'timedOut':timed_out,'timeoutSeconds':timeout,'elapsedHostNs':time.monotonic_ns()-started,
                'stdoutBytes':len(out),'stderrBytes':len(err),'stdoutSHA256':sha(out),'stderrSHA256':sha(err),'noRetry':True}
        exclusive(directory/'receipt.json',result)
        if timed_out or code is None or check and code!=0:
            raise OperatorError(f'ADB command failed/timeout; retained at {directory}; no retry')
        return out,err,code,directory

    def focus(self):
        out,_,_,_=self.command(['shell','dumpsys','activity','activities'],timeout=3)
        lines=[x.strip()for x in out.decode(errors='replace').splitlines()if 'mResumedActivity:'in x or 'topResumedActivity='in x]
        if not any(ACTIVITY in line or PACKAGE+'/'+PACKAGE+'.CockpitActivity' in line for line in lines):
            raise OperatorError('ControlActivity is not the observed resumed app')
        windows,_,_,_=self.command(['shell','dumpsys','window'],timeout=3)
        focused=[x.strip()for x in windows.decode(errors='replace').splitlines()if 'mCurrentFocus='in x]
        if not any(PACKAGE in line for line in focused):
            raise OperatorError('A different/system window currently owns focus')
        return lines

    def state(self, allow_absent=False, require_context=True):
        out,err,code,_=self.command(['shell','run-as',PACKAGE,'cat','files/latest-state.json'],timeout=3,check=False)
        if code:
            if allow_absent and b'No such file' in out+err:
                return None
            raise OperatorError('Native checkpoint unreadable; see logged command')
        try:
            state=json.loads(out)
        except Exception as e:
            raise OperatorError('Native checkpoint JSON invalid')from e
        if require_context and (state.get('run')!=self.run or state.get('generation')!=self.generation):
            raise OperatorError('Native checkpoint is a foreign/old run or generation')
        return state

    def wait_state(self, predicate, timeout=10, interval=.25):
        deadline=time.monotonic()+timeout;observations=0
        while True:
            state=self.state(allow_absent=True,require_context=False);observations+=1
            if state is not None and state.get('run')==self.run and state.get('generation')==self.generation and predicate(state):
                exclusive(self.root/f'wait-pass-{uuid.uuid4().hex}.json',{'atUTC':utc(),'observations':observations,'state':state,'predicate':'CALLER_SUPPLIED_NOT_A_SCENARIO_OR_ACTION'})
                return state
            if time.monotonic()>=deadline:
                exclusive(self.root/f'wait-timeout-{uuid.uuid4().hex}.json',{'atUTC':utc(),'observations':observations,'lastState':state,'status':'PREDICATE_NOT_OBSERVED','noActionSent':True})
                raise OperatorError('Bounded state wait expired; no action automatically sent')
            time.sleep(min(interval,max(0,deadline-time.monotonic())))

    def screenshot(self):
        out,_,_,directory=self.command(['exec-out','screencap','-p'],timeout=3)
        if not out.startswith(b'\x89PNG\r\n\x1a\n'):
            raise OperatorError('Screenshot is not PNG')
        path=directory/'screen.png';path.open('xb').write(out)
        return path

    def dump_ui(self, timeout=3):
        self.focus();remote='/sdcard/aeris-control01-ui-'+uuid.uuid4().hex+'.xml'
        self.command(['shell','uiautomator','dump','--compressed',remote],timeout=timeout)
        out,_,_,directory=self.command(['exec-out','cat',remote],timeout=3)
        ET.fromstring(out);path=directory/'ui.xml';path.open('xb').write(out)
        return out,path

    def cache_initial_geometry(self):
        state=self.state(allow_absent=True,require_context=False)
        if state is not None and not state.get('closed',False):
            raise OperatorError('Cache only before CONNECT/no session or after fully closed prior run')
        xml,path=self.dump_ui(timeout=3)
        names={'control01-'+x for x in BUTTONS}|STICKS
        self.geometry={name:unique_node(xml,name,require_enabled=False)for name in names}
        self.geometry_source=str(path)
        exclusive(self.root/'initial-geometry.json',{'atUTC':utc(),'sourceXML':str(path),'geometry':self.geometry,'cachedStateOrEnabledFlags':False})
        return dict(self.geometry)

    def _native_ready(self, description, state):
        f=state.get('flight',{});a=state.get('input',{});consent=a.get('consent')is True;armed=f.get('armed')is True;mode=f.get('mode');landed=f.get('landedState')
        if state.get('closed')or state.get('firstFailure'):
            return False
        key=description.removeprefix('control01-')
        checks={'consent':state.get('preflightReady')is True and not consent and state.get('releaseState')!='WAIT_HOLD',
                'guided':consent and not armed,'arm':consent and not armed and mode==4 and state.get('preflightReady')is True,
                'confirm-home':consent and armed and f.get('postArmHomePending')is True and f.get('homeObservedAtMs',-1)>f.get('armObservedAtMs',2**63),
                'takeoff':consent and armed and landed==1 and f.get('homeConfirmed')is True,
                'loiter':consent and armed and mode==4 and landed==2 and f.get('hoverObservedMs',0)>=1000,
                'hold':consent and armed and landed==2,'land':consent and armed and not state.get('rcOverrideActiveLocally'),
                'close':not armed and landed==1,'connect':False}
        return bool(checks.get(key,False))

    def _fresh_state(self, max_age_ms=1500):
        state=self.state();out,_,_,_=self.command(['shell','cat','/proc/uptime'],timeout=2)
        now_ms=int(Decimal(out.split()[0].decode())*1000)
        f=state.get('flight',{})
        for field in ('heartbeatMs','positionMs'):
            value=f.get(field,-1)
            if type(value)is not int or value<0 or now_ms-value<0 or now_ms-value>max_age_ms:
                raise OperatorError('Native AP observation stale/invalid before UI action: '+field)
        return state

    def inspect_cached_action(self, description, predicate=lambda s:True):
        if description not in self.geometry or description not in {'control01-'+x for x in BUTTONS}:
            raise OperatorError('Explicit pre-CONNECT geometry cache required for this button')
        self.focus();state=self._fresh_state()
        if not self._native_ready(description,state)or not predicate(state):
            raise OperatorError('Current native readiness refuses the requested button')
        screen=self.screenshot();ticket=Inspection(description,str(screen),sha(screen.read_bytes()),time.monotonic_ns(),self.geometry[description],self.run,self.generation,sha(json.dumps(state,sort_keys=True).encode()))
        exclusive(screen.parent/'inspection.json',{'description':ticket.description,'geometrySource':self.geometry_source,'state':state,'ticket':ticket.__dict__,'requiresCallerScreenshotReview':True,'tapSent':False})
        return ticket

    def commit_cached_tap(self, ticket, *, screenshot_reviewed, predicate=lambda s:True, max_review_age_seconds=5):
        if not screenshot_reviewed or ticket.run!=self.run or ticket.generation!=self.generation or ticket.description not in self.geometry or ticket.bounds!=self.geometry[ticket.description]:
            raise OperatorError('Caller screenshot review and exact context are required')
        age=time.monotonic_ns()-ticket.created_mono_ns
        if not 0<max_review_age_seconds<=10 or age<0 or age>max_review_age_seconds*1e9 or not Path(ticket.screenshot).resolve().is_relative_to(self.root.resolve()) or sha(Path(ticket.screenshot).read_bytes())!=ticket.screenshot_sha256:
            raise OperatorError('Screenshot inspection expired or bytes changed; no tap sent')
        marker=Path(ticket.screenshot).parent/'tap-consumed.json'
        if marker.exists():
            raise OperatorError('One-shot tap ticket already consumed; no retry')
        self.focus();state=self._fresh_state()
        if not self._native_ready(ticket.description,state)or not predicate(state):
            raise OperatorError('Native button readiness changed after screenshot review; no tap sent')
        left,top,right,bottom=ticket.bounds
        exclusive(marker,{'atUTC':utc(),'description':ticket.description,'center':[(left+right)//2,(top+bottom)//2],'status':'INTENT_RECORDED_BEFORE_ONE_TAP','automaticRetry':False})
        return self.command(['shell','input','tap',(left+right)//2,(top+bottom)//2],timeout=3)

    def tap_fresh_ui(self, description, predicate=lambda s:True, timeout=2):
        if description not in {'control01-'+x for x in BUTTONS}:
            raise OperatorError('Unknown button')
        xml,_=self.dump_ui(timeout=timeout);bounds=unique_node(xml,description,True,True)
        self.focus();state=self._fresh_state()
        if not self._native_ready(description,state)or not predicate(state):
            raise OperatorError('Native readiness refuses current UI node')
        left,top,right,bottom=bounds
        return self.command(['shell','input','tap',(left+right)//2,(top+bottom)//2],timeout=3)

    def start_stick_hold(self, description, horizontal, up, duration_ms):
        if description not in STICKS or description not in self.geometry or not(-1<=horizontal<=1 and -1<=up<=1)or not(1000<=duration_ms<=10000):
            raise OperatorError('Bounded stick hold and explicit initial geometry required')
        self.focus();state=self._fresh_state();f=state.get('flight',{});a=state.get('input',{})
        if not(a.get('consent')is True and f.get('mode')==5 and f.get('armed')is True and f.get('landedState')==2 and f.get('homeConfirmed')is True):
            raise OperatorError('Stick gesture requires actual LOITER airborne authority/Home observations')
        screen=self.screenshot();left,top,right,bottom=self.geometry[description];radius=.32*min(right-left,bottom-top)
        x=round((left+right)/2+horizontal*radius);y=round((top+bottom)/2-up*radius)
        directory=self._directory('gesture');argv=[ADB,'-s',SERIAL,'shell','input','touchscreen','swipe',str(x),str(y),str(x),str(y),str(duration_ms)]
        exclusive(directory/'gesture-plan.json',{'atUTC':utc(),'description':description,'bounds':self.geometry[description],'geometrySource':self.geometry_source,'freshScreenshot':str(screen),'horizontal':horizontal,'up':up,'durationMs':duration_ms,'inputMeaning':'REAL_INJECTED_ANDROID_MOTION_EVENT_HELD_POINTER_NOT_PHYSICAL_HID','state':state})
        return Gesture(self,argv,directory)

    def export_private(self, relative_path):
        if not re.fullmatch(r'files(?:/[A-Za-z0-9_.:-]+)*',relative_path)or '..' in relative_path.split('/'):
            raise OperatorError('Private export must be a safe files/ descendant')
        out,_,_,directory=self.command(['exec-out','run-as',PACKAGE,'tar','-cf','-','--',relative_path],timeout=10)
        path=directory/'private.tar';path.open('xb').write(out)
        exclusive(directory/'export.json',{'atUTC':utc(),'relativePath':relative_path,'archiveSHA256':sha(out),'bytes':len(out),'integrityAcceptance':'NOT_INFERRED_FROM_EXPORT'})
        return path
