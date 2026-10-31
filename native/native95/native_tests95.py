from pathlib import Path
import subprocess,json,hashlib,base64,shutil
R=Path(__file__).resolve().parents[2];N=R/'native/native95';E=R/'evidence/native95';W=N/'.host95';W.mkdir(exist_ok=True);J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');src=N/'src/vn/rtr/aeris/native95';names=['Json','DraftStore','RawJournal95','Dialect95','Profile95','WireGate95','DirectTransport95','GateReplay95Test','NativeJournal95Test'];subprocess.run([str(J/'javac'),'--release','8','-d',str(W),*[str(src/(n+'.java'))for n in names]],check=True,capture_output=True)
def run(cls,*args):return subprocess.run([str(J/'java'),'-cp',str(W),'vn.rtr.aeris.native95.'+cls,*map(str,args)],capture_output=True,text=True)
p=run('GateReplay95Test',E/'qualified94-stream.tsv');assert p.returncode==0,p.stderr;result={'positive':json.loads(p.stdout),'negative':[]}
for case in json.loads((E/'negative-cases.json').read_text()):
 p=run('GateReplay95Test',R/case['path']);assert p.returncode!=0 and case['expect']in p.stderr,(case,p.stdout,p.stderr);result['negative'].append({'name':case['name'],'expected':case['expect'],'pass':True,'detail':p.stderr})
p=run('NativeJournal95Test',E/'journal95-fixture');assert p.returncode==0,p.stderr;result['journal']=json.loads(p.stdout)
rows=(E/'journal95-fixture/raw.jsonl').read_bytes().splitlines();previous=''
for i,line in enumerate(rows):
 d=json.loads(line);body=line.rsplit(b',"sha256":',1)[0]+b'}';assert d['n']==i+1 and d['previous']==previous and hashlib.sha256(body).hexdigest()==d['sha256']and base64.b64decode(d['dataBase64'])==bytes([0,1,2,255]);previous=d['sha256']
result.update(status='PASS',checkCount=1+len(result['negative'])+result['journal']['checks']+1,shaReplay='PASS');(E/'native-tests95.json').open('x').write(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='negative'}))
