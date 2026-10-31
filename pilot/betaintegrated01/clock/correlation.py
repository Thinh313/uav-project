"""Bounded, sink-before-publication clock logic. No socket, grant or flight API.

The injected sink MUST durably retain each event before returning. Its failure
poisons this instance. Completed records live in that journal, not an unbounded
in-memory map. A caller must bind context to its observed transport/boot; this
module does not authenticate a peer or attest a remote clock.
"""
from collections import OrderedDict
from dataclasses import dataclass
import copy
import hashlib
import struct
import threading
from functools import wraps

U64_MAX = (1 << 64) - 1


class ClockError(RuntimeError):
    pass


def serialized(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return call


def uint(value, name):
    if type(value) is not int or not 0 <= value <= U64_MAX:
        raise ClockError(name + '_UINT64')
    return value


@dataclass(frozen=True)
class Context:
    run: str
    epoch: str
    boot: str

    def __post_init__(self):
        for value in (self.run, self.epoch, self.boot):
            if type(value) is not str or not 1 <= len(value) <= 128 or any(
                    ord(c) < 33 or ord(c) > 126 for c in value):
                raise ClockError('CONTEXT_IDENTIFIER')


class BoundedCorrelator:
    def __init__(self, context, peer, sink, *, max_pending=8, recent_limit=64,
                 timeout_ns=300_000_000, fresh_ns=250_000_000,
                 max_step_ns=2_000_000_000, max_offset_step_ns=50_000_000):
        if type(context) is not Context or not callable(sink):
            raise ClockError('CONTEXT_AND_DURABLE_SINK_REQUIRED')
        if (type(peer) is not tuple or len(peer) != 2 or
                type(peer[0]) is not str or not 1 <= len(peer[0]) <= 253 or
                type(peer[1]) is not int or not 1 <= peer[1] <= 65535):
            raise ClockError('PEER_REQUIRED')
        for value, lo, hi in ((max_pending, 1, 4096), (recent_limit, 0, 4096),
                              (timeout_ns, 1, U64_MAX), (fresh_ns, 1, U64_MAX),
                              (max_step_ns, 1, U64_MAX),
                              (max_offset_step_ns, 0, U64_MAX)):
            if type(value) is not int or not lo <= value <= hi:
                raise ClockError('POLICY_BOUND')
        if max_step_ns < timeout_ns:
            raise ClockError('SUSPEND_BOUND_BELOW_TIMEOUT')
        self.context, self.peer, self._sink = context, tuple(peer), sink
        self.max_pending, self.recent_limit = max_pending, recent_limit
        self.timeout_ns, self.fresh_ns, self.max_step_ns = timeout_ns, fresh_ns, max_step_ns
        self.max_offset_step_ns = max_offset_step_ns
        self._lock, self._writing = threading.RLock(), False
        self._pending, self._recent = OrderedDict(), OrderedDict()
        self._max_id, self._last_now, self._seq = -1, None, 0
        self._last_observed = None
        self._failed, self._calibration, self._last_guest_send = None, None, None
        self._pending_peak = self._recent_peak = 0

    def _write(self, kind, payload):
        if self._failed:
            raise ClockError('CLOCK_FAILED:' + self._failed)
        row = {'format': 'aeris-clock-event', 'version': 1,
               'sequence': self._seq + 1, 'run': self.context.run,
               'epoch': self.context.epoch, 'boot': self.context.boot,
               'kind': kind, **copy.deepcopy(payload)}
        try:
            self._writing = True
            self._sink(copy.deepcopy(row))
        except Exception as exc:
            self._failed = 'DURABLE_SINK_FAILED:' + type(exc).__name__
            raise ClockError(self._failed) from exc
        finally:
            self._writing = False
        self._seq += 1

    def _check(self, now, context):
        if self._failed:
            raise ClockError('CLOCK_FAILED:' + self._failed)
        if self._writing:
            raise ClockError('REENTRANT_CLOCK_OPERATION')
        uint(now, 'MONOTONIC_TIME')
        if type(context) is not Context or context != self.context:
            self._write('REJECTED_CONTEXT', {'hostNs': now})
            raise ClockError('FOREIGN_CONTEXT')
        if self._last_observed is not None:
            reason = ('CLOCK_REGRESSION' if now < self._last_observed else
                      'SUSPEND_OR_STALE_GAP' if now - self._last_observed > self.max_step_ns else None)
            if reason:
                self._write(reason, {'hostNs': now, 'previousHostNs': self._last_observed})
                self._failed = reason
                raise ClockError(reason)
        self._last_observed = now

    def _remember(self, rid, item):
        if self.recent_limit:
            self._recent[rid] = item
            while len(self._recent) > self.recent_limit:
                self._recent.popitem(last=False)
        self._recent_peak = max(self._recent_peak, len(self._recent))

    def _evicted_on_retire(self):
        if self.recent_limit and len(self._recent) >= self.recent_limit:
            return next(iter(self._recent))
        return None

    def _expire(self, now):
        for rid in list(self._pending):
            sent = self._pending[rid]
            if now - sent > self.timeout_ns:
                self._write('TIMEOUT', {'id': rid, 'hostSendNs': sent,
                            'hostNs': now, 'evictedRecentID': self._evicted_on_retire(),
                            'freshCalibration': False})
                del self._pending[rid]
                self._remember(rid, (sent, 'TIMEOUT'))

    @serialized
    def register(self, rid, sent_ns, context):
        self._check(sent_ns, context)
        uint(rid, 'REQUEST_ID')
        if rid <= self._max_id:
            self._write('REJECTED_ID_REUSE', {'id': rid, 'hostNs': sent_ns,
                        'maxRegisteredID': self._max_id})
            self._last_now = sent_ns
            raise ClockError('NON_INCREASING_REQUEST_ID')
        self._expire(sent_ns)
        if len(self._pending) >= self.max_pending:
            self._write('REJECTED_PENDING_BOUND', {'id': rid, 'hostNs': sent_ns})
            self._last_now = sent_ns
            raise ClockError('PENDING_BOUND')
        self._write('REGISTERED', {'id': rid, 'hostSendNs': sent_ns})
        self._pending[rid] = sent_ns
        self._max_id, self._last_now = rid, sent_ns
        self._pending_peak = max(self._pending_peak, len(self._pending))

    @serialized
    def receive(self, raw, peer, now_ns, context):
        self._check(now_ns, context)
        if type(raw) is not bytes:
            raise ClockError('RAW_BYTES_REQUIRED')
        packet = {'hostNs': now_ns, 'peer': list(peer) if type(peer) is tuple else repr(peer),
                  'rawLength': len(raw), 'rawSHA256': hashlib.sha256(raw).hexdigest()}
        if len(raw) <= 4096:
            packet['rawHex'] = raw.hex()
            packet['rawBytesRetained'] = True
        else:
            packet['rawBytesRetained'] = False
        if peer != self.peer or len(raw) != 56:
            self._write('REJECTED_PACKET', {**packet, 'freshCalibration': False})
            self._last_now = now_ns
            raise ClockError('FOREIGN_OR_MALFORMED_PACKET')
        rid, g1, g2, usage, periods, throttles, throttled = struct.unpack('<7Q', raw)
        self._expire(now_ns)
        if rid in self._pending:
            sent, prior = self._pending[rid], 'PENDING'
        elif rid in self._recent:
            sent, prior = self._recent[rid]
        else:
            status = 'RETIRED_OR_UNKNOWN' if rid <= self._max_id else 'UNKNOWN_FUTURE_ID'
            self._write(status, {**packet, 'id': rid, 'freshCalibration': False})
            self._last_now = now_ns
            return {'id': rid, 'status': status, 'freshCalibration': False}
        low, high = sent - g1, now_ns - g2
        if g2 < g1 or now_ns < sent or low > high:
            self._write('REJECTED_CLOCK_BRACKET', {**packet, 'id': rid,
                        'hostSendNs': sent, 'guestReceiveNs': g1, 'guestSendNs': g2,
                        'offsetLowNs': low, 'offsetHighNs': high, 'freshCalibration': False})
            self._last_now = now_ns
            raise ClockError('INCONSISTENT_CLOCK_BRACKET')
        status = ('MATCHED' if prior == 'PENDING' else 'LATE_MATCHED'
                  if prior == 'TIMEOUT' else 'DUPLICATE_MATCHED')
        fresh = prior == 'PENDING'
        if fresh and self._calibration is not None:
            last_id, last_when, last_low, last_high = self._calibration
            if rid < last_id:
                status, fresh = 'REORDERED_MATCHED', False
            elif g1 < self._last_guest_send or high < last_low - self.max_offset_step_ns or low > last_high + self.max_offset_step_ns:
                self._write('GUEST_CLOCK_DISCONTINUITY', {**packet, 'id': rid,
                            'guestReceiveNs': g1, 'guestSendNs': g2,
                            'offsetLowNs': low, 'offsetHighNs': high,
                            'freshCalibration': False})
                self._failed = 'GUEST_CLOCK_DISCONTINUITY'
                raise ClockError(self._failed)
        result = {'id': rid, 'status': status, 'hostSendNs': sent,
                  'hostReceiveNs': now_ns, 'guestReceiveNs': g1, 'guestSendNs': g2,
                  'offsetLowNs': low, 'offsetHighNs': high,
                  'uncertaintyNs': high - low, 'cgroupUsageUs': usage,
                  'cgroupPeriods': periods, 'cgroupThrottles': throttles,
                  'cgroupThrottledUs': throttled, 'freshCalibration': fresh}
        self._write('RESPONSE', {**packet, **result,
                    'evictedRecentID': self._evicted_on_retire() if prior == 'PENDING' else None})
        if prior == 'PENDING':
            del self._pending[rid]
            self._remember(rid, (sent, status))
            if fresh:
                self._calibration = (rid, now_ns, low, high)
                self._last_guest_send = g2
        elif prior == 'TIMEOUT':
            self._recent[rid] = (sent, 'LATE')
        self._last_now = now_ns
        return result

    @serialized
    def tick(self, now_ns, context):
        self._check(now_ns, context)
        self._expire(now_ns)
        self._write('TICK', {'hostNs': now_ns})
        self._last_now = now_ns

    @serialized
    def invalidate(self, reason, now_ns, context):
        self._check(now_ns, context)
        if type(reason) is not str or not 1 <= len(reason) <= 128:
            raise ClockError('REASON_BOUND')
        self._write('INVALIDATED', {'hostNs': now_ns, 'reason': reason})
        self._last_now, self._failed = now_ns, reason

    @serialized
    def calibration(self, now_ns, context):
        self._check(now_ns, context)
        if self._calibration is None:
            return None
        rid, when, low, high = self._calibration
        if now_ns < when or now_ns - when > self.fresh_ns:
            return None
        return {'id': rid, 'hostReceiveNs': when, 'offsetLowNs': low,
                'offsetHighNs': high, 'uncertaintyNs': high - low,
                'ageNs': now_ns - when, 'scope': 'CORRELATED_NOT_AUTHENTICATED_OR_AIRCRAFT_SAFE'}

    @serialized
    def snapshot(self):
        return {'format': 'aeris-clock-state', 'version': 1,
                'run': self.context.run, 'epoch': self.context.epoch, 'boot': self.context.boot,
                'pending': len(self._pending), 'recent': len(self._recent),
                'pendingPeak': self._pending_peak, 'recentPeak': self._recent_peak,
                'maxPending': self.max_pending, 'recentLimit': self.recent_limit,
                'timeoutNs': self.timeout_ns, 'freshNs': self.fresh_ns,
                'maxStepNs': self.max_step_ns, 'maxOffsetStepNs': self.max_offset_step_ns,
                'maxRegisteredID': self._max_id, 'journalEvents': self._seq,
                'failed': self._failed, 'authorityRestorable': False,
                'calibrationState': ('FAILED' if self._failed else
                                     'BOOTSTRAP_UNCALIBRATED' if self._calibration is None else
                                     'BRACKET_REQUIRES_FRESHNESS_CHECK'),
                'holdsFullEventHistory': False}
