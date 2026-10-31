"""Contractor-only immutable-input comparison; no repair or product execution."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from datetime import datetime, timezone

R = Path(__file__).resolve().parents[3]
os.chdir(R)
cache = {}


def sha(p):
    k = str(Path(p).resolve())
    if k not in cache:
        h = hashlib.sha256()
        with Path(p).open('rb') as f:
            for b in iter(lambda: f.read(1048576), b''):
                h.update(b)
        cache[k] = h.hexdigest()
    return cache[k]


def identity(n):
    p = Path(n)
    try:
        s = p.lstat()
    except FileNotFoundError:
        return {'kind': 'MISSING'}
    d = {'kind': 'DIRECTORY' if p.is_dir() else 'REGULAR_FILE', 'mode': oct(stat.S_IMODE(s.st_mode)), 'bytes': 0, 'sha256': None}
    if p.is_symlink():
        d.update(kind='SYMLINK', linkTarget=os.readlink(p))
        if p.is_file():
            d.update(targetBytes=p.stat().st_size, sha256=sha(p))
    elif p.is_file():
        d.update(bytes=s.st_size, sha256=sha(p), mtimeNs=str(s.st_mtime_ns))
    return d


def main():
    tag = sys.argv[1]
    assert tag in ['before01', 'after01', 'after02', 'after03']
    legacy = 'evidence/coach01/preservation-missionbeta01-after.json'
    d = json.loads(Path(legacy).read_text())
    drift = [{'path': p, 'expected': v, 'actual': identity(p)} for p, v in d['observed'].items() if identity(p) != v]
    seals = []
    for n in ['evidence/simstability03/handoff-final01.json', 'evidence/betaintegrated01-m0/handoff-final01.json',
              'evidence/betaintegrated01-m1mock/handoff-final01.json', 'evidence/betaintegrated01-m1runtime/handoff-final01.json', 'evidence/betaintegrated01-m1control01/handoff-final01.json', 'evidence/betaintegrated01-m1control02/handoff-final01.json']:
        data = json.loads(Path(n).read_text())
        bad = []
        for p, expected in data['inventory'].items():
            actual = identity(p)
            if expected.get('kind') == 'SYMLINK_FIXTURE':
                ok = actual['kind'] == 'SYMLINK' and actual['linkTarget'] == expected['linkTarget']
            else:
                ok = actual['kind'] == 'REGULAR_FILE' and actual['bytes'] == expected['bytes'] and actual['sha256'] == expected['sha256']
                if 'mode' in expected:
                    want = int(expected['mode'], 8) if isinstance(expected['mode'], str) else expected['mode']
                    ok = ok and int(actual.get('mode', '0'), 8) == want
            if not ok:
                bad.append({'path': p, 'expected': expected, 'actual': actual})
        seals.append({'path': n, 'sha256': sha(n), 'entries': len(data['inventory']), 'drift': bad})
    tracked = subprocess.check_output(['git', 'status', '--porcelain', '-uno'], text=True).splitlines()
    ok = not drift and all(not s['drift'] for s in seals) and len(tracked) == 97 and all(s.startswith(' D ') for s in tracked)
    result = {'atUTC': datetime.now(timezone.utc).isoformat(), 'status': 'PASS_BOUNDARY_OBSERVATION' if ok else 'FAIL',
              'legacy': {'path': legacy, 'sha256': sha(legacy), 'entries': len(d['observed']), 'preexistingMissing': len(d['entryMissing']), 'drift': drift},
              'seals': seals, 'trackedStatus': tracked, 'trackedMissing97Only': len(tracked) == 97 and all(s.startswith(' D ') for s in tracked),
              'restorationAttempted': False, 'continuousPathPresenceClaim': False, 'ENDUREAcceptanceClaim': False}
    with Path('evidence/betaintegrated01-m1cockpit03/preservation-' + tag + '.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': result['status'], 'legacyDrift': len(drift), 'sealDrifts': [len(s['drift']) for s in seals]}))
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
