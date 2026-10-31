"""Independent cold native receiver adversarial corpus, never opens a socket."""
from pathlib import Path
import base64,hashlib,importlib.util,json,os,shutil,sys,datetime
R=Path(__file__).resolve().parents[4]
SOURCE=R/'native/betaintegrated01/runtime/receiver.py'
spec=importlib.util.spec_from_file_location('native_cold_independent',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
enc=lambda d:json.dumps(d,separators=(',',':')).encode()
out=R/('evidence/betaintegrated01-m1runtime/qa/native-cold'+sys.argv[1]);out.mkdir();before=sha(SOURCE);results=[]
normal=R/'evidence/betaintegrated01-m1runtime/qa/native-adapter01/fixtures/normal'

def result(name,path,expected):
    try:
        v=m.verify(path,'normal','epoch01')
        ok=v['byteSequenceComplete']==expected and v['publicationAllowed'] is False
        results.append({'id':name,'pass':ok,'verdict':v})
    except Exception as e:
        results.append({'id':name,'pass':not expected,'rejection':type(e).__name__+':'+str(e)})

def clone(name,skip=None):
    p=out/name;shutil.copytree(normal,p,ignore=(lambda p,n:[skip] if skip in n else []) if skip else None);return p

def reseal_last(p,mutate):
    files=sorted(p.glob('segment-*.jsonl'));file=files[-1];rows=[json.loads(l) for l in file.read_text().splitlines()];previous=rows[0]['previous']
    for row in rows:
        mutate(row)
        row['previous']=previous;row.pop('sha256');body=enc(row);previous=hashlib.sha256(body).hexdigest();row['sha256']=previous
    raw=b''.join(enc(row)+b'\n' for row in rows);file.write_bytes(raw)
    seal_path=p/file.name.replace('segment-','seal-').replace('.jsonl','.json');seal=json.loads(seal_path.read_bytes());seal['bytes']=len(raw);seal['sha256']=sha(file);seal['head']=previous;seal_raw=enc(seal);seal_path.write_bytes(seal_raw)
    session=json.loads((p/'session.json').read_bytes());session['head']=previous;session['lastSeal']=hashlib.sha256(seal_raw).hexdigest();(p/'session.json').write_bytes(enc(session))

result('BASELINE_UNATTESTED',normal,True)
p=clone('missing-seal','seal-000000.json');result('MISSING_SEAL',p,False)
p=clone('missing-segment','segment-000000.jsonl');result('MISSING_SEGMENT',p,False)
p=clone('appended');f=sorted(p.glob('segment-*.jsonl'))[-1];f.open('ab').write(b'{}\n');result('APPENDED_RAW',p,False)
p=clone('foreign-context');result('FOREIGN_CONTEXT',p,True)
v=m.verify(p,'foreign','epoch01');results[-1]={'id':'FOREIGN_CONTEXT','pass':v['byteSequenceComplete'] is False,'verdict':v}
p=clone('symlink','segment-000000.jsonl');(p/'segment-000000.jsonl').symlink_to(normal/'segment-000000.jsonl');result('SYMLINK',p,False)
p=clone('session-bool');s=json.loads((p/'session.json').read_bytes());s['version']=True;(p/'session.json').write_bytes(enc(s));result('SESSION_VERSION_BOOL',p,False)
p=clone('close-false-claims')
def mutate(row):
    if row['kind']=='SESSION_CLOSE':row['base64']=base64.b64encode(enc({'reason':'QA_CLOSE','authorityRestorable':True,'aircraftExecutionAccepted':True})).decode()
reseal_last(p,mutate);result('COHERENT_CLOSE_FALSE_CLAIMS',p,False)
p=clone('close-malformed')
def mutate(row):
    if row['kind']=='SESSION_CLOSE':row['base64']=base64.b64encode(b'not-json').decode()
reseal_last(p,mutate);result('COHERENT_CLOSE_MALFORMED',p,False)
anchor=sha(normal/'session.json');v=m.verify(p,'normal','epoch01',anchor);results.append({'id':'EXTERNAL_ANCHOR_REJECTS_CHANGED_BYTES','pass':v['byteSequenceComplete'] is False,'verdict':v})
data={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':sha(SOURCE),'sourceChanged':before!=sha(SOURCE),'results':results,'status':'PASS' if all(r['pass'] for r in results) else 'FAIL','APAndroidRuntimeLaunches':0,'scope':'Cold integrity/schema only; no source authentication or runtime dispatch proven'}
(out/'results.json').open('x').write(json.dumps(data,indent=2)+'\n');print(json.dumps({'status':data['status'],'checks':len(results),'failed':[r['id'] for r in results if not r['pass']],'sourceChanged':data['sourceChanged']}))
