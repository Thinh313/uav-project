"""External bounded owner for SIMTRAIN53, never invokes an old runtime helper."""
from pathlib import Path
import datetime,hashlib,json,shutil,socket,subprocess,sys,time,os,signal
R=Path(__file__).resolve().parents[2];E=R/'evidence/isolate61/runs';NAME='aeris-isolate61';IMAGE='rtr-aeris-sim32-trace-builder:local';AP=R/'runtime/sim32-instrument01-build/ardupilot/build/sitl/bin/arducopter'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,data):
 with p.open('x')as f:json.dump(data,f,indent=2);f.write('\n')
def command(args):return subprocess.check_output([str(x)for x in args],text=True,timeout=30).strip()
def launch(rid, load, wind, mode, request_id):
    pins=json.loads((R/'evidence/isolate61/source-pins.json').read_text())['files']
    for name,digest in pins.items():assert sha(R/name)==digest,('ISOLATE61_SOURCE_PIN',name)
    assert len(list((R/'evidence/isolate61/started').glob('*.json')))<2,'MAX_TWO_ACTUAL_ATTEMPTS'
    retained=sum(p.stat().st_blocks*512 for p in (R/'evidence/isolate61').rglob('*') if p.is_file())
    assert retained+2**30<=int(2.25*2**30),'ISOLATE61_CUMULATIVE_BUDGET'
    assert mode in ['baseline','optimized'];assert request_id.isalnum() and len(request_id)<=40
    reservation=json.loads((R/'evidence/isolate61/reservations'/f'{request_id}.json').read_text())
    allocation=reservation['allocation'];assert allocation=='none'
    trace_mode=reservation['traceMode'];assert trace_mode in ['bind','tmpfs']
    assert reservation=={'requestId':request_id,'mode':mode,'load':load,'wind':wind,'allocation':allocation,'traceMode':trace_mode}
    assert not(R/'evidence/isolate61/started'/f'{request_id}.json').exists()
    save(R/'evidence/isolate61/started'/f'{request_id}.json',{'requestId':request_id,'run':rid,'mode':mode,'allocation':allocation,'traceMode':trace_mode})
    assert rid.isalnum() and len(rid) <= 24
    assert load in ['empty','central','offset'] and wind in ['calm','gust']
    assert shutil.disk_usage(R).free > int(22.5*2**30), 'ISOLATE61_BOUNDED_PEAK_22_5GIB'
    assert subprocess.run(['docker','container','inspect',NAME],capture_output=True).returncode != 0
    for port, kind in [(9002,socket.SOCK_DGRAM),(9004,socket.SOCK_DGRAM),(9005,socket.SOCK_DGRAM),(5874,socket.SOCK_STREAM)]:
        with socket.socket(socket.AF_INET,kind) as s: s.bind(('127.0.0.1',port))
    admission = json.loads((R/'evidence/simtrain52/admission1.json').read_text())
    for p, h in admission['pins'].items(): assert sha(R/p) == h, ('PIN',p)
    oracle = json.loads((R/'evidence/sim32-pipe03/integrator-oracle.json').read_text())
    assert oracle['status'] == 'PASS_EXACT_BYTES_ALL_INPUTS'
    for p, h in oracle['sourcePins'].items(): assert sha(R/p) == h
    image_id = command(['docker','image','inspect',IMAGE,'--format','{{.Id}}'])
    E.mkdir(parents=True,exist_ok=True); out = E/rid; out.mkdir(); (out/'guest-state').mkdir(); save(out/'request.json',{'load':load,'wind':wind,'seed':32,'mode':mode,'requestId':request_id,'allocation':allocation,'traceMode':trace_mode})
    log = (out/'backend-console.txt').open('x')
    proc = subprocess.Popen([sys.executable,'-B',str(Path(__file__).with_name('backend.py')),rid],stdout=log,stderr=subprocess.STDOUT,cwd=R)
    wake_log=(out/'wake-process-console.txt').open('x')
    wakeproc=subprocess.Popen([sys.executable,'-B',str(Path(__file__).with_name('wake-process.py')),str(out)],stdout=wake_log,stderr=subprocess.STDOUT,cwd=R)
    cid = None; failure = None; stop_info = None
    try:
        for _ in range(50):
            if (out/'backend-ready.json').exists(): break
            if proc.poll() is not None: raise RuntimeError('BACKEND_START_FAILED')
            time.sleep(.1)
        assert (out/'backend-ready.json').exists()
        args = ['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=isolate61','--label','aeris.run='+rid,
                '--platform','linux/arm64','--pull','never','--network','bridge','--cpus','2','--memory','384m',
                '--tmpfs','/probe:rw,noexec,nosuid,size=16m',*(['--tmpfs','/ap-trace:rw,noexec,nosuid,size=144m'] if trace_mode=='tmpfs' else []),'--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m',
                '-p','127.0.0.1:9004:9004/udp','-p','127.0.0.1:5874:5760','-v',str(R/'runtime/sitl')+':/aeris:ro',
                '-v',str(AP)+':/aeris/arducopter:ro','-v',str(R/'pilot/sim32-pipe03')+':/instrument:ro',
                '-v',str(R/'pilot/isolate61')+':/diagnostics:ro','-v',str(R/'pilot/sim32')+':/sim32:ro','-v',str(out)+':/evidence',
                '-v',str(out/'guest-state')+':/state','-e','AERIS_INSTRUMENT=1','-e','AERIS_TRACE_MODE='+trace_mode,'-w','/state',IMAGE,
                '/bin/sh','/diagnostics/guest-entry.sh','/aeris/arducopter','-w','--model','JSON:192.168.65.254',
                '--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/sim32/sitl.parm',
                '--serial0=tcp:5760:nowait','--rate','1200','--speedup','1']
        cid = command(args)
        save(out/'launch.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':args,
             'mode':mode,'allocation':allocation,'traceMode':trace_mode,'requestId':request_id,'backendPid':proc.pid,'containerId':cid,'imageId':image_id,'apSha256':sha(AP),
             'driverSha256':sha(Path(__file__)),'rateHz':1200,'speedup':1,'negativeDebtCapUs':500000,
             'resourceFreeBytes':shutil.disk_usage(R).free,'peakBudgetBytes':2**30,
             'simulatorOnlyControlEndpoint':'127.0.0.1:5874','profile':{'load':load,'wind':wind},'uiControlAllowedAfterAttestation':True,'noAutomaticRetry':True})
        deadline=time.monotonic()+150
        while proc.poll() is None and time.monotonic()<deadline and not(out/'stop-request.json').exists():
            if shutil.disk_usage(R).free<20*2**30+768*2**20: raise RuntimeError('RESOURCE_HEADROOM_LOST')
            time.sleep(.1)
        if not(out/'stop-request.json').exists(): raise RuntimeError('UNREQUESTED_BACKEND_END_OR_DEADLINE')
    except Exception as e:
        failure = str(e)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(); failure = 'BACKEND_MANAGED_CLOSE_FAILED'
        log.close()
        if wakeproc.poll() is None:
            wakeproc.terminate();wakeproc.wait(timeout=5)
        wake_log.close()
        if cid:
            info=json.loads(command(['docker','container','inspect',NAME]))[0]
            assert info['Id']==cid and info['Config']['Labels']['aeris.run']==rid
            save(out/'container-before-stop.json',info)
            (out/'ap-console.txt').write_text(command(['docker','logs',NAME]))
            from archive import archive
            try:
                archive(cid,out,trace_mode)
                stop_info=command(['docker','stop','-t','3',NAME])
            except Exception as exc:
                failure='ARCHIVE_FAILED_CONTAINER_RETAINED:'+str(exc)
                save(out/'retained-container.json',{'containerId':cid,'name':NAME,'reason':failure,'mustNotStopBeforeVerifiedExport':True})
        save(out/'closure.json',{'backendExited':proc.poll() is not None,'backendExitCode':proc.returncode,
             'ownedContainerStopped':bool(stop_info),'error':failure,'stateRetained':True,'explicitStopRequested':(out/'stop-request.json').exists(),
             'freeBytes':shutil.disk_usage(R).free,'wakeProcessExitCode':wakeproc.returncode,'scope':'SIMULATOR_ONLY_CONTROL_SESSION'})
        # Required disk hygiene; never prune volumes or containers.
        (out/'docker-image-prune.txt').write_text(command(['docker','image','prune','-f']))
    print(json.dumps({'out':str(out.relative_to(R)),'error':failure,'closed':bool(stop_info)}))
    if failure: raise SystemExit(1)



if __name__=='__main__':launch(*sys.argv[1:6])
