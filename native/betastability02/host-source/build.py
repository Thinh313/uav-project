#!/usr/bin/env python3
"""Local Xcode-only build; no dependency download and no project copy."""
import datetime, hashlib, json, os, pathlib, shutil, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent
free = shutil.disk_usage(ROOT).free
if free < 20 * 1024**3:
    raise SystemExit('NATIVE_SOURCE_BUILD_REQUIRES_20_GIB')
cache = ROOT / '.swift-cache'
command = ['xcrun', 'swiftc', '-O', str(ROOT / 'Encoder.swift'), '-o', str(ROOT / 'aeris-native-source'), '-module-cache-path', str(cache)]
for framework in ['VideoToolbox', 'CoreVideo', 'CoreMedia', 'CoreGraphics', 'CoreText']:
    command += ['-framework', framework]
result = subprocess.run(command, text=True, capture_output=True, timeout=120)
receipt = {'format': 'aeris-native-source-build', 'version': 1, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': command, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr, 'freeBeforeBytes': free, 'compiler': subprocess.run(['xcrun','swiftc','--version'],text=True,capture_output=True,timeout=20).stdout, 'sourceSha256':hashlib.sha256((ROOT/'Encoder.swift').read_bytes()).hexdigest(), 'binarySha256':hashlib.sha256((ROOT/'aeris-native-source').read_bytes()).hexdigest() if result.returncode == 0 else None, 'scope':'HOST_SYNTHETIC_ENCODER_BUILD_ONLY', 'scratchRemoved':[]}
if cache.exists():
    shutil.rmtree(cache)
    receipt['scratchRemoved'].append(str(cache))
receipt['freeAfterBytes'] = shutil.disk_usage(ROOT).free
(ROOT/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({key:receipt[key] for key in ['exit','sourceSha256','binarySha256','scratchRemoved']}))
sys.exit(result.returncode)
