"""Owned bounded CPU injection; no filesystem traffic or unbounded allocation."""
import time
import signal
import os
import sys
import json

stopped = False


def stop(*_):
    global stopped
    stopped = True


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
started = time.monotonic()
cpu = time.process_time()
value = int(sys.argv[1])
iterations = 0
print(json.dumps({'pid': os.getpid(), 'seed': value, 'startedHostNs': time.monotonic_ns()}), flush=True)
while not stopped and time.monotonic() - started < 300:
    for _ in range(20000):
        value = (value * 1664525 + 1013904223) & 0xffffffff
    iterations += 20000
print(json.dumps({'pid': os.getpid(), 'iterations': iterations, 'checksum': value,
                  'cpuSeconds': time.process_time() - cpu,
                  'wallSeconds': time.monotonic() - started,
                  'stopRequested': stopped}), flush=True)
