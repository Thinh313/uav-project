#!/usr/bin/env python3
"""Read-only comparison against inherited pins; writes only this research increment."""
import datetime, hashlib, json, sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
scope = Path(__file__).resolve().parent
pins = {}
for name in ['evidence/simtrain53/preservation-before.json', 'evidence/simtrain53/artifact-fingerprints.json']:
    p = root/name
    data = json.loads(p.read_text())
    pins.update(data['files'])
    pins[name] = hashlib.sha256(p.read_bytes()).hexdigest()
failures = []
for name, expected in pins.items():
    p = root/name
    try:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024), b''):h.update(chunk)
        actual = h.hexdigest()
    except OSError as e:
        failures.append({'path':name,'expected':expected,'error':str(e)});continue
    if actual != expected:failures.append({'path':name,'expected':expected,'actual':actual})
report = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checked':len(pins),
          'endurePaths':sum('endure' in name.lower() for name in pins), 'failures':failures,
          'read_only':True, 'scope':'Inherited SIMTRAIN53 pins, no continuous-presence or ENDURE acceptance claim'}
out = scope / ('preservation-' + (sys.argv[1] if len(sys.argv)>1 else 'before') + '.json')
if out.exists(): raise SystemExit('Refusing to overwrite receipt')
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='failures'}|{'failureCount':len(failures)}))
sys.exit(bool(failures))
