"""Versioned, bounded parent-side AP event drainer and cold integrity reader.

The AP's inherited pipe is bounded and never a lossy ring. This writer does not
infer AP execution, source authenticity, or physical power-loss durability.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import zlib
from .fdm09 import varint,read_varint

PHYSICAL_CODEC="APSTAGE09_EXACT64_BLOCK128_DELTA"
BLOCK=struct.Struct("<4sHHI")
ESCAPE=b"\xff"*8
def event_basis(v):
    # Exact uint64 bit bijection for the two opaque arguments. Negative
    # producer deltas arrive in their original uint64 two's-complement bytes.
    signed=lambda n:n-2**64 if n>=2**63 else n
    return (*v[:5],v[5]-v[4],signed(v[6]),signed(v[7]),v[8])
def event_unbasis(v):
    if not all(type(n)is int for n in v)or not all(-(2**63)<=v[i]<2**63 for i in(6,7)):raise ValueError("APSTAGE09_BASIS_SIGNED64")
    return (*v[:5],v[5]+v[4],v[6]if v[6]>=0 else v[6]+2**64,v[7]if v[7]>=0 else v[7]+2**64,v[8])
def packed_event(raw,prior):
    if type(raw)is not bytes or len(raw)!=EVENT.size:raise ValueError("APSTAGE09_EXACT64")
    values=EVENT.unpack(raw)
    if values[0]>=100000000 or values[2]not in KINDS or not values[3]or values[4]>values[5]:raise ValueError("APSTAGE09_EVENT_SCHEMA")
    if prior is None:return raw
    best=raw
    for basis in(False,True):
        current=event_basis(values)if basis else values;previous=event_basis(prior)if basis else prior;data=[]
        for value,old in zip(current,previous):
            n=value-old;zz=(n<<1)if n>=0 else((-n<<1)-1)
            if zz>=2**64:break
            data.append(varint(zz))
        if len(data)!=9:continue
        data=b"".join(data)
        if len(data)+9>=len(best):continue
        best=ESCAPE+bytes([len(data)|(128 if basis else 0)])+data
    return best
def read_event(file,prior):
    first=file.read(8)
    if not first:return None,None
    if len(first)!=8:raise ValueError("APSTAGE09_PARTIAL_PREFIX")
    if first!=ESCAPE:
        tail=file.read(EVENT.size-8)
        if len(tail)!=EVENT.size-8:raise ValueError("APSTAGE09_PARTIAL_ABSOLUTE")
        raw=first+tail;return raw,raw
    if prior is None:raise ValueError("APSTAGE09_DELTA_WITHOUT_SEGMENT_STATE")
    length=file.read(1)
    if len(length)!=1 or not 9<=(length[0]&127)<=54:raise ValueError("APSTAGE09_DELTA_LENGTH")
    basis=bool(length[0]&128);data=file.read(length[0]&127)
    if len(data)!=(length[0]&127):raise ValueError("APSTAGE09_PARTIAL_DELTA")
    values=[];at=0
    for old in(event_basis(prior)if basis else prior):
        zz,at=read_varint(data,at);values.append(old+((zz>>1)^-(zz&1)))
    if at!=len(data):raise ValueError("APSTAGE09_TRAILING_DELTA")
    if basis:values=event_unbasis(values)
    try:raw=EVENT.pack(*values)
    except struct.error as error:raise ValueError("APSTAGE09_TYPED_OVERFLOW")from error
    return raw,first+length+data
def block_bytes(payload,count,originals):
    if type(payload)is not bytes or type(count)is not int or not 1<=count<=128 or not count*9<=len(payload)<=count*64:raise ValueError("APSTAGE09_BLOCK_BOUND")
    if type(originals)is not bytes or len(originals)!=count*EVENT.size:raise ValueError("APSTAGE09_BLOCK_ORIGINALS_BOUND")
    if BLOCK.size+len(payload)>=len(originals):return originals
    prefix=BLOCK.pack(b"APS9",count,len(payload),0);return prefix[:-4]+struct.pack("<I",zlib.crc32(prefix[:-4]+payload)&0xffffffff)+payload
def records(file):
    # No event escapes this iterator before its ENTIRE bounded block CRC passes.
    # Physical block is returned once with its first original record for hashes.
    import io
    prior=None
    while True:
        prefix=file.read(4)
        if not prefix:return
        if len(prefix)!=4:raise ValueError("APSTAGE09_PARTIAL_BLOCK_PREFIX")
        if prefix!=b"APS9":
            tail=file.read(EVENT.size-4)
            if len(tail)!=EVENT.size-4:raise ValueError("APSTAGE09_PARTIAL_PLAIN64")
            raw=prefix+tail;prior=EVENT.unpack(raw)
            if prior[0]>=100000000:raise ValueError("APSTAGE09_PLAIN_SEQUENCE_BOUND")
            yield raw,raw;continue
        header=prefix+file.read(BLOCK.size-4)
        if len(header)!=BLOCK.size:raise ValueError("APSTAGE09_PARTIAL_BLOCK_HEADER")
        magic,count,length,crc=BLOCK.unpack(header)
        if magic!=b"APS9"or not 1<=count<=128 or not count*9<=length<=count*64:raise ValueError("APSTAGE09_BLOCK_HEADER_BOUND")
        payload=file.read(length)
        if len(payload)!=length or crc!=(zlib.crc32(header[:-4]+payload)&0xffffffff):raise ValueError("APSTAGE09_BLOCK_CRC_OR_PARTIAL")
        decoded=io.BytesIO(payload)
        for i in range(count):
            raw,physical=read_event(decoded,prior)
            if raw is None:raise ValueError("APSTAGE09_BLOCK_RECORD_COUNT")
            prior=EVENT.unpack(raw);yield raw,header+payload if i==0 else b""
        if decoded.read(1):raise ValueError("APSTAGE09_BLOCK_TRAILING_PAYLOAD")

EVENT = struct.Struct('<QQIIQQQQq')
KINDS = frozenset(range(10, 15)) | frozenset(range(20, 25))


def _uint(value):
    return type(value) is int and 0 <= value < 2**64


def _sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _schema(obj, kind, context):
    formats = {'header': 'aeris-ap-pipe-stage', 'seal': 'aeris-ap-stage-seal', 'terminal': 'aeris-ap-stage-terminal'}
    if type(obj) is not dict or obj.get('format') != formats[kind] or type(obj.get('version')) is not int or obj['version'] != 2 or obj.get('physicalCodec')!=PHYSICAL_CODEC:
        raise ValueError('FORMAT_VERSION')
    if any(type(obj.get(k)) is not str or obj[k] != v for k, v in context.items()):
        raise ValueError('CONTEXT_SCHEMA')
    if kind == 'terminal':
        for key in ('events', 'segments'):
            if not _uint(obj.get(key)):
                raise ValueError('TERMINAL_NUMERIC_TYPE')
        if type(obj.get('apExit')) is not int or not -(2**31) <= obj['apExit'] < 2**31:
            raise ValueError('AP_EXIT_TYPE')
        if (obj.get('byteSequenceComplete') is not True or obj.get('pipeEOF') is not True or
                obj.get('APExecutionAccepted') is not False or obj.get('publicationAllowed') is not False or
                not _sha(obj.get('lastSegmentSHA256'))):
            raise ValueError('TERMINAL_FLAGS')
    else:
        for key in ('ordinal', 'startSequence'):
            if not _uint(obj.get(key)):
                raise ValueError('SEGMENT_NUMERIC_TYPE')
        if not _sha(obj.get('previousSegmentSHA256')):
            raise ValueError('PREVIOUS_SHA_TYPE')
        if kind == 'header':
            if type(obj.get('eventBytes')) is not int or obj['eventBytes'] != EVENT.size:
                raise ValueError('EVENT_BYTES_TYPE')
        elif not _uint(obj.get('events')) or not _uint(obj.get('nextSequence')) or not _sha(obj.get('sha256')):
            raise ValueError('SEAL_SCHEMA')


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def exclusive(path, body):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        writeall(fd, body)
        os.fsync(fd)
    finally:
        os.close(fd)
    syncdir(Path(path).parent)


def syncdir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def writeall(fd, body):
    while body:
        n = os.write(fd, body)
        if n <= 0:
            raise OSError('ZERO_WRITE')
        body = body[n:]


class StageDrainer:
    def __init__(self, root, run, epoch, boot, *, events_per_chunk=16384, max_events=720000):
        for value in (run, epoch, boot):
            if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value):
                raise ValueError('IDENTITY')
        for value, limit in ((events_per_chunk, 262144), (max_events, 100000000)):
            if type(value) is not int or not 1 <= value <= limit:
                raise ValueError('BOUND')
        self.root = Path(root)
        self.root.mkdir(mode=0o700)
        syncdir(self.root.parent)
        self.context = {'run': run, 'epoch': epoch, 'boot': boot}
        self.events_per_chunk, self.max_events = events_per_chunk, max_events
        self.total = self.ordinal = self.chunk_events = 0
        self.previous = '0' * 64
        self.fd = None
        self.failed = False
        self.closed = False
        self.tail = b''
        self.tid = None
        self.last_frame = None
        self.frame_events = 0
        self._open()

    def _open(self):
        self.path = self.root / ('stage-%06d.bin' % self.ordinal)
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        head = {'format': 'aeris-ap-pipe-stage', 'version': 2, 'physicalCodec':PHYSICAL_CODEC, **self.context,
                'ordinal': self.ordinal, 'startSequence': self.total,
                'previousSegmentSHA256': self.previous, 'eventBytes': EVENT.size}
        body = canonical(head) + b'\n'
        writeall(self.fd, body)
        os.fsync(self.fd)
        syncdir(self.root)
        self.hash = hashlib.sha256(body)
        self.logical_hash=hashlib.sha256();self.previous_event=None;self.block_original=bytearray();self.block_physical=bytearray();self.block_events=0;self.block_write_started=False
        self.chunk_events = 0

    def _flush_block(self):
        if not self.block_events:return
        if self.block_write_started:raise RuntimeError('APSTAGE09_UNCERTAIN_BLOCK_NOT_RETRIED')
        stored=block_bytes(bytes(self.block_physical),self.block_events,bytes(self.block_original));self.block_write_started=True
        writeall(self.fd,stored);self.hash.update(stored);self.block_original.clear();self.block_physical.clear();self.block_events=0;self.block_write_started=False

    def _seal(self):
        self._flush_block()
        os.fsync(self.fd)
        os.close(self.fd)
        self.fd = None
        sealed_hash = self.hash.hexdigest()
        seal = {'format': 'aeris-ap-stage-seal', 'version': 2, 'physicalCodec':PHYSICAL_CODEC, **self.context,
                'ordinal': self.ordinal, 'startSequence': self.total - self.chunk_events,
                'events': self.chunk_events, 'nextSequence': self.total,
                'sha256': sealed_hash, 'previousSegmentSHA256': self.previous,'logicalEventSHA256':self.logical_hash.hexdigest()}
        exclusive(self.root / ('stage-%06d.seal.json' % self.ordinal), canonical(seal) + b'\n')
        self.previous = sealed_hash
        self.ordinal += 1

    def feed(self, body):
        if self.failed or self.closed:
            raise RuntimeError('DRAINER_STATE_OR_INPUT_BOUND')
        if type(body) is not bytes or len(body) > 65536:
            self.fail('INPUT_BOUND_OR_TYPE')
            raise RuntimeError('DRAINER_STATE_OR_INPUT_BOUND')
        self.tail += body
        while len(self.tail) >= EVENT.size:
            raw, self.tail = self.tail[:EVENT.size], self.tail[EVENT.size:]
            seq, frame, kind, tid, begin, end, arg, extra, result = EVENT.unpack(raw)
            try:
                if seq != self.total or kind not in KINDS or not tid or begin > end:
                    raise ValueError('EVENT_SEQUENCE_KIND_OR_TIME')
                if self.tid is None:
                    self.tid = tid
                if tid != self.tid:
                    raise ValueError('MULTIPLE_PRODUCERS')
                if self.last_frame is not None and frame < self.last_frame:
                    raise ValueError('FRAME_REGRESSION')
                if frame != self.last_frame:
                    self.last_frame, self.frame_events = frame, 0
                self.frame_events += 1
                if self.frame_events > 10:
                    raise ValueError('EVENTS_PER_FRAME_BOUND')
                if self.total >= self.max_events:
                    raise ValueError('EVENT_CAPACITY')
                if self.fd is None:
                    self._open()
                stored=packed_event(raw,self.previous_event)
                self.block_original.extend(raw);self.block_physical.extend(stored);self.block_events+=1
                self.logical_hash.update(raw);self.previous_event=EVENT.unpack(raw)
                if self.block_events==128:self._flush_block()
                self.total += 1
                self.chunk_events += 1
                if self.chunk_events == self.events_per_chunk:
                    self._seal()
            except Exception as exc:
                self.fail(type(exc).__name__ + ':' + str(exc), raw)
                raise

    def fail(self, reason, rejected=b''):
        self.failed = True
        if self.fd is not None:
            try:
                if self.block_events and not self.block_write_started:
                    try:self._flush_block()
                    except Exception:pass
                if self.block_original:
                    try:exclusive(self.root/'failure-pending-events.bin',bytes(self.block_original))
                    except Exception:pass
                os.fsync(self.fd)
            finally:
                os.close(self.fd)
                self.fd = None
        try:
            exclusive(self.root / 'failure.json', canonical({
                **self.context, 'reason': reason[:512], 'retainedEvents': self.total,
                'rejectedHex': rejected.hex(), 'pendingTailHex': self.tail.hex(),
                'complete': False,'pendingOriginalEvents':self.block_events,'pendingBlockWriteUncertain':self.block_write_started}) + b'\n')
        except OSError:
            pass

    def finish(self, *, ap_exit, eof):
        if self.failed or self.closed:
            raise RuntimeError('DRAINER_NOT_CLOSABLE')
        if type(ap_exit) is not int or type(eof) is not bool:
            self.fail('TERMINAL_OBSERVATIONS_TYPE')
            raise RuntimeError('TERMINAL_OBSERVATIONS_TYPE')
        if self.tail or not eof:
            self.fail('TRUNCATED_EVENT_OR_MISSING_EOF')
            raise RuntimeError('TRUNCATED_EVENT_OR_MISSING_EOF')
        if self.fd is not None:
            self._seal()
        terminal = {'format': 'aeris-ap-stage-terminal', 'version': 2, 'physicalCodec':PHYSICAL_CODEC, **self.context,
                    'events': self.total, 'segments': self.ordinal,
                    'lastSegmentSHA256': self.previous, 'apExit': ap_exit,
                    'pipeEOF': eof, 'byteSequenceComplete': True,
                    'APExecutionAccepted': False, 'publicationAllowed': False}
        exclusive(self.root / 'terminal.json', canonical(terminal) + b'\n')
        self.closed = True
        return {'terminalSHA256': hashlib.sha256(canonical(terminal) + b'\n').hexdigest(),
                'status': 'DRAINED_BYTES_LOCAL_SYNC_ACKNOWLEDGED', **terminal}


def _regular(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        os.close(fd)
        raise ValueError('NOT_EXCLUSIVE_REGULAR')
    return os.fdopen(fd, 'rb')


def verify_stage(root, run, epoch, boot, *, terminal_sha256=None):
    """Cold integrity only. Trusted anchor must be supplied outside this tree."""
    root = Path(root)
    expected = {'run': run, 'epoch': epoch, 'boot': boot}
    with _regular(root / 'terminal.json') as f:
        raw = f.read(8193)
    if len(raw) > 8192:
        raise ValueError('TERMINAL_BOUND')
    terminal = json.loads(raw)
    _schema(terminal, 'terminal', expected)
    if any(terminal.get(k) != v for k, v in expected.items()):
        raise ValueError('CONTEXT')
    if terminal_sha256 is not None and hashlib.sha256(raw).hexdigest() != terminal_sha256:
        raise ValueError('EXTERNAL_ANCHOR')
    segments = terminal.get('segments')
    if type(segments) is not int or not 1 <= segments <= 100000:
        raise ValueError('SEGMENT_BOUND')
    allowed = {'terminal.json'}
    total = 0
    previous = '0' * 64
    tid = last_frame = None
    frame_events = 0
    for ordinal in range(segments):
        name = 'stage-%06d' % ordinal
        allowed.update((name + '.bin', name + '.seal.json'))
        with _regular(root / (name + '.seal.json')) as f:
            seal_raw = f.read(8193)
        if len(seal_raw) > 8192:
            raise ValueError('SEAL_BOUND')
        seal = json.loads(seal_raw)
        _schema(seal, 'seal', expected)
        h = hashlib.sha256()
        n = 0;logical_hash=hashlib.sha256()
        with _regular(root / (name + '.bin')) as f:
            line = f.readline(4097)
            if len(line) > 4096 or not line.endswith(b'\n'):
                raise ValueError('HEADER_BOUND')
            head = json.loads(line)
            _schema(head, 'header', expected)
            h.update(line)
            for obj in (head, seal):
                if any(obj.get(k) != v for k, v in expected.items()) or obj.get('ordinal') != ordinal or obj.get('startSequence') != total or obj.get('previousSegmentSHA256') != previous:
                    raise ValueError('CHAIN_CONTEXT')
            for record,physical in records(f):
                h.update(physical);logical_hash.update(record)
                seq, frame, kind, event_tid, begin, end, arg, extra, result = EVENT.unpack(record)
                if seq != total + n or kind not in KINDS or not event_tid or begin > end:
                    raise ValueError('EVENT_CHRONOLOGY')
                if tid is None:
                    tid = event_tid
                if event_tid != tid or (last_frame is not None and frame < last_frame):
                    raise ValueError('PRODUCER_OR_FRAME')
                if frame != last_frame:
                    last_frame, frame_events = frame, 0
                frame_events += 1
                if frame_events > 10:
                    raise ValueError('FRAME_EVENT_BOUND')
                n += 1
        if logical_hash.hexdigest()!=seal.get('logicalEventSHA256'):raise ValueError('APSTAGE09_LOGICAL_EXACT64_SHA')
        if h.hexdigest() != seal.get('sha256') or type(seal.get('events')) is not int or seal['events'] != n or seal.get('nextSequence') != total + n:
            raise ValueError('HASH_OR_COUNT')
        total += n
        previous = h.hexdigest()
    if {p.name for p in root.iterdir()} != allowed:
        raise ValueError('MEMBERSHIP')
    if terminal.get('events') != total or terminal.get('lastSegmentSHA256') != previous or terminal.get('pipeEOF') is not True:
        raise ValueError('TERMINAL_MISMATCH')
    return {'status': 'COMPLETE_BYTES_EXTERNAL_ANCHOR_MATCH' if terminal_sha256 else 'COMPLETE_BYTES_UNATTESTED',
            'events': total, 'segments': segments, 'apExit': terminal['apExit'],
            'publicationAllowed': False, 'APExecutionAccepted': False}
