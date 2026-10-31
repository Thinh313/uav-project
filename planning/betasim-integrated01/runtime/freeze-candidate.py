#!/usr/bin/env python3
"""Root-only freeze after independent source HOLD gate; no build or actors."""
from pathlib import Path
import argparse,json,os,sys
P=Path(__file__).resolve();R=P.parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(P.parent/'source'),str(R)]
from aeris_runtime.candidate import freeze
p=argparse.ArgumentParser();p.add_argument('--native-receipt',required=True);p.add_argument('--qa-gate',required=True);p.add_argument('--label',required=True);a=p.parse_args()
print(json.dumps(freeze(R/'evidence/betasim-integrated01/candidates',Path(a.native_receipt),Path(a.qa_gate),label=a.label)))
