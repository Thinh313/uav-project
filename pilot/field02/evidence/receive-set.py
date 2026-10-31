#!/usr/bin/env python3
"""FIELD01 delivery receiver: independent flight/capture linkage before any ledger write.

Accepts a bounded immutable folder plus expected index SHA256. No extraction,
camera authenticity, physical exposure claim, flight command or restored rights.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tarfile
import uuid
from receiver import (canonical, digest, exact, finite, identity, is_sha, parse_json,
                      regular_bytes, require, safe_dir, directory_sync, validate_package)

MAX_FLIGHT = 32 * 2**20
MAX_CAPTURE = 4 * 2**20
MAX_TOTAL = 64 * 2**20
MAX_CAPTURES = 16
MAX_LEDGER = 4 * 2**20
MAX_RECORDS = 1024
FLIGHT_TARGET = 'FIELD01_FLIGHT_RECEIVER_V1'
FLIGHT_CLI = Path(__file__).absolute().parent.parent / 'flight' / 'receive-flight.mjs'

def flight_members(data):
    # Raw headers/checksums/paths are already checked by the separately invoked Node receiver.
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
        members = archive.getmembers()
        require(1 <= len(members) <= 16 and all(m.isfile() for m in members), 'FLIGHT_REGULAR_MEMBERS')
        result = {}
        total = 0
        for member in members:
            require(re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,98}', member.name) and member.name not in result and
                    0 < member.size <= MAX_FLIGHT, 'FLIGHT_MEMBER_BOUND_OR_PATH')
            total += member.size
            require(total <= MAX_FLIGHT, 'FLIGHT_CONTENT_BOUND')
            result[member.name] = archive.extractfile(member).read(member.size + 1)
            require(len(result[member.name]) == member.size, 'FLIGHT_MEMBER_TRUNCATED')
        return result

def check_delivery(folder, index_sha256, receiver_id, sender_id):
    require(identity(receiver_id) and identity(sender_id) and is_sha(index_sha256), 'EXPECTED_IDENTITY_AND_INDEX_SHA_REQUIRED')
    root = safe_dir(folder)
    raw_index = regular_bytes(root / 'index.json', 131072)
    require(digest(raw_index) == index_sha256, 'INDEX_SHA')
    index = parse_json(raw_index)
    require(exact(index, {'schemaVersion', 'kind', 'deliveryId', 'receiverId', 'senderId', 'sourceKind', 'actualImages',
                          'authorityRestorable', 'flight', 'captures'}) and
            type(index['schemaVersion']) is int and index['schemaVersion'] == 1 and index['kind'] == 'FIELD01_DELIVERY_SET' and
            identity(index['deliveryId']) and index['receiverId'] == receiver_id and index['senderId'] == sender_id and
            index['sourceKind'] == 'SYNTHETIC' and type(index['actualImages']) is int and index['actualImages'] == 0 and
            index['authorityRestorable'] is False and canonical(index) == raw_index, 'INDEX_SCHEMA_OR_RECEIVER')
    flight = index['flight']
    require(exact(flight, {'path', 'sizeBytes', 'sha256', 'manifestSha256', 'receiverId', 'run'}) and
            flight['path'] == 'flight.tar' and type(flight['sizeBytes']) is int and 0 < flight['sizeBytes'] <= MAX_FLIGHT and
            is_sha(flight['sha256']) and is_sha(flight['manifestSha256']) and flight['receiverId'] == FLIGHT_TARGET and
            isinstance(flight['run'], str) and re.fullmatch(r's[a-f0-9]{20}', flight['run']), 'INDEX_ACCEPTED_SITL_FLIGHT')
    captures = index['captures']
    require(isinstance(captures, list) and 1 <= len(captures) <= MAX_CAPTURES, 'INDEX_CAPTURE_COUNT')
    for i, descriptor in enumerate(captures):
        require(exact(descriptor, {'path', 'sizeBytes', 'sha256'}) and descriptor['path'] == f'capture-{i+1:02}.tar' and
                type(descriptor['sizeBytes']) is int and 0 < descriptor['sizeBytes'] <= MAX_CAPTURE and is_sha(descriptor['sha256']), 'INDEX_CAPTURE_DESCRIPTOR')
    expected_paths = {'index.json', 'flight.tar'} | {c['path'] for c in captures}
    require({p.name for p in root.iterdir()} == expected_paths, 'DELIVERY_EXACT_FILE_SET')
    data = {}
    total = len(raw_index)
    for descriptor in [flight] + captures:
        path = descriptor['path']
        data[path] = regular_bytes(root / path, MAX_FLIGHT if path == 'flight.tar' else MAX_CAPTURE)
        require(len(data[path]) == descriptor['sizeBytes'] and digest(data[path]) == descriptor['sha256'], 'DELIVERY_MEMBER_SHA_OR_SIZE:' + path)
        total += len(data[path])
        require(total <= MAX_TOTAL, 'DELIVERY_TOTAL_BOUND')
    # Every capture package is checked without calling receiver.receive or changing any ledger.
    parsed = [validate_package(data[c['path']], receiver_id, sender_id) for c in captures]
    capture_ids, package_ids, transfer_ids = set(), set(), set()
    for manifest, _ in parsed:
        require(manifest['captureId'] not in capture_ids and manifest['packageId'] not in package_ids and
                manifest['transferId'] not in transfer_ids, 'DELIVERY_DUPLICATE_CAPTURE_PACKAGE_OR_TRANSFER')
        capture_ids.add(manifest['captureId'])
        package_ids.add(manifest['packageId'])
        transfer_ids.add(manifest['transferId'])
    flight_options = {'archive': str(root / 'flight.tar'), 'manifestSha256': flight['manifestSha256'],
                      'archiveSha256': flight['sha256'], 'receiverId': FLIGHT_TARGET, 'expectedRun': flight['run']}
    node = subprocess.run(['node', '--max-old-space-size=256', str(FLIGHT_CLI), json.dumps(flight_options)],
                          capture_output=True, timeout=45, check=False)
    require(len(node.stdout) <= 131072 and len(node.stderr) <= 131072 and node.returncode == 0,
            'FLIGHT_RECEIVER_REJECTED:' + node.stderr.decode('utf-8', errors='replace')[:512])
    node_receipt = parse_json(node.stdout.strip())
    require(node_receipt['status'] == 'PASS_TRANSPORT_AND_RAW_REPLAY' and
            node_receipt['acceptedSimulatorExecution'] is True and node_receipt['run'] == flight['run'] and
            node_receipt['manifestSha256'] == flight['manifestSha256'] and node_receipt['archiveSha256'] == flight['sha256'] and
            node_receipt['authorityRestorable'] is False and node_receipt['physicalFlightProven'] is False, 'FLIGHT_NOT_ACCEPTED_SIMULATOR_REPLAY')
    members = flight_members(data['flight.tar'])
    review = parse_json(members['review.json'])
    session = parse_json(members['session.json'])
    document = parse_json(members['document92.json'])
    manifest = parse_json(members['manifest.json'])
    require(manifest['accepted'] is True and review['accepted'] is True and review['mode'] == 'sitl' and
            session.get('mode', 'sitl') == 'sitl' and session['run'] == review['run'] == flight['run'] and
            document['mission']['sha256'] == review['modelSha256'] and
            document['compiled']['plan']['sha256'] == review['planSha256'] and identity(session['boot']), 'FLIGHT_DOCUMENT_SESSION_REVIEW')
    expected = {'flightRun': flight['run'], 'flightBoot': session['boot'],
                'modelSha256': review['modelSha256'], 'planSha256': review['planSha256']}
    positions = []
    for line in members['raw.jsonl'].splitlines():
        if b'FIELD01_POSITION_REFERENCE' in line:
            record = parse_json(line)
            if record['kind'] == 'FIELD01_POSITION_REFERENCE':
                positions.append(record)
    require(bool(positions), 'FLIGHT_POSITION_REFERENCE_REQUIRED')
    bindings = []
    for capture_manifest, sidecar in parsed:
        require(all(sidecar['context'][k] == value and capture_manifest['context'][k] == value and
                    capture_manifest['link'][k] == value for k, value in expected.items()), 'CAPTURE_FLIGHT_CONTEXT_LINK_MISMATCH')
        position = sidecar['position']
        require(position is not None and position['method'] == 'NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC' and
                position['hostMonoMs'] == sidecar['timing']['referenceHostMonoMs'], 'DELIVERY_NEAREST_REFERENCE_POSITION_REQUIRED')
        nearest = min(positions, key=lambda row: abs(row['data']['hostMonoMs'] - position['hostMonoMs']))
        reference = nearest['data']
        delta = abs(reference['hostMonoMs'] - position['hostMonoMs'])
        require(finite(delta) and delta <= 1500 and reference['run'] == flight['run'] and reference['boot'] == session['boot'] and
                reference['modelSha256'] == review['modelSha256'] and reference['planSha256'] == review['planSha256'] and
                all(reference[k] == position[k] for k in ('latitudeDeg', 'longitudeDeg', 'altitudeMslM', 'relativeHomeM')) and
                reference['ellipsoidAltitudeM'] is None and reference['sensorTimeUncertaintyMs'] is None and
                reference['physicalExposurePosition'] is False, 'CAPTURE_RAW_HOST_REFERENCE_MISMATCH')
        bindings.append({'captureId': sidecar['captureId'], 'packageId': capture_manifest['packageId'],
                         'transferId': capture_manifest['transferId'], 'captureKey': digest(canonical({'captureId': sidecar['captureId'], 'context': sidecar['context']})),
                         'frameId': sidecar['frameId'], 'feed': sidecar['context']['feed'], 'payloadId': sidecar['context']['payloadId'],
                         'originalSha256': capture_manifest['files'][0]['sha256'], 'sidecarSha256': capture_manifest['files'][1]['sha256'],
                         'positionMethod': position['method'], 'referenceRawRecord': nearest['n'], 'referenceRawSha256': nearest['sha256'],
                         'hostReferenceDeltaMs': delta})
    return {'status': 'VALIDATED_NO_LEDGER_WRITE', 'schemaVersion': 1, 'kind': 'FIELD01_DELIVERY_RECEIPT',
            'deliveryId': index['deliveryId'], 'indexSha256': index_sha256, 'receiverId': receiver_id, 'senderId': sender_id,
            **expected, 'flightArchiveSha256': flight['sha256'], 'flightManifestSha256': flight['manifestSha256'],
            'acceptedSimulatorExecution': True, 'captureCount': len(bindings), 'syntheticJpegCount': len(bindings),
            'captureBindings': bindings, 'flightReceipt': node_receipt, 'totalBytes': total,
            'integrity': 'EXACT_BYTES_CONTEXT_RAW_HOST_REFERENCE_AND_CANONICAL_SIMULATOR_REPLAY',
            'authenticityProven': False, 'physicalFlightProven': False, 'actualImages': 0, 'qualifiedForSurvey': False,
            'sensorExposureAccuracy': 'UNKNOWN', 'sensorClockUncertainty': 'UNKNOWN', 'authorityRestorable': False, 'restoredAuthority': 'NONE'}

def commit_receipt(receipt, state_root, folder):
    require(not Path(state_root).absolute().is_relative_to(Path(folder).absolute()), 'RECEIVER_STATE_MUST_BE_SEPARATE')
    root = safe_dir(state_root, create=True)
    lock = root / 'delivery-receiver.lock'
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    owned = os.fstat(fd)
    try:
        lock_bytes = canonical({'pid': os.getpid(), 'nonce': str(uuid.uuid4()), 'authority': 'NONE'})
        require(os.write(fd, lock_bytes) == len(lock_bytes), 'RECEIVER_LOCK_SHORT_WRITE')
        os.fsync(fd)
        directory_sync(root)
        ledger = root / 'delivery-receipts.jsonl'
        try:
            previous = regular_bytes(ledger, MAX_LEDGER)
        except FileNotFoundError:
            previous = b''
        require(not previous or previous.endswith(b'\n'), 'DELIVERY_LEDGER_TORN')
        seen_delivery, seen_index, seen_run, seen_capture, seen_transfer, seen_package = (set() for _ in range(6))
        head, seq = '0' * 64, 0
        def replay_keys(r, add):
            require(r['receiverId'] == receipt['receiverId'] and r['senderId'] == receipt['senderId'] and
                    r['restoredAuthority'] == 'NONE' and r['authorityRestorable'] is False and r['actualImages'] == 0,
                    'DELIVERY_LEDGER_IDENTITY')
            pairs = [(seen_delivery, r['deliveryId']), (seen_index, r['indexSha256']), (seen_run, r['flightRun'])]
            for binding in r['captureBindings']:
                pairs += [(seen_capture, binding['captureKey']), (seen_transfer, binding['transferId']), (seen_package, binding['packageId'])]
            for seen, key in pairs:
                require(key not in seen, 'DELIVERY_REPLAY')
            if add:
                for seen, key in pairs:
                    seen.add(key)
        for line in previous.splitlines():
            record = parse_json(line)
            require(exact(record, {'schemaVersion', 'seq', 'previousHash', 'receipt', 'hash'}) and
                    type(record['schemaVersion']) is int and record['schemaVersion'] == 1 and type(record['seq']) is int and
                    record['seq'] == seq + 1 and record['previousHash'] == head and canonical(record) == line, 'DELIVERY_LEDGER_CHAIN')
            base = {k: v for k, v in record.items() if k != 'hash'}
            require(record['hash'] == digest(canonical(base)), 'DELIVERY_LEDGER_HASH')
            replay_keys(record['receipt'], True)
            seq, head = record['seq'], record['hash']
        require(seq < MAX_RECORDS, 'DELIVERY_LEDGER_RECORD_LIMIT')
        replay_keys(receipt, False)
        accepted = {**receipt, 'status': 'ACCEPTED_DURABLE_DELIVERY'}
        base = {'schemaVersion': 1, 'seq': seq + 1, 'previousHash': head, 'receipt': accepted}
        record = {**base, 'hash': digest(canonical(base))}
        line = canonical(record) + b'\n'
        require(len(previous) + len(line) <= MAX_LEDGER, 'DELIVERY_LEDGER_BYTE_LIMIT')
        journal_fd = os.open(ledger, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        try:
            require(stat.S_ISREG(os.fstat(journal_fd).st_mode), 'DELIVERY_LEDGER_TYPE')
            view = memoryview(line)
            while view:
                n = os.write(journal_fd, view)
                require(n > 0, 'DELIVERY_LEDGER_SHORT_WRITE')
                view = view[n:]
            os.fsync(journal_fd)
            directory_sync(root)
        finally:
            os.close(journal_fd)
        return {**accepted, 'journal': {'seq': record['seq'], 'hash': record['hash']}}
    finally:
        os.close(fd)
        current = lock.lstat()
        if current.st_ino == owned.st_ino and current.st_dev == owned.st_dev and not stat.S_ISLNK(current.st_mode):
            lock.unlink()
            directory_sync(root)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder')
    parser.add_argument('--index-sha256', required=True)
    parser.add_argument('--receiver', required=True)
    parser.add_argument('--sender', required=True)
    parser.add_argument('--state')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    try:
        require(args.check_only or args.state, 'EXPLICIT_RECEIVER_STATE_REQUIRED')
        require(not args.check_only or not args.state, 'CHECK_ONLY_HAS_NO_LEDGER_STATE')
        result = check_delivery(args.folder, args.index_sha256, args.receiver, args.sender)
        if not args.check_only:
            result = commit_receipt(result, args.state, args.folder)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RecursionError, UnicodeError, tarfile.TarError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'QUARANTINE', 'reason': str(error), 'actualImages': 0, 'authorityRestorable': False, 'restoredAuthority': 'NONE'}))
        return 2

if __name__ == '__main__':
    sys.exit(main())
