"""Independent AP-stage cold-schema adversarial cases; no AP process/socket."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from datetime import datetime, timezone

R = Path(__file__).resolve().parents[4]
SOURCE = R / 'pilot/betaintegrated01/runtime/ap_stage.py'
spec = importlib.util.spec_from_file_location('apstage_independent_qa', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    out = R / ('evidence/betaintegrated01-m1runtime/qa/ap-stage-schema' + sys.argv[1])
    out.mkdir()
    before = sha(SOURCE)
    normal = out / 'normal'
    d = mod.StageDrainer(normal, 'run01', 'epoch01', 'boot01', events_per_chunk=1, max_events=10)
    d.feed(mod.EVENT.pack(0, 0, 10, 1234, 1, 2, 1200, 0, 0))
    anchor = d.finish(ap_exit=0, eof=True)['terminalSHA256']
    baseline = mod.verify_stage(normal, 'run01', 'epoch01', 'boot01', terminal_sha256=anchor)
    results = [{'id': 'BASELINE', 'pass': baseline['events'] == 1 and baseline['publicationAllowed'] is False}]
    mutations = [
        ('TERMINAL_FORMAT', 'terminal.json', 'format', 'foreign'),
        ('TERMINAL_VERSION', 'terminal.json', 'version', False),
        ('TERMINAL_EVENTS_BOOL', 'terminal.json', 'events', True),
        ('TERMINAL_APEXIT_STRING', 'terminal.json', 'apExit', '0'),
        ('TERMINAL_COMPLETE_FALSE', 'terminal.json', 'byteSequenceComplete', False),
        ('SEAL_FORMAT', 'stage-000000.seal.json', 'format', 'foreign'),
        ('SEAL_VERSION', 'stage-000000.seal.json', 'version', False),
        ('SEAL_ORDINAL_BOOL', 'stage-000000.seal.json', 'ordinal', False),
        ('SEAL_NEXTSEQ_BOOL', 'stage-000000.seal.json', 'nextSequence', True),
    ]
    for name, file, key, value in mutations:
        tree = out / name
        shutil.copytree(normal, tree)
        obj = json.loads((tree / file).read_bytes())
        obj[key] = value
        (tree / file).write_bytes(mod.canonical(obj) + b'\n')
        try:
            verdict = mod.verify_stage(tree, 'run01', 'epoch01', 'boot01')
            results.append({'id': name, 'pass': False, 'unexpectedVerdict': verdict})
        except Exception as exc:
            results.append({'id': name, 'pass': True, 'rejection': type(exc).__name__ + ':' + str(exc)})
    result = {'atUTC': datetime.now(timezone.utc).isoformat(), 'sourceBefore': before, 'sourceAfter': sha(SOURCE),
              'status': 'PASS' if all(r['pass'] for r in results) else 'FAIL_SCHEMA', 'results': results,
              'scope': 'Independent malformed-schema negative fixtures; no AP/Android/runtime launches; anchor omitted deliberately to test schema not signer authentication'}
    (out / 'results.json').open('x').write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'checks': len(results), 'failed': [r['id'] for r in results if not r['pass']], 'sourceChanged': before != result['sourceAfter']}))


if __name__ == '__main__':
    main()
