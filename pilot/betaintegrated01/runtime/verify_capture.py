"""Cold cross-layer receiver. Integrity/model replay, never flight execution."""
import base64
import hashlib
import json
import struct
from collections import OrderedDict
from pathlib import Path
from .ap_stage import EVENT, verify_stage
from .physics_reference import Model
from .physics import profile
from pilot.betaintegrated01.journal import verify_journal


def verify_capture(out, run, epoch, boot, *, expected_host_anchor, expected_stage_anchor,
                   load='empty', wind='calm', seed=32):
    out = Path(out)
    journal = verify_journal(out / 'journal', run, epoch, expected_commit=expected_host_anchor)
    stage = verify_stage(out / 'ap-stage', run, epoch, boot, terminal_sha256=expected_stage_anchor)
    model = Model(profile(load, wind, seed))
    frame = 0
    raw = None
    sensor = None
    phase = 'RX'
    stage_rows = 0
    origins = []
    clock_registered = 0
    clock_matched = 0
    current_clock_id = None
    current_clock = None
    pending_clock = OrderedDict()
    recent_clock = OrderedDict()
    maximum_clock_id = 0
    seen_stage_frame = -1
    maximum_group_ns = 0
    for p in sorted((out / 'journal').glob('segment-*.jsonl')):
        with p.open('rb') as f:
            for line in f:
                body = json.loads(line)['body']
                kind, payload = body['kind'], body['payload']
                if kind == 'RX':
                    assert phase == 'RX' and body['frame'] == frame
                    raw = base64.b64decode(payload['base64'], validate=True)
                    assert len(raw) == 40
                    magic, rate, wireframe, *pwm = struct.unpack('<HHI16H', raw)
                    assert magic == 18458 and rate == 1200 and wireframe == frame
                    sensor = ('\n' + json.dumps(model.step(pwm, 1/rate), separators=(',', ':'), allow_nan=False) + '\n').encode()
                    phase = 'INTENT'
                elif kind == 'INTENT':
                    assert phase == 'INTENT' and base64.b64decode(payload['base64'], validate=True) == sensor
                    phase = 'SENT'
                elif kind == 'SENT':
                    assert phase == 'SENT'
                    frame += 1
                    phase = 'RX'
                elif kind == 'EVENT':
                    event_kind, data = payload['eventKind'], payload['data']
                    if event_kind == 'TIMING_ORIGIN':
                        origins.append(data['hostMonotonicNs'])
                    elif event_kind == 'CLOCK':
                        assert data['run'] == run and data['epoch'] == epoch and data['boot'] == boot
                        if data['kind'] == 'REGISTERED':
                            rid = data['id']
                            assert type(rid) is int and rid > maximum_clock_id
                            assert type(data['hostSendNs']) is int and data['hostSendNs'] >= 0
                            maximum_clock_id = rid
                            pending_clock[rid] = data['hostSendNs']
                            assert len(pending_clock) <= 8
                            clock_registered += 1
                        elif data['kind'] == 'TIMEOUT':
                            rid = data['id']
                            assert rid in pending_clock and data['hostSendNs'] == pending_clock[rid]
                            assert data['hostNs']-pending_clock[rid] > 300000000
                            recent_clock[rid] = (pending_clock.pop(rid), 'TIMEOUT')
                        elif data['kind'] == 'RESPONSE':
                            for numeric_field in ('rawLength', 'id', 'hostSendNs', 'hostReceiveNs', 'hostNs',
                                                  'offsetLowNs', 'offsetHighNs', 'guestReceiveNs', 'guestSendNs', 'uncertaintyNs'):
                                assert type(data.get(numeric_field)) is int
                            raw_clock = bytes.fromhex(data['rawHex'])
                            assert len(raw_clock) == 56 and data['rawLength'] == 56
                            assert data['rawSHA256'] == hashlib.sha256(raw_clock).hexdigest()
                            rid, g1, g2, usage, periods, throttles, throttled = struct.unpack('<7Q', raw_clock)
                            assert data['id'] == rid and data['peer'] == ['127.0.0.1', 9014]
                            source = pending_clock.get(rid) if rid in pending_clock else recent_clock.get(rid, (None,))[0]
                            assert source is not None and data['hostSendNs'] == source
                            received = data['hostReceiveNs']
                            assert data['hostNs'] == received and received >= source and g2 >= g1
                            low, high = source-g1, received-g2
                            assert low <= high and data['offsetLowNs'] == low and data['offsetHighNs'] == high
                            assert data['guestReceiveNs'] == g1 and data['guestSendNs'] == g2 and data['uncertaintyNs'] == high-low
                            if data['status'] == 'MATCHED':
                                assert rid in pending_clock and data['freshCalibration'] is True
                                assert received-source <= 300000000
                                clock_matched += 1
                                current_clock_id = rid
                                current_clock = (received, low, high)
                                recent_clock[rid] = (pending_clock.pop(rid), 'MATCHED')
                            else:
                                assert data['freshCalibration'] is False and rid in recent_clock
                        while len(recent_clock) > 64:
                            recent_clock.popitem(last=False)
                    elif event_kind == 'STAGE':
                        fields = data['fields']
                        assert data['frame'] == seen_stage_frame + 1
                        seen_stage_frame = data['frame']
                        assert fields['clockIDAtReceive'] == current_clock_id and fields['clockIDBeforeSend'] == current_clock_id
                        assert current_clock is not None and len(origins) == 1
                        assert origins[0]+fields['clockCheckAtReceiveSinceOriginNs']-current_clock[0] == fields['clockAgeAtReceiveNs']
                        assert origins[0]+fields['clockCheckBeforeSendSinceOriginNs']-current_clock[0] == fields['clockAgeBeforeSendNs']
                        assert 0 <= fields['clockAgeAtReceiveNs'] <= 250000000 and 0 <= fields['clockAgeBeforeSendNs'] <= 250000000
                        times = [fields[name] for name in ('clockCheckAtReceiveSinceOriginNs', 'receiveSinceOriginNs', 'computeBeginSinceOriginNs',
                                 'computeEndSinceOriginNs', 'clockCheckBeforeSendSinceOriginNs', 'sendBeginSinceOriginNs', 'sendEndSinceOriginNs', 'frameGroupEndSinceOriginNs')]
                        assert times == sorted(times)
                        maximum_group_ns = max(maximum_group_ns, times[-1]-times[0])
                        stage_rows += 1
    assert phase == 'RX' and len(origins) == 1 and stage_rows == frame == journal['frames']
    # AP stage groups stream in order. One final unadmitted AP frame is allowed
    # only with the exact separately retained pending-servo packet.
    coverage = 0
    group_frame = None
    group_kinds = []
    last_AP_frame = None
    legal_groups = ([10, 11, 12, 13, 14, 20, 21, 24], [10, 11, 12, 13, 14, 20, 21, 22, 23, 24])
    partial_tail = None
    for p in sorted((out / 'ap-stage').glob('stage-*.bin')):
        with p.open('rb') as f:
            f.readline(4097)
            while True:
                record = f.read(EVENT.size)
                if not record:
                    break
                seq, event_frame, kind, tid, begin, end, arg, extra, result = EVENT.unpack(record)
                if group_frame is None:
                    group_frame = event_frame
                if event_frame != group_frame:
                    if group_frame < frame:
                        assert group_frame == coverage and group_kinds in legal_groups
                        coverage += 1
                    else:
                        raise AssertionError('MORE_THAN_ONE_UNADMITTED_AP_FRAME')
                    group_frame, group_kinds = event_frame, []
                assert kind not in group_kinds, 'DUPLICATE_AP_STAGE_KIND'
                group_kinds.append(kind)
                last_AP_frame = event_frame
    if group_frame is not None:
        if group_frame < frame:
            assert group_frame == coverage and group_kinds in legal_groups
            coverage += 1
        else:
            pending = json.loads((out / 'pending-servo.json').read_text())
            raw_pending = bytes.fromhex(pending['rawHex'])
            assert len(raw_pending) == 40
            magic, rate, pending_frame, *_ = struct.unpack('<HHI16H', raw_pending)
            assert pending['run'] == run and pending['epoch'] == epoch and pending['boot'] == boot
            assert magic == 18458 and rate == 1200 and type(pending['admittedFrames']) is int and pending['admittedFrames'] == frame
            assert group_frame == frame == pending_frame and pending['sensorSent'] is False and pending['modelStepComputed'] is False
            assert pending['reason'] == 'UNADMITTED_AT_OWNED_STOP'
            assert type(pending['peer']) is list and len(pending['peer']) == 2 and type(pending['peer'][0]) is str and type(pending['peer'][1]) is int and 1 <= pending['peer'][1] <= 65535
            assert group_kinds in ([10], [10, 11], [10, 11, 12])
            partial_tail = {'frame': group_frame, 'kinds': group_kinds, 'classification': 'UNADMITTED_PENDING_SERVO'}
    assert coverage == frame and frame > 0
    return {'status': 'EXACT_ADMITTED_FRAME_AND_ORIGINAL_MODEL_BYTES_PASS', 'frames': frame,
            'stageRows': stage_rows, 'APCoveredFrames': coverage, 'APEventCount': stage['events'],
            'APExit': stage['apExit'], 'unadmittedTail': partial_tail,
            'clockRegistered': clock_registered, 'clockMatched': clock_matched,
            'clockFreshnessCheckedAtReceiveAndBeforeSend': True, 'maximumFrameGroupNs': maximum_group_ns,
            'originalPurePythonReplay': True, 'pacerSourceUnchanged': 'CHECK_SOURCE_PINS_SEPARATELY',
            'publicationAllowed': False, 'APExecutionAccepted': False,
            'HeraCalibrated': False, 'actualRTF': 'READ_BACKEND_AND_TIMING_RECEIPTS_SEPARATELY'}
