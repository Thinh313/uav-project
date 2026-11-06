#!/usr/bin/env python3
"""Check one raw private-files TAR against the team m803 continuation pin. Read-only; prints the proof.
Run from the tree root. Exit 1 with the contract error if any check fails."""
from pathlib import Path
import argparse,importlib.util,json,sys
B=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('continuation_l16',B/'continuation_l16.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
ap=argparse.ArgumentParser();ap.add_argument('--tar',required=True);ap.add_argument('--tar-sha',required=True);ap.add_argument('--pin',default=str(B/'m803-continuation-pin.json'));ap.add_argument('--pin-sha',required=True);a=ap.parse_args()
try:proof=c.verify(a.tar,a.tar_sha,a.pin,a.pin_sha,repo=Path.cwd())
except ValueError as e:print(json.dumps({'status':'CONTINUATION_CONTRACT_REFUSED','error':str(e)}));sys.exit(1)
sys.stdout.write(json.dumps(proof,sort_keys=True)+'\n')
