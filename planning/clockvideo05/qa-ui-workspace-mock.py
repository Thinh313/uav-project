"""Actual app ws() wire shape strictdecode; no host requests."""
import importlib.util,json,base64
from pathlib import Path
spec=importlib.util.spec_from_file_location('ui05',Path(__file__).with_name('qa-ui.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);doc={'mission':{'sha256':'a'*64},'compiled':{'plan':{'sha256':'b'*64}}};ws={'ok':True,'token':'ROOT','revision':1,'bodyBase64':base64.b64encode(json.dumps(doc).encode()).decode(),'pending':False};cases=[]
assert m.workspace_document(ws)==doc;cases.append('actual_app_ws_wire_shape_decodes')
for name,value in[('pending',{**ws,'pending':True}),('malformed_base64',{**ws,'bodyBase64':'not!base64'}),('notjson',{**ws,'bodyBase64':base64.b64encode(b'bad json').decode()}),('invented_document_only',{'ok':True,'document':doc,'pending':False}),('oversize',{**ws,'bodyBase64':'a'*1600001})]:
 try:m.workspace_document(value);raise RuntimeError('MUST_FAIL')
 except(AssertionError,ValueError,UnicodeError):cases.append(name)
print(json.dumps({'status':'PASS','checks':len(cases),'cases':cases,'runtimeStarted':False,'adbCalls':0},indent=2))
