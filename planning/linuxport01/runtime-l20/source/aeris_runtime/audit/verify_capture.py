"""Cold cross-layer receiver. Integrity/model replay, never flight execution."""
import base64
import hashlib
import json
import struct
from collections import OrderedDict
from pathlib import Path
from ..foundation.ap_stage09 import EVENT, verify_stage, records
from pilot.betaintegrated01.runtime.physics_reference import Model
from pilot.betaintegrated01.runtime.physics_reference import profile
from importlib import import_module
verify_journal=import_module('aeris_runtime.foundation.journal_base').verify_journal
from .clock_receiver import verify_clock,verify_frame_reference
from ..foundation.fdm09 import original_lines,CODEC


def verify_capture(out, run, epoch, boot, *, expected_host_anchor, expected_stage_anchor,
                   load='empty', wind='calm', seed=32,expected_clock_anchor=None,source_amendment=None,maximum_seconds=1960):
    out = Path(out)
    journal = verify_journal(out / 'journal', run, epoch, expected_commit=expected_host_anchor,expected_physical_codec=CODEC)
    clocks=verify_clock(out,run,epoch,boot,expected_anchor=expected_clock_anchor,source_amendment=source_amendment,maximum_seconds=maximum_seconds)
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
            for line in original_lines(f,run,epoch):
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
                        if data['hostMonotonicNs']!=clocks['originHostNs']:raise ValueError('CLOCK_FRAME_ORIGIN_BINDING')
                    elif event_kind == 'STAGE':
                        fields = data['fields']
                        assert data['frame'] == seen_stage_frame + 1
                        seen_stage_frame = data['frame']
                        assert len(origins)==1
                        verify_frame_reference(fields,origins[0],clocks['publications'])
                        assert fields.get('clockAdmissionScopeVersion')==9 and fields.get('originalReceiveKind')==1
                        assert type(fields.get('originalReceiveSinceOriginNs'))is int and 0<=fields['originalReceiveSinceOriginNs']==fields['receiveSinceOriginNs']<=fields['clockAdmissionSinceOriginNs']==fields['clockCheckAtAdmissionSinceOriginNs']
                        assert type(fields.get('unadmittedClockWaitNs'))is int and 0<=fields['unadmittedClockWaitNs']<=100000000
                        assert fields['clockAdmissionSinceOriginNs']-fields['originalReceiveSinceOriginNs']<=500000000
                        if fields['unadmittedClockWaitNs']:assert 0<=fields['clockWaitPriorID']<fields['clockIDAtAdmission']
                        times = [fields[name] for name in ('receiveSinceOriginNs','clockCheckAtAdmissionSinceOriginNs', 'computeBeginSinceOriginNs',
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
            for record,physical in records(f):
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
                if event_frame < frame:
                    assert kind not in group_kinds, 'DUPLICATE_ADMITTED_AP_STAGE_KIND'
                else:
                    if kind == 10:
                        assert arg == 1200 and extra == 0 and result == 0
                    elif kind == 11:
                        assert arg == 40 and result == 40
                    elif kind != 12:
                        raise AssertionError('UNADMITTED_AP_SENSOR_OR_ADVANCE_STAGE')
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
            if group_kinds not in ([10], [10, 11]):
                assert group_kinds[:3] == [10, 11, 12]
                repetitions = group_kinds[3:]
                assert all(kind == (10 if i % 2 == 0 else 11) for i, kind in enumerate(repetitions))
            partial_tail = {'frame': group_frame, 'kinds': group_kinds,
                            'classification': 'UNADMITTED_PENDING_SERVO_WITH_RETRANSMIT_OBSERVATIONS',
                            'servoSendAttempts': group_kinds.count(10),
                            'notGroundOrExecutionEvidence': True}
    assert coverage == frame and frame > 0
    return {'status': 'EXACT_ADMITTED_FRAME_AND_ORIGINAL_MODEL_BYTES_PASS', 'frames': frame,
            'stageRows': stage_rows, 'APCoveredFrames': coverage, 'APEventCount': stage['events'],
            'APExit': stage['apExit'], 'unadmittedTail': partial_tail,
            'clockRegistered':clocks['registered'],'clockMatched':clocks['matched'],'independentClockJournal':clocks['integrity'],'clockPublicationCount':len(clocks['publications']),
            'clockFreshnessCheckedAtReceiveAndBeforeSend': True, 'maximumFrameGroupNs': maximum_group_ns,
            'originalPurePythonReplay': True, 'pacerSourceUnchanged': 'CHECK_SOURCE_PINS_SEPARATELY',
            'publicationAllowed': False, 'APExecutionAccepted': False,
            'HeraCalibrated': False, 'actualRTF': 'READ_BACKEND_AND_TIMING_RECEIPTS_SEPARATELY'}
