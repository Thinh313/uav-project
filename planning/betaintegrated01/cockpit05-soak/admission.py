"""Read-only actual-host readiness probe. Never launches an emulator or AP.

A successful observation expires immediately: each launcher must independently
check live entry and perform its own real guard priming before starting.
"""
from pathlib import Path
import datetime, hashlib, importlib, json, os, re, shutil, subprocess, sys, time

R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R))
from pilot.betaintegrated01.runtime02.journal.admission import DiskGuard


def main(tag):
    assert re.fullmatch(r'entry\d{2}', tag)
    E = R / 'evidence/betaintegrated01-cockpit05-soak'
    target = E / (tag + '.json')
    assert not target.exists()
    contract_module = importlib.import_module('planning.betaintegrated01.cockpit05-soak.host.contract')
    contract = contract_module.build_input_contract()
    raw = subprocess.check_output(['pmset', '-g', 'batt'], text=True, timeout=3)
    match = re.search(r'(\d+)%', raw)
    ac = "'AC Power'" in raw
    percent = int(match[1]) if match else None
    power_ok = ac or (percent is not None and percent >= 30)
    free = shutil.disk_usage(R).free
    budget = contract_module.task_budget(free)
    prime = None
    error = None
    if budget['admitted'] and power_ok:
        try:
            guard = DiskGuard(R)
            prime = guard.prime()
            guard.check()
            free = shutil.disk_usage(R).free
            budget = contract_module.task_budget(free)
        except Exception as exc:
            error = repr(exc)
    ready = budget['admitted'] and power_ok and prime is not None and error is None
    result = {
        'atUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'observedHostNs': time.monotonic_ns(),
        'status': 'OBSERVED_READY_NOT_A_LAUNCH_PERMIT' if ready else 'NOT_ADMITTED_NO_RUNTIME_STARTED',
        'reason': 'ENTRY_BELOW20_GIB' if not budget['admitted'] else 'POWER_ENTRY30_OR_AC' if not power_ok else error,
        'actualFreeBytes': free, 'actualFreeGiB': free / 2**30, 'budget': budget,
        'power': {'raw': raw, 'ACObserved': ac, 'batteryPercent': percent,
                  'userAuthorizedBattery30Entry20Stop': True},
        'actualPrime': prime, 'primeError': error,
        'selectedAPK_SHA256': contract['apkSHA256'], 'selectedSourceSHA256': contract['APKSourceSHA256'],
        'originalRuntimeInputsVerified': contract['originalRuntimeInputs'],
        'selectedAPKInputsVerified': contract['selectedAPKInputs'],
        'installedAPKIdentityObserved': False,
        'sourceSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'runtimeStarts': 0, 'actualThirtyMinuteAccepted': False,
        'expiresImmediatelyRecheckAtEachActualLaunch': True,
    }
    with target.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    print(json.dumps({'status': result['status'], 'reason': result['reason'], 'freeGiB': result['actualFreeGiB']}))


if __name__ == '__main__':
    main(sys.argv[1])
