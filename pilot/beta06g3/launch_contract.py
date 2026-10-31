"""Offline-only G3 launch contract. Does not execute Docker or launch a guest."""
from pathlib import Path
import hashlib
import stat

BINARY_SHA256 = '1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41'
MAX_STREAM_BYTES = 2 * 1024 * 1024


def require_executable_artifact(path, expected_sha256=BINARY_SHA256):
    p = Path(path)
    s = p.lstat()
    if not stat.S_ISREG(s.st_mode) or p.is_symlink():
        raise ValueError('REGULAR_NONLINK_BINARY_REQUIRED')
    data = p.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ValueError('EXACT_BINARY_SHA_REQUIRED')
    if len(data) < 64 or data[:4] != b'\x7fELF' or data[4:6] != b'\x02\x01' or int.from_bytes(data[18:20], 'little') != 183:
        raise ValueError('ELF64_LE_AARCH64_REQUIRED')
    # Runtime is image-default root; require all three execute bits to keep
    # the artifact usable under a future explicit non-root identity too.
    mode = stat.S_IMODE(s.st_mode)
    if mode != 0o755:
        raise ValueError('EXECUTABLE_MODE_0755_REQUIRED')
    return {'sha256': digest, 'bytes': s.st_size, 'mode': '0755', 'architecture': 'ELF64_LE_AARCH64', 'allocationOrExecutionPerformed': False}


def require_durable_create_command(argv):
    if len(argv) < 2 or argv[1] != 'create':
        raise ValueError('CREATE_BEFORE_START_REQUIRED')
    if any(v == '--rm' or v.startswith('--rm=') for v in argv):
        raise ValueError('NO_AUTOREMOVE_DIAGNOSTICS_REQUIRED')
    if any(v == '--privileged' or v.startswith('--privileged=') for v in argv):
        raise ValueError('NO_PRIVILEGE_CHANGE')
    return True


class LaunchEvidenceContract:
    """Pure state machine, not a runtime implementation or durable store."""
    def __init__(self):
        self.phase = 'NEW'
        self.cid = None

    def created(self, cid, *, intent_fsynced, result_fsynced, inspect_fsynced):
        if self.phase != 'NEW' or len(cid) != 64 or any(c not in '0123456789abcdef' for c in cid):
            raise ValueError('EXACT_CREATED_CONTAINER_ID_REQUIRED')
        if not all([intent_fsynced, result_fsynced, inspect_fsynced]):
            raise ValueError('PRESTART_DURABLE_RECEIPTS_REQUIRED')
        self.cid, self.phase = cid, 'CREATED_RECORDED'

    def permit_single_start(self, *, event_capture_ready, attached_output_ready):
        if self.phase != 'CREATED_RECORDED' or not event_capture_ready or not attached_output_ready:
            raise ValueError('PRESTART_CAPTURE_REQUIRED')
        self.phase = 'START_CONSUMED'
        return self.cid

    def terminal(self, *, inspect_fsynced, output_fsynced, wait_fsynced, events_fsynced):
        if self.phase != 'START_CONSUMED' or not all([inspect_fsynced, output_fsynced, wait_fsynced, events_fsynced]):
            raise ValueError('TERMINAL_CAPTURE_INCOMPLETE')
        self.phase = 'CLOSED_RETAIN_CONTAINER_NO_AUTORETRY'


def retain_prefix(data, limit=MAX_STREAM_BYTES):
    if not 0 < limit <= MAX_STREAM_BYTES:
        raise ValueError('STREAM_BUDGET_BOUND')
    return {'retained': data[:limit], 'observedBytes': len(data), 'truncated': len(data) > limit,
            'acceptanceEligible': len(data) <= limit}
