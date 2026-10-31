"""Owned emulator-only test fixture with external storage/process guard.

Never starts AP or dispatches a MAVLink/aircraft command. No physical device.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

R = Path(__file__).resolve().parents[3]
os.chdir(R)
E = R / 'evidence/betaintegrated01-m1control02/emulator01'
W = R / '.local/betaintegrated01/android'
SDK = R / '.local/native86-android/sdk'
ADB = '/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
STOP = False


def halt(*_):
    global STOP
    STOP = True


def put(name, value):
    with (E / name).open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def free():
    s = os.statvfs(R)
    return s.f_bavail * s.f_frsize


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def power_observation():
    raw=subprocess.check_output(['pmset','-g','batt'],text=True)
    ac="'AC Power'"in raw; m=re.search(r'(\d+)%',raw)
    percent=int(m.group(1))if m else None
    if not ac and percent is None:raise RuntimeError('UNKNOWN_POWER_STATE')
    return {'raw':raw,'ACObserved':ac,'batteryPercent':percent,'userAuthorizedBattery':True}


def main():
    E.mkdir(exist_ok=False)
    assert free() >= 20 * 2**30, 'ENTRY20GiB'
    power=power_observation();assert power['ACObserved']or power['batteryPercent']>=30,'POWER_ENTRY_REFUSED'
    devices = subprocess.check_output([ADB, 'devices'], text=True)
    assert 'emulator-5582' not in devices, 'SERIAL_ALREADY_OWNED'
    for port in [5582, 5583]:
        with socket.socket() as s:
            s.bind(('127.0.0.1', port))
    profile = json.loads((R / 'evidence/betaintegrated01-m0/target-profile01.json').read_text())
    verified = {}
    for key in ['emulator', 'systemImage', 'systemImageProperties', 'adb']:
        row = profile['artifactFiles'][key]
        observed = sha(row['path'])
        assert observed == row['sha256'], key + '_DRIFT'
        verified[key] = {'path': row['path'], 'sha256': observed}
    avd = W / 'avd/aeris-beta-m1.avd'
    template = (R / '.local/field02/avd/aeris-field02.avd/config.ini').read_text()
    config = template.replace('avd.name = aeris-field02', 'avd.name = aeris-beta-m1').replace('hw.cpu.ncore = 2', 'hw.cpu.ncore = 4')
    if sys.argv[1:] == ['02']:
        assert (avd / 'config.ini').read_text() == config, 'OWNED_AVD_CONFIG_CHANGED'
        assert (avd.parent / 'aeris-beta-m1.ini').read_text() == 'avd.ini.encoding=UTF-8\npath=' + str(avd) + '\ntarget=android-33\n'
    else:
        avd.mkdir(parents=True, exist_ok=False)
        (avd / 'config.ini').open('x').write(config)
        (avd.parent / 'aeris-beta-m1.ini').open('x').write('avd.ini.encoding=UTF-8\npath=' + str(avd) + '\ntarget=android-33\n')
    env = dict(os.environ, ANDROID_AVD_HOME=str(avd.parent), ANDROID_USER_HOME=str(W / 'user'), ANDROID_HOME=str(SDK), ANDROID_SDK_ROOT=str(SDK))
    argv = [str(SDK / 'emulator/emulator'), '-avd', 'aeris-beta-m1', '-port', '5582', '-no-window',
            '-accel', 'on', '-gpu', 'host', '-no-snapshot', '-no-boot-anim', '-camera-back', 'none', '-camera-front', 'none',
            '-memory', '2048', '-cores', '4', '-no-metrics']
    put('prelaunch.json', {'atUTC': datetime.now(timezone.utc).isoformat(), 'argv': argv, 'verifiedPrerequisites': verified,
                          'AVDConfigSHA256': sha(avd / 'config.ini'), 'newOwnedAVD': str(avd), 'previousAVDWritten': False,
                          'freeBytes': free(), 'scope': 'ANDROID_BOOTSTRAP_ONLY_NO_AP_NO_GRANT',
                          'powerPolicy':power,'powerPolicySHA256':sha(R/'evidence/betaintegrated01-m1control02/power-policy01.json'),'maxWallSeconds': 2400, 'guardFloorGiB': 10, 'reserveMiB': 256, 'forecastSeconds': 15})
    log = (E / 'console.txt').open('xb')
    process = subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    stamp = subprocess.check_output(['ps', '-p', str(process.pid), '-o', 'lstart='], text=True).strip()
    put('launch.json', {'pid': process.pid, 'processStart': stamp, 'processGroup': process.pid, 'argv': argv,
                        'atUTC': datetime.now(timezone.utc).isoformat(), 'serial': 'emulator-5582'})
    started = time.monotonic()
    last_time = started
    last_free = free()
    last_wall = time.time()
    reason = 'OWNER_STOP'
    booted = False
    try:
        with (E / 'guard.jsonl').open('x') as stream:
            while not STOP and process.poll() is None:
                now = time.monotonic()
                wall = time.time()
                wall_mono_gap=(wall-last_wall)-(now-last_time)
                available = free()
                rate = max(0, (last_free - available) / max(.001, now - last_time))
                forecast = available - rate * 15
                power = power_observation()
                row = {'monotonicNs': time.monotonic_ns(), 'freeBytes': available, 'forecastFreeBytes': forecast,
                       'ACObserved': power['ACObserved'], 'batteryPercent':power['batteryPercent'], 'userAuthorizedBattery':True, 'elapsedSeconds': now - started, 'bootObserved': booted,'wallMonoGapSeconds':wall_mono_gap}
                stream.write(json.dumps(row) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
                if abs(wall_mono_gap)>2:
                    reason='SUSPEND_OR_WALL_CLOCK_JUMP_NOT_ACCEPTED'
                    break
                if forecast < 10 * 2**30 + 256 * 2**20:
                    reason = 'FLOOR_OR_FORECAST'
                    break
                if not row['ACObserved']and row['batteryPercent']<=20:
                    reason = 'AUTHORIZED_BATTERY_LOW20'
                    break
                if (E / 'console.txt').stat().st_size > 16 * 2**20:
                    reason = 'CONSOLE_BUDGET'
                    break
                if now - started > 2400:
                    reason = 'WALL_BUDGET'
                    break
                if not booted:
                    q = subprocess.run([ADB, '-s', 'emulator-5582', 'shell', 'getprop', 'sys.boot_completed'], capture_output=True, text=True, timeout=8)
                    if q.returncode == 0 and q.stdout.strip() == '1':
                        booted = True
                        put('boot-observed.json', {'atUTC': datetime.now(timezone.utc).isoformat(), 'elapsedSeconds': now - started,
                                                   'sys.boot_completed': '1', 'serial': 'emulator-5582'})
                    elif now - started > 240:
                        reason = 'BOOT_TIMEOUT'
                        break
                last_time, last_free, last_wall = now, available, wall
                time.sleep(2)
            if process.poll() is not None:
                reason = 'PROCESS_EXIT'
    finally:
        if process.poll() is None:
            actual = subprocess.run(['ps', '-p', str(process.pid), '-o', 'lstart='], capture_output=True, text=True).stdout.strip()
            if actual == stamp and os.getpgid(process.pid) == process.pid:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=25)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
        log.close()
        put('closure.json', {'atUTC': datetime.now(timezone.utc).isoformat(), 'reason': reason, 'emulatorExit': process.poll(),
                             'bootObserved': booted, 'elapsedSeconds': time.monotonic() - started, 'freeBytes': free(),
                             'APStartedByThisFixture': False, 'flightCommandSent': False})


if __name__ == '__main__':
    if sys.argv[1:] == ['02']:
        E = R / 'evidence/betaintegrated01-m1control02/emulator01'
    else:
        assert not sys.argv[1:], 'ONLY_ATTEMPT01_OR02'
    signal.signal(signal.SIGTERM, halt)
    signal.signal(signal.SIGINT, halt)
    main()
