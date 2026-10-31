"""Real filesystem/15s guard, scripted socket/selector doubles, zero live IO."""
from pathlib import Path
import json
import struct
import sys
import time
import threading
from types import SimpleNamespace
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
from mock_tests import packet
from pilot.betaintegrated01.control01 import transport
from pilot.betaintegrated01.runtime02.journal import verify_journal
from pilot.betaintegrated01.runtime02.frame_adapter import FrameAdapter,SERVO
from pilot.betaintegrated01.runtime.physics import Model,profile


def main():
    out=R/'evidence/betaintegrated01-m1control01/host/hub-mock02';out.mkdir()
    calls=[];sockets=[];selector=None;hub=None;adapter_ready=threading.Event()
    native_bytes=packet(0,struct.pack('<IBBBBB',0,6,8,0,4,3),system=255,component=190)
    passive_bytes=packet(0,struct.pack('<IBBBBB',5,2,3,129,4,3),seq=0)
    passive_bytes+=packet(33,struct.pack('<IiiiihhhH',1000,108540000,1068070000,13000,3000,0,0,0,0),seq=1)
    passive_bytes+=packet(245,bytes([0,2]),seq=2)

    class FakeSocket:
        def __init__(self,*a,**k):self.role='unset';self.closed=False;self.raw=[];self.sends=[];sockets.append(self)
        def setsockopt(self,*a):pass
        def settimeout(self,*a):pass
        def setblocking(self,*a):pass
        def bind(self,endpoint):assert endpoint==('127.0.0.1',5961);self.role='listener'
        def listen(self,*a):pass
        def connect(self,endpoint):
            if endpoint==('127.0.0.1',5962):self.role='passive';self.raw=[passive_bytes]
            elif endpoint==('127.0.0.1',5963):self.role='upstream'
            else:raise AssertionError('FOREIGN_ENDPOINT')
        def accept(self):
            child=FakeSocket();child.role='native';child.raw=[native_bytes]
            return child,('127.0.0.1',45010)
        def recv(self,n):
            assert not self.closed
            if not self.raw:raise BlockingIOError()
            raw=self.raw.pop(0);assert len(raw)<=n;return raw
        def send(self,body):
            assert self.role!='passive','PASSIVE_MUST_NEVER_TRANSMIT'
            assert not self.closed;self.sends.append(bytes(body));calls.append((self.role,bytes(body)))
            return len(body)
        def shutdown(self,*a):pass
        def close(self):self.closed=True

    class FakeSelector:
        def __init__(self):self.keys={};self.step=0
        def register(self,sock,events,data):self.keys[sock]=SimpleNamespace(fileobj=sock,events=events,data=data)
        def get_key(self,sock):
            if sock not in self.keys:raise KeyError(sock)
            return self.keys[sock]
        def modify(self,sock,events,data):self.register(sock,events,data)
        def unregister(self,sock):
            if sock not in self.keys:raise KeyError(sock)
            del self.keys[sock]
        def close(self):self.keys.clear()
        def select(self,timeout):
            time.sleep(.01)
            if not adapter_ready.is_set():return[]
            self.step+=1
            roles={k.data:k for k in self.keys.values()}
            if self.step==1:return[(roles['listener'],1)]
            if self.step==2:return[(roles['native'],1)]
            if self.step==3:return[(roles['passive'],1)]
            if self.step==4:
                (out/'cut-request.json').write_text(json.dumps({'run':'rhub','epoch':'ehub','boot':'bhub',
                      'action':'CUT_NATIVE_LINK','nonce':'n1','hostNs':time.monotonic_ns()}));return[]
            if self.step==5:
                assert hub.state.cut_latched
                return[(roles['listener'],1)]
            hub.stop_event.set();return[]

    old_socket,old_selector=transport.socket.socket,transport.selectors.DefaultSelector
    transport.socket.socket=FakeSocket;transport.selectors.DefaultSelector=FakeSelector
    try:
        hub=transport.TransportHub(out,'rhub','ehub','bhub',60)
        started=time.monotonic_ns();hub.start()
        adapter=FrameAdapter(out/'journal','rhub','ehub',Model(profile()),max_frames=32)
        wait_until=time.monotonic()+5
        while not hub.ready.wait(.1):
            adapter.journal.guard.check()
            assert time.monotonic()<wait_until and hub.error is None
        adapter.event('AFTER_BOTH_REAL_GUARDS_PRIMED',{'bothReal':True})
        for frame in range(2):
            adapter.receive(SERVO.pack(18458,1200,frame,*([1000]*16)),('127.0.0.1',45011),lambda body:len(body),
                            clock_read=lambda:{'id':1,'hostReceiveNs':time.monotonic_ns(),'offsetLowNs':0,'offsetHighNs':10})
        fdm=adapter.close()
        adapter_ready.set();hub.thread.join(4);assert not hub.thread.is_alive()
        elapsed=time.monotonic_ns()-started
        fdm_cold=verify_journal(out/'journal','rhub','ehub',expected_commit=fdm['commitAnchor'])
        assert fdm_cold['frames']==2 and fdm_cold['stageRows']==2
        assert adapter.journal.guard.prime_receipt['elapsedRealMonotonicNs']>=15000000000
        assert hub.journal.guard.prime_receipt['elapsedRealMonotonicNs']>=15000000000
        assert elapsed<25_000_000_000,'PRIMING_WAS_NOT_CONCURRENT'
    finally:
        transport.socket.socket=old_socket;transport.selectors.DefaultSelector=old_selector
    assert hub.error is None,hub.error
    assert elapsed>=15_000_000_000 and hub.state.cut_latched
    assert calls==[('upstream',native_bytes)]
    assert all(not s.sends for s in sockets if s.role=='passive')
    assert all(s.closed for s in sockets)
    assert hub.passive.latest['GLOBAL_POSITION_INT']['relativeAltitudeMm']==3000
    result=verify_journal(out/'transport-journal','rhub','ehub',expected_commit=hub.result['commitAnchor'])
    assert result['state']=='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'
    report={'status':'PASS_CONCURRENT_REAL15S_FDM_HUB_GUARDS_MOCK_NETWORK','realPrimeAndCaseNs':elapsed,
            'nativeUnmodifiedBytesForwarded':len(native_bytes),'passiveApplicationTXBytes':0,
            'cutLatched':True,'reconnectRejected':True,'ownedSocketsClosed':len(sockets),
            'actualOSSocketObjectsCreated':0,'APStarts':0,'AndroidStarts':0,
            'FDMCold':fdm_cold,'FDMPriming':adapter.journal.guard.prime_receipt,'HubPriming':hub.journal.guard.prime_receipt,'coldJournal':result,'snapshot':hub.passive.snapshot()}
    (out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'realPrimeSeconds':elapsed/1e9,'fakeSocketCount':len(sockets)}))


if __name__=='__main__':main()
