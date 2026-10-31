"""Bounded actual filesystem/mock seam checks; starts no AP, Android or sockets."""
from pathlib import Path
import base64
import hashlib
import json
import os
import struct
import sys
import time

R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R))
from pilot.betaintegrated01.runtime.frame_adapter import FrameAdapter, SERVO
from pilot.betaintegrated01.runtime.ap_stage import StageDrainer, EVENT, verify_stage
from pilot.betaintegrated01.runtime.physics import Model, profile
from pilot.betaintegrated01.runtime.physics_reference import Model as OriginalModel
from pilot.betaintegrated01.journal import verify_journal, FileIO


def main():
    destination = R / 'evidence/betaintegrated01-m1runtime/host/mock02'
    destination.mkdir()
    results = []
    mismatches = []
    comparisons = 0
    for load in ('empty', 'central', 'offset'):
        for wind in ('calm', 'crosswind', 'gust'):
            config = profile(load, wind, 32)
            new, reference = Model(config), OriginalModel(config)
            for frame in range(200):
                pwm = [1000 + (frame * (i + 1) * 17 % 901) for i in range(16)]
                a = json.dumps(new.step(pwm, 1/1200), separators=(',', ':'), allow_nan=False).encode()
                b = json.dumps(reference.step(pwm, 1/1200), separators=(',', ':'), allow_nan=False).encode()
                comparisons += 1
                if a != b:
                    mismatches.append({'load': load, 'wind': wind, 'frame': frame})
                    break
    assert not mismatches, mismatches
    results.append({'case': 'exact_original_model_differential', 'comparisons': comparisons, 'profiles': 9, 'status': 'PASS'})
    operations = []
    io = FileIO(hook=lambda operation, path, size: operations.append(operation))
    adapter = FrameAdapter(destination / 'normal', 'r01', 'e01', Model(profile()), max_frames=32, io=io)
    sent = []
    for frame in range(32):
        packet = SERVO.pack(18458, 1200, frame, *([1000] * 16))
        def send(body):
            assert 'fsync' in operations
            operations.clear()
            sent.append(body)
            return len(body)
        adapter.receive(packet, ('127.0.0.1', 45000), send, clock_read=lambda: {'id': 1, 'hostReceiveNs': time.monotonic_ns(), 'offsetLowNs': 0, 'offsetHighNs': 10})
    receipt = adapter.close()
    cold = verify_journal(destination / 'normal', 'r01', 'e01', expected_commit=receipt['commitAnchor'])
    assert cold['frames'] == 32 and cold['stageRows'] == 32 and not cold['publicationAllowed']
    assert len(sent) == 32
    results.append({'case': 'frame_group_fsync_stage_exact32', 'status': 'PASS', 'cold': cold})
    invalid = FrameAdapter(destination / 'badframe', 'r02', 'e02', Model(profile()), max_frames=32)
    try:
        invalid.receive(SERVO.pack(18458, 1200, 1, *([1000] * 16)), ('127.0.0.1', 45000), lambda body: (_ for _ in ()).throw(AssertionError('MUST_NOT_SEND')), clock_read=lambda: None)
        raise AssertionError('MUST_REJECT_GAP')
    except ValueError:
        pass
    assert invalid.failed and (destination / 'badframe-rejected.json').exists()
    results.append({'case': 'rejected_gap_exact_raw_zero_send', 'status': 'PASS'})
    short = FrameAdapter(destination / 'shortsend', 'r03', 'e03', Model(profile()), max_frames=32)
    try:
        short.receive(SERVO.pack(18458, 1200, 0, *([1000] * 16)), ('127.0.0.1', 45000), lambda body: len(body)-1, clock_read=lambda: {'id': 1, 'hostReceiveNs': time.monotonic_ns(), 'offsetLowNs': 0, 'offsetHighNs': 10})
        raise AssertionError('MUST_REJECT_SHORT_SEND')
    except RuntimeError:
        pass
    cold = verify_journal(destination / 'shortsend', 'r03', 'e03')
    assert cold['state'] == 'INCOMPLETE_RECORDING'
    results.append({'case': 'short_send_unknown_not_complete', 'status': 'PASS', 'cold': cold})
    stage = StageDrainer(destination / 'stage', 'r01', 'e01', 'b01', events_per_chunk=7, max_events=90)
    for i in range(90):
        frame, index = divmod(i, 10)
        kind = [10, 11, 12, 13, 14, 20, 21, 22, 23, 24][index]
        stage.feed(EVENT.pack(i, frame, kind, 42, i+1, i+1, 0, 0, 0))
    terminal = stage.finish(ap_exit=-15, eof=True)
    cold = verify_stage(destination / 'stage', 'r01', 'e01', 'b01', terminal_sha256=terminal['terminalSHA256'])
    assert cold['events'] == 90 and cold['segments'] == 13
    results.append({'case': 'AP_stage90_across13segments', 'status': 'PASS', 'cold': cold})
    paths = [R / 'pilot/betaintegrated01/runtime'/n for n in ['frame_adapter.py', 'ap_stage.py', 'clock_socket.py', 'backend.py', 'ap_supervisor.py', 'physics.py', 'physics_reference.py']]
    report = {'status': 'PASS_BUILDER_SCOPED_MOCK', 'results': results,
              'sourceSHA256': {str(p.relative_to(R)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'APLaunches': 0, 'AndroidLaunches': 0, 'socketLaunches': 0,
              'sourceExactDifferentialIsNotFirmwareOrHeraCalibration': True}
    (destination / 'results.json').open('x').write(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'groups': len(results), 'modelComparisons': comparisons}))


if __name__ == '__main__':
    main()
