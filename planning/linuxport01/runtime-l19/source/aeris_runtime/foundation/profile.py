"""Bounded diagnostic metrics; every actual raw frame/record remains untouched."""
import bisect,heapq,time
from contextlib import contextmanager
PHASES=('serialize','guard','write','fsync','STAGE','recvwait');ALL=frozenset(('write','fsync'));BOUNDS=(100_000,500_000,1_000_000,5_000_000,20_000_000,100_000_000,250_000_000)
class Profile:
 def __init__(self):self.phases={p:[0,0,0,0,0,0,[0]*8,[]]for p in PHASES};self.serial=0
 def call(self,phase):
  s=self.phases[phase];s[0]+=1;self.serial+=1
  if self.serial>100_000_000:raise ValueError('PROFILE_OPERATION_BOUND')
  return s
 def _record(self,s,begin,end,cpu):
  if type(begin)is not int or type(end)is not int or type(cpu)is not int or not 0<=begin<=end or cpu<0:raise ValueError('PROFILE_DOMAIN')
  wall=end-begin;s[1]+=1;s[2]+=wall;s[3]+=cpu
  if wall>s[4]:s[4]=wall
  if cpu>s[5]:s[5]=cpu
  s[6][bisect.bisect_right(BOUNDS,wall)]+=1;heap=s[7]
  if len(heap)<32 or(wall,self.serial)>heap[0][:2]:
   entry=(wall,self.serial,dict(beginHostNs=begin,endHostNs=end,wallNs=wall,threadCPUNs=cpu))
   if len(heap)<32:heapq.heappush(heap,entry)
   else:heapq.heapreplace(heap,entry)
 def observe(self,phase,begin,end,cpu):
  if phase not in ALL:raise ValueError('EXTERNAL_TIMING_ONLY_WRITE_FSYNC')
  self._record(self.call(phase),begin,end,cpu)
 @contextmanager
 def measure(self,phase):
  if phase in ALL or phase not in self.phases:raise ValueError('SAMPLED_PROFILE_PHASE')
  s=self.call(phase)
  if(s[0]-1)%16:yield;return
  begin=time.monotonic_ns();cpu=time.thread_time_ns()
  try:yield
  finally:self._record(s,begin,time.monotonic_ns(),time.thread_time_ns()-cpu)
 def snapshot(self):
  phases={}
  for phase,s in self.phases.items():phases[phase]=dict(calls=s[0],measuredCount=s[1],expectedMeasuredCount=s[0]if phase in ALL else(s[0]+15)//16,coverage='ALL_REUSE_EXISTING_DIAGNOSTICIO_CLOCKS'if phase in ALL else'DETERMINISTIC_FIRST_AND_EVERY16_CALLS',measuredWallTotalNs=s[2],measuredThreadCPUTotalNs=s[3],measuredWallMaxNs=s[4],measuredThreadCPUMaxNs=s[5],measuredHistogram=s[6],measuredWorst32=[r[2]for r in sorted(s[7],reverse=True)],sampledMaximaAreNotFullCoverage=phase not in ALL)
  return dict(format='aeris-compact10-host-memory-profile',version=1,operations=self.serial,phases=phases,maxOperations=100_000_000,maxPhases=6,maximumWorstSpansPerPhase=32,clock='HOST_MONOTONIC_NS_AND_CURRENT_THREAD_TIME_NS',phaseDurations='NESTED_INCLUSIVE_MEASURED_ONLY_DO_NOT_SUM_OR_ATTRIBUTE_EXCLUSIVE_CAUSE',nonCPUWallCause='UNKNOWN_IO_WAIT_AND_OR_DESCHEDULE',timingOverhead='NOT_SUBTRACTED_REQUIRES_MEASURED_BASELINE',hotExtraFileWrites=0,guardCoverageStarts='POST_CONSTRUCTOR_WRAPPER_ACTUAL_PRIME_AND_INITIAL_CHECKS_UNTIMED_NOT_SKIPPED',IOCoverageStarts='PROFILE_IO_PROVIDED_BEFORE_BASE_CONSTRUCTOR',captureStop='AFTER_JOURNAL_CLOSE_BEFORE_PROFILE_PUBLICATION_GUARD',allRawFrameRecordCoverage='UNCHANGED_FULL',metricsSamplingDoesNotDropRawFrames=True)
