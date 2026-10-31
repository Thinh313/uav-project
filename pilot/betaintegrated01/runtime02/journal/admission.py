"""Bounded arithmetic and actual-host disk guard, with no simulator side effects."""
from collections import deque
import shutil,time,os

GIB=2**30
RESERVE=256*2**20
MAX_INT=2**63-1

def integer(n,name,minimum=0):
    if type(n)is not int or not minimum<=n<=MAX_INT:raise ValueError('BOUND:'+name)
    return n

def checked_sum(*ns):
    total=0
    for n in ns:
        total+=integer(n,'sum')
        if total>MAX_INT:raise ValueError('ARITHMETIC_OVERFLOW')
    return total

def estimate_admission(*,free_bytes,duration_seconds,rate_hz,max_wal_bytes_per_frame,
                       max_trace_events_per_frame,trace_event_bytes,
                       max_stage_bytes_per_frame,max_video_bytes_per_second,
                       metadata_bytes,copies,export_peak_bytes,capacity_frames):
    """Every rate is a declared upper bound, not an observed average/compression guess."""
    vals=locals().copy()
    for k,v in vals.items():integer(v,k,1 if k in ['duration_seconds','rate_hz','max_wal_bytes_per_frame','copies','capacity_frames'] else 0)
    frames=duration_seconds*rate_hz
    if frames>MAX_INT:raise ValueError('ARITHMETIC_OVERFLOW')
    perframe=checked_sum(max_wal_bytes_per_frame,max_trace_events_per_frame*trace_event_bytes,max_stage_bytes_per_frame)
    primary=checked_sum(frames*perframe,duration_seconds*max_video_bytes_per_second,metadata_bytes)
    required=checked_sum(primary*copies,export_peak_bytes,10*GIB,RESERVE)
    return {'admitted':free_bytes>=20*GIB and frames<=capacity_frames and free_bytes>=required,
            'frames':frames,'primaryUpperBoundBytes':primary,'requiredFreeBytes':required,
            'reason':'ENTRY_BELOW20_GIB'if free_bytes<20*GIB else'CAPACITY_FRAME_BOUND'if frames>capacity_frames else'INSUFFICIENT_DECLARED_BUDGET'if free_bytes<required else'ADMITTED_DECLARED_BOUNDS_ONLY',
            'provenance':'CALLER_DECLARED_UPPER_BOUNDS_NOT_EMPIRICAL_SIZING','runtimeLaunched':False}

DISK_POLICY = {'version': 2, 'entryBytes': 20*GIB, 'floorBytes': 10*GIB,
               'reserveBytes': RESERVE, 'horizonNs': 15_000_000_000,
               'samplePeriodNs': 100_000_000, 'maximumCheckGapNs': 2_000_000_000,
               'maximumSamples': 192, 'requiresRealPriming': True,
               'sampling': 'CADENCE_CAPPED_KEEP_WINDOW_BOUNDARY_PREDECESSOR',
               'perWriteFloorAndForecast': True}


class DiskGuardError(OSError):
    def __init__(self, reason, diagnostic):
        super().__init__(reason)
        self.diagnostic = diagnostic


class ForecastWindow:
    """Pure deterministic math seam. This object alone never grants real writes."""
    def __init__(self):
        self.samples = deque(maxlen=DISK_POLICY['maximumSamples'])
        self.checks = 0
        self.last_check_ns = None
        self.first_ns = None
        self.primed = False
        self.last = None
        self.failed = None

    def observe(self, now_ns, free, requested_bytes=0, *, priming=False):
        if self.failed is not None:
            raise DiskGuardError('ACTUAL_HOST_DISK_GUARD_FAILED:'+self.failed, self.diagnostic())
        integer(now_ns, 'monotonic_ns');integer(free, 'actual_free');integer(requested_bytes, 'requested_bytes')
        self.checks += 1
        reason = None
        if self.first_ns is None:
            self.first_ns = now_ns
        if self.last_check_ns is not None:
            if now_ns < self.last_check_ns:
                reason = 'ACTUAL_HOST_DISK_MONOTONIC_REGRESSION'
            elif now_ns-self.last_check_ns > DISK_POLICY['maximumCheckGapNs']:
                reason = 'ACTUAL_HOST_DISK_OBSERVATION_GAP_NEEDS_REPRIME'
        self.last_check_ns = now_ns
        if not self.samples or now_ns-self.samples[-1][0] >= DISK_POLICY['samplePeriodNs']:
            self.samples.append((now_ns, free))
        cutoff = now_ns-DISK_POLICY['horizonNs']
        while len(self.samples)>2 and self.samples[1][0] <= cutoff:
            self.samples.popleft()
        oldest_ns, oldest_free = self.samples[0]
        span_ns = now_ns-oldest_ns
        horizon_observed = span_ns >= DISK_POLICY['horizonNs']
        if horizon_observed and reason is None:
            self.primed = True
        rate = max(0, oldest_free-free)*1_000_000_000/span_ns if span_ns>0 else 0.0
        forecast = free-requested_bytes-rate*15 if horizon_observed else None
        floor = DISK_POLICY['floorBytes']+DISK_POLICY['reserveBytes']
        if free-requested_bytes < floor:
            reason = 'ACTUAL_HOST_DISK_FLOOR10_RESERVE256'
        elif reason is None and not self.primed and not priming:
            reason = 'ACTUAL_HOST_DISK_NOT_REAL_15S_PRIMED'
        elif reason is None and forecast is not None and forecast < floor:
            reason = 'ACTUAL_HOST_DISK_FORECAST15_FLOOR10_RESERVE256'
        self.last = {'policyVersion':2, 'checks':self.checks, 'sampleCount':len(self.samples),
                     'historySpanNs':span_ns, 'firstObservationNs':self.first_ns,
                     'oldestSampleNs':oldest_ns, 'oldestSampleFreeBytes':oldest_free,
                     'currentObservationNs':now_ns, 'currentFreeBytes':free,
                     'requestedBytes':requested_bytes, 'declineBytesPerSecond':rate,
                     'forecastFreeBytes':forecast, 'floorAndReserveBytes':floor,
                     'primed':self.primed, 'reason':reason}
        if reason is not None:
            self.failed = reason
            raise DiskGuardError(reason, self.diagnostic())
        return self.last

    def diagnostic(self):
        return {**(self.last or {}), 'samples':[[t,free] for t,free in self.samples],
                'samplePolicy':dict(DISK_POLICY), 'evidenceType':'DETERMINISTIC_MATH_INPUTS_UNLESS_WRAPPED_BY_ACTUAL_DISK_GUARD'}


class DiskGuard:
    """Runtime has no clock/free-space injection and cannot skip real priming."""
    def __init__(self, path):
        self.path = path
        self.device = os.stat(path).st_dev
        self.window = ForecastWindow()
        self.prime_receipt = None

    def _observe(self, requested_bytes=0, *, priming=False):
        now_ns=time.monotonic_ns();free=shutil.disk_usage(self.path).free
        try:
            return self.window.observe(now_ns,free,requested_bytes,priming=priming)
        except DiskGuardError as exc:
            exc.diagnostic.update(evidenceType='ACTUAL_HOST_STATVFS_MONOTONIC_OBSERVATIONS', path=str(self.path))
            raise

    def prime(self):
        if self.prime_receipt is not None:
            raise RuntimeError('DISK_GUARD_ALREADY_PRIMED_NO_RESET')
        start=time.monotonic_ns()
        first=self._observe(priming=True)
        if first['currentFreeBytes'] < DISK_POLICY['entryBytes']:
            raise DiskGuardError('ACTUAL_HOST_DISK_ENTRY_BELOW20_GIB', self.diagnostic())
        while not self.window.primed:
            time.sleep(.1)
            self._observe(priming=True)
        final=self._observe()
        if final['currentFreeBytes'] < DISK_POLICY['entryBytes']:
            raise DiskGuardError('ACTUAL_HOST_DISK_ENTRY_BELOW20_GIB', self.diagnostic())
        self.prime_receipt={**final, 'elapsedRealMonotonicNs':time.monotonic_ns()-start,
                            'source':'ACTUAL_HOST_15S_PRIME_NO_SYNTHETIC_SEED'}
        return dict(self.prime_receipt)

    def rebind(self,path):
        if os.stat(path).st_dev != self.device:
            raise RuntimeError('DISK_GUARD_DEVICE_CHANGED')
        self.path=path
        self.check()

    def check(self,requested_bytes=0):
        return self._observe(requested_bytes)['currentFreeBytes']

    def diagnostic(self):
        return {**self.window.diagnostic(), 'path':str(self.path),
                'evidenceType':'ACTUAL_HOST_STATVFS_MONOTONIC_OBSERVATIONS'}
