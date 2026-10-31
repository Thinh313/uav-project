"""Execute actual controller top-level with bounded, explicitly synthetic IO.

Only the R assignment is AST-rebound. No controller branch, command argument,
cleanup block or exception handler is rewritten. Local Python worker threads run
actual bootstrap/observer functions; all sockets/processes are in-memory fakes.
"""
import sys
sys.dont_write_bytecode = True
import ast
import base64
import builtins
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import threading
import time
import types
from unittest.mock import patch

ROOT05 = Path(__file__).resolve().parents[3]
BASE05 = Path(__file__).with_name("runtime04.py")
SPEC05 = importlib.util.spec_from_file_location("frozen_bootstrap04_for05", Path(__file__).with_name("bootstrap04.py"))
HELPER05 = importlib.util.module_from_spec(SPEC05)
SPEC05.loader.exec_module(HELPER05)
REAL_THREAD05, REAL_SLEEP05, REAL_MONO05 = threading.Thread, time.sleep, time.monotonic
REAL_OPEN05, REAL_FSYNC05, REAL_SHA05 = builtins.open, os.fsync, hashlib.sha256
CID05, RUN05 = "a"*64, "s"+"5"*20
BINARY05 = b"NONEXECUTABLE_LIFECYCLE05_BINARY_FIXTURE"
BINARY_SHA05 = "011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482"


class ForbiddenHostAccess05(BaseException):
    pass


class InjectedFatal05(BaseException):
    """Declared fatal sentinel, never an actual host access attempt."""
    pass


class RootBinding05(ast.NodeTransformer):
    def __init__(self): self.changed = []
    def visit_Assign(self, node):
        if any(isinstance(t, ast.Name) and t.id == "R" for t in node.targets):
            expected = "Path(__file__).resolve().parents[3]"
            if ast.unparse(node.value) != expected:
                raise AssertionError("UNEXPECTED_ROOT_BINDING")
            self.changed.append({"line": node.lineno, "old": expected, "new": "Path(__mock_root05)"})
            node.value = ast.copy_location(ast.Call(func=ast.Name(id="Path", ctx=ast.Load()), args=[ast.Name(id="__mock_root05", ctx=ast.Load())], keywords=[]), node.value)
        return node


class File05:
    def __init__(self, rig, file, path, mode): self.rig,self.file,self.path,self.mode=rig,file,path,mode
    def __getattr__(self, key): return getattr(self.file,key)
    def __enter__(self): return self
    def __exit__(self,*args): self.close()
    def write(self, value):
        if self.rig.flag("closure_write") and self.path.name=="closure.json":
            self.rig.event("FAULT_CLOSURE_WRITE");raise OSError("CLOSURE_WRITE_FAILURE05")
        return self.file.write(value)
    def close(self):
        self.rig.event("FILE_CLOSE",file=self.path.name)
        self.file.close()


class Message05:
    def __init__(self, mid, **values): self.mid=mid;self.__dict__.update(values)
    def get_type(self): return "BAD_DATA" if self.mid==-1 else "MOCK_LIFECYCLE"
    def get_srcSystem(self): return 42
    def get_srcComponent(self): return 1
    def get_msgId(self): return self.mid


class Socket05:
    def __init__(self, rig, kind): self.rig,self.kind,self.closed,self.reads=rig,kind,False,0;self.ready=threading.Event()
    def __enter__(self): return self
    def __exit__(self,*args):self.close()
    def setsockopt(self,*args):pass
    def bind(self,address):self.rig.event("BIND_ONLY",address=list(address))
    def settimeout(self,value):self.timeout=value
    def fileno(self):return -1 if self.closed else 500
    def send(self,*args):raise ForbiddenHostAccess05("NO_TX_ALLOWED05")
    sendall=send
    def recv(self, bound):
        self.reads+=1
        if self.kind=="bootstrap" and self.reads==1 and self.rig.flag("bootstrap_eof"):
            if self.rig.flag("oom"):self.rig.ap_running=False;self.rig.oom=True
            if self.rig.flag("missing_container"):self.rig.ap_running=False;self.rig.container_missing=True
            self.rig.event("BOOTSTRAP_EOF_OBSERVED");return b""
        if self.reads==1:
            self.rig.event("SOCKET_DATA",kind=self.kind);return b"\xfdSYNTHETIC_LIFECYCLE_ONLY"
        self.ready.set()
        for _ in range(1000):
            if self.closed or self.rig.ns.get("stopping"):
                raise OSError("MOCK_SOCKET_CLOSED")
            REAL_SLEEP05(.001)
            raise socket.timeout("PASSIVE_IDLE05")
        raise ForbiddenHostAccess05("MOCK_READ_BOUND05")
    def shutdown(self,*args):
        self.rig.event("SOCKET_SHUTDOWN",kind=self.kind)
        if self.rig.flag("socket_cleanup")and self.kind!="bind":
            raise OSError("SOCKET_SHUTDOWN_FAILURE05")
        if self.closed:raise OSError("ALREADY_CLOSED05")
    def close(self):
        self.rig.event("SOCKET_CLOSE",kind=self.kind)
        self.closed=True
        if self.rig.flag("socket_cleanup")and self.kind!="bind":
            raise OSError("SOCKET_CLOSE_FAILURE05")


class Peer05:
    pid=55005
    def __init__(self,rig):self.rig,self.alive=rig,True
    def poll(self):
        if self.rig.flag("observer_then_poll") and self.rig.ns.get("obs_error"):
            self.rig.event("SECONDARY_PEER_POLL_FAILURE",knownObserver=self.rig.ns.get("obs_error"));raise OSError("SECONDARY_POLL_FAILURE05")
        return None if self.alive else 0
    def terminate(self):
        self.rig.event("PEER_TERMINATE")
        if self.rig.flag("peer_cleanup"):raise OSError("TERMINATE_FAILURE05")
        self.alive=False
    def wait(self,timeout):
        self.rig.event("PEER_WAIT",timeout=timeout)
        if self.rig.flag("peer_cleanup"):raise subprocess.TimeoutExpired("MOCK_PEER",timeout)
        return 0
    def kill(self):
        self.rig.event("PEER_KILL");self.alive=False
        if self.rig.flag("peer_cleanup"):raise OSError("KILL_REPORTED_FAILURE05")


class Thread05:
    def __init__(self,rig,target,daemon=False,**kwargs):
        self.rig,self.target,self.kind=rig,target,target.__name__;self.done=threading.Event()
        def work():
            try:target()
            except BaseException as e:rig.worker_errors.append({"kind":self.kind,"error":repr(e)})
            finally:self.done.set()
        self.thread=REAL_THREAD05(target=work,daemon=True)
    def start(self):
        self.rig.event("THREAD_START",kind=self.kind)
        if self.kind=="observe" and self.rig.flag("observer_start"):
            raise OSError("OBSERVER_THREAD_START_FAILURE05")
        self.thread.start()
        # Deterministic injected scheduler: let actual first recv/decode or
        # actual caught failure happen before returning to the caller.
        until=REAL_MONO05()+2
        while REAL_MONO05()<until:
            sockets=[s for s in self.rig.sockets if s.kind==("observer"if self.kind=="observe"else"bootstrap")]
            if self.done.is_set() or any(s.ready.is_set()for s in sockets):return
            REAL_SLEEP05(.001)
        raise ForbiddenHostAccess05("THREAD_FIRST_PROGRESS_TIMEOUT05")
    def join(self,timeout):
        self.rig.event("THREAD_JOIN",kind=self.kind)
        self.thread.join(min(timeout,.3))
    def is_alive(self):return self.thread.is_alive()


class Rig05:
    def __init__(self, scenario, root, controller):
        self.scenario,self.root,self.controller=scenario,root,controller
        self.events=[];self.files=[];self.sockets=[];self.threads=[];self.peers=[];self.worker_errors=[]
        self.ns={};self.now=100.;self.sleeps=0;self.disk_calls=0;self.connects=[];self.ap_running=False;self.ap_started=False;self.container_missing=False;self.oom=False;self.stdout=io.StringIO();self.lock=threading.RLock()
    def flag(self,name):return bool(self.scenario.get("flags",{}).get(name,False))
    def event(self,name,**values):
        with self.lock:
            if len(self.events)>=2048:raise ForbiddenHostAccess05("EVENT_BOUND05")
            self.events.append({"n":len(self.events)+1,"name":name,"mockMono":self.now,**values})
    def open(self,file,mode="r",*args,**kwargs):
        if isinstance(file,int):raise ForbiddenHostAccess05("UNEXPECTED_FD_OPEN05")
        p=Path(file).resolve();write=any(c in mode for c in"wax+")
        allowed=p.is_relative_to(self.root) or(not write and p==self.controller)
        if not allowed:raise ForbiddenHostAccess05("OUTSIDE_MOCK_ROOT_IO05:"+str(p))
        if write and self.flag("closure_open")and p.name=="closure.json":self.event("FAULT_CLOSURE_OPEN");raise OSError("CLOSURE_OPEN_FAILURE05")
        if write and self.flag("prestop_capture")and p.name=="prestop-diagnostics04.json":self.event("FAULT_PRESTOP_OPEN");raise OSError("PRESTOP_CAPTURE_FAILURE05")
        f=File05(self,REAL_OPEN05(file,mode,*args,**kwargs),p,mode)
        self.files.append(f);return f
    def fsync(self,fd):
        selected=next((f for f in reversed(self.files)if not f.closed and f.fileno()==fd),None)
        if selected is None:raise ForbiddenHostAccess05("UNTRACKED_FSYNC05")
        if self.flag("closure_fsync")and selected.path.name=="closure.json":self.event("FAULT_CLOSURE_FSYNC");raise OSError("CLOSURE_FSYNC_FAILURE05")
        REAL_FSYNC05(fd)
    def digest(self,data=b""):
        if data==BINARY05:
            return types.SimpleNamespace(hexdigest=lambda:BINARY_SHA05)
        return REAL_SHA05(data)
    def disk(self,path):
        if Path(path)!=self.root:raise ForbiddenHostAccess05("UNEXPECTED_DISK_ROOT05")
        self.disk_calls+=1
        free=31*2**30
        if self.flag("resource")and self.disk_calls>1:free=20*2**30
        return types.SimpleNamespace(free=free,total=460*2**30,used=400*2**30)
    def sleep(self,amount):
        self.now+=amount;self.sleeps+=1
        if self.flag("deadline")or self.flag("pending_stale"):
            self.now+=901
        if self.sleeps>12:raise ForbiddenHostAccess05("MAIN_LOOP_BOUND05")
        REAL_SLEEP05(.001)
    def inspect_bytes(self,wrong=False):
        if self.container_missing:raise OSError("OWNED_CONTAINER_MISSING05")
        return json.dumps([{"Id":"c"*64 if wrong else CID05,"Name":"/aeris-integration03","RestartCount":0,"Config":{"Labels":{"aeris.task":"integration03","aeris.run":RUN05}},"State":{"Running":self.ap_running,"Status":"running"if self.ap_running else"exited","Pid":17 if self.ap_running else 0,"ExitCode":137 if self.oom else 0,"OOMKilled":self.oom,"Paused":False,"Restarting":False,"Error":"","StartedAt":"2026-10-20T01:00:00Z","FinishedAt":"0001-01-01T00:00:00Z"}}]).encode()
    def probe_runner(self,args,timeout,limit):
        self.event("READONLY_PROBE",args=list(args))
        if args[:2]==["docker","inspect"]:return self.inspect_bytes(self.flag("wrong_identity"))
        if args[:2]==["docker","logs"]:
            if self.flag("prestop_capture"):raise OSError("LOG_PROBE_FAILURE05")
            return b"SYNTHETIC bounded AP console\n"
        if args[:4]!=["docker","exec",CID05,"cat"]:raise ForbiddenHostAccess05("UNEXPECTED_PROBE_COMMAND05")
        family=6 if args[-1].endswith("tcp6")else 4;addr="0"*(32 if family==6 else 8)
        return("sl local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode\n0: "+addr+":1680 "+addr+":0000 0A 00000000:00000000 00:00000000 00000000 0 0 1\n").encode()
    def run(self,args,**kwargs):
        self.event("SUBPROCESS_RUN",args=list(args))
        if args==["docker","inspect","aeris-integration03"]:return types.SimpleNamespace(returncode=1)
        raise ForbiddenHostAccess05("UNEXPECTED_SUBPROCESS_RUN05")
    def check_output(self,args,**kwargs):
        self.event("COMMAND",args=list(args))
        if args[:2]==["docker","run"]:
            assert not self.ap_started;self.ap_running=self.ap_started=True
            requested=self.root/"evidence/integration03-runtime/runs"/RUN05/"stop-request.json"
            if not self.flag("deadline"):requested.write_text('{"synthetic":true}')
            return CID05+"\n"
        if args==["docker","inspect",CID05]:return self.inspect_bytes().decode()
        if args==["docker","logs",CID05]:
            if self.flag("fatal"):
                self.event("INJECTED_FATAL_BOUNDARY");raise InjectedFatal05("INJECTED_FATAL_BOUNDARY05")
            if self.flag("boot_then_logs")and self.ns.get("bootstrapError"):
                self.event("SECONDARY_LOGS_FAILURE",knownBootstrap=self.ns["bootstrapError"]);raise OSError("SECONDARY_LOGS_FAILURE05")
            return"SERIAL5 on TCP port 5767"
        if args==["docker","stop","--time","3",CID05]:
            if self.container_missing:raise OSError("OWNED_CONTAINER_MISSING05")
            self.ap_running=False
            if self.flag("stop_failure"):raise OSError("STOP_REPORTED_FAILURE05")
            return CID05
        raise ForbiddenHostAccess05("UNEXPECTED_COMMAND05:"+repr(args))
    def popen(self,args,**kwargs):
        self.event("PEER_POPEN",args=list(args))
        if args!=["node","planning/integration03/runtime/peers.mjs",RUN05,"nominal"]:raise ForbiddenHostAccess05("UNEXPECTED_POPEN05")
        if self.flag("popen"):raise OSError("PEER_START_FAILURE05")
        p=Peer05(self);self.peers.append(p);return p
    def connect(self,address,timeout):
        if address not in(("127.0.0.1",5940),("127.0.0.1",5941)):raise ForbiddenHostAccess05("UNEXPECTED_CONNECT05")
        self.connects.append(list(address));kind="bootstrap"if address[1]==5941 else"observer";self.event("CONNECT",kind=kind)
        if kind=="bootstrap"and self.flag("refused"):raise ConnectionRefusedError("BOOTSTRAP_REFUSED05")
        s=Socket05(self,kind);self.sockets.append(s);return s
    def socket(self,*args,**kwargs):
        s=Socket05(self,"bind");self.sockets.append(s);return s
    def thread(self,*args,**kwargs):
        t=Thread05(self,*args,**kwargs);self.threads.append(t);return t
    def oracle_spec(self,name,path):
        if name!="m97"or Path(path)!=self.root/"pilot/apstream40/oracle-v2.py":raise ForbiddenHostAccess05("UNEXPECTED_MODULE05")
        rig=self
        class Parser:
            def __init__(self,*args):pass
            def parse_buffer(self,data):
                if rig.flag("observer_crc")or rig.flag("observer_then_poll"):return[Message05(-1)]
                armed=rig.flag("pending_stale")
                return[Message05(0,base_mode=128 if armed else 0,custom_mode=4),Message05(245,landed_state=2 if armed else 1),Message05(33,lat=108540000,lon=1068070000,relative_alt=0)]
        return types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda m:setattr(m,"MAVLink",Parser)))
    def helper_module(self):
        rig=self;m=types.ModuleType("bootstrap04")
        m.DockerProbe04=lambda cid,run:HELPER05.DockerProbe04(cid,run,rig.probe_runner)
        m.ReadinessJournal04=HELPER05.ReadinessJournal04;m.CID04=HELPER05.CID04
        m.bootstrap_stream04=lambda *a,**kw:HELPER05.bootstrap_stream04(*a,**kw,connector=rig.connect,clock=lambda:rig.now,sleep=rig.sleep)
        m.stop_owned04=lambda *a,**kw:HELPER05.stop_owned04(*a,**kw,clock=lambda:rig.now)
        return m


def execute05(controller_path, scenario, scratch_root):
    """Returns synthetic receipt; never writes operational evidence namespace."""
    controller=Path(controller_path).resolve();scratch=Path(scratch_root).resolve()
    if controller.parent!=BASE05.parent or controller.name not in("runtime04.py","runtime05.py"):
        raise AssertionError("CONTROLLER_PATH_BOUND05")
    allowed=[ROOT05/".local/integration03-lifecycle05"/role for role in("builder","qa")]
    if not any(scratch.is_relative_to(p)and scratch!=p for p in allowed):raise AssertionError("SCRATCH_BOUND05")
    if scratch.exists():raise AssertionError("NO_MOCK_REUSE05")
    scratch.mkdir(parents=True);rig=Rig05(copy.deepcopy(scenario),scratch,controller)
    for rel,data in {"runtime/sitl/arducopter":BINARY05,"planning/integration03/runtime/sitl.parm":b"# SYNTHETIC05\n","planning/integration03/runtime/peers.mjs":b"// never executed\n","native/native98/message-intervals-chan3.txt":b"0 1000000\n"}.items():
        p=scratch/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    e=scratch/"evidence/integration03-runtime";e.mkdir(parents=True)
    (e/"admission.json").write_text(json.dumps({"status":"PHASE_ADMITTED","allowedRuns":[RUN05],"minAdmissionBytes":29*2**30,"runtimeGuardBytes":21*2**30}))
    run_dir=e/"runs"/RUN05
    run_dir.mkdir(parents=True);(run_dir/"ap-state").mkdir()
    # A safe stop request tests the actual fresh-ground predicate; stale scenario
    # must remain pending and terminate only via the unchanged deadline instead.
    # Stopfile is introduced by the injected external fixture after APcreation,
    # never before the controller's existing-run/no-restart check.
    raw=controller.read_bytes();tree=ast.parse(raw.decode(),filename=str(controller));binding=RootBinding05();tree=binding.visit(tree);assert len(binding.changed)==1;ast.fix_missing_locations(tree)
    ns={"__file__":str(controller),"__name__":"__main__","__mock_root05":str(scratch)};rig.ns=ns;exit_code=0;exception=None
    original_runs=ROOT05/"evidence/integration03-runtime/runs"
    baseline_real_children=set(original_runs.iterdir())if original_runs.exists()else set()
    stack=contextlib.ExitStack()
    try:
        for obj,name,value in[(builtins,"open",rig.open),(io,"open",rig.open),(os,"fsync",rig.fsync),(hashlib,"sha256",rig.digest),(shutil,"disk_usage",rig.disk),(subprocess,"run",rig.run),(subprocess,"check_output",rig.check_output),(subprocess,"Popen",rig.popen),(socket,"socket",rig.socket),(socket,"create_connection",rig.connect),(socket,"getaddrinfo",lambda *a,**k:(_ for _ in()).throw(ForbiddenHostAccess05("REAL_DNS05"))),(threading,"Thread",rig.thread),(time,"monotonic",lambda:rig.now),(time,"monotonic_ns",lambda:int(rig.now*1e9)),(time,"sleep",rig.sleep),(signal,"signal",lambda *a:None),(importlib.util,"spec_from_file_location",rig.oracle_spec),(importlib.util,"module_from_spec",lambda spec:types.SimpleNamespace()),(sys,"argv",[str(controller),RUN05,"nominal"])]:stack.enter_context(patch.object(obj,name,value))
        stack.enter_context(patch.dict(sys.modules,{"bootstrap04":rig.helper_module()}))
        with contextlib.redirect_stdout(rig.stdout):
            try:exec(compile(tree,str(controller),"exec"),ns)
            except SystemExit as error:exit_code=error.code if isinstance(error.code,int)else 2
            except InjectedFatal05 as error:exception=repr(error);exit_code=1
            except Exception as error:exception=repr(error);exit_code=1
    finally:
        # Audit and force cleanup WHILE EVERY HOSTSIDE GUARD REMAINS PATCHED.
        # If a worker cannot quiesce, leave guards installed and abort this test
        # process; never restore real networking underneath an escaped worker.
        leaked_files=[f.path.name for f in rig.files if not f.closed]
        live_threads=[t.kind for t in rig.threads if t.is_alive()]
        live_peers=[p.pid for p in rig.peers if p.alive]
        live_sockets=[s.kind for s in rig.sockets if not s.closed]
        rig.ns["stopping"]=True
        for sock in rig.sockets:sock.closed=True
        for thread in rig.threads:
            if thread.thread.ident is not None:thread.thread.join(.5)
        escaped=[t.kind for t in rig.threads if t.is_alive()]
        if escaped:
            raise ForbiddenHostAccess05("CONTAINMENT_FAILED_GUARDS_REMAIN_INSTALLED05:"+repr(escaped))
        for f in rig.files:
            if not f.closed:f.file.close()
        stack.close()
    receipts={};receipt_errors={};partial_receipts={}
    for p in run_dir.glob("*.json"):
        if p.name=="stop-request.json":continue
        raw_receipt=p.read_bytes()
        try:
            if len(raw_receipt)>131072:raise ValueError("RECEIPT_BYTE_BOUND05")
            receipts[p.name]=json.loads(raw_receipt)
        except (ValueError,UnicodeError)as error:
            receipt_errors[p.name]=str(error)[:240]
            partial_receipts[p.name]={"size":len(raw_receipt),"sha256":REAL_SHA05(raw_receipt).hexdigest(),"prefixBase64":base64.b64encode(raw_receipt[:4096]).decode(),"prefixOnly":len(raw_receipt)>4096}
    result={"format":"aeris-lifecycle05-synthetic","scenario":scenario,"controllerSha256":REAL_SHA05(raw).hexdigest(),"rootBinding":binding.changed,"binaryDigestFixture":"sentinel bytes map to pinned digest; no firmware authenticity claim","oracleFixture":"synthetic HB/land/position only; no CRC/flight proof","threadScheduler":"real local Python workers; start waits actual first receive/decode/caughtfailure under fakes","exitCode":exit_code,"exception":exception,"stdout":rig.stdout.getvalue(),"events":rig.events,"receipts":receipts,"receiptErrors":receipt_errors,"partialReceipts":partial_receipts,"containmentGuardsRestoredAfterQuiescence":True,"bootstrapConnects":sum(x[1]==5941 for x in rig.connects),"socketTXBytes":0,"leaksBeforeHarnessCleanup":{"files":leaked_files,"threads":live_threads,"peers":live_peers,"sockets":live_sockets,"apRunning":rig.ap_running},"workerErrors":rig.worker_errors,"syntheticOnly":True}
    assert set(original_runs.iterdir())==baseline_real_children,"REAL_OPERATIONAL_RUN_NAMESPACE_CHANGED05"
    shutil.rmtree(scratch)
    result["scratchRemoved"]=str(scratch.relative_to(ROOT05))
    return result
