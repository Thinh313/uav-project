"""Bounded arithmetic and actual-host disk guard, with no simulator side effects."""
from collections import deque
import shutil,time

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

class DiskGuard:
    """Cannot be disabled by a synthetic admission test or FileIO fault injection."""
    def __init__(self,path):self.path=path;self.samples=deque(maxlen=64)
    def check(self,requested_bytes=0):
        integer(requested_bytes,'requested_bytes')
        now=time.monotonic();free=shutil.disk_usage(self.path).free
        self.samples.append((now,free))
        while len(self.samples)>1 and now-self.samples[0][0]>15:self.samples.popleft()
        start,initial=self.samples[0];rate=max(0,(initial-free)/max(.001,now-start))
        if free-requested_bytes-rate*15<10*GIB+RESERVE:raise OSError('ACTUAL_HOST_DISK_FORECAST15_FLOOR10_RESERVE256')
        return free
