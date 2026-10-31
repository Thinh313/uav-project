"""Bounded reference physics backend; control runs in a separately attested Node adapter."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, os, shutil, signal, socket, struct, subprocess, sys, time

R = Path(__file__).resolve().parents[2]
E = R / 'evidence/pace58/runs'
IMAGE = 'rtr-aeris-sim32-trace-builder:local'
NAME = 'aeris-pace58'
AP = R / 'runtime/sim32-instrument01-build/ardupilot/build/sitl/bin/arducopter'
sys.path[:0] = [str(R / 'pilot/sim32-pipe03'), str(R / 'pilot/sim32-journal04'),
                str(R / 'runtime/sim32-pipe03-build/host-native'), str(R / 'pilot/sim32')]


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def save(p, data):
    with p.open('x') as f: json.dump(data, f, indent=2); f.write('\n')


def command(args):
    return subprocess.check_output([str(x) for x in args], text=True, timeout=30).strip()


def backend(out):
    from fast_physics import Model, profile
    from wal_journal import encode
    from compact import CompactWal as Wal, Rows
    from gc_observer import GCObserver
    from epoch import Epoch
    from tuning import configure, encoder
    from clock_host import ClockObserver
    state = out / 'backend-state'; state.mkdir()
    configuration = json.loads((out/'request.json').read_text()); mode=configuration['mode']; assert mode in ['baseline','optimized']; tuning=configure(mode); model = Model(profile(configuration['load'], configuration['wind']))
    if mode=='optimized': encode=lambda value:encoder.encode(value).encode()
    mock = out.parent == R/'evidence/pace58/mock'
    source = 'MOCK_LOOPBACK_DATAGRAM_NOT_AP' if mock else 'ACTUAL_PACE58_AP_EXTERNAL_PHYSICS'
    wal = Wal(out, {'source': source, 'clockDomain': 'host-monotonic',
                    'epochScope': out.name, 'controlTransport':'SEPARATE_ATTESTED_NODE_MAVLINK'}, limit=384*2**20)
    epoch = Epoch(state, out, out.name)
    clock = None; stopped = False; frames = 0; previous = None; peer = None; first = None; last = None
    error = None; stages = Rows(144000,6); cpu_stages=Rows(144000,7); gc_observer=GCObserver()
    def stop(*args):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('127.0.0.1', 9002)); s.settimeout(.1)
            if mode=='optimized':
                s.setblocking(True);s.setsockopt(socket.SOL_SOCKET,socket.SO_RCVTIMEO,struct.pack('@ll',0,100000))
            clock = ClockObserver(out, out.name, epoch.id)
            save(out/'backend-ready.json', {'pid': os.getpid(), 'epoch': epoch.id, 'port': 9002, 'mode':mode, 'tuning':tuning})
            start = time.monotonic()
            while not stopped and frames < 144000:
                epoch.check()
                if clock.error: raise RuntimeError('CLOCK_OBSERVER:' + clock.error)
                if time.monotonic()-start > 150: raise RuntimeError('PROBE_DEADLINE')
                try: data, address = s.recvfrom(1024)
                except (socket.timeout,BlockingIOError): continue
                rx = time.monotonic_ns();cpu_rx=time.thread_time_ns()
                if stopped: save(out/'unadmitted-tail.json', {'rawHex': data.hex(), 'reason': 'STOP_OBSERVED'}); break
                if len(data) != 40:
                    wal.append('RX', 0xffffffff, encode({'source':source,'rawHex':data.hex(),'hostReceiveNs':rx,'peer':address,'rejection':'SERVO_SHAPE'}),flush=True)
                    raise RuntimeError('SERVO_SHAPE')
                magic, rate, frame, *pwm = struct.unpack('<HHI16H', data)
                wal.append('RX', frame, encode({'source': source, 'rawHex': data.hex(),
                                              'hostReceiveNs': rx, 'peer': address}))
                if magic != 18458 or rate != 1200: raise RuntimeError('SERVO_FORMAT_OR_RATE')
                if previous is not None and frame != previous+1: raise RuntimeError('FRAME_GAP_OR_DUPLICATE')
                if peer is not None and address != peer: raise RuntimeError('FOREIGN_PEER')
                epoch.check(); gc_observer.frame=frame;cpu_a=time.thread_time_ns(); a = time.monotonic_ns()
                sensors=model.step(pwm,1/rate)
                payload=('\n'+(encoder.encode(sensors) if mode=='optimized' else json.dumps(sensors,separators=(',',':'),allow_nan=False))+'\n').encode()
                aux=model.snapshot() if mode=='optimized' else None
                computed = time.monotonic_ns();cpu_computed=time.thread_time_ns()
                row = {'frame': frame, 'rate': rate, 'servoHex': data.hex(), 'sensorUtf8': payload.decode(),
                       'hostReceiveNs': rx, 'computeStartNs': a, 'computeEndNs': computed,
                       'modelAux': aux if mode=='optimized' else model.snapshot(), 'epoch': epoch.id, 'source': 'MOCK_LOOPBACK_REFERENCE_PHYSICS' if mock else 'ACTUAL_PACE58_AP_SERVO_TO_REFERENCE_PHYSICS'}
                body = encode(row)
                wal.append('INTENT', frame, struct.pack('<II', len(body), 0)+body, flush=True)
                barrier = time.monotonic_ns();cpu_barrier=time.thread_time_ns(); epoch.check()
                returned = s.sendto(payload, address); sent = time.monotonic_ns();cpu_sent=time.thread_time_ns()
                if returned != len(payload): raise RuntimeError('SEND_OUTCOME_UNKNOWN')
                wal.append('SENT', frame, encode({'returnedBytes': returned, 'expectedBytes': len(payload),
                                                'hostSendReturnNs': sent, 'observation': 'LOCAL_UDP_RETURN_NOT_EXECUTION'}))
                stages.append([frame, rx, a, computed, barrier, sent])
                if frames % 20 == 0:
                    snapshot={**(aux if mode=='optimized' else model.snapshot()),'frame':frame,'epoch':epoch.id,'run':out.name,'hostMonotonicNs':rx,'receivedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'MOCK_LOOPBACK_REFERENCE_PHYSICS' if mock else 'ACTUAL_PACE58_AP_SERVO_TO_REFERENCE_PHYSICS','rateHz':1200}
                    pending=state/'physics.pending';pending.write_text(json.dumps(snapshot));os.replace(pending,state/'physics.json')
                cpu_stages.append([frame,cpu_rx,cpu_a,cpu_computed,cpu_barrier,cpu_sent,time.thread_time_ns()])
                previous = frame; peer = address; frames += 1; epoch.progress()
                if first is None: first = rx
                last = rx
                if frames % 200 == 0 and shutil.disk_usage(R).free < 20*2**30+512*2**20:
                    raise RuntimeError('RESOURCE_HEADROOM_LOST')
            wal.append('CLOSE', 0, encode({'intentAndSentFrames': frames, 'noAutomaticResume': True}), flush=True)
    except Exception as e:
        error = str(e)
    finally:
        gc_observer.phase='closing'
        gc_result=gc_observer.seal()
        if clock: clock.seal()
        epoch.close(); wal.close()
        save(out/'backend-stages.json', list(stages))
        save(out/'backend-cpu-stages.json',list(cpu_stages))
        save(out/'gc-observer.json',gc_result)
        wall = (last-first)/1e9 if frames > 1 else None
        save(out/'backend-result.json', {'status': 'CAPTURE_CLOSED' if error is None else 'FAILED', 'error': error,
              'traceRepresentation':'BOUNDED_CONTIGUOUS_UINT64_NO_DROP','cpuClockDomain':'HOST_THREAD_CPU_NS','mode':mode,'tuning':tuning,'frames': frames, 'activeReceiveWallSeconds': wall, 'modelSeconds': model.t,
              'activeReceiveRTF': (frames-1)/1200/wall if wall else None, 'epoch': epoch.id,
              'journalPolicy': 'fsync-before-publish', 'clockError': clock.error if clock else 'NOT_STARTED',
              'scope': 'Actual AP external reference physics capture; not calibrated Hera or gate acceptance'})
    if error: raise SystemExit(1)



if __name__ == '__main__':
    mock_cli=sys.argv[1]=='mock';rid=sys.argv[2]if mock_cli else sys.argv[1];assert rid.isalnum()and len(rid)<=24
    backend((R/'evidence/pace58/mock'if mock_cli else E)/rid)
