"""Read-only Contractor preservation observation; writes only this task's receipt."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, os, sys

R = Path(__file__).resolve().parents[3]
os.chdir(R)
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('frozen04_boundary_reader', R / 'planning/betaintegrated01/m1cockpit04/check_boundary.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
E = R / 'evidence/betaintegrated01-cockpit05-entry10'


def main(tag):
    assert tag in ('before01', 'after01', 'after02')
    legacy_path = 'evidence/coach01/preservation-missionbeta01-after.json'
    legacy = json.loads((R / legacy_path).read_text())
    legacy_drift = [{'path': p, 'expected': v, 'actual': base.identity(p)}
                    for p, v in legacy['observed'].items() if base.identity(p) != v]
    seals = []
    for name in [
        'evidence/simstability03/handoff-final01.json',
        'evidence/betaintegrated01-m0/handoff-final01.json',
        'evidence/betaintegrated01-m1mock/handoff-final01.json',
        'evidence/betaintegrated01-m1runtime/handoff-final01.json',
        'evidence/betaintegrated01-m1control01/handoff-final01.json',
        'evidence/betaintegrated01-m1control02/handoff-final01.json',
        'evidence/betaintegrated01-m1cockpit03/handoff-final01.json',
        'evidence/betaintegrated01-m1cockpit04/handoff-final02.json',
        'evidence/betaintegrated01-cockpit05-native/handoff-final.json',
        'evidence/betaintegrated01-cockpit05-soak/handoff-final.json',
    ]:
        data = json.loads((R / name).read_text())
        drift = []
        for path, expected in data['inventory'].items():
            actual = base.identity(path)
            if expected.get('kind') == 'SYMLINK_FIXTURE':
                ok = actual['kind'] == 'SYMLINK' and actual['linkTarget'] == expected['linkTarget']
            else:
                ok = actual['kind'] == 'REGULAR_FILE' and actual['bytes'] == expected['bytes'] and actual['sha256'] == expected['sha256']
                if 'mode' in expected:
                    want = int(expected['mode'], 8) if isinstance(expected['mode'], str) else expected['mode']
                    ok = ok and int(actual.get('mode', '0'), 8) == want
            if not ok:
                drift.append({'path': path, 'expected': expected, 'actual': actual})
        seals.append({'path': name, 'sha256': base.sha(name), 'entries': len(data['inventory']), 'drift': drift})
    result = {
        'atUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'PASS_CURRENT_PRESERVATION' if not legacy_drift and all(not s['drift'] for s in seals) else 'FAIL',
        'legacy': {'path': legacy_path, 'sha256': base.sha(legacy_path), 'entries': len(legacy['observed']),
                   'preexistingMissing': len(legacy['entryMissing']), 'drift': legacy_drift},
        'seals': seals, 'restorationAttempted': False, 'continuousPathPresenceClaim': False,
        'ENDUREAcceptanceClaim': False, 'productionSigning': False,
    }
    with (E / ('preservation-' + tag + '.json')).open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({'status': result['status'], 'legacyEntries': result['legacy']['entries'],
                      'legacyDrift': len(legacy_drift), 'sealEntries': [s['entries'] for s in seals],
                      'sealDrifts': [len(s['drift']) for s in seals]}))
    return 0 if result['status'].startswith('PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1]))
