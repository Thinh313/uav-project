"""Current-source clock→journal→sensor and stage cold receiver composition."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import time

R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R))
from pilot.betaintegrated01.runtime.frame_adapter import FrameAdapter, SERVO
from pilot.betaintegrated01.runtime.ap_stage import StageDrainer, EVENT
from pilot.betaintegrated01.runtime.verify_capture import verify_capture
from pilot.betaintegrated01.runtime.physics import Model, profile
from pilot.betaintegrated01.clock.correlation import Context, BoundedCorrelator


def main():
    out = R / 'evidence/betaintegrated01-m1runtime/host/composed03'
    out.mkdir()
    adapter = FrameAdapter(out / 'journal', 'r11', 'e11', Model(profile()), max_frames=64)
    context = Context('r11', 'e11', 'b11')
    clock = BoundedCorrelator(context, ('127.0.0.1', 9014), lambda row: adapter.event('CLOCK', row))
    stage = StageDrainer(out / 'ap-stage', 'r11', 'e11', 'b11', events_per_chunk=17, max_events=640)
    sent = 0
    for frame in range(64):
        now = time.monotonic_ns()
        clock.register(frame+1, now, context)
        packet = struct.pack('<7Q', frame+1, now, now, 0, 0, 0, 0)
        clock.receive(packet, ('127.0.0.1', 9014), time.monotonic_ns(), context)
        def send(body):
            nonlocal sent
            sent += 1
            return len(body)
        adapter.receive(SERVO.pack(18458, 1200, frame, *([1000] * 16)), ('127.0.0.1', 45001), send,
                        clock_read=lambda: clock.calibration(time.monotonic_ns(), context))
        for i, kind in enumerate([10, 11, 12, 13, 14, 20, 21, 22, 23, 24]):
            stage.feed(EVENT.pack(frame*10+i, frame, kind, 42, now, now, 0, 0, 0))
    host = adapter.close()
    ap = stage.finish(ap_exit=-15, eof=True)
    cold = verify_capture(out, 'r11', 'e11', 'b11', expected_host_anchor=host['commitAnchor'],
                          expected_stage_anchor=ap['terminalSHA256'])
    assert cold['frames'] == sent == 64 and cold['clockMatched'] == 64
    pins = {str(p.relative_to(R)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (R / 'pilot/betaintegrated01/runtime').glob('*.py')}
    result = {'status': 'PASS_COMPOSED_MOCK_NOT_AP_EXECUTION', 'cold': cold, 'sourceSHA256': pins,
              'APLaunches': 0, 'AndroidLaunches': 0, 'socketLaunches': 0,
              'clockAndAPEvents': 'SYNTHETIC_TEST_INPUTS_REAL_CORRELATOR_AND_FILESYSTEM'}
    (out / 'results.json').open('x').write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'frames': cold['frames'], 'clockMatched': cold['clockMatched']}))


if __name__ == '__main__':
    main()
