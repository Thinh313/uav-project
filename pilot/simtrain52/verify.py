"""Read back every raw frame against the immutable original; never launch SITL."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import shutil
import sys

R = Path(__file__).resolve().parents[2]
E = R / 'evidence/simtrain52'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def enc(x):
    return json.dumps(x, separators=(',', ':'), allow_nan=False)


def main():
    output = E / ('verification' + (sys.argv[1] if len(sys.argv) > 1 else '1') + '.json')
    assert not output.exists(), 'Append a new numbered receipt'
    assert shutil.disk_usage(R).free >= 20 * 2**30 + 2 * 2**20, 'FLOOR'
    baseline = json.loads((E / 'preservation-before.json').read_text())
    changed = [{'path': p, 'actual': sha(R / p) if (R / p).is_file() else None,
                'expected': h} for p, h in baseline['files'].items()
               if not (R / p).is_file() or sha(R / p) != h]
    spec = importlib.util.spec_from_file_location('original52', R / 'evidence/sim32/source-final/pilot/sim32/physics.py')
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    fixture = json.loads((E / 'model-fixture.json').read_text())
    case_results = []
    for c in fixture['cases']:
        p = E / 'model1' / (c['id'] + '.jsonl')
        assert sha(p) == c['rawSha256'], ('RAW_SHA', c['id'])
        with p.open() as f:
            header = json.loads(next(f))
            assert header['rawAllFramesRetained'] and header['rateHz'] == 1200
            assert header['profile'] == c['profile']
            model = original.Model(header['profile'])
            assert c['samples'][0] == {'frame': -1, **model.snapshot()}
            count = 0
            for i, line in enumerate(f):
                frame = json.loads(line)
                assert frame['frame'] == i
                assert frame['pwm'] == [1000 if i < 120 else 1800] * 4 + [1000] * 12
                assert frame['sensorUtf8'] == enc(model.step(frame['pwm'], 1 / 1200)), ('SENSOR', c['id'], i)
                assert enc(frame['aux']) == enc(model.snapshot()), ('AUX', c['id'], i)
                if (i + 1) % 20 == 0:
                    assert c['samples'][(i + 1) // 20] == {'frame': i, **frame['aux']}
                count += 1
            assert count == c['rawFrames'] == 2400
            assert len(c['samples']) == 121 and c['samples'][-1]['frame'] == 2399
            case_results.append({'case': c['id'], 'sensorAndAuxBytesChecked': count,
                                 'renderSamplesChecked': 121, 'rawSha256': sha(p)})
    assert all(sha(R / p) == h for p, h in fixture['sourcePins'].items()), 'ORACLE_PINS'
    # Enumeration is read-only. Importing this helper does not run its CLI.
    spec = importlib.util.spec_from_file_location('guard52', R / 'pilot/apstream40/guard.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    endure_same = guard.endure() == baseline['endurePaths']
    contracts = json.loads((E / 'contracts3.json').read_text())
    browser = json.loads((E / 'browser4/receipt.json').read_text())
    allocated = sum(p.stat().st_blocks * 512 for base in [R / 'pilot/simtrain52', E]
                    for p in base.rglob('*') if p.is_file())
    free = shutil.disk_usage(R).free
    passed = (not changed and endure_same and allocated < baseline['budgetBytes']
              and free >= 20 * 2**30 and contracts['checks'] == 50
              and all(x['pass'] for x in contracts['results'])
              and browser['status'] == 'PASS_ART_AND_MOCK_ONLY')
    out = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'status': 'PASS_FOUNDATION_ONLY' if passed else 'FAIL',
           'review': 'Single agent build/verify phases, not independent review',
           'protectedCount': len(baseline['files']), 'changed': changed,
           'endurePathSetUnchanged': endure_same, 'endurePathCount': len(guard.endure()),
           'rawReplay': case_results, 'mockContractChecks': contracts['checks'],
           'browserChecks': browser['checks'], 'renderer': browser['metrics']['renderer'],
           'allocatedBytes': allocated, 'budgetBytes': baseline['budgetBytes'], 'freeBytes': free,
           'liveSITLStarted': (R / 'evidence/simtrain52-probe/idle01/launch.json').exists(), 'runtimeG1Accepted': False,
           'hardwareProjectorAccepted': False, 'heraFidelityAccepted': False,
           'newSoftwareSignature': False}
    with output.open('x') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in out.items() if k not in ('rawReplay', 'changed')}))
    assert passed, out['changed'][:5]


if __name__ == '__main__':
    main()
