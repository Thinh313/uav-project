"""Adds exported-window causality to independent sample arithmetic checker."""
from pathlib import Path
import importlib.util,json,argparse
spec=importlib.util.spec_from_file_location('qa_report_base',Path(__file__).with_name('qa-report.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def check(report,targets):
 r=base.check(report,targets);a=report['measurementStartMs'];b=report['measurementEndMs'];assert base.finite(a)and base.finite(b)and b>=a and abs((b-a)-report['durationMs'])<1e-6
 assert all(a<=s['displayMs']<=b for s in report['samples'])
 r['measurementStartMs']=a;r['measurementEndMs']=b;r['scope']='Same-browser software source→canvas proxy. Exported window bounds/duration/sample display membership checked. Foreground and source/image correlation remain browser-self-report/source-bound; no sensor/GPU/glass-to-glass measurement.';return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('report',type=Path);p.add_argument('--profile',type=Path,default=Path('media/big02/profile01.json'));a=p.parse_args();print(json.dumps(check(json.loads(a.report.read_text()),json.loads(a.profile.read_text())['targets']),indent=2))
