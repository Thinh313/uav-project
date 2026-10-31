"""Actual guard and deterministic socket doubles; never creates live services."""
from pathlib import Path
import json,struct,sys,time,hashlib
from types import SimpleNamespace
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(R/'planning/betaintegrated01/m1control01/host'))
from mock_tests import packet
from pilot.betaintegrated01.control05 import transport
from pilot.betaintegrated01.runtime02.journal import verify_journal


def run_case(base,name,post_byte_eof):
    out=base/name;out.mkdir();sockets=[];attempts=0;hub=None
    heartbeat=packet(0,struct.pack('<IBBBBB',5,2,3,129,4,3))
    class Sock:
        def __init__(self,*a,**k):self.role='none';self.closed=False;self.queue=[];self.sends=0;sockets.append(self)
        def setsockopt(self,*a):pass
        def settimeout(self,*a):pass
        def setblocking(self,*a):pass
        def bind(self,e):assert e==('127.0.0.1',5961);self.role='listener'
        def listen(self,*a):pass
        def connect(self,e):
            nonlocal attempts
            assert e==('127.0.0.1',5962);attempts+=1;self.role='passive'
            self.queue=[b'']if attempts<=2 else[b'0',b' ',b'0 ',b'0 '+heartbeat]+([b'']if post_byte_eof else[])
        def recv(self,n):
            if self.queue:return self.queue.pop(0)
            raise BlockingIOError()
        def send(self,b):self.sends+=1;raise AssertionError('NO_MAV_TX')
        def shutdown(self,*a):pass
        def close(self):self.closed=True
    class Selector:
        def __init__(self):self.keys={}
        def register(self,s,e,d):self.keys[s]=SimpleNamespace(fileobj=s,data=d,events=e)
        def unregister(self,s):del self.keys[s]
        def close(self):self.keys.clear()
        def select(self,t):
            time.sleep(.02)
            passive=[k for k in self.keys.values()if k.data=='passive'and k.fileobj.queue]
            if passive:return[(passive[0],1)]
            if hub.passive.frames and not post_byte_eof:hub.stop_event.set()
            return[]
    old_socket,old_selector=transport.socket.socket,transport.selectors.DefaultSelector
    transport.socket.socket=Sock;transport.selectors.DefaultSelector=Selector
    try:
        hub=transport.TransportHub(out,'run-'+name,'epoch-'+name,'boot-'+name,60);hub._run()
    finally:transport.socket.socket=old_socket;transport.selectors.DefaultSelector=old_selector
    assert attempts==3 and hub.passive_startup.eofs==2 and hub.passive_startup.bytes_seen==len(heartbeat)+6 and hub.passive.envelope.pairs==3
    assert all(s.closed and s.sends==0 for s in sockets)
    if post_byte_eof:
        assert hub.error=='RuntimeError:PASSIVE_AP_EOF_NEW_EPOCH_REQUIRED',hub.error
        assert hub.result['status']=='TRANSPORT_FAILED_RETAINED_PREFIX'and'commitAnchor'not in hub.result
    else:
        assert hub.error is None,hub.error
        verified=verify_journal(out/'transport-journal','run-'+name,'epoch-'+name,expected_commit=hub.result['commitAnchor'])
        assert verified['state']=='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'
    return {'case':name,'initialEOFRetries':2,'attempts':attempts,'bytesBeforeEOF':hub.passive_startup.bytes_seen,
            'status':'PASS','actualOSSocketObjectsCreated':0,'APStarts':0,'retainedResult':hub.result}


def main():
    base=R/'evidence/betaintegrated01-m1control02/host/startup05-mock01';base.mkdir()
    p=transport.PassiveStartup();p.begin(100);p.eof(101);p.receive(b'\xfd')
    try:p.eof(102);raise AssertionError('PARTIAL_BYTE_EOF_MUST_NOT_RETRY')
    except RuntimeError as e:assert str(e)=='PASSIVE_AP_EOF_NEW_EPOCH_REQUIRED'
    q=transport.PassiveStartup();q.begin(100)
    try:q.eof(20_000_000_101);raise AssertionError('UNBOUNDED_STARTUP')
    except RuntimeError as e:assert str(e)=='PASSIVE_INITIAL_OBSERVATION_TIMEOUT_20S'
    cases=[run_case(base,'initial-eof-then-valid',False),run_case(base,'initial-eof-valid-then-terminal-eof',True)]
    report={'status':'PASS_BUILDER_STARTUP_FAULTS','cases':cases,'pureCases':2,
            'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(R/'pilot/betaintegrated01/control05').glob('*.py')},
            'actualOSSocketObjectsCreated':0,'APStarts':0,'guards':'actual15s each; threshold/prime unchanged'}
    (base/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'scriptedCases':2,'pureCases':2}))
if __name__=='__main__':main()
