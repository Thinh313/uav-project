"""Scoped source projection. Never executes an old CLI or writes old output paths."""
from pathlib import Path
import hashlib,json,datetime,shutil,time
R=Path(__file__).resolve().parents[2]
from guard import budget
BUDGET=budget();STOP=datetime.datetime.fromisoformat(BUDGET['runtimeStopUTC']).timestamp();MAX_AP_SECONDS=BUDGET.get('apSeconds')
if type(MAX_AP_SECONDS) is not int or MAX_AP_SECONDS != 300: raise RuntimeError('AP_SECONDS_POLICY_REQUIRED')
CLOSE_RESERVE_SECONDS=5
def read(kind):
 p=R/'pilot/simtrain53'/kind;s=p.read_text();return p,s

def backend_source():
 p,s=read('backend.py');s=s.replace('simtrain53','simhand01').replace('SIMTRAIN53','SIMHAND01')
 s=s.replace('frames < 144000','frames < '+str(MAX_AP_SECONDS*1200)).replace('if time.monotonic()-start > 150:', 'if time.time() >= '+repr(STOP-CLOSE_RESERVE_SECONDS)+':')
 s=s.replace("    from wal_journal import Wal, encode", """    from wal_journal import Wal as BaseWal, encode
    class Wal(BaseWal):
        # Existing CRC, chain, sequence and fsync-before-send implementation is unchanged.
        def __init__(self, *args, **kwargs):
            self.ioWriteNs=0; self.ioWriteCalls=0; self.lastIntentIO=None
            super().__init__(*args, hook=self.io_hook, **kwargs)
        def io_hook(self, event, kind, frame, fd, data):
            if event=='wal-write':
                begin=time.monotonic_ns()
                try: return os.write(fd, data)
                finally:
                    self.ioWriteNs+=time.monotonic_ns()-begin; self.ioWriteCalls+=1
        def append(self, kind, frame, payload, flush=False):
            self.ioWriteNs=0; self.ioWriteCalls=0; start=time.monotonic_ns(); prior=len(self.flush_cost)
            result=super().append(kind, frame, payload, flush=flush)
            if kind=='INTENT': self.lastIntentIO=[self.ioWriteNs, self.flush_cost[-1] if len(self.flush_cost)>prior else None, time.monotonic_ns()-start, self.ioWriteCalls]
            return result""")
 s=s.replace('stages.append([frame, rx, a, computed, barrier, sent])', 'stages.append([frame, rx, a, computed, barrier, sent, *wal.lastIntentIO])')
 s=s.replace("            wal.append('CLOSE'", "            if not stopped: raise RuntimeError('UNREQUESTED_FRAME_BOUND')\n            wal.append('CLOSE'")
 s=s.replace("        epoch.close(); wal.close()", """        epoch.close(); wal.close()
        if error:
            seal={'format':'aeris-simstability03-failure-prefix','version':1,'status':'FAILED','error':error,'admittedFrames':frames,'walBytes':wal.bytes,'walRecords':wal.seq,'walHeadSha256':wal.chain.hex(),'successCloseWritten':False,'scope':'RETAINED_PREFIX_NOT_SUCCESSFUL_FLIGHT_OR_COMPLETE_CAPTURE'}
            with (out/'backend-failure-seal.json').open('x') as failure_file:
                json.dump(seal,failure_file); failure_file.write('\\n'); failure_file.flush(); os.fsync(failure_file.fileno())""")
 s=s.replace('limit=384*2**20' ,'limit='+str(768 if MAX_AP_SECONDS>210 else 512)+'*2**20')
 s=s.replace('20*2**30+512*2**20','10*2**30+256*2**20')
 return p,s

def runtime_source():
 p,s=read('runtime.py');s=s.replace('simtrain53','simhand01')
 start=s.index("    assert shutil.disk_usage(R).free > 24*2**30")
 end=s.index('    image_id = command',start)
 s=s[:start]+'''    from guard import admit_ap
    admit_ap(rid)
    def check_cancel():
        marker=os.environ.get('AERIS_SIMHAND_STOP_REQUEST')
        if marker and Path(marker).exists(): raise RuntimeError('CANCELLED_BEFORE_AP')
    check_cancel()
    global NAME
    NAME='aeris-simhand01-'+rid
    assert subprocess.run(['docker','container','inspect',NAME],capture_output=True).returncode != 0
    for port, kind in [(9002,socket.SOCK_DGRAM),(9004,socket.SOCK_DGRAM),(9005,socket.SOCK_DGRAM),(5870,socket.SOCK_STREAM)]:
        with socket.socket(socket.AF_INET,kind) as channel: channel.bind(('127.0.0.1',port))
'''+s[end:]
 s=s.replace("    proc = subprocess.Popen", """    check_cancel()
    with (out/'resource-intent.json').open('x') as intent_file:
        json.dump({'format':'aeris-simstability03-resource-intent','version':1,'run':rid,'containerName':NAME,'scope':'PLANNED_OWNERSHIP_BEFORE_BACKEND_SPAWN_NOT_PROOF_OF_CHILD_CREATION'},intent_file)
        intent_file.write('\\n'); intent_file.flush(); os.fsync(intent_file.fileno())
    intent_dir=os.open(out,os.O_RDONLY)
    try: os.fsync(intent_dir)
    finally: os.close(intent_dir)
    proc = subprocess.Popen""")
 s=s.replace("        args = ['docker'", "        check_cancel()\n        args = ['docker'")
 s=s.replace("        cid = command(args)", "        check_cancel()\n        cid = command(args)")
 s=s.replace("['docker','run','--rm','-d'", "['docker','run','-d'")
 s=s.replace('deadline=time.monotonic()+150', 'deadline=min(time.monotonic()+'+str(MAX_AP_SECONDS)+',time.monotonic()+max(0,'+repr(STOP-CLOSE_RESERVE_SECONDS)+'-time.time()))')
 s=s.replace('20*2**30+768*2**20','10*2**30+256*2**20')
 s=s.replace("        if cid:\n            info=json.loads(command(['docker','container','inspect',NAME]))[0]", """        no_container_observed=False; container_observation='UNKNOWN'
        try:
            inspected=subprocess.run(['docker','container','inspect',NAME],capture_output=True,text=True,timeout=30)
            if inspected.returncode==0:
                observed=json.loads(inspected.stdout)[0]
                assert observed['Config']['Labels']['aeris.run']==rid and observed['Config']['Labels']['aeris.task']=='simhand01', 'CONTAINER_OWNER_MISMATCH'
                if cid is not None: assert observed['Id']==cid, 'CONTAINER_ID_MISMATCH'
                cid=observed['Id']; container_observation='EXACT_OWNED_CONTAINER'
            elif inspected.returncode==1 and ('No such object' in inspected.stderr or 'No such container' in inspected.stderr):
                no_container_observed=True; container_observation='NO_CONTAINER_OBSERVED_BY_UNIQUE_NAME'
            else: raise RuntimeError('CONTAINER_INSPECT_UNCONFIRMED')
        except Exception as inspect_error:
            failure='CLOSURE_UNCONFIRMED:'+str(inspect_error)
        if cid and container_observation=='EXACT_OWNED_CONTAINER':
            info=observed""")
 s=s.replace("            save(out/'container-before-stop.json',info)\n            (out/'ap-console.txt').write_text(command(['docker','logs',NAME]))", """            try:
                save(out/'container-before-stop.json',info)
                (out/'ap-console.txt').write_text(command(['docker','logs',NAME]))
            except Exception as log_error: failure='CONTAINER_DIAGNOSTIC_FAILED:'+str(log_error)""")
 s=s.replace("            stop_info=command(['docker','stop','-t','3',NAME])", """            try: stop_info=command(['docker','stop','-t','3',NAME])
            except Exception as stop_error: failure='OWNED_CONTAINER_STOP_UNCONFIRMED:'+str(stop_error)""")
 s=s.replace("'ownedContainerStopped':bool(stop_info),'error':failure", "'ownedContainerStopped':bool(stop_info),'noContainerObserved':no_container_observed,'containerObservation':container_observation,'containerId':cid,'containerName':NAME,'error':failure")
 s=s.replace("'backendPid':proc.pid,'containerId':cid", "'backendPid':proc.pid,'containerName':NAME,'containerId':cid")
 s=s.replace("'rateHz':1200,'speedup':1", "'apSeconds':"+str(MAX_AP_SECONDS)+",'closureReserveSeconds':"+str(CLOSE_RESERVE_SECONDS)+",'rateHz':1200,'speedup':1")
 s=s.replace("'peakBudgetBytes':2*2**30", "'peakBudgetBytes':512*2**20")
 return p,s

def readback_source():
 p,s=read('readback.py');return p,s.replace('simtrain53','simhand01').replace('SIMTRAIN53','SIMHAND01')

def execute(kind,file):
 p,s={'backend':backend_source,'runtime':runtime_source,'readback':readback_source}[kind]()
 ns={'__name__':'__main__','__file__':str(file)}
 exec(compile(s,str(file)+'#'+hashlib.sha256(s.encode()).hexdigest(),'exec'),ns)
