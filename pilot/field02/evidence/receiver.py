#!/usr/bin/env python3
"""Independent Python stdlib FIELD01 receiver; integrity is not authenticity.

Does not extract archives or restore sender/flight/payload authority. Retains a
durable replay journal; a stale receiver.lock requires operator investigation.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import uuid

MAX_IMAGE = 4 * 1024 * 1024
MAX_JSON = 131072
MAX_TAR = MAX_IMAGE + MAX_JSON * 2 + 4096
MAX_RECORDS = 2048
MAX_LEDGER = 4 * 1024 * 1024
REFERENCE_METHODS = {'HOST_RECEIPT_BRACKET_REFERENCE_ONLY', 'NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC'}
CONTEXT = {'gatewaySession', 'stationId', 'modelSha256', 'planSha256', 'flightRun',
           'flightBoot', 'payloadId', 'sourceRun', 'sourceBoot', 'configId', 'feed'}
LINK = {'schemaVersion', 'captureId', 'modelSha256', 'planSha256', 'flightRun',
        'flightBoot', 'payloadId', 'sourceKind', 'actualImages'}

def require(condition, code):
    if not condition:
        raise ValueError(code)

def exact(value, fields):
    return isinstance(value, dict) and set(value) == set(fields)

def identity(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}', value) is not None

def digest(value):
    return hashlib.sha256(value).hexdigest()

def is_sha(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

def parse_json(data):
    require(len(data) <= MAX_JSON, 'JSON_LIMIT')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'JSON_DUPLICATE_KEY')
            result[key] = value
        return result
    def constant(_):
        raise ValueError('JSON_NONFINITE')
    return json.loads(data.decode('utf-8', errors='strict'), object_pairs_hook=pairs, parse_constant=constant)

def regular_bytes(path, limit):
    path = Path(path).absolute()
    safe_dir(path.parent)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_size <= limit, 'FILE_TYPE_OR_LIMIT')
        chunks = []
        remaining = info.st_size + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b''.join(chunks)
        require(len(data) == info.st_size, 'FILE_CHANGED')
        return data
    finally:
        os.close(fd)

def safe_dir(path, create=False):
    path = Path(path).absolute()
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            require(create, 'DIRECTORY_MISSING')
            current.mkdir(mode=0o700)
            info = current.lstat()
        require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), 'DIRECTORY_SYMLINK_OR_TYPE')
    return path

def directory_sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def tar_members(data):
    require(len(data) <= MAX_TAR and len(data) % 512 == 0, 'TAR_LIMIT_OR_ALIGNMENT')
    result = {}
    offset = 0
    expected = ['original.jpg', 'sidecar.json', 'manifest.json']
    for index in range(3):
        header = data[offset:offset + 512]
        require(len(header) == 512 and any(header), 'TAR_MISSING_MEMBER')
        raw_name = header[:100].split(b'\0', 1)[0]
        name = raw_name.decode('ascii', 'strict')
        require(name == expected[index] and name not in result, 'TAR_ALLOWLIST_OR_ORDER')
        require(header[156:157] == b'0' and header[257:263] == b'ustar\0' and
                header[263:265] == b'00' and not any(header[345:500]), 'TAR_REGULAR_USTAR_ONLY')
        checksum_text = header[148:156].strip(b'\0 ')
        size_text = header[124:136].strip(b'\0 ')
        require(re.fullmatch(b'[0-7]+', checksum_text) and re.fullmatch(b'[0-7]+', size_text), 'TAR_OCTAL')
        computed = sum(header[:148]) + 8 * 32 + sum(header[156:])
        require(int(checksum_text, 8) == computed, 'TAR_CHECKSUM')
        length = int(size_text, 8)
        require(0 < length <= (MAX_IMAGE if index == 0 else MAX_JSON), 'TAR_MEMBER_SIZE')
        start = offset + 512
        end = start + length
        offset = start + ((length + 511) // 512) * 512
        require(offset <= len(data) and not any(data[end:offset]), 'TAR_TRUNCATION_OR_PADDING')
        result[name] = data[start:end]
    require(data[offset:] == bytes(1024), 'TAR_EXACT_THREE_MEMBERS')
    return result

def jpeg_structure(data):
    """Independent bounded marker walk; not decoding or a security certificate."""
    require(20 <= len(data) <= MAX_IMAGE and data[:2] == b'\xff\xd8' and data[-2:] == b'\xff\xd9', 'JPEG_BOUNDARY')
    pos = 2
    frame = scan = False
    for _ in range(65536):
        require(pos < len(data) and data[pos] == 255, 'JPEG_MARKER')
        while pos < len(data) and data[pos] == 255:
            pos += 1
        require(pos < len(data), 'JPEG_TRUNCATED')
        marker = data[pos]
        pos += 1
        if marker == 217:
            require(pos == len(data) and frame and scan, 'JPEG_END')
            return
        require(marker not in (0, 216) and not 208 <= marker <= 215, 'JPEG_MARKER_TYPE')
        if marker == 1:
            continue
        require(pos + 2 <= len(data), 'JPEG_LENGTH')
        length = int.from_bytes(data[pos:pos+2], 'big')
        require(length >= 2 and pos + length <= len(data), 'JPEG_LENGTH')
        if marker in (192, 193, 194):
            require(not frame and length >= 11, 'JPEG_FRAME')
            height = int.from_bytes(data[pos+3:pos+5], 'big')
            width = int.from_bytes(data[pos+5:pos+7], 'big')
            components = data[pos+7]
            require(0 < height <= 8192 and 0 < width <= 8192 and components in (1, 3, 4) and
                    length == 8 + 3 * components, 'JPEG_DIMENSIONS')
            frame = True
        elif 195 <= marker <= 207 and marker not in (196, 200, 204):
            raise ValueError('JPEG_UNSUPPORTED_FRAME')
        if marker == 218:
            require(frame and length >= 6 and length == 6 + 2 * data[pos+2], 'JPEG_SCAN')
            scan = True
            pos += length
            while pos < len(data):
                if data[pos] != 255:
                    pos += 1
                elif pos+1 < len(data) and (data[pos+1] == 0 or 208 <= data[pos+1] <= 215):
                    pos += 2
                elif pos+1 < len(data) and data[pos+1] == 255:
                    pos += 1
                else:
                    break
        else:
            pos += length
    raise ValueError('JPEG_MARKER_LIMIT')

def finite(value):
    return type(value) in (int, float) and math.isfinite(value)

def validate_sidecar(s, original, manifest):
    require(exact(s, {'schemaVersion', 'kind', 'sourceKind', 'actualImages', 'captureId', 'frameId',
                      'context', 'position', 'timing', 'file'}) and type(s['schemaVersion']) is int and s['schemaVersion'] == 1 and
            s['kind'] == 'FIELD01_SYNTHETIC_CAPTURE' and s['sourceKind'] == 'SYNTHETIC' and
            type(s['actualImages']) is int and s['actualImages'] == 0, 'SIDECAR_SCHEMA')
    context = s['context']
    require(exact(context, CONTEXT) and all(is_sha(v) if k.endswith('Sha256') else identity(v)
                                         for k, v in context.items()), 'SIDECAR_CONTEXT')
    require(s['captureId'] == manifest['captureId'] and s['frameId'] == manifest['frameId'] and
            context == manifest['context'], 'SIDECAR_MANIFEST_CONTEXT')
    require(exact(s['file'], {'name', 'mime', 'sizeBytes', 'sha256'}) and
            s['file'] == {'name': 'original.jpg', 'mime': 'image/jpeg', 'sizeBytes': len(original), 'sha256': digest(original)}, 'SIDECAR_FILE')
    timing = s['timing']
    tk = {'sourceTimestampUs', 'sourceToHostLowerMs', 'sourceToHostUpperMs', 'referenceHostMonoMs', 'method', 'physicalExposureTime'}
    require(isinstance(timing, dict) and exact(timing, tk | ({'reason'} if 'reason' in timing else set())) and
            timing['method'] == 'BOUND_SOURCE_CLOCK_TO_HOST_RECEIPT' and timing['physicalExposureTime'] == 'UNKNOWN' and
            type(timing['sourceTimestampUs']) is int and 0 <= timing['sourceTimestampUs'] <= 9007199254740991 and
            all(finite(timing[k]) for k in ('sourceToHostLowerMs', 'sourceToHostUpperMs', 'referenceHostMonoMs')) and
            timing['sourceToHostLowerMs'] <= timing['sourceToHostUpperMs'] and timing['referenceHostMonoMs'] >= 0, 'SIDECAR_TIMING')
    if 'reason' in timing:
        require(isinstance(timing['reason'], str) and 0 < len(timing['reason']) <= 512, 'SIDECAR_REASON')
    p = s['position']
    if p is None:
        require(bool(timing.get('reason')), 'UNLOCATED_REASON_REQUIRED')
    else:
        pk = {'latitudeDeg', 'longitudeDeg', 'altitudeMslM', 'relativeHomeM', 'datum', 'method',
              'qualifiedForSurvey', 'sensorTimeUncertaintyMs', 'hostMonoMs'}
        require(isinstance(p, dict) and exact(p, pk | ({'observationBefore', 'observationAfter'} & set(p))) and
                all(finite(p[k]) for k in ('latitudeDeg', 'longitudeDeg', 'altitudeMslM', 'relativeHomeM', 'hostMonoMs')) and
                abs(p['latitudeDeg']) <= 90 and abs(p['longitudeDeg']) <= 180 and p['hostMonoMs'] >= 0 and
                p['datum'] == 'MSL' and p['method'] in REFERENCE_METHODS and
                p['qualifiedForSurvey'] is False and p['sensorTimeUncertaintyMs'] is None, 'SIDECAR_REFERENCE_POSITION')
    link = manifest['link']
    require(exact(link, LINK) and type(link['schemaVersion']) is int and link['schemaVersion'] == 1 and link['captureId'] == s['captureId'] and
            link['sourceKind'] == 'SYNTHETIC' and type(link['actualImages']) is int and link['actualImages'] == 0 and
            all(link[k] == context[k] for k in ('modelSha256', 'planSha256', 'flightRun', 'flightBoot', 'payloadId')), 'LINK_CONTEXT')

def validate_package(data, receiver_id, sender_id):
    require(identity(receiver_id) and identity(sender_id), 'RECEIVER_IDENTITY')
    files = tar_members(data)
    manifest = parse_json(files['manifest.json'])
    require(exact(manifest, {'schemaVersion', 'kind', 'sourceKind', 'actualImages', 'transferId', 'senderId', 'receiverId',
                             'captureId', 'frameId', 'context', 'link', 'files', 'packageId'}) and
            type(manifest['schemaVersion']) is int and manifest['schemaVersion'] == 1 and manifest['kind'] == 'FIELD01_SYNTHETIC_HANDOFF' and
            manifest['sourceKind'] == 'SYNTHETIC' and type(manifest['actualImages']) is int and manifest['actualImages'] == 0 and
            all(identity(manifest[k]) for k in ('transferId', 'senderId', 'receiverId', 'captureId', 'frameId')) and
            is_sha(manifest['packageId']), 'MANIFEST_SCHEMA')
    require(manifest['receiverId'] == receiver_id and manifest['senderId'] == sender_id, 'RECEIVER_OR_SENDER_MISMATCH')
    base = {k: v for k, v in manifest.items() if k != 'packageId'}
    require(canonical(manifest) == files['manifest.json'] and digest(canonical(base)) == manifest['packageId'], 'MANIFEST_HASH')
    descriptors = manifest['files']
    require(isinstance(descriptors, list) and len(descriptors) == 2, 'MANIFEST_FILES')
    for descriptor, name in zip(descriptors, ('original.jpg', 'sidecar.json')):
        require(exact(descriptor, {'path', 'sizeBytes', 'sha256'}) and descriptor['path'] == name and
                type(descriptor['sizeBytes']) is int and descriptor['sizeBytes'] == len(files[name]) and
                descriptor['sha256'] == digest(files[name]), 'FILE_HASH_SIZE_OR_PATH')
    jpeg_structure(files['original.jpg'])
    sidecar = parse_json(files['sidecar.json'])
    validate_sidecar(sidecar, files['original.jpg'], manifest)
    return manifest, sidecar

def receive(package_path, state_root, receiver_id, sender_id):
    # Validate before taking durable-state lock: rejected inputs cannot consume replay state.
    raw = regular_bytes(package_path, MAX_TAR)
    manifest, sidecar = validate_package(raw, receiver_id, sender_id)
    root = safe_dir(state_root, create=True)
    lock_path = root / 'receiver.lock'
    lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    owned = os.fstat(lock_fd)
    try:
        os.write(lock_fd, canonical({'nonce': str(uuid.uuid4()), 'pid': os.getpid(), 'authority': 'NONE'}))
        os.fsync(lock_fd)
        directory_sync(root)
        journal = root / 'receipts.jsonl'
        try:
            previous = regular_bytes(journal, MAX_LEDGER)
        except FileNotFoundError:
            previous = b''
        require(not previous or previous.endswith(b'\n'), 'RECEIVER_JOURNAL_TORN')
        seen_transfers, seen_captures = set(), set()
        head, seq = '0' * 64, 0
        for line in previous.splitlines():
            record = parse_json(line)
            require(exact(record, {'schemaVersion', 'seq', 'previousHash', 'receipt', 'hash'}) and
                    type(record['schemaVersion']) is int and record['schemaVersion'] == 1 and
                    type(record['seq']) is int and record['seq'] == seq+1 and record['previousHash'] == head and
                    canonical(record) == line, 'RECEIVER_JOURNAL_CHAIN')
            base = {k: v for k, v in record.items() if k != 'hash'}
            require(record['hash'] == digest(canonical(base)), 'RECEIVER_JOURNAL_HASH')
            receipt = record['receipt']
            require(receipt['receiverId'] == receiver_id and receipt['senderId'] == sender_id and
                    receipt['authority'] == 'NONE' and receipt['actualImages'] == 0, 'RECEIVER_JOURNAL_IDENTITY')
            require(receipt['transferId'] not in seen_transfers and receipt['captureKey'] not in seen_captures, 'RECEIVER_JOURNAL_REPLAY')
            seen_transfers.add(receipt['transferId'])
            seen_captures.add(receipt['captureKey'])
            head, seq = record['hash'], record['seq']
        require(seq < MAX_RECORDS, 'RECEIVER_RECORD_QUOTA')
        capture_key = digest(canonical({'captureId': manifest['captureId'], 'context': manifest['context']}))
        require(manifest['transferId'] not in seen_transfers, 'TRANSFER_REPLAY')
        require(capture_key not in seen_captures, 'CAPTURE_REPLAY')
        receipt = {'status': 'ACCEPTED', 'receiverId': receiver_id, 'senderId': sender_id,
                   'transferId': manifest['transferId'], 'captureId': manifest['captureId'], 'captureKey': capture_key,
                   'packageId': manifest['packageId'], 'tarSha256': digest(raw),
                   'originalSha256': manifest['files'][0]['sha256'], 'sidecarSha256': manifest['files'][1]['sha256'],
                   'positionMethod': sidecar['position']['method'] if sidecar['position'] else 'UNLOCATED',
                   'qualifiedForSurvey': False, 'sensorExposureAccuracy': 'UNKNOWN', 'sensorClockUncertainty': 'UNKNOWN',
                   'integrity': 'EXACT_BYTES_AND_CONTEXT_VERIFIED', 'authenticity': 'NOT_ATTESTED', 'actualImages': 0, 'authority': 'NONE'}
        base = {'schemaVersion': 1, 'seq': seq+1, 'previousHash': head, 'receipt': receipt}
        record = {**base, 'hash': digest(canonical(base))}
        line = canonical(record) + b'\n'
        require(len(previous) + len(line) <= MAX_LEDGER, 'RECEIVER_BYTE_QUOTA')
        fd = os.open(journal, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        try:
            require(stat.S_ISREG(os.fstat(fd).st_mode), 'RECEIVER_JOURNAL_TYPE')
            view = memoryview(line)
            while view:
                written = os.write(fd, view)
                require(written > 0, 'RECEIVER_SHORT_WRITE')
                view = view[written:]
            os.fsync(fd)
            directory_sync(root)
        finally:
            os.close(fd)
        return {'receipt': receipt, 'journal': {'seq': record['seq'], 'hash': record['hash']}, 'restoredAuthority': 'NONE'}
    finally:
        os.close(lock_fd)
        current = lock_path.lstat()
        if current.st_ino == owned.st_ino and current.st_dev == owned.st_dev and not stat.S_ISLNK(current.st_mode):
            lock_path.unlink()
            directory_sync(root)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package')
    parser.add_argument('--state', required=True)
    parser.add_argument('--receiver', required=True)
    parser.add_argument('--sender', required=True)
    args = parser.parse_args()
    try:
        result = receive(args.package, args.state, args.receiver, args.sender)
        print(json.dumps(result, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, RecursionError, UnicodeError) as error:
        print(json.dumps({'status': 'QUARANTINE', 'reason': str(error), 'actualImages': 0, 'authority': 'NONE'}))
        return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
