"""Linux tiny observer processes only; no ArduPilot code, model, socket or flight."""
import json
import os
import struct
import subprocess
import time

results = []
for mode in ('normal', 'foreign', 'closed', 'backpressure'):
    readfd, writefd = os.pipe()
    if mode == 'closed':
        os.close(readfd)
    started = time.monotonic()
    child = subprocess.Popen(['/new/.build/emitter-harness', mode],
                             env={**os.environ, 'AERIS_STAGE_FD': str(writefd)},
                             pass_fds=(writefd,), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.close(writefd)
    stdout, stderr = child.communicate(timeout=5)
    raw = b''
    if mode != 'closed':
        while True:
            block = os.read(readfd, 65536)
            if not block:
                break
            raw += block
        os.close(readfd)
    assert len(raw) % 64 == 0
    for i in range(len(raw)//64):
        assert struct.unpack_from('<Q', raw, i*64)[0] == i
    if mode == 'normal':
        assert child.returncode == 0 and len(raw) == 192
    elif mode == 'foreign':
        assert child.returncode == 96 and len(raw) == 64 and b'multiple-producers' in stderr
    elif mode == 'closed':
        assert child.returncode in (-13, 96) and not raw
    else:
        assert child.returncode == 96 and b'backpressure-deadline' in stderr
        assert 1.8 <= time.monotonic()-started < 5
    results.append({'mode': mode, 'exit': child.returncode, 'bytesRetained': len(raw),
                    'completeRecords': len(raw)//64, 'stderr': stderr.decode(),
                    'seconds': time.monotonic()-started, 'status': 'PASS'})
print(json.dumps({'status': 'PASS_LINUX_ARM_OBSERVER_UNIT_NOT_AP', 'results': results,
                  'APLaunches': 0, 'sockets': 0}))
