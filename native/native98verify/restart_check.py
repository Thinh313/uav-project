from ui98 import *
owned();tag=sys.argv[1];assert tag in ['process','coldboot'];out=E/('restart-'+tag);out.mkdir()
def pull():
 raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(raw))as t:files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
 return raw,files
before,files=pull();(out/'before.tar').open('xb').write(before);keep={k:hashlib.sha256(v).hexdigest()for k,v in files.items()if k.startswith(('./direct95/','./workspaces/'))};assert keep
if tag=='coldboot':assert keep==json.loads((E/'restart-process/verification.json').read_text())['keptSHA256'],'COLD_BOOT_STORAGE_DRIFT'
claim=json.loads((E/'runs/s098d5c41e36548be9071/launch.json').read_text());assert(E/'runs/s098d5c41e36548be9071/closure.json').exists();q={k:claim[k]for k in ['run','containerId','pid','startedAt','binarySha256']};adb('shell','am','force-stop',P);adb('shell','am','start','-n',P+'/.ShellActivity','--es','source87','direct','--es','owned95',"'"+json.dumps(q,separators=(',',':'))+"'");time.sleep(1);last();tap94('open-workspace83');tap94('Workspace');time.sleep(5);capture('restart-'+tag+'-no-restored-authority');journal('restart-'+tag+'-workspace');after,files2=pull();(out/'after.tar').open('xb').write(after);assert keep=={k:hashlib.sha256(v).hexdigest()for k,v in files2.items()if k.startswith(('./direct95/','./workspaces/'))},'PERSISTENCE_DRIFT'
# Inspect every raw tail and preserved review independently; no new live generation.
runs=[]
for name,b in files2.items():
 if name.startswith('./direct95/')and name.endswith('/raw.jsonl'):
  rows=[json.loads(line)for line in b.splitlines()];assert rows[-1]['kind']=='CLOSED';runs.append(name)
ui=[len(b)for name,b in files2.items()if name.startswith('./ui96/')and name.endswith('.jsonl')];assert len(ui)<=16 and max(ui)<=2*2**20 and sum(ui)<=16*2**20
r={'status':'PASS','tag':tag,'scope':'Activity process force-stop/relaunch on owned emulator; coldboot outer receipt separately required'if tag=='process'else'After owned emulator coldboot, then explicit Activity relaunch','crossBootBytesVerified':tag=='coldboot','preservedRawAndWorkspaceFiles':len(keep),'closedRuns':runs,'noNewRawGeneration':True,'noControlAuthorityRestored':True,'uiGenerations':len(ui),'uiMaxBytes':max(ui),'uiTotalBytes':sum(ui),'keptSHA256':keep};(out/'verification.json').open('x').write(json.dumps(r,indent=2));print(json.dumps({k:r[k]for k in ['status','tag','preservedRawAndWorkspaceFiles','uiGenerations']}))
