"""Upstream Python decoding of actual JS serializer bytes; no IO/runtime beyond local files."""
import sys,json,importlib.util
from pathlib import Path
from guard import R,H,E,sha,append
sys.dont_write_bytecode=True
path=R/sys.argv[1];input=json.loads(path.read_text());schema=json.loads((H/'definitions.mjs').read_text().split('export const DEFINITIONS=',1)[1].rstrip().rstrip(';'))
modules={}
for version in [1,2]:
 spec=importlib.util.spec_from_file_location('apstream40_verify_oracle'+str(version),H/f'oracle-v{version}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);modules[version]=m
results=[]
for v in input['vectors']:
 try:
  decoded=modules[v['version']].MAVLink(None).parse_char(bytes.fromhex(v['rawHex'])).to_dict();decoded.pop('mavpackettype',None);fields={}
  for f in schema[str(v['id'])]['fields']:
   if f['name'] in decoded:
    value=decoded[f['name']]
    if f['type']=='char' and isinstance(value,bytes):value=value.decode('ascii')
    if '64' in f['type']:value=[str(n) for n in value] if isinstance(value,list) else str(value)
   else:
    zero='' if f['type']=='char' else '0' if '64' in f['type'] else 0
    value=[zero]*f['array'] if f['array'] and f['type']!='char' else zero
   fields[f['name']]=value
  results.append({'id':v['id'],'version':v['version'],'pattern':v['pattern'],'pass':fields==v['expected']})
 except Exception as e:results.append({'id':v['id'],'version':v['version'],'pass':False,'error':str(e)})
obj={'status':'PASS' if results and all(r['pass'] for r in results) else 'FAIL','checks':len(results),'results':results,'inputPath':str(path.relative_to(R)),'inputSha256':sha(path),'oracleHashes':{str((H/f'oracle-v{v}.py').relative_to(R)):sha(H/f'oracle-v{v}.py') for v in [1,2]},'runtimeOrSigning':False}
p=append('oracle-check',obj);print(json.dumps({'receipt':str(p),'status':obj['status'],'checks':len(results),'failures':sum(not r['pass'] for r in results)}));assert obj['status']=='PASS'
