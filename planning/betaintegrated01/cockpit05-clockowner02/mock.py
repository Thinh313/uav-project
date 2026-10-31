"""Deterministic publication/frame fault seams; memory journals are NOT actual priming."""
from pathlib import Path
from importlib import import_module
from dataclasses import asdict,replace
import hashlib,json,threading,time,struct,shutil,os
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-clockowner02'
P=import_module(H+'.policy');O=import_module(H+'.runtime.owner');A=import_module(H+'.runtime.frame_adapter');D=import_module('planning.betaintegrated01.cockpit05-clockdiag01.diagnostics');base=import_module('planning.betaintegrated01.cockpit05-clockdiag01.mock');J=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal');B=import_module(H+'.runtime.backend');E=R/'evidence/betaintegrated01-cockpit05-clockowner02/host'


class MemoryClockJournal:
    def __init__(self):self.seq=0;self.head='0'*64;self.rows=[];self.block=None;self.enter=threading.Event();self.guard=base.MockGuard()
    def append_event(self,kind,data):
        if self.block==kind:self.enter.set();self.release.wait(2)
        raw=json.dumps([self.seq,kind,data],sort_keys=True).encode();self.head=hashlib.sha256(bytes.fromhex(self.head)+raw).hexdigest();self.rows.append((self.seq,kind,data,self.head));self.seq+=1;return self.seq-1


class Alive:
    def is_alive(self):return True


def make_owner():
    owner=O.ClockOwner(E,'mockrun','epoch','boot',180,'a'*64);owner.journal=MemoryClockJournal();owner.thread=Alive();return owner


def fresh(owner,n):
    now=time.monotonic_ns();row={'run':'mockrun','epoch':'epoch','boot':'boot','id':n,'hostReceiveNs':now,'offsetLowNs':0,'offsetHighNs':1,'uncertaintyNs':1,'kind':'RESPONSE','freshCalibration':True}
    owner.sink(row);owner.publish(row)


def adapter(root,owner,pause):
    root.mkdir();a=object.__new__(A.FrameAdapter);a.root=root/'journal';a.model=base.Model();a.max_frames=1;a.peer=None;a.frames=a.stage_rows=0;a.current=None;a.origin_ns=time.monotonic_ns()-10_000_000;a.failed=a.closed=False;a.first_rx=a.last_rx=None;a.diagnostic_io=D.DiagnosticIO();a.latest_diagnostic=None;a.journal=base.MemoryJournal(pause);a.clock_owner=owner;return a


def main():
    E.mkdir(parents=True,exist_ok=True);out=E/'mock02';out.mkdir(exist_ok=False);scratch=out/'scratch';scratch.mkdir();results=[]
    def test(name,fn):
        try:results.append({'case':name,'pass':True,'detail':fn()})
        except BaseException as e:results.append({'case':name,'pass':False,'error':repr(e)})
    def publication_order():
        o=make_owner();o.journal.block='CLOCK_PUBLICATION';o.journal.release=threading.Event();now=time.monotonic_ns();row={'run':'mockrun','epoch':'epoch','boot':'boot','id':1,'hostReceiveNs':now,'offsetLowNs':0,'offsetHighNs':1,'uncertaintyNs':1,'kind':'RESPONSE','freshCalibration':True};o.sink(row)
        thread=threading.Thread(target=lambda:o.publish(row));thread.start();assert o.journal.enter.wait(1);assert o.calibration()is None
        o.journal.release.set();thread.join(1);assert not thread.is_alive();assert o.calibration()['id']==1
        return 'No publication visible while syntheticclockpublicationfsync is blocked'
    test('publish only after durablepublicationappend returns',publication_order)
    def delayed():
        o=make_owner();fresh(o,1);a=adapter(scratch/'delay',o,True);stop=threading.Event()
        def progress():
            n=2
            while not stop.wait(.025):fresh(o,n);n+=1
        t=threading.Thread(target=progress);t.start();calls=[]
        try:r=a.receive(struct.pack('<HHI16H',18458,1200,0,*([1500]*16)),('127.0.0.1',9002),lambda b:calls.append(b)or len(b),clock_read=o.calibration)
        finally:stop.set();t.join(1)
        assert a.frames==a.stage_rows==1 and a.model.calls==1 and len(calls)==1
        stage=[x[2]for x in a.journal.rows if x[0]=='STAGE'][0];assert stage['clockPublicationAtSend']>stage['clockPublicationAtReceive']and stage['clockAtomicPermitAgeNs']<=250000000
        import_module(H+'.runtime.receiver').verify_frame_reference(stage,a.origin_ns,{seq:{'data':data,'recordSHA256':sha}for seq,kind,data,sha in o.journal.rows if kind=='CLOCK_PUBLICATION'})
        # Actual recordsize under selected longest clockfields with representative context.
        payload={'eventKind':'STAGE','data':{'frame':0,'fields':stage}};J.writer.bounded_value(payload,2048)if hasattr(J,'writer')else None
        from pilot.betaintegrated01.runtime.ap_stage import canonical
        wire={'body':{'v':2,'run':'r'*64,'epoch':'e'*64,'segment':0,'seq':0,'previous':'0'*64,'kind':'EVENT','frame':None,'payload':payload},'crc32':'f'*8,'sha256':'f'*64}
        assert len(canonical(wire))+1<=2048
        return {'modelCalls':1,'sends':1,'stage':stage,'maxContextSTAGEBytes':len(canonical(wire))+1,'memoryPrefixOnly':True}
    test('287ms mainINTENTpause independentclockprogress exactlyonesend',delayed)
    def faults():
        modes=['death','stale','failed','foreign','forged','boolean','overflow'];seen=[]
        for mode in modes:
            o=make_owner();fresh(o,1);reference=o.calibration();calls=[]
            if mode=='death':o.thread=type('Dead',(),{'is_alive':lambda self:False})()
            if mode=='stale':time.sleep(.255)
            if mode=='failed':o.latch_failure(OSError('MOCK_CLOCK_FSYNC'))
            if mode=='foreign':reference['boot']='other'
            if mode=='forged':reference['clockPublicationSHA256']='b'*64
            if mode=='boolean':reference['id']=True
            if mode=='overflow':
                o.events=o.maximum_events
                try:fresh(o,2)
                except RuntimeError as e:o.latch_failure(e)
            try:o.dispatch(reference,lambda ns:calls.append(ns))
            except Exception:pass
            else:raise AssertionError('faultaccepted:'+mode)
            assert not calls;assert o.failed is not None
            seen.append(mode)
        return seen
    test('clockdeath stale failure foreign forged bool overflow refuse network',faults)
    def adapter_faults():
        answers=[]
        for mode in('callback_oserror','clock_failure_after_INTENT','stale_after_INTENT'):
            o=make_owner();fresh(o,1);a=adapter(scratch/mode,o,mode=='stale_after_INTENT');calls=[]
            if mode=='clock_failure_after_INTENT':
                original=a.journal.record_frame
                def record(frame,raw,compute,send):
                    def wrapped_compute(body):
                        result=compute(body);o.latch_failure(OSError('MOCK_CLOCK_OWNER_FSYNC'));return result
                    return original(frame,raw,wrapped_compute,send)
                a.journal.record_frame=record
            def send(body):calls.append(body);raise OSError('MOCK_SOCKET_CALLBACK_UNKNOWN')
            try:a.receive(struct.pack('<HHI16H',18458,1200,0,*([1500]*16)),('127.0.0.1',9002),send,clock_read=o.calibration)
            except J.JournalError as error:assert str(error)=='SEND_OUTCOME_UNKNOWN'
            else:raise AssertionError('faultaccepted:'+mode)
            assert a.model.calls==1 and a.frames==a.stage_rows==0 and a.failed
            assert [x[0]for x in a.journal.rows]==['RX','INTENT','UNKNOWN']
            diag=a.latest_diagnostic
            assert len(calls)==(1 if mode=='callback_oserror'else 0)
            expected='SOCKET_CALLBACK_OUTCOME_UNKNOWN'if calls else'NOT_SENT_SOCKET_CALLBACK_NOT_ENTERED'
            assert diag['localSendClassification']['type']==expected
            answers.append({'fault':mode,'calls':len(calls),'classification':expected,'exceptionChain':diag['exceptionChain'],'memoryPrefixNotActualDurableWAL':True})
        return answers
    test('fullFrameAdapter callbackOSError vs clockfailure/stale afterINTENT preserve UNKNOWN no resend',adapter_faults)
    def capacity():
        answers=[]
        for seconds in(180,1960):
            pol=P.clock_policy(seconds).validate();events=P.clock_events(seconds);bound=events*2048+pol.max_segments*(2048+4096)+32768+8192
            assert bound<=pol.quota_bytes
            answers.append({'seconds':seconds,'events':events,'upperBytesIncludingFramingMeta':bound,'quota':pol.quota_bytes})
        assert P.campaign_budget()['taskHardPeakBytes']<10*2**30
        return answers
    test('formalallclockevent+framing+metadatafits64/512MiB',capacity)
    def cleanup():
        class C:
            def __init__(self):self.stop_event=threading.Event();self.closed=False
            def close(self,timeout):self.closed=True
        class Hub:
            def __init__(self):self.stop_event=threading.Event();self.done=threading.Event();self.stopped=False
            def stop(self):self.stopped=True
        c,h=C(),Hub();assert B.cleanup_runtime(c,h)==[];assert c.closed and c.stop_event.is_set()and h.stopped
        return 'Startup/post-maincleanup signals and joins both owners; no servicesstarted'
    test('constructorfailure cleanup has explicitboundedbothownerstop',cleanup)
    removed=sum(p.stat().st_size for p in scratch.rglob('*')if p.is_file());shutil.rmtree(scratch)
    result={'status':'PASS'if all(x['pass']for x in results)else'FAIL','cases':results,'syntheticMemoryJournalNotDurabilityProof':True,'actualDiskPrimeOrSocketRuntimeOrAP':False,'scratchRemoved':str(scratch),'removedBytes':removed}
    (out/'results.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
