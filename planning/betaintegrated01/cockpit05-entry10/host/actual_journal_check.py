"""Root-only tiny real host journal check. Synthetic frames, actual disk/15s prime/fsync.
Import is inert; no AP, emulator, socket, sensor or signature actions.
"""
from pathlib import Path
from importlib import import_module
import argparse,hashlib,json,os,shutil,time,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
H='planning.betaintegrated01.cockpit05-entry10'
j=import_module(H+'.runtime.journal')
OLD=import_module('pilot.betaintegrated01.runtime02.journal')
E=R/'evidence/betaintegrated01-cockpit05-entry10/host/real-journal01'


def main():
    required=10*2**30+256*2**20+2**30//100
    if shutil.disk_usage(R).free<required:raise RuntimeError('TINY_HOST_IO_FLOOR_RESERVE_PLUS0.01GIB_HEADROOM')
    if E.exists():raise RuntimeError('ONE_EXECUTION_REAL_JOURNAL01_NO_RETRY')
    E.mkdir();started=time.monotonic_ns();sync_count=0;trace=[];journal=None
    def put(name,value):
        raw=(json.dumps(value,indent=2)+'\n').encode()
        if len(raw)>32768:raise RuntimeError('TINY_EVIDENCE_BOUND')
        with(E/name).open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
    def hook(operation,path,n):
        nonlocal sync_count
        if operation=='fsync':sync_count+=1
    try:
        put('before.json',{'actualFreeBytes':shutil.disk_usage(R).free,'requiredFreeBytes':required,'sourceSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inputProvenance':'SYNTHETIC_HOST_JOURNAL_ONLY_NO_AP_SENSOR','realPrimeExpectedSeconds':15,'APStarted':False,'noRetry':True})
        journal=j.SegmentedJournal(E/'journal','entry10-real-host','epoch',j.Policy(segment_bytes=16384,quota_bytes=65536,max_record_bytes=2048,max_segments=4,termination_reserve_bytes=8192),io=j.FileIO(hook))
        for frame in range(2):
            computed=[]
            def compute(raw):computed.append(sync_count);return ('SYNTHETIC_SENSOR_'+str(frame)).encode()
            def local_sink(intent):
                assert sync_count>computed[-1],'INTENT_FSYNC_BEFORE_LOCAL_MOCK_SINK'
                trace.append({'frame':frame,'computeFsyncCount':computed[-1],'sinkFsyncCount':sync_count,'intentSHA256':hashlib.sha256(intent).hexdigest(),'localSinkOnly':True});return len(intent)
            journal.record_frame(frame,('SYNTHETIC_RX_'+str(frame)).encode(),compute,local_sink)
            journal.append_stage(frame,{'mockComputeNs':0})
        result=journal.close();put('external-commit.json',result)
        cold=j.verify_journal(E/'journal','entry10-real-host','epoch',expected_commit=result['commitAnchor'])
        assert cold['frames']==2 and cold['state']=='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'
        try:OLD.verify_journal(E/'journal','entry10-real-host','epoch',expected_commit=result['commitAnchor'])
        except OLD.VerificationError as exc:assert str(exc)=='DISK_GUARD_POLICY';old_rejected=str(exc)
        else:raise AssertionError('OLD_ENTRY20_READER_ACCEPTED_NEW10_MANIFEST')
        rows=[]
        for p in sorted((E/'journal').glob('segment-*.jsonl')):
            for line in p.read_bytes().splitlines():
                if len(rows)>=24:raise RuntimeError('TINY24_RECORD_BOUND')
                rows.append(json.loads(line))
        assert rows and len(rows)==cold['records'] and all(row['body']['run']=='entry10-real-host'for row in rows),'EXPECTED_NONEMPTY_EXACT_ALL_TINY_RECORDS'
        inventory={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in(E/'journal').iterdir()}
        put('proof.json',{'status':'REAL_HOST_ENTRY10_JOURNAL_CLOSED_COLD_PASS_ONLY','actualPrime':journal.guard.prime_receipt,'guardDiagnostic':journal.guard.diagnostic(),'cold':cold,'mockSinkTrace':trace,'oldReceiverRejected':old_rejected,'inventory':inventory,'firstAtMost24Records':rows,'elapsedRealNs':time.monotonic_ns()-started,'noAPOrEmulator':True,'inputProvenance':'SYNTHETIC_HOST_JOURNAL_FRAMES_NOT_ACTUAL_AP_FRAMES','flightOrThirtyMinuteAccepted':False})
        total=sum(p.stat().st_size for p in E.rglob('*')if p.is_file());assert total<65536,('TINY_EVIDENCE64K',total)
        print(json.dumps({'status':'REAL_HOST_JOURNAL_PASS_NOT_FLIGHT','path':str(E),'bytes':total,'frames':2,'actualPrimeNs':journal.guard.prime_receipt['elapsedRealMonotonicNs']}))
    except BaseException as exc:
        if journal is not None and not journal.closed:journal.abort('REAL_HOST_CHECK:'+str(exc)[:160])
        put('failure.json',{'error':repr(exc),'actualPrime':None if journal is None else journal.guard.prime_receipt,'elapsedRealNs':time.monotonic_ns()-started,'noRetry':True,'failedPrefixRetained':True,'APStarted':False})
        raise


if __name__=='__main__':main()
