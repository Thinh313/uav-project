#!/usr/bin/env python3
"""Read-only: no slot mkdir, ledger, SDK/device query or runtime actor."""
from pathlib import Path
import argparse,json,os,sys
REPO=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--candidate-sha',required=True);p.add_argument('--spec',required=True);p.add_argument('--slot',choices=('s01',),required=True);a=p.parse_args()
candidate=Path(a.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(REPO),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=a.candidate_sha);sys.path[:0]=[str(candidate/'source'),str(REPO)]
from aeris_runtime.preview10 import preview
result=preview(candidate,a.candidate_sha,REPO/'evidence/writerstage15'/a.slot,REPO/'planning/writerstage15',Path(a.spec))
print(json.dumps(result,sort_keys=True));raise SystemExit(0 if all(result[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted'))else 2)
