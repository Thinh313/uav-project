"""Run original-byte peer fixtures on the selected new source, own scratch only.
External ADB/TCP are injected; real OS pipes/budget writes, no Android claim.
"""
from pathlib import Path
import hashlib,importlib.util,io,json,sys,unittest
REPO=Path(__file__).resolve().parents[3]
SOURCE=REPO/'planning/betasim-integrated01/runtime/source'
OUT=REPO/'evidence/betasim-integrated01/qa'
sys.path[:0]=[str(SOURCE),str(REPO)]
import aeris_runtime
assert Path(aeris_runtime.__file__).resolve().is_relative_to(SOURCE)
path=REPO/'evidence/runtime-transport15/task/builder/test_full15.py'
spec=importlib.util.spec_from_file_location('readonly_original_stream_fixture',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.HERE=OUT
before={str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest()for p in SOURCE.rglob('*.py')}
stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(m.Full15))
after={str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest()for p in SOURCE.rglob('*.py')}
number=1
while(OUT/('stream-regression-%02d.json'%number)).exists():number+=1
v={'format':'aeris-betasim-independent-source-stream-regression','version':1,'status':'PASS_HOST_MOCK_NOT_ANDROID'if r.wasSuccessful()and before==after else'FAIL','groups':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'sourceChangedDuringReview':before!=after,'originalFixtureSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'fixtureAuthorsReused':True,'QAExecutionIndependent':True,'originalTestOutput':stream.getvalue(),'sourceSHA256':before,'actualAndroid':False,'actualADB':False,'actualTCPPeer':False,'scratchRemoved':not(OUT/'full-mock-scratch').exists()}
(OUT/('stream-regression-%02d.json'%number)).write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({k:v[k]for k in('status','groups','failures','errors','sourceChangedDuringReview','scratchRemoved')}));print(stream.getvalue());raise SystemExit(not r.wasSuccessful())
