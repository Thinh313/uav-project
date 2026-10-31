"""Bounded per-attempt console marker observer. No process/network/file operations."""
import hashlib
MARKERS={'waiting':b'Waiting for connection','serial0':b'SERIAL0 on TCP port 5760'}
CHUNK_BYTES=65536
TAIL_BYTES=65536
STREAM_BYTES=2*2**20
class SerialReadiness:
 def __init__(self,attempt):
  if not isinstance(attempt,str) or not attempt or len(attempt)>128:raise ValueError('EXACT_ATTACHED_ATTEMPT_REQUIRED')
  self.attempt=attempt;self.tails={s:b'' for s in ['stdout','stderr']};self.counts={s:0 for s in self.tails};self.hashes={s:hashlib.sha256() for s in self.tails};self.markers={};self.failed=None
 def feed(self,stream,data,*,attempt):
  if attempt!=self.attempt:raise ValueError('ATTACHED_ATTEMPT_MISMATCH')
  if self.failed:raise ValueError(self.failed)
  if stream not in self.tails or not isinstance(data,bytes) or len(data)>CHUNK_BYTES:raise ValueError('READINESS_STREAM_OR_CHUNK_BOUND')
  if self.counts[stream]+len(data)>STREAM_BYTES:self.failed='READINESS_STREAM_OVERFLOW';raise ValueError(self.failed)
  old=self.counts[stream];tail=self.tails[stream];joined=tail+data;base=old-len(tail)
  for name,marker in MARKERS.items():
   at=joined.find(marker)
   if at>=0 and name not in self.markers:self.markers[name]={'stream':stream,'offsetBytes':base+at,'marker':marker.decode('ascii')}
  self.counts[stream]+=len(data);self.hashes[stream].update(data);self.tails[stream]=joined[-TAIL_BYTES:]
 def ready(self,*,alive):
  if alive is not True:raise ValueError('ATTACHED_PROCESS_NOT_ALIVE')
  if self.failed:raise ValueError(self.failed)
  return set(self.markers)==set(MARKERS)
 def proof(self,*,alive):
  if not self.ready(alive=alive):raise ValueError('BOTH_ORIGINAL_SERIAL_MARKERS_REQUIRED')
  return {'attempt':self.attempt,'markers':{k:dict(v) for k,v in self.markers.items()},'streams':{s:{'retainedPrefixBytes':self.counts[s],'retainedPrefixSha256':self.hashes[s].hexdigest()} for s in self.tails},'perStreamTailBoundBytes':TAIL_BYTES,'perStreamCaptureBoundBytes':STREAM_BYTES,'noCrossStreamConcatenation':True,'serialConsoleOnly':True,'telemetryFirmwareExecutionFlightProven':False}
