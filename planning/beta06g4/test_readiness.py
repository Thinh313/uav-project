"""Source/mock corrective tests; never invokes Docker, a binary, listener or runtime."""
from pathlib import Path
import importlib.util,unittest,hashlib,sys
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('g4readiness',ROOT/'pilot/beta06g4/flight/readiness.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ACTUAL=ROOT/'evidence/beta06/generation03/flight/runs/se15994472d0e479cbaa8/diagnostics'
class Tests(unittest.TestCase):
 def observer(self):return m.SerialReadiness('current')
 def feed(self,o,stream,b):o.feed(stream,b,attempt='current')
 def test_actual_G3_replay_old_false_new_true(self):
  stdout=(ACTUAL/'attach-stdout.bin').read_bytes();stderr=(ACTUAL/'attach-stderr.bin').read_bytes();self.assertEqual((len(stdout),len(stderr)),(249,52));self.assertFalse(all(v in stdout for v in m.MARKERS.values()));o=self.observer();self.feed(o,'stdout',stdout);self.feed(o,'stderr',stderr);self.assertTrue(o.ready(alive=True));p=o.proof(alive=True);self.assertEqual(p['markers']['waiting']['stream'],'stdout');self.assertEqual(p['markers']['serial0']['stream'],'stderr');self.assertEqual(p['streams']['stderr']['retainedPrefixSha256'],hashlib.sha256(stderr).hexdigest())
 def test_stdout_only(self):
  o=self.observer();self.feed(o,'stdout',b'Waiting for connection\nSERIAL0 on TCP port 5760');self.assertTrue(o.ready(alive=True))
 def test_stderr_only(self):
  o=self.observer();self.feed(o,'stderr',b'Waiting for connection\nSERIAL0 on TCP port 5760');self.assertTrue(o.ready(alive=True))
 def test_split_chunks_original_stream(self):
  o=self.observer()
  for b in [b'xWaiting fo',b'r connection',b'\nSERIAL0 on TCP port 57',b'60']:self.feed(o,'stdout',b)
  self.assertTrue(o.ready(alive=True));self.assertEqual(o.proof(alive=True)['markers']['waiting']['offsetBytes'],1)
 def test_cross_stream_fragment_negative(self):
  o=self.observer();self.feed(o,'stdout',b'Waiting for connection\nSERIAL0 on TCP port 57');self.feed(o,'stderr',b'60');self.assertFalse(o.ready(alive=True))
 def test_incomplete_marker(self):
  o=self.observer();self.feed(o,'stderr',b'Waiting for connection\nSERIAL0 on TCP port');self.assertFalse(o.ready(alive=True))
 def test_attempt_reset(self):
  old=self.observer();self.feed(old,'stdout',b'Waiting for connection\nSERIAL0 on TCP port 5760');new=self.observer();self.assertFalse(new.ready(alive=True));self.assertTrue(old.ready(alive=True))
 def test_attempt_mismatch_refused(self):
  o=self.observer()
  with self.assertRaisesRegex(ValueError,'MISMATCH'):o.feed('stdout',b'Waiting for connection',attempt='old')
  self.assertEqual(o.counts['stdout'],0)
 def test_early_exit_never_ready(self):
  o=self.observer();self.feed(o,'stdout',b'Waiting for connection\nSERIAL0 on TCP port 5760')
  with self.assertRaisesRegex(ValueError,'NOT_ALIVE'):o.ready(alive=False)
 def test_overflow_fail_closed(self):
  o=self.observer()
  for _ in range(m.STREAM_BYTES//m.CHUNK_BYTES):self.feed(o,'stdout',b'x'*m.CHUNK_BYTES)
  with self.assertRaisesRegex(ValueError,'OVERFLOW'):self.feed(o,'stdout',b'x')
  with self.assertRaisesRegex(ValueError,'OVERFLOW'):o.ready(alive=True)
 def test_chunk_and_stream_bounds(self):
  o=self.observer()
  for stream,b in [('stdout',b'x'*(m.CHUNK_BYTES+1)),('merged',b'Waiting for connection')]:
   with self.assertRaisesRegex(ValueError,'BOUND'):self.feed(o,stream,b)
  self.assertEqual(sum(o.counts.values()),0)
 def test_bounded_tails_and_persistent_marker_proof(self):
  o=self.observer();self.feed(o,'stdout',b'Waiting for connection\nSERIAL0 on TCP port 5760')
  for _ in range(30):self.feed(o,'stdout',b'x'*m.CHUNK_BYTES)
  self.assertLessEqual(sum(map(len,o.tails.values())),2*m.TAIL_BYTES);self.assertTrue(o.ready(alive=True));self.assertEqual(o.proof(alive=True)['markers']['waiting']['offsetBytes'],0)
if __name__=='__main__':unittest.main()
