"""One scoped object replacement/relink using pinned cached ARM build inputs."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess

R = Path(__file__).resolve().parents[4]
OLD = R / 'runtime/sim32-instrument01-build/ardupilot'
NEW = R / 'runtime/betaintegrated01'
E = R / 'evidence/betaintegrated01-m1runtime/host'
IMAGE = 'rtr-aeris-sim32-trace-builder:local'
IMAGE_ID = 'sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert shutil.disk_usage(R).free >= 20 * 2**30
    output = NEW / 'dist/arducopter-m1-stagepipe'
    assert not output.exists()
    assert subprocess.check_output(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'], text=True).strip() == IMAGE_ID
    objects = sorted((OLD / 'build/sitl/ArduCopter').glob('*.o'))
    assert len(objects) == 74
    inputs = [*objects, OLD / 'build/sitl/lib/libArduCopter_libs.a', OLD / 'build/sitl/liblittlefs.a',
              OLD / 'build/sitl/bin/arducopter', OLD / 'libraries/SITL/SIM_StageTrace.cpp',
              OLD / 'libraries/SITL/SIM_JSON.cpp', OLD / 'libraries/SITL/SIM_Aircraft.cpp',
              NEW / 'src/SIM_StageTrace.cpp']
    pins = {str(p.relative_to(R)): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in inputs}
    script = '''set -eu
g++ -std=gnu++11 -O3 -fno-exceptions -fdata-sections -ffunction-sections -Wall -Wextra -Werror -c /src/SIM_StageTrace.cpp -o /new/.build/SIM_StageTrace.cpp.0.o
cp /old/build/sitl/lib/libArduCopter_libs.a /new/.build/libArduCopter_libs.a
ar r /new/.build/libArduCopter_libs.a /new/.build/SIM_StageTrace.cpp.0.o
g++ -fno-exceptions -Wl,--gc-sections -pthread -Wl,--wrap,malloc '''
    script += ' '.join('/old/' + str(p.relative_to(OLD)) for p in objects)
    script += ' -Wl,--start-group /new/.build/libArduCopter_libs.a /old/build/sitl/liblittlefs.a -Wl,--end-group -lm -lrt -o /new/dist/arducopter-m1-stagepipe\n'
    cmd = ['docker', 'run', '--rm', '--name', 'aeris-betaintegrated01-compiler', '--pull', 'never', '--network', 'none',
           '--platform', 'linux/arm64', '--cpus', '2', '--memory', '512m', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
           '-v', str(OLD) + ':/old:ro', '-v', str(NEW) + ':/new', '-v', str(NEW / 'src') + ':/src:ro', IMAGE, '/bin/sh', '-c', script]
    receipt = {'atUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'image': IMAGE, 'imageId': IMAGE_ID,
               'command': cmd, 'inputs': pins, 'hostPeakForecastBytes': 100 * 2**20,
               'containerPeakForecastBytes': 100 * 2**20, 'APLaunches': 0, 'wholeSourceCopy': False}
    (E / 'ap-build-admission01.json').open('x').write(json.dumps(receipt, indent=2) + '\n')
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    (E / 'ap-build-log01.txt').open('x').write(result.stdout + result.stderr)
    assert result.returncode == 0, 'Compiler/relink failed, see retained log'
    assert output.stat().st_size < 16 * 2**20
    assert all(sha(R / p) == item['sha256'] for p, item in pins.items())
    final = {'status': 'NEW_ARM_ARTIFACT_BUILT_NOT_RUNTIME_QUALIFIED', 'path': str(output.relative_to(R)),
             'sha256': sha(output), 'bytes': output.stat().st_size, 'baselineAP': pins[str((OLD / 'build/sitl/bin/arducopter').relative_to(R))],
             'onlyReplacementObject': str((NEW / 'src/SIM_StageTrace.cpp').relative_to(R)),
             'inputsUnchanged': True, 'APLaunches': 0, 'modelOrPacerSourceChanged': False}
    (E / 'ap-build01.json').open('x').write(json.dumps(final, indent=2) + '\n')
    for p in (NEW / '.build').iterdir():
        if p.name in ('SIM_StageTrace.cpp.0.o', 'libArduCopter_libs.a'):
            p.unlink()
    print(json.dumps(final))


if __name__ == '__main__':
    main()
