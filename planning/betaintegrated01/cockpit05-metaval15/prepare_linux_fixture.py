"""Bounded explicit metadata fixtures. No Android, AP, Docker or sockets."""
from pathlib import Path
from importlib import import_module
import argparse,json,hashlib
N='planning.betaintegrated01.cockpit05-metaval15'
def main():
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();out=Path(args.output).resolve();C=import_module(N+'.flight.contract');S=import_module(N+'.adapter.state_binding')
 if not out.is_relative_to(C.E/'host')or out.exists():raise ValueError('NEW_E15_HOST_FIXTURE_DIRECTORY_ONLY')
 out.mkdir();(out/'raw').mkdir();S.prepare_fresh_case_state(C.ROOT,out/'state','metaval15-linux-probe')
 cfg=C.build_config(C.ROOT,'nominal','metaval15-linux-probe','epoch','boot',out/'raw','metaval15-linux-probe',maximum_seconds=180)
 old=json.loads((C.ROOT/'evidence/betaintegrated01-cockpit05-clockterm14/actual-short01/raw/run-config.json').read_bytes());S.prepare_fresh_case_state(C.ROOT,out/'old-state',old['caseID'])
 (out/'run-config.json').write_text(json.dumps(cfg,separators=(',',':'))+'\n');(out/'old-run-config.json').write_text(json.dumps(old,separators=(',',':'))+'\n')
 pins={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()for p in out.rglob('*')if p.is_file()};raw=json.dumps({'format':'aeris-metaval15-linux-fixture','version':1,'sourceOnlyMetadataNotFlight':True,'sourcePins':C.policy().source_binding(),'fixturePins':pins,'newHostPolicySHA256':cfg['externalRecordingPolicy']['amendmentSHA256'],'nativeReceiptSHA256':C.EXPECTED_BUILD_RECEIPT_SHA256},indent=2).encode();assert len(raw)<=131072
 (out/'fixture.json').write_bytes(raw);assert sum(p.stat().st_size for p in out.rglob('*')if p.is_file())<=262144;print(json.dumps({'fixture':str(out),'fixtureSHA256':hashlib.sha256(raw).hexdigest(),'hostPolicySHA256':cfg['externalRecordingPolicy']['amendmentSHA256'],'APStarted':False,'deviceCommands':False}))
if __name__=='__main__':main()
