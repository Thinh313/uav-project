#!/usr/bin/env python3
"""Apply unchanged kernel bites with applicability recorded for this non-rollup domain.

The transfer bites CLI assumes every domain publishes a distribution. This project
does not: rollup_field is null and no coverage is published, so denominator bite is N/A.
The original failing full-suite receipt is retained; no kernel code is modified.
"""
import copy, json, shutil, sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'02_Refinery_MethodBox'))
import bites
import refinery

domain=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'research/ragas-baseline'
cfg,claims,registry,aggregates,canonical=refinery.run_pipeline(str(domain))
results=[]
for name,fn in bites.BITES:
    if name=='DISTRIBUTION_NO_DENOMINATOR' and cfg.get('rollup_field') is None:
        results.append({'check':name,'status':'N/A','reason':'No distribution/coverage is published; rollup_field=null'})
        continue
    tmp,dst=bites._copy(domain)
    try:
        if name=='CAPTURE_MISSING':
            # Transfer bite deletes first *.html, which can be an unclaimed extra capture.
            # Target a claim's actual snapshot (including tagged source .txt) instead.
            first=json.loads((dst/'claims.jsonl').read_text().splitlines()[0])
            (dst/'snapshots'/first['capture']['snapshot']).unlink()
            bit,last=bites._expect_bite(dst,'CAPTURE_MISSING')
        else:
            bit,last=fn(dst)
    finally:shutil.rmtree(tmp)
    results.append({'check':name,'status':'N/A' if bit is None else 'PASS' if bit else 'FAIL','reason':last})
for name,target in [('fabricated_cell',copy.deepcopy(registry)),('fabricated_aggregate',copy.deepcopy(aggregates))]:
    if name=='fabricated_cell':
        victim=next((cell for record in target.values() for cell in record['fields'].values() if cell.get('value') is not None),None)
        if victim is None:
            raise RuntimeError('No sourced cell to challenge')
        victim['value']='invented'
        args=(cfg,claims,target,aggregates)
    else:
        target['n']=999
        args=(cfg,claims,registry,target)
    try:refinery.audit(*args)
    except refinery.GateError:
        results.append({'check':name,'status':'PASS','reason':'Auditor rejected tampered derived output'})
    else:results.append({'check':name,'status':'FAIL','reason':'Auditor did not reject derived output'})
print(json.dumps({'results':results,'scope':'Applicable injected faults; no semantic source validation'},ensure_ascii=False,indent=2))
sys.exit(1 if any(r['status']=='FAIL' for r in results) else 0)
