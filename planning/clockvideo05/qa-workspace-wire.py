"""Actual app-derived wire fixture against actual helper decoder; no runtime/import side effects."""
import ast,base64,json,hashlib,datetime,copy
from pathlib import Path
src=Path('planning/clockvideo05/qa-ui.py');node=next(x for x in ast.parse(src.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='workspace_document');ns={'base64':base64,'json':json};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-decoder>','exec'),ns);decode=ns['workspace_document'];fixture=json.loads(Path('evidence/field02/clockvideo05/qa-actual-ws-contract01.json').read_text());rows=[]
def test(name,f):
 try:f();rows.append({'name':name,'status':'PASS'})
 except Exception as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
def rejects(w):
 try:decode(w)
 except Exception:return
 raise AssertionError('MISSING_WIRE_REJECTION')
def valid():assert decode(fixture['workspace'])==fixture['decodedExpected']
test('exactactualfrozenappwsfunctionshape_decodes_expectedmodelandplan',valid)
def bads():
 for v in [None,{}, {'ok':True,'pending':False,'document':fixture['decodedExpected']},{**fixture['workspace'],'pending':True},{**fixture['workspace'],'bodyBase64':None}]:rejects(v)
test('inventeddocument_missingbody_pendingwrongshape_reject',bads)
def badbase():
 for v in ['!',fixture['workspace']['bodyBase64']+'=',base64.b64encode(b'not-json').decode(),base64.b64encode(b'\xff\xfe').decode(),base64.b64encode(b'[]').decode(),base64.b64encode(b'{}').decode()]:rejects({**fixture['workspace'],'bodyBase64':v})
test('noncanonicalmalformedbase64_badUTF8_JSONarray_missingmission_reject',badbase)
def large():rejects({**fixture['workspace'],'bodyBase64':'A'*1600001})
test('declaredwirebudgetoversize_rejectbeforedecode',large)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_ACTUAL_WORKSPACE_WIRE_CONTRACT'if all(x['status']=='PASS'for x in rows)else'FAIL','source':str(src),'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'actualProducerFixture':{'path':'evidence/field02/clockvideo05/qa-actual-ws-contract01.json','sha256':hashlib.sha256(Path('evidence/field02/clockvideo05/qa-actual-ws-contract01.json').read_bytes()).hexdigest()},'rows':rows,'scope':'ActualhelperAST andactualfrozenappws-derivedshape withfakedocument; noADB/HTTP/UI/AP. Fixes priorQAfixtureintegrationmiss; doesnotreplaceactualgroundmapping/pixeltest.'}
with Path(__import__('sys').argv[1]).open('x')as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r));assert r['status'].startswith('PASS')
