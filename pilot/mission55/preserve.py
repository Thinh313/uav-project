#!/usr/bin/env python3
"""Observe inherited frozen pins; never repair, mutate or launch anything."""
import datetime, hashlib, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evidence/mission55'
OUT.mkdir(exist_ok=True)
pins={}
for name in ['evidence/simtrain53/preservation-before.json','evidence/simtrain53/artifact-fingerprints.json','research/ragas54/artifact-fingerprints.json']:
    path=ROOT/name
    pins.update(json.loads(path.read_text())['files'])
    pins[name]=hashlib.sha256(path.read_bytes()).hexdigest()
failures=[]
for name,expected in pins.items():
    try:
        h=hashlib.sha256()
        with (ROOT/name).open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        if h.hexdigest()!=expected:failures.append({'path':name,'expected':expected,'actual':h.hexdigest()})
    except OSError as e:failures.append({'path':name,'error':str(e)})
fs=os.statvfs(ROOT);free=fs.f_bavail*fs.f_frsize
phase=sys.argv[1]
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':phase,'checked':len(pins),
         'failures':failures,'freeBytes':free,'floorBytes':20*1024**3,'floorPass':free>=20*1024**3,
         'readOnly':True,'scope':'Inherited pin observations only; no continuous-presence or endurance acceptance claim'}
target=OUT/f'preservation-{phase}.json'
if target.exists():raise SystemExit('Receipt already exists')
target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='failures'}|{'failures':len(failures)}))
sys.exit(bool(failures) or not receipt['floorPass'])
