"""Bounded offline verifier child capture. Not callable from the live pipeline."""
import hashlib
import os
import selectors
import signal
import subprocess
import time
from planning.betarc01.archive.common_rc01 import need


def capture(argv, payload, *, cwd, seconds=45):
    need(len(payload) <= 256 * 1024, 'OFFLINE_INPUT256K')
    start = time.monotonic_ns(); selector = selectors.DefaultSelector(); process = None
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}; limits = {'stdout': 32768, 'stderr': 8192}
    sent = 0; failure = None; eof = {'stdout': False, 'stderr': False}; cleanup_errors = []; code = None
    try:
        process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        for name in ('stdin', 'stdout', 'stderr'):
            stream = getattr(process, name); os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_WRITE if name == 'stdin' else selectors.EVENT_READ, name)
        while selector.get_map():
            if time.monotonic_ns() - start > seconds * 10 ** 9:
                raise TimeoutError('OFFLINE_CRYPTO_DEADLINE')
            for key, _ in selector.select(.05):
                name = key.data
                if name == 'stdin':
                    if sent < len(payload):
                        sent += os.write(key.fileobj.fileno(), payload[sent:sent + 65536])
                    if sent == len(payload): selector.unregister(key.fileobj); key.fileobj.close()
                else:
                    block = os.read(key.fileobj.fileno(), min(65536, limits[name] + 1 - len(buffers[name])))
                    if not block:
                        eof[name] = True; selector.unregister(key.fileobj); key.fileobj.close(); continue
                    buffers[name].extend(block)
                    need(len(buffers[name]) <= limits[name], 'OFFLINE_CAPTURE_BOUND_' + name)
        code = process.wait(timeout=max(.01, seconds - (time.monotonic_ns() - start) / 1e9))
    except BaseException as error:
        failure = type(error).__name__ + ':' + str(error)
    finally:
        if process is not None and process.poll() is None:
            try:
                try: os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    process.wait(timeout=2)
            except BaseException as error:
                cleanup_errors.append('owned-offline-group:' + str(error))
        if process is not None:
            code = process.poll()
            for name in ('stdin', 'stdout', 'stderr'):
                stream = getattr(process, name)
                try:
                    if stream is not None and not stream.closed: stream.close()
                except BaseException as error: cleanup_errors.append('offline-' + name + ':' + str(error))
        try: selector.close()
        except BaseException as error: cleanup_errors.append('offline-selector:' + str(error))
    result = {'format': 'aeris-betarc01-offline-verifier-capture', 'version': 1,
              'argv': argv, 'pid': None if process is None else process.pid, 'startedHostNs': start,
              'finishedHostNs': time.monotonic_ns(), 'exit': code, 'failure': failure,
              'stdoutEOF': eof['stdout'], 'stderrEOF': eof['stderr'], 'cleanupErrors': cleanup_errors,
              'ownedChildExited': process is None or code is not None,
              'stdinBytesSent': sent, 'stdinSHA256': hashlib.sha256(payload).hexdigest(),
              'stdoutBytes': len(buffers['stdout']), 'stderrBytes': len(buffers['stderr']),
              'stdoutSHA256': hashlib.sha256(buffers['stdout']).hexdigest(),
              'stderrSHA256': hashlib.sha256(buffers['stderr']).hexdigest(),
              'captureComplete': failure is None and all(eof.values()) and not cleanup_errors,
              'authorityRestorable': False}
    return result, bytes(buffers['stdout']), bytes(buffers['stderr'])
