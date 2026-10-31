"""Real UDP seam, driven only between complete frame groups by the same owner."""
import socket
import struct
import time
from pilot.betaintegrated01.clock.correlation import Context, BoundedCorrelator


class ClockSocket:
    def __init__(self, run, epoch, boot, sink, peer=('127.0.0.1', 9014), *, maximum_seconds=60, diagnostic=None):
        if peer != ('127.0.0.1', 9014):
            raise ValueError('CLOCK_ENDPOINT_ALLOWLIST')
        self.context = Context(run, epoch, boot)
        self.peer = peer
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 0))
        self.sock.setblocking(False)
        if type(maximum_seconds) is not int or not 1 <= maximum_seconds <= 1800:
            self.sock.close()
            raise ValueError('CLOCK_DURATION_BOUND')
        self.max_events = (maximum_seconds + 15) * 120 + 100
        self.events = 0
        self.diagnostic = diagnostic
        self.diagnostic_written = False
        def durable(row):
            if self.events >= self.max_events:
                if self.diagnostic is not None and not self.diagnostic_written:
                    self.diagnostic({'reason': 'CLOCK_TOTAL_EVENT_CAPACITY', 'attemptedEvent': row,
                                     'retainedEvents': self.events, 'complete': False})
                    self.diagnostic_written = True
                raise RuntimeError('CLOCK_TOTAL_EVENT_CAPACITY')
            sink(row)
            self.events += 1
        self.correlator = BoundedCorrelator(self.context, peer, durable, max_pending=8, recent_limit=64)
        self.next_request = 0
        self.request_id = 0
        self.closed = False

    def poll(self):
        if self.closed:
            raise RuntimeError('CLOCK_CLOSED')
        if time.monotonic_ns() < self.next_request:
            return
        for _ in range(8):
            try:
                raw, ancillary, flags, peer = self.sock.recvmsg(4097)
            except BlockingIOError:
                break
            try:
                if flags & socket.MSG_TRUNC:
                    raise RuntimeError('CLOCK_DATAGRAM_TRUNCATED')
                self.correlator.receive(raw, peer, time.monotonic_ns(), self.context)
            except Exception as exc:
                if self.diagnostic is not None and not self.diagnostic_written:
                    self.diagnostic({'reason': type(exc).__name__ + ':' + str(exc), 'rawHex': raw.hex(),
                                     'peer': repr(peer), 'socketTruncated': bool(flags & socket.MSG_TRUNC),
                                     'exactReceivedBytesRetained': not bool(flags & socket.MSG_TRUNC)})
                    self.diagnostic_written = True
                raise
        now = time.monotonic_ns()
        if now >= self.next_request:
            self.correlator.tick(now, self.context)
            self.request_id += 1
            self.correlator.register(self.request_id, now, self.context)
            raw = struct.pack('<Q', self.request_id)
            sent = self.sock.sendto(raw, self.peer)
            if sent != len(raw):
                raise RuntimeError('CLOCK_LOCAL_SEND_UNKNOWN')
            self.next_request = now + 100_000_000

    def calibration(self):
        return self.correlator.calibration(time.monotonic_ns(), self.context)

    def close(self):
        self.closed = True
        self.sock.close()
        return self.correlator.snapshot()
