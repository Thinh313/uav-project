#!/usr/bin/env python3
"""Read-only: no slot mkdir, ledger, SDK/device query or runtime actor."""
from pathlib import Path
import argparse,json,os,sys
REPO=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--candidate-sha',required=True);p.add_argument('--spec',required=True);p.add_argument('--slot',choices=('r301','r302','m101','m102','m201','m202','g101','g102','g201','g202','g203','g204','g301','g302','g303','g304','g401','g402'),required=True);p.add_argument('--seconds',type=int,choices=(180,760),default=180);a=p.parse_args()
candidate=Path(a.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(REPO),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=a.candidate_sha);sys.path[:0]=[str(candidate/'source'),str(REPO)]
from aeris_runtime.preview10 import preview
result=preview(candidate,a.candidate_sha,REPO/'evidence/betarc01'/a.slot,REPO/'planning/betarc01',Path(a.spec),seconds=a.seconds)
print(json.dumps(result,sort_keys=True));raise SystemExit(0 if all(result[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted'))else 2)
