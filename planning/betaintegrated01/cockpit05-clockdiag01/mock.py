"""Synthetic in-memory WAL pauses + real tiny FileIO diagnostics; no AP/runtime starts."""
from pathlib import Path
from importlib import import_module
import hashlib,json,os,shutil,struct,time
R=Path(__file__).resolve().parents[3]
H='planning.betaintegrated01.cockpit05-clockdiag01'
D=import_module(H+'.diagnostics');A=import_module(H+'.frame_adapter')
JournalError=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal').JournalError
E=R/'evidence/betaintegrated01-cockpit05-clockdiag01'


class MockGuard:
    def check(self,n=0):return 19*2**30


class MemoryJournal:
    """Only the group state/order seam; rows are not actual durable WAL records."""
    def __init__(self,pause=False,unknown=False):self.pause=pause;self.frames=0;self.phase='BETWEEN';self.rows=[];self.send_called=False;self.guard=MockGuard();self.closed=False;self.failed=False
    def record_frame(self,frame,raw,compute,send):
        self.rows.append(('RX',frame,raw));self.phase='RX';intent=compute(raw);self.rows.append(('INTENT',frame,intent))
        if self.pause:time.sleep(.287)
        self.phase='INTENT_DURABLE';self.send_called=True
        try:result=send(intent)
        except Exception as e:self.rows.append(('UNKNOWN',frame,type(e).__name__));raise JournalError('SEND_OUTCOME_UNKNOWN')from e
        assert result==len(intent);self.rows.append(('SENT',frame,result));self.frames+=1;self.phase='BETWEEN'
    def append_stage(self,frame,row):self.rows.append(('STAGE',frame,row))
    def abort(self,reason):self.failed=True;self.failure=reason


class Model:
    def __init__(self):self.t=0;self.calls=0
    def step(self,pwm,dt):self.t+=dt;self.calls+=1;return {'timestamp':self.t,'syntheticMockOnly':True}


def build_adapter(root,pause=False):
    root.mkdir();adapter=object.__new__(A.FrameAdapter);adapter.root=root/'journal';adapter.model=Model();adapter.max_frames=1;adapter.peer=None;adapter.frames=adapter.stage_rows=0;adapter.current=None;adapter.origin_ns=time.monotonic_ns();adapter.failed=adapter.closed=False;adapter.first_rx=adapter.last_rx=None;adapter.diagnostic_io=D.DiagnosticIO();adapter.latest_diagnostic=None;adapter.journal=MemoryJournal(pause)
    return adapter


def check():
    E.mkdir(exist_ok=True);scope=E/'mock01';scope.mkdir(exist_ok=False);scratch=scope/'scratch';scratch.mkdir();results=[]
    def test(name,fn):
        try:results.append({'case':name,'pass':True,'detail':fn()})
        except Exception as e:results.append({'case':name,'pass':False,'error':repr(e)})
    def run(stale):
        adapter=build_adapter(scratch/('pause'if stale else'udpunknown'),stale);received=time.monotonic_ns();calls=[]
        bracket={'id':1,'hostReceiveNs':received,'offsetLowNs':0,'offsetHighNs':1}
        def clock():return bracket if time.monotonic_ns()-received<=250000000 else None
        def network(body):calls.append(body);raise OSError('MOCK_UDP_ERROR_NOT_REAL_NETWORK')
        raw=struct.pack('<HHI16H',18458,1200,0,*([1500]*16))
        try:adapter.receive(raw,('127.0.0.1',9002),network,clock_read=clock)
        except JournalError as e:assert str(e)=='SEND_OUTCOME_UNKNOWN'
        else:raise AssertionError('noerror')
        diag=adapter.latest_diagnostic;assert adapter.failed and adapter.journal.failed;assert adapter.model.calls==1 and adapter.frames==adapter.stage_rows==0
        assert [r[0]for r in adapter.journal.rows]==['RX','INTENT','UNKNOWN']
        assert diag['exceptionChain'][0]['type']=='JournalError'
        if stale:
            assert not calls;assert diag['exceptionChain'][1]['message']=='CLOCK_BRACKET_NOT_FRESH_250MS'
            assert diag['localSendClassification']['type']=='NOT_SENT_SOCKET_CALLBACK_NOT_ENTERED'
            assert diag['frameAttempt']['lastClockCheck']['lastAcceptedBracketAgeNs']>=287000000
        else:
            assert len(calls)==1 and diag['exceptionChain'][1]['type']=='OSError'
            assert diag['localSendClassification']['type']=='SOCKET_CALLBACK_OUTCOME_UNKNOWN'
        return {'classification':diag['localSendClassification'],'chain':diag['exceptionChain'],'finalClock':diag['frameAttempt']['lastClockCheck'],'networkCalls':len(calls),'modelCalls':1,'retainedMemoryRows':[r[0]for r in adapter.journal.rows],'syntheticPrefixNotDurableWALProof':True}
    test('287ms INTENT pause freshnessrefusal network0 typedNOT_SENT no success',lambda:run(True))
    test('actual callback entry OSError stays UNKNOWN not NOT_SENT',lambda:run(False))
    def io():
        observer=D.DiagnosticIO();path=scratch/'io.bin';fd=observer.open_exclusive(path)
        try:
            for _ in range(6):assert observer.write(fd,b'MOCK_IO_BYTES')==13;observer.fsync(fd)
        finally:observer.close(fd)
        state=observer.snapshot();assert len(state['lastOperations'])==8 and state['totalObservedOperations']==12
        assert all(x['wallNs']>=0 and x['threadCPUNs']>=0 for x in state['lastOperations'])
        return state
    test('real tiny write/fsync timing bounded8 no OSwait attribution',io)
    def bodydiff():
        source=(R/'pilot/betaintegrated01/runtime02/frame_adapter.py').read_text();before=source[source.index('    def receive('):source.index('\n    def reject(')]
        new=(R/'planning/betaintegrated01/cockpit05-clockdiag01/frame_adapter.py').read_text();after=new[new.index('    def receive('):].rstrip()
        # Remove only diagnostic statements to verify exact old control body.
        begin=after.index("                current['lastClockCheck']");end=after.index('                if (',begin);after=after[:begin]+after[end:]
        after=after.replace("                current['lastAcceptedClock']=bounded_bracket(bracket,now)\n",'').replace("            self.capture_failure(exc, current, raw)\n",'')
        assert before.rstrip()==after;return 'All old receive equations/order/250ms/send/body identical after removing diagnostic-only statements'
    test('receive exact old algorithm modulo diagnostics only',bodydiff)
    files=list(scratch.rglob('*'));removedBytes=sum(p.stat().st_size for p in files if p.is_file());shutil.rmtree(scratch)
    result={'status':'PASS'if all(r['pass']for r in results)else'FAIL','cases':results,'actualJournalPrimeOrAPFrames':False,'mockPauseUsesRealWallSleepButMemoryJournal':True,'runtimeAPAndroidStarts':0,'scratchRemoved':str(scratch),'removedBytes':removedBytes,'scratchExistsAfter':scratch.exists()}
    (scope/'results.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'cases':len(results)}));return result

if __name__=='__main__':
    value=check()
    if value['status']!='PASS':raise SystemExit(1)
