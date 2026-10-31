"""Owned host JSON FDM. No MAVLink writer; no automatic flight dispatch."""
from pathlib import Path
import argparse
import datetime
import json
import os
import signal
import socket
import time
from pilot.betaintegrated01.runtime.ap_stage import canonical, exclusive
from .frame_adapter import FrameAdapter
from ..host.admission import DiskGuardError
from pilot.betaintegrated01.cockpit04.clock_socket import ClockSocket
from pilot.betaintegrated01.runtime.physics import Model, profile
from .transport import TransportHub


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if config['bind'] != ['127.0.0.1', 9012] or config['requestedSpeedup'] != 1 or config['capMs'] != 500:
        raise ValueError('CONFIGURATION_ALLOWLIST')
    from ..host.policy02 import validate_recording_policy
    policy_amendment = validate_recording_policy(config)
    duration = config['maximumSeconds']
    if type(duration) is not int or duration not in (60,90,1960):
        raise ValueError('DURATION')
    run, epoch, boot = config['run'], config['epoch'], config['boot']
    out = Path(config['evidence'])
    if not out.is_dir():
        raise ValueError('EVIDENCE_PARENT')
    hub=TransportHub(out,run,epoch,boot,duration)
    hub.start()
    try:
        adapter = FrameAdapter(out / 'journal', run, epoch, Model(profile(config['load'], config['wind'], config['seed'])),
                               max_frames=duration * 1200, maximum_seconds=duration)
    except DiskGuardError as exc:
        hub.stop_event.set()
        print(json.dumps({'status':'FAILED_DURING_REAL_GUARD_PRIME','run':run,'epoch':epoch,'boot':boot,
                          'frames':0,'stageRows':0,'error':str(exc),'guardDiagnostic':exc.diagnostic,
                          'commitAnchor':None,'journalWritesAccepted':False}),flush=True)
        raise SystemExit(1)
    wait_deadline=time.monotonic()+5
    while not hub.ready.wait(.1):
        adapter.journal.guard.check()
        if hub.error or time.monotonic()>wait_deadline:
            hub.stop_event.set();adapter.journal.abort('TRANSPORT_PRIME_OR_READY_FAILED')
            raise RuntimeError('TRANSPORT_PRIME_OR_READY_FAILED:'+str(hub.error))
    clock = None
    stop = {'requested': False, 'atNs': None}
    start = last_rx = time.monotonic()
    error = None
    pending = None
    peer = None
    clock_ready = False

    def request_stop(signum, frame):
        stop.update(requested=True, atNs=time.monotonic_ns())

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('127.0.0.1', 9012))
        sock.settimeout(.05)
        exclusive(out / 'backend-identity.json', canonical({'pid': os.getpid(), 'run': run, 'epoch': epoch,
                  'boot': boot, 'endpoint': config['bind'], 'source': 'COCKPIT05_ENTRY10_EXPLICIT_RECORDING_POLICY', 'externalRecordingPolicy': policy_amendment, 'guardPrimed': True, 'guardPolicyVersion': 2, 'guardPriming': adapter.journal.guard.prime_receipt,'transportGuardPriming':hub.journal.guard.prime_receipt,'transportReady':True}) + b'\n')
        try:
            clock = ClockSocket(run, epoch, boot, lambda row: adapter.event('CLOCK', row),
                                maximum_seconds=duration,
                                diagnostic=lambda row: exclusive(out / 'clock-rejected.json', canonical(row) + b'\n'))
            while True:
                if hub.error:raise RuntimeError('TRANSPORT_HUB:'+hub.error)
                clock.poll()
                bracket = clock.calibration()
                if bracket is not None and not clock_ready:
                    exclusive(out / 'clock-ready.json', canonical({'run': run, 'epoch': epoch, 'boot': boot,
                              'firstObservedBracket': bracket, 'notSourceAuthentication': True}) + b'\n')
                    clock_ready = True
                now = time.monotonic()
                if now - start > duration + 5:
                    raise RuntimeError('DURATION_BOUND_NO_PENDING_RECEIPT')
                if adapter.frames and now - last_rx > 3:
                    raise RuntimeError('SERVO_STALE_3S')
                if stop['requested'] and now - (stop['atNs'] / 1e9) > 3:
                    raise RuntimeError('STOP_NO_NEXT_SERVO_3S')
                try:
                    raw, ancillary, flags, address = sock.recvmsg(1025)
                except socket.timeout:
                    continue
                last_rx = time.monotonic()
                if flags & socket.MSG_TRUNC:
                    adapter.reject(raw, address, 'TRUNCATED_DATAGRAM', socket_truncated=True)
                    raise RuntimeError('TRUNCATED_DATAGRAM')
                if peer is None:
                    peer = address
                if address != peer:
                    adapter.reject(raw, address, 'FOREIGN_SERVO_PEER')
                    raise RuntimeError('FOREIGN_SERVO_PEER')
                clock.poll()
                if clock.calibration() is None:
                    adapter.reject(raw, address, 'CLOCK_UNCALIBRATED_OR_STALE_250MS')
                    raise RuntimeError('CLOCK_UNCALIBRATED_OR_STALE_250MS')
                if stop['requested'] or adapter.frames >= duration * 1200 or last_rx - start >= duration:
                    pending = {'rawHex': raw.hex(), 'peer': list(address), 'reason': 'UNADMITTED_AT_OWNED_STOP',
                               'admittedFrames': adapter.frames, 'run': run, 'epoch': epoch, 'boot': boot,
                               'modelStepComputed': False, 'sensorSent': False}
                    exclusive(out / 'pending-servo.json', canonical(pending) + b'\n')
                    break
                adapter.receive(raw, address, lambda body: sock.sendto(body, address), clock_read=clock.calibration)
            clock_state = clock.close()
            clock = None
            adapter.event('BACKEND_STOP', {'frames': adapter.frames, 'pendingRetained': pending is not None})
            result = adapter.close()
            transport=hub.stop()
            result.update(transport=transport,status='HOST_CAPTURE_CLOSED_NOT_FLIGHT_ACCEPTANCE', clock=clock_state,
                          pendingUnadmittedRetained=pending is not None)
        except Exception as exc:
            error = type(exc).__name__ + ':' + str(exc)
            try:
                adapter.journal.abort(error)
            except Exception:
                pass
            result = {'status': 'FAILED_RETAINED_PREFIX', 'error': error, 'frames': adapter.frames,
                      'stageRows':adapter.stage_rows,'journalCompletedFrames':adapter.journal.frames,
                      'lastFrameAttempt':adapter.current,
                      'run': run, 'epoch': epoch, 'boot': boot, 'publicationAllowed': False, 'guardDiagnostic': getattr(exc,'diagnostic',adapter.journal.guard.diagnostic())}
        finally:
            if not hub.done.is_set():
                try:hub.stop()
                except Exception:pass
            if clock is not None:
                clock.close()
    result['atUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['boot'] = boot
    exclusive(out / 'backend-result.json', canonical(result) + b'\n')
    print(json.dumps({'status': result['status'], 'run': run, 'epoch': epoch, 'boot': boot,
                      'frames': adapter.frames, 'error': error,
                      'stageRows':adapter.stage_rows,'journalCompletedFrames':adapter.journal.frames,
                      'commitAnchor': result.get('commitAnchor'),'transportCommitAnchor':result.get('transport',{}).get('commitAnchor'), 'guardDiagnostic': result.get('guardDiagnostic'),
                      'scope': 'LIVE_PARENT_CHANNEL_LOCAL_SYNC_ACK_NOT_REMOTE_AUTH'}), flush=True)
    raise SystemExit(1 if error else 0)


if __name__ == '__main__':
    main()
