"""Root QA orchestration only: preserve interrupted pre-launch journal and use frozen controller.
No imported timing anchors, source changes, runtime quota changes or automatic inputs.
"""
from pathlib import Path
import hashlib, importlib.util, json, os, socket, sys

P = Path(__file__).resolve().parent
R = P.parents[1]
E = R / 'evidence/beta06/generation02'
prior = E / 'root-controller02.jsonl'
receipt = json.loads((E / 'root-interruption-recovery03.json').read_text())
assert hashlib.sha256(prior.read_bytes()).hexdigest() == receipt['priorJournalSHA256']
rows = [json.loads(s) for s in prior.read_text().splitlines()]
assert all(v['event'] in {'NEW_PROCESS_NO_RESTORED_ANCHORS', 'EXPLICIT_COMMAND', 'COMMAND_REFUSED_NO_AUTOMATIC_RETRY'} for v in rows)
for name in ['host-app02', 'host-app02-restart', 'host-console1.txt', 'android-attempt02.json', 'android-launch-permit02.json']:
    assert not (E / name).exists(), 'PRIOR_RUNTIME_OR_ANCHOR_UNCERTAIN_NO_RESTART'
for port in [8872, 8873, 5582, 5583, 5972]:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', port))
spec = importlib.util.spec_from_file_location('frozen_root_controller', P / 'qa-root-controller.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with (E / 'root-controller-resume03.jsonl').open('x') as journal:
    ctl = module.Controller('02', journal=journal)
    ctl.seen.update(v['commandId'] for v in rows if v['event'] == 'EXPLICIT_COMMAND')
    ctl.emit('NEW_PROCESS_NO_RESTORED_ANCHORS', plan=module.plan(), priorPrelaunchJournalSHA256=receipt['priorJournalSHA256'], recoveryReceiptSHA256=hashlib.sha256((E / 'root-interruption-recovery03.json').read_bytes()).hexdigest())
    try:
        for line in sys.stdin:
            try:
                assert len(line) <= 8192
                value = ctl.command(json.loads(line))
                print(json.dumps({'ok': True, 'result': value}, default=str), flush=True)
            except BaseException as error:
                ctl.emit('COMMAND_REFUSED_NO_AUTOMATIC_RETRY', error=str(error))
                print(json.dumps({'ok': False, 'error': str(error)}), flush=True)
    finally:
        ctl.close()
