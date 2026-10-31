"""New diagnostic receive variant; equations/send ordering/freshness unchanged."""
from pathlib import Path
from importlib import import_module
import hashlib,json,struct,time
from pilot.betaintegrated01.runtime.ap_stage import exclusive,canonical
from .diagnostics import DiagnosticIO,exception_chain,send_classification
AcceptedFrameAdapter=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.frame_adapter').FrameAdapter
SERVO=struct.Struct('<HHI16H')


def bounded_bracket(value,now):
    result={'checkedHostNs':now,'calibrationReturnedDictionary':type(value)is dict}
    if type(value)is dict:
        for key in('id','hostReceiveNs','offsetLowNs','offsetHighNs','uncertaintyNs'):
            number=value.get(key)
            result[key]=number if type(number)is int and -(2**63)<=number<2**63 else None
        result['ageNs']=now-result['hostReceiveNs']if result.get('hostReceiveNs')is not None else None
    return result


class FrameAdapter(AcceptedFrameAdapter):
    def __init__(self,*args,**kwargs):
        io=kwargs.pop('io',None)
        if io is not None and not isinstance(io,DiagnosticIO):raise ValueError('DIAGNOSTIC_IO_REQUIRED_NO_SILENT_REPLACEMENT')
        self.diagnostic_io=io or DiagnosticIO();self.latest_diagnostic=None
        super().__init__(*args,io=self.diagnostic_io,**kwargs)

    def capture_failure(self,error,current,raw):
        self.latest_diagnostic={'format':'aeris-clock-send-failure-diagnostic','version':1,
          'exceptionChain':exception_chain(error),'frameAttempt':dict(current),
          'localSendClassification':send_classification(current),'IO':self.diagnostic_io.snapshot(),
          'rawRX_SHA256':hashlib.sha256(raw if type(raw)is bytes else b'').hexdigest(),
          'noFrameReplay':True,'noFrameDrop':True,'freshnessLimitNs':250_000_000,
          'journalFormatOrUNKNOWNRewritten':False,'actualAPExecutionAccepted':False}
        try:
            body=canonical(self.latest_diagnostic)+b'\n'
            if len(body)>32768:raise RuntimeError('DIAGNOSTIC32KiB_BOUND')
            self.journal.guard.check(len(body))
            exclusive(self.root.parent/(self.root.name+'-clockdiag.json'),body)
        except Exception as publication:
            self.latest_diagnostic['diagnosticPublicationError']=exception_chain(publication)
            # Preserve original failure and always let the original reject/abort run.
            return

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
                current['lastClockCheck'] = bounded_bracket(bracket, now)
                prior = current.get('lastAcceptedClock')
                if type(bracket)is not dict and type(prior)is dict and type(prior.get('hostReceiveNs'))is int:
                    current['lastClockCheck']['lastAcceptedHostReceiveNs']=prior['hostReceiveNs']
                    current['lastClockCheck']['lastAcceptedBracketAgeNs']=now-prior['hostReceiveNs']
                if (type(bracket) is not dict or type(bracket.get('id')) is not int or
                        type(bracket.get('hostReceiveNs')) is not int or
                        type(bracket.get('offsetLowNs')) is not int or type(bracket.get('offsetHighNs')) is not int or
                        bracket['offsetLowNs'] > bracket['offsetHighNs'] or
                        not 0 <= now - bracket['hostReceiveNs'] <= 250_000_000):
                    raise ValueError('CLOCK_BRACKET_NOT_FRESH_250MS')
                current['lastAcceptedClock']=bounded_bracket(bracket,now)
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
            self.capture_failure(exc, current, raw)
            self.reject(raw, peer, type(exc).__name__ + ':' + str(exc), receive_context=current)
            raise

