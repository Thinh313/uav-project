"""Owned host JSON FDM. No MAVLink writer; no automatic flight dispatch."""
from pathlib import Path
import argparse
import datetime
import json
import os
import signal
import socket
import time
from .ap_stage import canonical, exclusive
from .frame_adapter import FrameAdapter
from .clock_socket import ClockSocket
from .physics import Model, profile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if config['bind'] != ['127.0.0.1', 9012] or config['requestedSpeedup'] != 1 or config['capMs'] != 500:
        raise ValueError('CONFIGURATION_ALLOWLIST')
    duration = config['maximumSeconds']
    if type(duration) is not int or not 1 <= duration <= 1800:
        raise ValueError('DURATION')
    run, epoch, boot = config['run'], config['epoch'], config['boot']
    out = Path(config['evidence'])
    if not out.is_dir():
        raise ValueError('EVIDENCE_PARENT')
    adapter = FrameAdapter(out / 'journal', run, epoch, Model(profile(config['load'], config['wind'], config['seed'])),
                           max_frames=duration * 1200)
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
                  'boot': boot, 'endpoint': config['bind'], 'source': 'M1_ISOLATED_EXTERNAL_FDM'}) + b'\n')
        try:
            clock = ClockSocket(run, epoch, boot, lambda row: adapter.event('CLOCK', row),
                                maximum_seconds=duration,
                                diagnostic=lambda row: exclusive(out / 'clock-rejected.json', canonical(row) + b'\n'))
            while True:
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
            result.update(status='HOST_CAPTURE_CLOSED_NOT_FLIGHT_ACCEPTANCE', clock=clock_state,
                          pendingUnadmittedRetained=pending is not None)
        except Exception as exc:
            error = type(exc).__name__ + ':' + str(exc)
            try:
                adapter.journal.abort(error)
            except Exception:
                pass
            result = {'status': 'FAILED_RETAINED_PREFIX', 'error': error, 'frames': adapter.frames,
                      'run': run, 'epoch': epoch, 'boot': boot, 'publicationAllowed': False}
        finally:
            if clock is not None:
                clock.close()
    result['atUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['boot'] = boot
    exclusive(out / 'backend-result.json', canonical(result) + b'\n')
    print(json.dumps({'status': result['status'], 'run': run, 'epoch': epoch, 'boot': boot,
                      'frames': adapter.frames, 'error': error,
                      'commitAnchor': result.get('commitAnchor'),
                      'scope': 'LIVE_PARENT_CHANNEL_LOCAL_SYNC_ACK_NOT_REMOTE_AUTH'}), flush=True)
    raise SystemExit(1 if error else 0)


if __name__ == '__main__':
    main()
