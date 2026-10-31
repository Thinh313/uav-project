#!/usr/bin/env python3
"""Read-only semantic CLI. Output JSON to stdout; no endpoint, upload or signing."""
import argparse,json,sys
from pathlib import Path
from semantic import compare_plans,ContractError
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('command',choices=['compare'])
p.add_argument('before',type=Path);p.add_argument('after',type=Path)
args=p.parse_args()
try:
    def read(path):
        with path.open('rb') as f:raw=f.read(262145)
        if len(raw)>262144:raise ContractError('INPUT_LIMIT_256K')
        try:return raw.decode('utf-8')
        except UnicodeDecodeError as e:raise ContractError('UTF8_INVALID') from e
    result=compare_plans(read(args.before),read(args.after))
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    sys.exit({'EQUAL_DECLARED_SCOPE':0,'DIFFERENT':2,'REVIEW_REQUIRED':3}[result['verdict']])
except (ContractError,OSError) as e:
    print(json.dumps({'verdict':'REJECTED','error':str(e),'flightReady':False},ensure_ascii=False));sys.exit(4)
