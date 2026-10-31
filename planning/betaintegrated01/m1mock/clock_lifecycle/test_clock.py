"""Tests the product clock module; no network or AP processes."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location('beta_clock', ROOT/'pilot/betaintegrated01/clock/correlation.py')
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)
C = M.Context('run1', 'epoch1', 'boot1')
PEER = ('127.0.0.1', 19001)

def packet(rid, receive, send=None):
    return struct.pack('<7Q', rid, receive, receive if send is None else send, 1, 2, 3, 4)

class ClockTests(unittest.TestCase):
    def make(self, sink=None, **policy):
        self.rows = []
        return M.BoundedCorrelator(C, PEER, sink or self.rows.append, **policy)

    def test_durable_stream_over_1024_and_bounded_retirement(self):
        path = Path(os.environ['CLOCK_EVIDENCE'])/'clock-stream.jsonl'
        with path.open('x', encoding='utf-8') as f:
            def sink(row):
                f.write(json.dumps(row, sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
            clock = self.make(sink, recent_limit=7, max_pending=3)
            for rid in range(2049):
                base = rid*1000
                clock.register(rid, base, C)
                r = clock.receive(packet(rid, base-100 if base>=100 else base, base-100 if base>=100 else base), PEER, base+20, C)
                self.assertTrue(r['freshCalibration'])
            state = clock.snapshot()
            self.assertEqual(state['pending'], 0)
            self.assertEqual(state['recent'], 7)
            self.assertEqual(state['journalEvents'], 4098)
            self.assertFalse(state['holdsFullEventHistory'])
            self.assertLessEqual(state['pendingPeak'], 3)
            self.assertLessEqual(state['recentPeak'], 7)
            retired = clock.receive(packet(0, 0), PEER, 2048021, C)
            self.assertFalse(retired['freshCalibration'])
            with self.assertRaises(M.ClockError): clock.register(0, 2048022, C)
        with path.open() as f:
            rows = [json.loads(line) for line in f]
        self.assertEqual(len(rows), 4100)
        self.assertEqual([r['sequence'] for r in rows], list(range(1, 4101)))
        self.assertEqual(sum(r['kind']=='RESPONSE' for r in rows), 2049)
        self.assertTrue(all(r['run']=='run1' and r['boot']=='boot1' for r in rows))

    def test_timeout_late_duplicate_unknown_and_pending_bound(self):
        c = self.make(timeout_ns=20, max_step_ns=1000, recent_limit=2, max_pending=1)
        c.register(1, 100, C)
        with self.assertRaises(M.ClockError): c.register(2, 101, C)
        c.tick(121, C)
        self.assertEqual(c.receive(packet(1, 100), PEER, 122, C)['status'], 'LATE_MATCHED')
        self.assertFalse(c.receive(packet(1, 100), PEER, 123, C)['freshCalibration'])
        self.assertIsNone(c.calibration(123, C))
        self.assertEqual(c.receive(packet(9, 100), PEER, 124, C)['status'], 'UNKNOWN_FUTURE_ID')

    def test_reordered_and_honest_bracket(self):
        c = self.make()
        c.register(1, 100, C); c.register(2, 110, C)
        r = c.receive(packet(2, 50, 55), PEER, 120, C)
        self.assertEqual((r['offsetLowNs'],r['offsetHighNs']), (60,65))
        r = c.receive(packet(1, 40, 45), PEER, 121, C)
        self.assertEqual(r['status'], 'REORDERED_MATCHED')
        self.assertFalse(r['freshCalibration'])
        self.assertEqual(c.calibration(122, C)['id'], 2)
        c.register(3, 123, C)
        with self.assertRaises(M.ClockError): c.receive(packet(3, 200, 300), PEER, 130, C)
        self.assertEqual(self.rows[-1]['kind'], 'REJECTED_CLOCK_BRACKET')
        self.assertFalse(self.rows[-1]['freshCalibration'])

    def test_sink_publication_order_and_failure_poison(self):
        holder = {}; observed = []
        def sink(row):
            observed.append(holder['c'].snapshot())
            if row['kind']=='RESPONSE': raise OSError('injected fsync failure')
        c = self.make(sink); holder['c']=c
        c.register(1, 100, C)
        self.assertEqual(observed[0]['pending'], 0)
        with self.assertRaises(M.ClockError): c.receive(packet(1, 90), PEER, 120, C)
        self.assertEqual(observed[-1]['pending'], 1)
        self.assertEqual(c.snapshot()['pending'], 1)
        self.assertEqual(c.snapshot()['journalEvents'], 1)
        self.assertIn('DURABLE_SINK_FAILED', c.snapshot()['failed'])
        with self.assertRaises(M.ClockError): c.calibration(121, C)

    def test_foreign_malformed_boot_and_uint_fences(self):
        c = self.make(); c.register(1, 100, C)
        for raw,peer,context in [(packet(1,90),('127.0.0.1',9),C),(b'bad',PEER,C),(packet(1,90),PEER,M.Context('run1','epoch1','boot2'))]:
            with self.assertRaises(M.ClockError): c.receive(raw,peer,110,context)
        self.assertIsNone(c.calibration(111,C))
        for bad in (True,-1,1.0,float('inf'),1<<64):
            with self.assertRaises(M.ClockError): c.register(bad,112,C)
        state=c.snapshot();state['pending']=500
        self.assertEqual(c.snapshot()['pending'],1)

    def test_stale_suspend_regression_and_guest_reset(self):
        c=self.make(fresh_ns=5,max_step_ns=1000,timeout_ns=500)
        c.register(1,100,C);c.receive(packet(1,90),PEER,110,C)
        self.assertIsNone(c.calibration(116,C))
        with self.assertRaises(M.ClockError): c.tick(99,C)
        self.assertEqual(c.snapshot()['failed'],'CLOCK_REGRESSION')
        c=self.make(max_step_ns=1000,timeout_ns=500);c.register(1,0,C)
        with self.assertRaises(M.ClockError):c.tick(1001,C)
        self.assertEqual(c.snapshot()['failed'],'SUSPEND_OR_STALE_GAP')
        c=self.make(max_offset_step_ns=0);c.register(1,100,C);c.receive(packet(1,90),PEER,110,C);c.register(2,120,C)
        with self.assertRaises(M.ClockError):c.receive(packet(2,1),PEER,130,C)
        self.assertEqual(c.snapshot()['failed'],'GUEST_CLOCK_DISCONTINUITY')

    def test_reentrant_mutation_blocked_and_snapshot_copy(self):
        holder={}; rejected=[]
        def sink(row):
            try:holder['c'].tick(100,C)
            except M.ClockError:rejected.append(True)
            row['run']='mutated'
        c=self.make(sink);holder['c']=c;c.register(1,100,C)
        self.assertEqual(rejected,[True]);self.assertEqual(c.snapshot()['run'],'run1')
        self.assertIsNone(c.calibration(100,C))

if __name__=='__main__':unittest.main(verbosity=2)
