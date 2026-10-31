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
from importlib import import_module
FrameAdapter=import_module('planning.betaintegrated01.cockpit05-compact10.runtime.frame_adapter').FrameAdapter
DiskGuardError=import_module('planning.betaintegrated01.cockpit05-clockowner02.admission').DiskGuardError
ClockOwner=import_module('planning.betaintegrated01.cockpit05-clockterm14.runtime.owner').ClockOwner
from pilot.betaintegrated01.runtime.physics import Model, profile
TransportHub=import_module('planning.betaintegrated01.cockpit05-clockowner02.runtime.transport').TransportHub


def cleanup_runtime(clock,hub):
    clock.stop_event.set();hub.stop_event.set();errors=[]
    try:clock.close(timeout=20)
    except BaseException as error:errors.append(repr(error))
    try:
        if not hub.done.is_set():hub.stop()
    except BaseException as error:errors.append(repr(error))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if config['bind'] != ['127.0.0.1', 9012] or config['requestedSpeedup'] != 1 or config['capMs'] != 500:
        raise ValueError('CONFIGURATION_ALLOWLIST')
    from .policy import validate_recording_policy
    policy_amendment = validate_recording_policy(config)
    import_module('planning.betaintegrated01.cockpit05-clockterm14.flight.contract').validate_native_selection(config)
    duration = config['maximumSeconds']
    if type(duration) is not int or duration not in (180,1960):
        raise ValueError('DURATION')
    run, epoch, boot = config['run'], config['epoch'], config['boot']
    out = Path(config['evidence'])
    if not out.is_dir():
        raise ValueError('EVIDENCE_PARENT')
    origin_ns=time.monotonic_ns()
    clock = ClockOwner(out,run,epoch,boot,duration,policy_amendment['amendmentSHA256'],origin_ns=origin_ns)
    hub=TransportHub(out,run,epoch,boot,duration)
    try:
        clock.start()
        hub.start()
        try:
            adapter = FrameAdapter(out / 'journal', run, epoch, Model(profile(config['load'], config['wind'], config['seed'])),
                                   max_frames=duration * 1200, maximum_seconds=duration, clock_owner=clock,origin_ns=origin_ns)
        except DiskGuardError as exc:
            hub.stop_event.set()
            print(json.dumps({'status':'FAILED_DURING_REAL_GUARD_PRIME','run':run,'epoch':epoch,'boot':boot,
                              'frames':0,'stageRows':0,'error':str(exc),'guardDiagnostic':exc.diagnostic,
                              'commitAnchor':None,'journalWritesAccepted':False}),flush=True)
            raise SystemExit(1)
        wait_deadline=time.monotonic()+5
        while not(hub.ready.wait(.1)and clock.ready.is_set()):
            adapter.journal.guard.check()
            if hub.error or clock.failed or time.monotonic()>wait_deadline:
                hub.stop_event.set();adapter.journal.abort('TRANSPORT_PRIME_OR_READY_FAILED')
                raise RuntimeError('TRANSPORT_PRIME_OR_READY_FAILED:'+str(hub.error))
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
                      'boot': boot, 'endpoint': config['bind'], 'source': 'CLOCKTERM14_EXPLICIT_HOST_DELIVERY_RECORDING_POLICY', 'externalRecordingPolicy': policy_amendment, 'guardPrimed': True, 'guardPolicyVersion': 2, 'guardPriming': adapter.journal.guard.prime_receipt,'transportGuardPriming':hub.journal.guard.prime_receipt,'transportReady':True,'clockOwnerReady':True,'clockGuardPriming':clock.journal.guard.prime_receipt}) + b'\n')
            try:
                while True:
                    if hub.error:raise RuntimeError('TRANSPORT_HUB:'+hub.error)
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
                        with adapter.profile.measure('recvwait'):
                            raw, ancillary, flags, address = sock.recvmsg(1025)
                    except socket.timeout:
                        adapter.journal.guard.check()
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
                adapter.event('BACKEND_STOP', {'frames': adapter.frames, 'pendingRetained': pending is not None})
                result = adapter.close()
                host_profile=adapter.profile.snapshot();host_profile.update(run=run,epoch=epoch,boot=boot,journalClosed=True,initialGuardPrimeAndConstructorChecksProfiled=False)
                body=canonical(host_profile)+b'\n'
                if len(body)>131072:raise ValueError('HOST_PROFILE128KiB_BOUND')
                adapter.journal.guard.check(len(body));exclusive(out/'host-profile.json',body);result['hostProfileSHA256']=__import__('hashlib').sha256(body).hexdigest()
                transport=hub.stop()
                result.update(clockCommitAnchor=clock_state['commitAnchor'],transport=transport,status='HOST_CAPTURE_CLOSED_NOT_FLIGHT_ACCEPTANCE', clock=clock_state,
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
                if not clock.done.is_set():
                    try:clock.close()
                    except Exception:pass
    finally:
        cleanup_runtime(clock,hub)
    clock._write_delivery()
    delivery_path=out/'clock-delivery-diagnostic.json'
    result['clockDeliveryDiagnosticSHA256']=__import__('hashlib').sha256(delivery_path.read_bytes()).hexdigest()if delivery_path.is_file()else None
    result['clockDeliveryDiagnosticError']=clock.delivery_publication_error
    result['atUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['boot'] = boot
    exclusive(out / 'backend-result.json', canonical(result) + b'\n')
    print(json.dumps({'status': result['status'], 'run': run, 'epoch': epoch, 'boot': boot,
                      'frames': adapter.frames, 'error': error,
                      'stageRows':adapter.stage_rows,'journalCompletedFrames':adapter.journal.frames,
                      'hostProfileSHA256':result.get('hostProfileSHA256'),'clockDeliveryDiagnosticSHA256':result.get('clockDeliveryDiagnosticSHA256'),'clockDeliveryDiagnosticError':result.get('clockDeliveryDiagnosticError'),
                      'commitAnchor': result.get('commitAnchor'),'transportCommitAnchor':result.get('transport',{}).get('commitAnchor'),'clockCommitAnchor':result.get('clockCommitAnchor'), 'guardDiagnostic': result.get('guardDiagnostic'),
                      'scope': 'LIVE_PARENT_CHANNEL_LOCAL_SYNC_ACK_NOT_REMOTE_AUTH'}), flush=True)
    raise SystemExit(1 if error else 0)


if __name__ == '__main__':
    main()
