"""Current-source receipts, fresh semantic replay and protected SHA verification."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'evidence/mavflight37'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

logic = json.loads((OUT / 'logic4.json').read_text())
replay = json.loads((OUT / 'replay4.json').read_text())
oracle = json.loads((OUT / 'oracle-check2.json').read_text())
before = json.loads((OUT / 'preservation-before.json').read_text())
checks = []
def check(name, condition):
    checks.append({'name': name, 'pass': bool(condition)})

check('634 latest logic checks pass', logic['status'] == 'MOCK_PASS' and logic['checkCount'] == logic['passed'] == 634)
check('logic source hashes match current bytes', all(sha(ROOT / p) == s for p, s in logic['sourceHashes'].items()))
check('41 current corpus scenarios and 6 semantic bites pass', replay['status'] == 'MOCK_PASS' and replay['replay']['caseCount'] == 41 and len(replay['bites']) == 6 and all(b['rejected'] for b in replay['bites']))
check('replay code hashes match current bytes', all(sha(ROOT / p) == s for p, s in replay['sourceHashes'].items()))
check('880 upstream parser checks pass with exact inputs/oracles', oracle['status'] == 'PASS' and oracle['checks'] == oracle['passed'] == 880 and all(sha(ROOT / p) == s for p, s in {**oracle['inputHashes'], **oracle['oracleHashes']}.items()))
snippet = """import{readFile}from'node:fs/promises';import{replayCorpus}from'./pilot/mavflight37/scenarios.mjs';import{replayCorpus as oldReplay}from'./pilot/apflight36/corpus.mjs';const fresh=await replayCorpus(JSON.parse(await readFile('evidence/mavflight37/corpus4.json','utf8')));const old=await oldReplay(JSON.parse(await readFile('evidence/apflight36/corpus6.json','utf8')));console.log(JSON.stringify({fresh,old}));"""
process = subprocess.run(['node', '--input-type=module', '-e', snippet], cwd=ROOT, capture_output=True, text=True, timeout=30)
fresh = json.loads(process.stdout) if process.returncode == 0 else None
check('fresh separate replay equals current receipt', fresh is not None and fresh['fresh'] == replay['replay'])
original = json.loads((ROOT / 'evidence/apflight36/replay6.json').read_text())['replay']
check('33 APFLIGHT36 scenarios exactly reproduce original receipt', fresh is not None and fresh['old'] == original and logic['regression']['status'] == 'MOCK_PASS')
pins = {}
for name in ['schema-generation.json', 'mapping-source-pins.json']:
    d = json.loads((OUT / name).read_text())
    pins.update(d.get('pins', d.get('files', {})))
check('all XML/generator/mapping source pins stable', all(sha(ROOT / p) == s for p, s in pins.items()))
syntax = []
for p in HERE.glob('*.mjs'):
    r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True, timeout=15)
    syntax.append({'path': str(p.relative_to(ROOT)), 'exit': r.returncode, 'stderr': r.stderr})
check('all JS syntax checks pass', all(r['exit'] == 0 for r in syntax))
forbidden = re.compile(r'node:(?:net|dgram|child_process)|\bfetch\s*\(|\bWebSocket\b|\.listen\s*\(')
check('adapter has no network/process/transport import', all(not forbidden.search((HERE / n).read_text()) for n in ['wire.mjs', 'session.mjs', 'fence.mjs', 'telemetry.mjs']))
failures = []
for rel, s in before['files'].items():
    q = ROOT / rel
    current = sha(q) if q.is_file() else None
    if current != s:
        failures.append({'path': rel, 'expectedSha256': s, 'observedSha256': current})
check('all admission protected SHA unchanged', not failures)
endure = set()
for parent in ['evidence', 'pilot', '.local', 'delivery/releases']:
    for folder in (ROOT / parent).glob('*endure*'):
        if folder.is_dir():
            endure.update(str(q.relative_to(ROOT)) for q in folder.rglob('*') if q.is_file())
for parent in ['docs', 'delivery']:
    endure.update(str(q.relative_to(ROOT)) for q in (ROOT / parent).glob('*ENDURE*') if q.is_file())
check('ENDURE inventory unchanged', endure == set(before['endureGuardPaths']))
owned = [q for d in [HERE, OUT] for q in d.rglob('*') if q.is_file()]
allocated = sum(q.stat().st_blocks * 512 for q in owned)
vfs = os.statvfs(ROOT)
free = vfs.f_bavail * vfs.f_frsize
check('allocated source/evidence below 8MiB and free above 20GiB', allocated < 8 * 2**20 and free >= 20 * 2**30)
check('no task temporary/build/cache directory created', not any(q.name in ['__pycache__', 'node_modules', 'build', 'dist'] for d in [HERE, OUT] for q in d.rglob('*') if q.is_dir()))
n = 1
while (OUT / f'verification{n}.json').exists():
    n += 1
report = {'at': datetime.now(timezone.utc).isoformat(), 'status': 'MOCK_ADAPTER_VERIFIED' if all(c['pass'] for c in checks) else 'FAIL',
          'checks': checks, 'requirementsImplemented': 8, 'requirementsTotal': 8, 'scope': 'RESTRICTED_OFFLINE_MOCK_ONLY',
          'syntax': syntax, 'protectedCount': len(before['files']), 'protectedDeltas': failures,
          'endureGuardCount': len(endure), 'allocatedBytes': allocated, 'freeBytes': free,
          'sameAgentSeparateInvocation': True, 'runtime_SITL_Emulator_APK_RealFirmware': 'NOT_CHECKED',
          'networkSent': False, 'newSignature': False, 'originalPathContinuousPresence': 'NOT_CLAIMED',
          'sourcePins': pins, 'receiptHashes': {str((OUT / name).relative_to(ROOT)): sha(OUT / name) for name in ['logic4.json', 'replay4.json', 'oracle-check2.json', 'preservation-before.json']}}
with (OUT / f'verification{n}.json').open('x') as f:
    json.dump(report, f, indent=2)
    f.write('\n')
print(json.dumps({'status': report['status'], 'checks': len(checks), 'failures': [c for c in checks if not c['pass']], 'protectedCount': report['protectedCount'], 'protectedDeltas': len(failures), 'allocatedMiB': allocated / 2**20, 'freeGiB': free / 2**30}))
assert report['status'] == 'MOCK_ADAPTER_VERIFIED'
