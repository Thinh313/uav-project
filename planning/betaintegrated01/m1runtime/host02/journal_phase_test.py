"""Real15s disk prime, mock send and a fault precisely after durable SENT."""
from pathlib import Path
import hashlib
import json
import sys
import time
R=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime02.frame_adapter import FrameAdapter,SERVO
from pilot.betaintegrated01.runtime02.journal import FileIO,verify_journal
from pilot.betaintegrated01.runtime.physics import Model,profile


class StageFailure(FileIO):
    def write(self,fd,body):
        try:
            row=json.loads(bytes(body)).get('body',{})
        except (ValueError,AttributeError):
            row={}
        if row.get('kind')=='EVENT' and row.get('payload',{}).get('eventKind')=='STAGE' and row['payload']['data']['frame']==2:
            raise OSError('FAULT_STAGE_APPEND_AFTER_DURABLE_SENT')
        return super().write(fd,body)


def main():
    out=R/'evidence/betaintegrated01-m1runtime/host02/phase01';out.mkdir()
    started=time.monotonic_ns()
    adapter=FrameAdapter(out/'journal','rphase02','ephase02',Model(profile()),max_frames=32,io=StageFailure())
    primed=time.monotonic_ns()
    assert primed-started>=15_000_000_000
    assert adapter.journal.guard.prime_receipt['source']=='ACTUAL_HOST_15S_PRIME_NO_SYNTHETIC_SEED'
    sends=[]
    def send(body):sends.append(body);return len(body)
    clock=lambda:{'id':1,'hostReceiveNs':time.monotonic_ns(),'offsetLowNs':0,'offsetHighNs':10}
    try:
        for frame in range(3):adapter.receive(SERVO.pack(18458,1200,frame,*([1000]*16)),('127.0.0.1',45003),send,clock_read=clock)
        raise AssertionError('MUST_FAIL_STAGE_APPEND')
    except OSError as exc:assert str(exc)=='FAULT_STAGE_APPEND_AFTER_DURABLE_SENT'
    assert len(sends)==adapter.frames==adapter.journal.frames==3
    assert adapter.stage_rows==2
    rejected=json.loads((out/'journal-rejected.json').read_text())
    assert rejected['alreadyAdmitted'] is True and rejected['rejectionIsNotAdmittedFrame'] is False
    assert rejected['frameAttempt']['SENTGroupAcknowledged'] is True
    assert rejected['frameAttempt']['phase']=='STAGE_APPEND' and rejected['frameAttempt']['attemptedStage'] is not None
    try:adapter.receive(SERVO.pack(18458,1200,3,*([1000]*16)),('127.0.0.1',45003),send,clock_read=clock);raise AssertionError('NO_FUTURE_CALLBACK')
    except RuntimeError:pass
    assert len(sends)==3
    cold=verify_journal(out/'journal','rphase02','ephase02')
    assert cold['frames']==3 and cold['stageRows']==2 and cold['state']=='INCOMPLETE_RECORDING'
    pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'pilot/betaintegrated01/runtime02').rglob('*.py')}
    report={'status':'PASS_REAL_PRIME_AND_POST_SENT_STAGE_FAULT','primingRealNs':primed-started,
            'primingReceipt':adapter.journal.guard.prime_receipt,'guardFinalDiagnostic':adapter.journal.guard.diagnostic(),
            'localCallbacks':len(sends),'completedSentGroups':adapter.frames,'completedStageRows':adapter.stage_rows,
            'independentColdJournal':cold,'rejectedDiagnostic':rejected,'sourceSHA256':pins,
            'APStarts':0,'AndroidStarts':0,'sockets':0,'syntheticFreeSpaceInjectedIntoRuntime':False}
    (out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'primeSeconds':(primed-started)/1e9,'groups':adapter.frames,'stageRows':adapter.stage_rows}))


if __name__=='__main__':main()
