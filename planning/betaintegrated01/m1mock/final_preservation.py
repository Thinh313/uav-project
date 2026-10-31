"""Read-only comparison of historical identities; writes only a new M1 receipt."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
CACHE = {}


def sha(path):
    path = Path(path)
    key = str(path.resolve())
    if key not in CACHE:
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
        CACHE[key] = h.hexdigest()
    return CACHE[key]


def identity(path):
    p = Path(path)
    try:
        s = p.lstat()
    except FileNotFoundError:
        return {'kind': 'MISSING'}
    out = {'kind': 'OTHER', 'mode': oct(stat.S_IMODE(s.st_mode)), 'bytes': 0, 'sha256': None}
    if p.is_symlink():
        out.update(kind='SYMLINK', linkTarget=os.readlink(p))
        if p.is_file():
            out.update(targetBytes=p.stat().st_size, sha256=sha(p))
    elif p.is_file():
        out.update(kind='REGULAR_FILE', bytes=s.st_size, sha256=sha(p), mtimeNs=str(s.st_mtime_ns))
    elif p.is_dir():
        out['kind'] = 'DIRECTORY'
    return out


def main():
    legacy_path = Path('evidence/coach01/preservation-missionbeta01-after.json')
    legacy = json.loads(legacy_path.read_text())
    drift = []
    for path, expected in legacy['observed'].items():
        actual = identity(path)
        if actual != expected:
            drift.append({'path': path, 'expected': expected, 'actual': actual})
    seals = []
    for name in ['evidence/simstability03/handoff-final01.json', 'evidence/betaintegrated01-m0/handoff-final01.json']:
        data = json.loads(Path(name).read_text())
        bad = []
        for path, expected in data['inventory'].items():
            actual = identity(path)
            ok = actual['kind'] == 'REGULAR_FILE' and actual['bytes'] == expected['bytes'] and actual['sha256'] == expected['sha256']
            if 'mode' in expected:
                mode = int(actual.get('mode', '0'), 8)
                want = expected['mode']
                want = int(want, 8) if isinstance(want, str) else want
                ok = ok and mode == want
            if not ok:
                bad.append({'path': path, 'expected': expected, 'actual': actual})
        seals.append({'path': name, 'sha256': sha(name), 'entries': len(data['inventory']), 'drift': bad})
    qa_path = 'evidence/betaintegrated01-m1mock/qa/FINAL-QA01.json'
    qa = json.loads(Path(qa_path).read_text())
    pins = [{'path': p, 'expected': h, 'actual': sha(p)} for p, h in qa['sourceSHA256'].items()]
    tracked = subprocess.check_output(['git', 'status', '--porcelain', '-uno'], text=True).splitlines()
    scratch = list(Path('native/betaintegrated01/.build').rglob('*'))
    files = [p for p in Path('evidence/betaintegrated01-m1mock').rglob('*') if p.is_file()]
    result = {
        'format': 'aeris-m1mock-final-preservation', 'atUTC': datetime.now(timezone.utc).isoformat(),
        'legacyBaseline': {'path': str(legacy_path), 'sha256': sha(legacy_path), 'entries': len(legacy['observed']),
                           'preexistingMissing': len(legacy['entryMissing']), 'drift': drift},
        'historicalSeals': seals, 'independentQAReceiptSHA256': sha(qa_path), 'sourcePins': pins,
        'trackedStatus': tracked, 'trackedMissing97Unchanged': len(tracked) == 97 and all(x.startswith(' D ') for x in tracked),
        'remainingOwnedClassOutputs': [str(p) for p in scratch if p.is_file()],
        'evidenceBeforeThisReceipt': {'files': len(files), 'bytes': sum(p.stat().st_size for p in files)},
        'freeBytes': os.statvfs('.').f_bavail * os.statvfs('.').f_frsize,
        'restorationAttempted': False, 'continuousPathPresenceClaim': False, 'ENDUREAcceptanceClaim': False,
    }
    ok = not drift and all(not s['drift'] for s in seals) and all(p['expected'] == p['actual'] for p in pins)
    ok = ok and result['trackedMissing97Unchanged'] and not result['remainingOwnedClassOutputs']
    result['status'] = 'PASS_PRESERVED_AT_FINAL_OBSERVATION' if ok else 'FAIL_PRESERVATION'
    with Path('evidence/betaintegrated01-m1mock/preservation-final01.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': result['status'], 'legacyDrift': len(drift), 'sealDrift': [len(s['drift']) for s in seals],
                      'sourcePins': len(pins), 'budget': result['evidenceBeforeThisReceipt'], 'freeGiB': result['freeBytes']/2**30}))
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
