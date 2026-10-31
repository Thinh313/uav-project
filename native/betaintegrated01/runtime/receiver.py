"""Cold native raw receiver. Integrity is not dispatch execution or source trust."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(raw):
    def pairs(rows):
        out = {}
        for k, v in rows:
            if k in out:
                raise ValueError('DUPLICATE_KEY')
            out[k] = v
        return out
    return json.loads(raw, object_pairs_hook=pairs)


def integer(value, low=0):
    return type(value) is int and low <= value < 2**63


def verify(root, run, epoch, expected_commit=None):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('RUN_DIRECTORY')
    entries = list(root.iterdir())
    if len(entries) > 8194 or any(p.is_symlink() or not p.is_file() for p in entries):
        raise ValueError('REGULAR_FLAT_MEMBERSHIP_REQUIRED')
    if any(not re.fullmatch(r'(writer\.lock|session\.json|segment-\d{6}\.jsonl|seal-\d{6}\.json)', p.name) for p in entries):
        raise ValueError('UNEXPECTED_MEMBER')
    files = sorted(root.glob('segment-*.jsonl'))
    if len(files) > 4096:
        raise ValueError('SEGMENT_BOUND')
    head = prior_seal = ''
    sequence = 0
    last_time = -1
    kinds = {}
    pending_intent = None
    closed = False
    complete = True
    reason = None
    raw_bytes = 0
    records = 0
    try:
        for segment, path in enumerate(files):
            if path.name != f'segment-{segment:06d}.jsonl' or path.stat().st_size > 8*2**20:
                raise ValueError('SEGMENT_ORDER_SIZE')
            raw = path.read_bytes()
            if not raw.endswith(b'\n'):
                raise ValueError('PARTIAL_RECORD')
            first = sequence+1
            lines = raw.splitlines(keepends=True)
            for index, line in enumerate(lines):
                if len(line) > 16384:
                    raise ValueError('ROW_BOUND')
                row = parse(line)
                required = {'format','version','run','epoch','segment','n','previous','monotonicNs','kind','base64','sha256'}
                if set(row) != required or row['format'] != 'aeris-native-record' or type(row['version']) is not int or row['version'] != 1 or row['run'] != run or row['epoch'] != epoch:
                    raise ValueError('RECORD_SCHEMA_CONTEXT')
                if not integer(row['n'], 1) or row['n'] != sequence+1 or not integer(row['segment']) or row['segment'] != segment or row['previous'] != head or not integer(row['monotonicNs']) or row['monotonicNs'] < last_time:
                    raise ValueError('RECORD_SEQUENCE_CLOCK')
                if not isinstance(row['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
                    raise ValueError('RECORD_SHA_TYPE')
                body = line.rstrip(b'\n')
                suffix = (',"sha256":"'+row['sha256']+'"}').encode()
                if not body.endswith(suffix) or sha(body[:-len(suffix)]+b'}') != row['sha256']:
                    raise ValueError('RECORD_SHA')
                if not isinstance(row['kind'], str) or not re.fullmatch('[A-Z][A-Z0-9_]{0,47}', row['kind']):
                    raise ValueError('RECORD_KIND')
                data = base64.b64decode(row['base64'], validate=True)
                if len(data)>8192:
                    raise ValueError('PAYLOAD_BOUND')
                if closed:
                    raise ValueError('ROW_AFTER_CLOSE')
                kind = row['kind']
                if index == 0:
                    h = parse(data)
                    if kind != 'HEADER' or set(h) != {'format','version','segment','previousSeal'} or h['format'] != 'aeris-native-segments' or type(h['version']) is not int or h['version'] != 1 or type(h['segment']) is not int or h['segment'] != segment or h['previousSeal'] != prior_seal:
                        raise ValueError('SEGMENT_HEADER')
                elif kind == 'HEADER':
                    raise ValueError('DUPLICATE_HEADER')
                if kind == 'TX_INTENT':
                    if pending_intent is not None:
                        raise ValueError('OVERLAPPING_TX_INTENT')
                    pending_intent = data
                elif kind == 'TX_WRITTEN':
                    if pending_intent != data:
                        raise ValueError('TX_WRITTEN_WITHOUT_EXACT_INTENT')
                    pending_intent = None
                elif kind == 'TX_UNKNOWN':
                    u = parse(data)
                    if set(u) != {'wireSHA256','reason'} or type(u['reason']) is not str or not re.fullmatch('[A-Za-z0-9_]{1,128}', u['reason']) or pending_intent is None or u.get('wireSHA256') != sha(pending_intent):
                        raise ValueError('UNKNOWN_WITHOUT_INTENT')
                    pending_intent = None
                    complete = False
                    reason = 'UNKNOWN_TRANSMISSION'
                elif kind == 'SESSION_CLOSE':
                    if pending_intent is not None:
                        raise ValueError('CLOSE_WITH_PENDING_INTENT')
                    close = parse(data)
                    if set(close) != {'reason','authorityRestorable','aircraftExecutionAccepted'} or type(close['reason']) is not str or not re.fullmatch('[A-Z0-9_:-]{1,128}', close['reason']) or close['authorityRestorable'] is not False or close['aircraftExecutionAccepted'] is not False:
                        raise ValueError('CLOSE_PAYLOAD_SCHEMA')
                    closed = True
                sequence = row['n'];last_time = row['monotonicNs'];head = row['sha256']
                records += 1;kinds[kind] = kinds.get(kind, 0)+1
            seal_path = root/f'seal-{segment:06d}.json'
            if not seal_path.is_file():
                raise ValueError('UNSEALED_SEGMENT')
            seal_raw = seal_path.read_bytes();seal = parse(seal_raw)
            expected = {'format':'aeris-native-seal','version':1,'run':run,'epoch':epoch,'segment':segment,'file':path.name,'bytes':len(raw),'sha256':sha(raw),'first':first,'last':sequence,'head':head,'previousSeal':prior_seal}
            if set(seal) != set(expected) or any(type(seal[k]) is not type(v) or seal[k] != v for k,v in expected.items()):
                raise ValueError('SEGMENT_SEAL')
            prior_seal = sha(seal_raw);raw_bytes += len(raw)
        session_path = root/'session.json'
        if not session_path.is_file() or not closed or not files:
            raise ValueError('SESSION_UNCLOSED')
        session_raw = session_path.read_bytes();session = parse(session_raw)
        expected = {'format':'aeris-native-session','version':1,'run':run,'epoch':epoch,'segments':len(files),'records':sequence,'head':head,'lastSeal':prior_seal,'authorityRestorable':False,'publicationAllowed':False}
        if set(session) != set(expected) or any(type(session[k]) is not type(v) or session[k] != v for k,v in expected.items()):
            raise ValueError('SESSION_BINDING')
        expected_names = {'writer.lock','session.json'} | {f'segment-{i:06d}.jsonl' for i in range(len(files))} | {f'seal-{i:06d}.json' for i in range(len(files))}
        if {p.name for p in entries} != expected_names:
            raise ValueError('EXACT_MEMBERSHIP')
        commit = sha(session_raw)
        if expected_commit is not None and expected_commit != commit:
            raise ValueError('EXTERNAL_COMMIT_MISMATCH')
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as ex:
        complete = False
        reason = str(ex)
        commit = None
    return {'format':'aeris-native-cold-verification','version':1,'run':run,'epoch':epoch,
            'status':('COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH' if expected_commit else 'COMPLETE_BYTES_UNATTESTED') if complete else 'INCOMPLETE_OR_INVALID_RECORDING',
            'byteSequenceComplete':complete,'writerCommitAttested':bool(complete and expected_commit),
            'records':records,'segmentsObserved':len(files),'rawBytes':raw_bytes,'kinds':kinds,
            'pendingIntent':pending_intent is not None,'sessionSHA256':commit,'reason':reason,
            'publicationAllowed':False,'authorityRestorable':False,'APExecutionAccepted':False}


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('root');p.add_argument('run');p.add_argument('epoch');p.add_argument('--expected-commit')
    a = p.parse_args();result = verify(a.root,a.run,a.epoch,a.expected_commit)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['byteSequenceComplete'] else 2)
