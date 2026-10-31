"""Single-owner external-FDM integration of the sealed M1 journal foundation."""
import json
import struct
import time
import hashlib
from pathlib import Path
from .journal import Policy, SegmentedJournal
from pilot.betaintegrated01.runtime.ap_stage import exclusive, canonical

SERVO = struct.Struct('<HHI16H')


class FrameAdapter:
    def __init__(self, root, run, epoch, model, *, max_frames, peer=None, io=None):
        if type(max_frames) is not int or not 1 <= max_frames <= 2**32:
            raise ValueError('FRAME_BOUND')
        self.model, self.max_frames, self.peer = model, max_frames, peer
        self.root = Path(root)
        self.frames = 0
        self.stage_rows = 0
        self.current = None
        self.origin_ns = time.monotonic_ns()
        self.failed = self.closed = False
        self.first_rx = self.last_rx = None
        self.journal = SegmentedJournal(root, run, epoch, Policy(
            segment_bytes=8 * 1024 * 1024, quota_bytes=max_frames * 8192 + 16 * 2**20,
            max_record_bytes=2048, max_segments=max(32, (max_frames * 8192 // (8 * 1024 * 1024)) + 64),
            termination_reserve_bytes=16384), io=io)
        self.journal.append_event('TIMING_ORIGIN', {'hostMonotonicNs': self.origin_ns,
                                  'stageDomain': 'HOST_MONOTONIC_RELATIVE_TO_ORIGIN'})

    def event(self, kind, data):
        if self.failed or self.closed:
            raise RuntimeError('FRAME_ADAPTER_CLOSED')
        self.journal.append_event(kind, data)

    def receive(self, raw, peer, send, *, clock_read):
        """No replay or resend: one admitted servo frame, one fsynced sensor intent."""
        if self.failed or self.closed:
            raise RuntimeError('FRAME_ADAPTER_CLOSED')
        current = {'phase': 'VALIDATION', 'journalAdmissionAttempted': False,
                   'localCallbackInvoked': False, 'localReturnKnown': False,
                   'SENTGroupAcknowledged': False, 'attemptedStage': None}
        self.current = current
        try:
            if type(raw) is not bytes or len(raw) != SERVO.size:
                raise ValueError('SERVO_LENGTH')
            magic, rate, frame, *pwm = SERVO.unpack(raw)
            if magic != 18458 or rate != 1200 or frame != self.frames:
                raise ValueError('SERVO_MAGIC_RATE_OR_FRAME')
            if self.frames >= self.max_frames:
                raise ValueError('ADMITTED_FRAME_CAPACITY')
            if type(peer) is not tuple or len(peer) != 2 or type(peer[0]) is not str or type(peer[1]) is not int:
                raise ValueError('SERVO_PEER')
            if self.peer is None:
                self.peer = peer
            if peer != self.peer:
                raise ValueError('FOREIGN_SERVO_PEER')
            if any(not 0 <= value <= 2200 for value in pwm):
                raise ValueError('PWM_BOUND')
            def fresh_bracket():
                bracket = clock_read()
                now = time.monotonic_ns()
                if (type(bracket) is not dict or type(bracket.get('id')) is not int or
                        type(bracket.get('hostReceiveNs')) is not int or
                        type(bracket.get('offsetLowNs')) is not int or type(bracket.get('offsetHighNs')) is not int or
                        bracket['offsetLowNs'] > bracket['offsetHighNs'] or
                        not 0 <= now - bracket['hostReceiveNs'] <= 250_000_000):
                    raise ValueError('CLOCK_BRACKET_NOT_FRESH_250MS')
                return bracket, now
            bracket, checked_ns = fresh_bracket()
            rx = time.monotonic_ns()
            row = {'receiveSinceOriginNs': rx-self.origin_ns, 'wireFrame': frame, 'rateHz': rate,
                   'clockCheckAtReceiveSinceOriginNs': checked_ns-self.origin_ns,
                   'clockIDAtReceive': bracket['id'], 'clockAgeAtReceiveNs': checked_ns-bracket['hostReceiveNs']}
            if self.first_rx is None:
                self.first_rx = rx
            self.last_rx = rx

            def compute(body):
                current['phase'] = 'COMPUTING'
                row['computeBeginSinceOriginNs'] = time.monotonic_ns()-self.origin_ns
                sensor = self.model.step(pwm, 1 / rate)
                row['computeEndSinceOriginNs'] = time.monotonic_ns()-self.origin_ns
                result = ('\n' + json.dumps(sensor, separators=(',', ':'), allow_nan=False) + '\n').encode()
                if len(result) > 768:
                    raise ValueError('SENSOR_BOUND_768')
                row['sensorBytes'] = len(result)
                current['sensorBytes'] = len(result)
                current['phase'] = 'INTENT_WRITE_SYNC_PENDING'
                return result

            def dispatch(body):
                current['phase'] = 'BEFORE_SEND_CLOCK_RECHECK'
                bracket, checked_ns = fresh_bracket()
                row['clockIDBeforeSend'] = bracket['id']
                row['clockCheckBeforeSendSinceOriginNs'] = checked_ns-self.origin_ns
                row['clockAgeBeforeSendNs'] = checked_ns-bracket['hostReceiveNs']
                row['sendBeginSinceOriginNs'] = time.monotonic_ns()-self.origin_ns
                current['phase'] = 'SOCKET_CALLBACK'
                current['localCallbackInvoked'] = True
                result = send(body)
                current['localReturnedBytes'] = result if type(result) is int and -(2**63)<=result<2**63 else None
                current['localReturnKnown'] = type(result) is int and result == len(body)
                current['phase'] = 'LOCAL_RETURN_SNT_RECORD_PENDING'
                row['sendEndSinceOriginNs'] = time.monotonic_ns()-self.origin_ns
                return result

            current['journalAdmissionAttempted'] = True
            current['phase'] = 'JOURNAL_FRAME_GROUP'
            self.journal.record_frame(frame, raw, compute, dispatch)
            current['SENTGroupAcknowledged'] = True
            current['phase'] = 'SENT_GROUP_DURABLE'
            self.frames += 1
            row['frameGroupEndSinceOriginNs'] = time.monotonic_ns()-self.origin_ns
            current['phase'] = 'STAGE_APPEND'
            current['attemptedStage'] = dict(row)
            self.journal.append_stage(frame, row)
            self.stage_rows += 1
            current['phase'] = 'FRAME_AND_STAGE_COMPLETE'
            return {'frames': self.frames, 'modelSeconds': self.model.t, 'lastFrame': frame}
        except Exception as exc:
            self.reject(raw, peer, type(exc).__name__ + ':' + str(exc), receive_context=current)
            raise

    def reject(self, raw, peer, reason, *, socket_truncated=False, receive_context=None):
        self.failed = True
        body = raw if type(raw) is bytes else b''
        context = receive_context or {'phase':'REJECTED_BEFORE_FRAME_API','journalAdmissionAttempted':False,
                    'localCallbackInvoked':False,'localReturnKnown':False,'SENTGroupAcknowledged':False,'attemptedStage':None}
        try:
            exclusive(self.root.parent / (self.root.name + '-rejected.json'), canonical({
                'reason': reason[:512], 'rawHex': body[:1025].hex(), 'inputBytes': len(body),
                'rawSHA256': hashlib.sha256(body).hexdigest(), 'peer': repr(peer)[:256],
                'socketTruncated': bool(socket_truncated), 'exactReceivedBytesRetained': not socket_truncated and len(body) <= 1025,
                'retainedPrefixBytes': min(len(body), 1025), 'completedFrames': self.frames,
                'completedStageRows':self.stage_rows, 'journalCompletedFrames':self.journal.frames,
                'journalPhaseAtFailure':self.journal.phase, 'frameAttempt':dict(context),
                'alreadyAdmitted': True if context['SENTGroupAcknowledged'] else None if context['journalAdmissionAttempted'] else False,
                'inputAdmissionClassification': 'COMPLETE_SENT_GROUP_ACKNOWLEDGED' if context['SENTGroupAcknowledged'] else 'JOURNAL_ATTEMPTED_OR_PARTIAL' if context['journalAdmissionAttempted'] else 'NOT_ADMITTED_VALIDATION_REJECTION',
                'sensorReplay': False, 'rejectionIsNotAdmittedFrame': not context['journalAdmissionAttempted']}) + b'\n')
        finally:
            self.journal.abort('FRAME_ADAPTER:' + reason[:512])

    def close(self):
        if self.failed or self.closed:
            raise RuntimeError('FRAME_ADAPTER_CLOSED')
        result = self.journal.close()
        self.closed = True
        wall = (self.last_rx - self.first_rx) / 1e9 if self.frames > 1 else None
        return {**result, 'frames': self.frames, 'modelSeconds': self.model.t,
                'stageRows':self.stage_rows,
                'receiveWallSeconds': wall,
                'actualRTF': ((self.frames - 1) / 1200 / wall) if wall else None,
                'requestedSpeedup': 1, 'capMs': 500, 'framesDropped': 0,
                'APExecutionAccepted': False, 'HeraCalibrated': False}
